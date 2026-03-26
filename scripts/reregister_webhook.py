"""
Registra el webhook de ClickUp y actualiza el secret en GCP de forma atómica.

Flujo:
  1. Elimina webhooks existentes en estado FAILING o SUSPENDED (slate limpio)
  2. Registra el webhook en ClickUp → obtiene el nuevo secret
  3. Sube el nuevo secret a Secret Manager → obtiene número de versión exacto
  4. Fuerza nueva revisión de Cloud Run con la versión EXACTA del secret
     (no `:latest` para evitar race condition con propagación de Secret Manager)
  5. Espera a que la nueva revisión esté lista (polling)
  6. Verifica estado del webhook

Uso:
  python3 -m scripts.reregister_webhook

Requisitos:
  - CLICKUP_API_TOKEN en .env
  - gcloud autenticado con permisos sobre el proyecto ortega-473114
"""

import os
import sys
import time
import subprocess
import httpx
from dotenv import load_dotenv
from google.cloud import secretmanager

load_dotenv()

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
CLICKUP_API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
CLICKUP_LIST_ID   = "901403238634"
CLICKUP_TEAM_ID   = "31633845"
WEBHOOK_URL       = "https://nexus-legal-api-223080314602.us-central1.run.app/webhooks/clickup"

GCP_PROJECT_ID    = "ortega-473114"
SECRET_NAME       = "CLICKUP_WEBHOOK_SECRET"
CLOUD_RUN_SERVICE = "nexus-legal-api"
CLOUD_RUN_REGION  = "us-central1"

HEADERS = {
    "Authorization": CLICKUP_API_TOKEN,
    "Content-Type":  "application/json",
}


# ---------------------------------------------------------------------------
# Paso 0: Eliminar webhooks con fallos acumulados
# ---------------------------------------------------------------------------
def delete_failing_webhooks() -> None:
    """
    Elimina webhooks apuntando a nuestro endpoint que estén en estado
    FAILING o SUSPENDED, para empezar con un slate limpio.
    """
    print("\n[0/4] Limpiando webhooks con fallos...")

    url      = f"https://api.clickup.com/api/v2/team/{CLICKUP_TEAM_ID}/webhook"
    response = httpx.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    webhooks = response.json().get("webhooks", [])

    deleted = 0
    for wh in webhooks:
        endpoint = wh.get("endpoint", "")
        health   = wh.get("health", {}).get("status", "").upper()
        wh_id    = wh.get("id")

        if endpoint != WEBHOOK_URL:
            continue

        if health in ("FAILING", "SUSPENDED", "FAILED"):
            del_response = httpx.delete(
                f"https://api.clickup.com/api/v2/webhook/{wh_id}",
                headers=HEADERS,
                timeout=15,
            )
            if del_response.status_code in (200, 204):
                print(f"    🗑️  Eliminado webhook {wh_id} (estado: {health})")
                deleted += 1
            else:
                print(f"    ⚠️  No se pudo eliminar {wh_id}: HTTP {del_response.status_code}")

    if deleted == 0:
        print("    ℹ️  No había webhooks en estado FAILING/SUSPENDED para eliminar.")


# ---------------------------------------------------------------------------
# Paso 1: Registrar webhook en ClickUp
# ---------------------------------------------------------------------------
def register_webhook() -> tuple[str, str]:
    """
    Registra el webhook y devuelve (webhook_id, webhook_secret).
    """
    print("\n[1/4] Registrando webhook en ClickUp...")

    url     = f"https://api.clickup.com/api/v2/team/{CLICKUP_TEAM_ID}/webhook"
    payload = {
        "endpoint": WEBHOOK_URL,
        "events":   ["taskCreated", "taskUpdated", "taskMoved", "taskStatusUpdated"],
        "list_id":  int(CLICKUP_LIST_ID),
    }

    response = httpx.post(url, headers=HEADERS, json=payload, timeout=15)
    response.raise_for_status()
    data = response.json()

    webhook_id     = data.get("id") or data.get("webhook", {}).get("id")
    webhook_secret = data.get("webhook", {}).get("secret")

    if not webhook_secret:
        raise ValueError(f"ClickUp no devolvió el secret. Respuesta: {data}")

    print(f"    ✅ Webhook registrado — ID: {webhook_id}")
    return webhook_id, webhook_secret


# ---------------------------------------------------------------------------
# Paso 2: Actualizar Secret Manager
# ---------------------------------------------------------------------------
def update_secret_manager(secret_value: str) -> int:
    """
    Agrega una nueva versión del secret en GCP Secret Manager.
    Devuelve el número de versión exacto (ej: 15).

    Usar el número exacto en Cloud Run evita el race condition donde
    `:latest` puede resolver a la versión anterior si la propagación
    de Secret Manager aún no completó.
    """
    print(f"\n[2/4] Actualizando '{SECRET_NAME}' en Secret Manager...")

    client      = secretmanager.SecretManagerServiceClient()
    secret_path = f"projects/{GCP_PROJECT_ID}/secrets/{SECRET_NAME}"

    response = client.add_secret_version(
        request={
            "parent":  secret_path,
            "payload": {"data": secret_value.encode("utf-8")},
        }
    )
    # response.name → "projects/ortega-473114/secrets/CLICKUP_WEBHOOK_SECRET/versions/15"
    version_number = int(response.name.split("/")[-1])

    print(f"    ✅ Secret actualizado — versión exacta: {version_number}")
    return version_number


