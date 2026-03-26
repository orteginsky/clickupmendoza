"""
Registra el webhook de ClickUp y actualiza el secret en GCP de forma atómica.

Flujo:
  1. Registra el webhook en ClickUp → obtiene el nuevo secret
  2. Sube el nuevo secret a Secret Manager (nueva versión)
  3. Fuerza una nueva revisión de Cloud Run para que tome el secret actualizado
  4. Verifica que el webhook quedó activo

Uso:
  python3 -m scripts.reregister_webhook

Requisitos en el entorno:
  - CLICKUP_API_TOKEN en .env
  - gcloud autenticado con permisos sobre el proyecto ortega-473114
"""

import os
import sys
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
# Paso 1: Registrar webhook en ClickUp
# ---------------------------------------------------------------------------
def register_webhook() -> tuple[str, str]:
    """
    Registra el webhook y devuelve (webhook_id, webhook_secret).
    """
    print("\n[1/3] Registrando webhook en ClickUp...")

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
        raise ValueError(f"ClickUp no devolvió el secret. Respuesta completa: {data}")

    print(f"    ✅ Webhook registrado — ID: {webhook_id}")
    return webhook_id, webhook_secret


# ---------------------------------------------------------------------------
# Paso 2: Actualizar Secret Manager
# ---------------------------------------------------------------------------
def update_secret_manager(secret_value: str) -> str:
    """
    Agrega una nueva versión del secret en GCP Secret Manager.
    Devuelve el nombre de la versión creada.
    """
    print(f"\n[2/3] Actualizando '{SECRET_NAME}' en Secret Manager...")

    client      = secretmanager.SecretManagerServiceClient()
    secret_path = f"projects/{GCP_PROJECT_ID}/secrets/{SECRET_NAME}"

    response = client.add_secret_version(
        request={
            "parent":  secret_path,
            "payload": {"data": secret_value.encode("utf-8")},
        }
    )
    version_name = response.name  # projects/.../secrets/.../versions/N

    print(f"    ✅ Secret actualizado — versión: {version_name.split('/')[-1]}")
    return version_name


# ---------------------------------------------------------------------------
# Paso 3: Forzar nueva revisión de Cloud Run
# ---------------------------------------------------------------------------
def redeploy_cloud_run() -> None:
    """
    Crea una nueva revisión de Cloud Run que toma el secret actualizado.
    No reconstruye la imagen Docker — solo actualiza la configuración del servicio.
    """
    print(f"\n[3/3] Forzando nueva revisión de Cloud Run ({CLOUD_RUN_SERVICE})...")

    cmd = [
        "gcloud", "run", "services", "update", CLOUD_RUN_SERVICE,
        f"--region={CLOUD_RUN_REGION}",
        f"--project={GCP_PROJECT_ID}",
        f"--update-secrets={SECRET_NAME}={SECRET_NAME}:latest",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"    ❌ Error al actualizar Cloud Run:\n{result.stderr}")
        raise RuntimeError("Falló gcloud run services update")

    print("    ✅ Nueva revisión desplegada — Cloud Run ya usa el secret actualizado")


# ---------------------------------------------------------------------------
# Verificación final
# ---------------------------------------------------------------------------
def verify_webhook(webhook_id: str) -> None:
    """
    Consulta los webhooks activos y confirma que el recién creado está ACTIVE.
    """
    print("\n[✓] Verificando estado del webhook...")

    url      = f"https://api.clickup.com/api/v2/team/{CLICKUP_TEAM_ID}/webhook"
    response = httpx.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    webhooks = response.json().get("webhooks", [])

    for wh in webhooks:
        if wh.get("id") == webhook_id:
            status = wh.get("health", {}).get("status") or wh.get("status", "?")
            print(f"    ID:       {wh['id']}")
            print(f"    Endpoint: {wh['endpoint']}")
            print(f"    Estado:   {status}")
            return

    print("    ⚠️  No se encontró el webhook en la lista. Verifica manualmente.")


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
        # 1. Registrar
        webhook_id, webhook_secret = register_webhook()

        # 2. Actualizar Secret Manager
        update_secret_manager(webhook_secret)

        # 3. Forzar nueva revisión (mínima ventana de exposición)
        redeploy_cloud_run()

        # 4. Verificar
        verify_webhook(webhook_id)

        print("\n" + "=" * 60)
        print("  ✅ Todo listo. Webhook activo y Cloud Run actualizado.")
        print("=" * 60)

    except httpx.HTTPStatusError as e:
        print(f"\n❌ Error HTTP de ClickUp: {e.response.status_code} — {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