# ---------------------------------------------------------------------------
# Paso 3: Forzar nueva revisión de Cloud Run con versión exacta
# ---------------------------------------------------------------------------
def redeploy_cloud_run(version_number: int) -> None:
    """
    Crea una nueva revisión de Cloud Run apuntando a la versión EXACTA
    del secret (no `:latest`) para evitar el race condition de propagación.
    Espera a que la revisión esté completamente lista antes de continuar.
    """
    secret_ref = f"{SECRET_NAME}={SECRET_NAME}:{version_number}"
    print(f"\n[3/4] Forzando nueva revisión de Cloud Run con secret versión {version_number}...")

    cmd = [
        "gcloud", "run", "services", "update", CLOUD_RUN_SERVICE,
        f"--region={CLOUD_RUN_REGION}",
        f"--project={GCP_PROJECT_ID}",
        f"--update-secrets={secret_ref}",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"    ❌ Error:\n{result.stderr}")
        raise RuntimeError("Falló gcloud run services update")

    print("    ⏳ Revisión creada, esperando a que esté lista...")
    _wait_for_revision_ready()
    print("    ✅ Nueva revisión activa y sirviendo tráfico.")


def _wait_for_revision_ready(timeout_seconds: int = 120, poll_interval: int = 5) -> None:
    """
    Consulta el estado de Cloud Run hasta que la revisión más reciente
    tenga condición Ready=True. Lanza TimeoutError si supera el límite.
    """
    cmd_describe = [
        "gcloud", "run", "services", "describe", CLOUD_RUN_SERVICE,
        f"--region={CLOUD_RUN_REGION}",
        f"--project={GCP_PROJECT_ID}",
        "--format=value(status.conditions[0].status)",
    ]

    elapsed = 0
    while elapsed < timeout_seconds:
        result = subprocess.run(cmd_describe, capture_output=True, text=True)
        ready_status = result.stdout.strip()

        if ready_status == "True":
            return

        print(f"    ... estado: {ready_status or 'actualizando'} ({elapsed}s)")
        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(
        f"Cloud Run no quedó listo en {timeout_seconds}s. "
        "Verifica manualmente en la consola."
    )


# ---------------------------------------------------------------------------
# Paso 4: Verificación final
# ---------------------------------------------------------------------------
def verify_webhook(webhook_id: str) -> None:
    """
    Consulta los webhooks activos y reporta el estado del recién creado.
    """
    print("\n[4/4] Verificando estado del webhook...")

    url      = f"https://api.clickup.com/api/v2/team/{CLICKUP_TEAM_ID}/webhook"
    response = httpx.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    webhooks = response.json().get("webhooks", [])

    for wh in webhooks:
        if wh.get("id") == webhook_id:
            health  = wh.get("health", {})
            status  = health.get("status", wh.get("status", "?"))
            failures = health.get("fail_count", 0)
            print(f"    ID:       {wh['id']}")
            print(f"    Endpoint: {wh['endpoint']}")
            print(f"    Estado:   {status}")
            print(f"    Fallos:   {failures}")
            if status.upper() not in ("ACTIVE",):
                print("    ⚠️  El webhook aún no muestra ACTIVE.")
                print("       Es normal si ClickUp tarda unos segundos en actualizar el estado.")
            return

    print("    ⚠️  No se encontró el webhook. Verifica manualmente con scripts/failing.py")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not CLICKUP_API_TOKEN:
        print("❌ Falta CLICKUP_API_TOKEN en el .env")
        sys.exit(1)

    print("=" * 60)
    print("  Re-registro atómico de webhook ClickUp")
    print("=" * 60)

    try:
        # 0. Limpiar webhooks con fallos
        delete_failing_webhooks()

        # 1. Registrar nuevo webhook
        webhook_id, webhook_secret = register_webhook()

        # 2. Subir secret a Secret Manager → obtener versión exacta
        version_number = update_secret_manager(webhook_secret)

        # 3. Actualizar Cloud Run con versión exacta + esperar que esté listo
        redeploy_cloud_run(version_number)

        # 4. Verificar
        verify_webhook(webhook_id)

        print("\n" + "=" * 60)
        print("  ✅ Todo listo. Webhook activo y Cloud Run actualizado.")
        print("=" * 60)

    except httpx.HTTPStatusError as e:
        print(f"\n❌ Error HTTP de ClickUp: {e.response.status_code} — {e.response.text}")
        sys.exit(1)
    except TimeoutError as e:
        print(f"\n⏰ Timeout: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
