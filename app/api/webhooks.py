"""
Endpoints para webhooks de ClickUp
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import httpx
import logging
import json
import uuid

from app.database import get_db
from app.repositories.lead_repository import LeadRepository
from app.services.lead_service import LeadService
from app.services.clickup_service import ClickUpService
from app.services.sheets_service import GoogleSheetsService
from app.config import settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/clickup")
async def clickup_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_signature: Optional[str] = Header(None)
):
    """
    Webhook optimizado: Responde rápido y procesa en segundo plano.
    NOTA: Persistencia en DB deshabilitada temporalmente.
    """
    # 1. Validación de Firma y Payload (Rápido)
    body = await request.body()
    body_text = body.decode("utf-8")

    clickup_service = ClickUpService()
    if not clickup_service.verify_webhook_signature(body_text, x_signature or ""):
        logger.warning("webhook_clickup | firma inválida rechazada")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = await request.json()
    except Exception as e:
        logger.error("webhook_clickup | JSON inválido: %s", e)
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    event = payload.get("event")
    task_id = payload.get("task_id")

    logger.info("webhook_clickup | event=%s task_id=%s", event, task_id)

    if not task_id:
        logger.warning("webhook_clickup | payload sin task_id, ignorado")
        raise HTTPException(status_code=400, detail="Missing task_id")

    # Solo procesar updates/creates
    if event not in ["taskUpdated", "taskCreated"]:
        logger.info("webhook_clickup | event=%s ignorado (no es update/create)", event)
        return {"status": "ignored", "event": event}

    # 2. Obtener datos básicos de la tarea
    logger.info("webhook_clickup | consultando ClickUp API para task_id=%s", task_id)
    task_data = await clickup_service.get_task(task_id)
    if not task_data:
        # Devolvemos 200 para que ClickUp no cuente esto como fallo del webhook.
        # La tarea puede haber sido eliminada o ser inaccesible temporalmente.
        logger.warning(
            "webhook_clickup | task_id=%s no encontrada en ClickUp API, ignorando", task_id
        )
        return {"status": "ignored", "reason": "task_not_found", "task_id": task_id}

    # 3. Lógica del Trigger
    link_intake_value = None
    custom_fields = task_data.get("custom_fields", [])
    ai_link_exists = False

    for field in custom_fields:
        field_id = field.get("id")

        # Detectar el Trigger (Link Intake)
        if field_id == settings.clickup_field_id_link_intake:
            link_intake_value = field.get("value")

        # Detectar Protección contra bucles (AI Link)
        if field_id == settings.clickup_field_id_ai_link:
            if field.get("value"):
                ai_link_exists = True

    if ai_link_exists:
        logger.info(
            "webhook_clickup | task_id=%s ya tiene Link AI, ignorado para evitar bucle", task_id
        )
        return {"status": "ignored", "reason": "already_processed"}

    # 4. Encolar tareas en Background (Fire and Forget)
    if link_intake_value:
        logger.info(
            "webhook_clickup | task_id=%s tiene Link Intake, encolando background tasks", task_id
        )

        # Encolamos el Dispatch a Filtros
        if settings.external_dispatch_enabled and settings.external_dispatch_url:
            background_tasks.add_task(
                _dispatch_to_external_service,
                task_id,
                task_data,
                link_intake_value
            )

        # Encolamos Sheets Sync
        if settings.google_sheets_enabled:
            background_tasks.add_task(
                _sync_to_google_sheets,
                task_data
            )
    else:
        logger.info(
            "webhook_clickup | task_id=%s sin Link Intake, solo se guarda en DB", task_id
        )

    # 5. Guardar en DB Local (Rápido)
    lead_data = LeadService.transform_clickup_task(task_data)
    repo = LeadRepository(db)
    repo.upsert(lead_data)
    logger.info("webhook_clickup | task_id=%s guardado en DB", task_id)

    # RESPONDER A CLICKUP INMEDIATAMENTE
    return {"status": "queued", "task_id": task_id}


async def _dispatch_to_external_service(task_id: str, task_data: dict, link_intake_value: str) -> bool:
    """
    Envía la solicitud al ENQUEUER (Cloud Tasks Wrapper).
    """
    logger.info("enqueuer_dispatch | task_id=%s preparando envío", task_id)

    try:
        base_url = settings.external_dispatch_callback_base_url.rstrip("/")
        callback_url = f"{base_url}/callbacks/filtros"

        worker_payload = {
            "task_id": task_id,
            "client_name": task_data.get("name"),
            "intake_url": link_intake_value,
            "nexus_callback_url": callback_url,
            "metadata": {
                "clickup_status": task_data.get("status", {}).get("status"),
                "clickup_url": task_data.get("url")
            }
        }

        enqueuer_payload = {
            "service": "filtros-ai",
            "worker_api_key": settings.filtros_api_key,
            "payload": worker_payload,
            "idempotency_key": f"task-{task_id}-{uuid.uuid4().hex[:6]}"
        }

        headers = {"Content-Type": "application/json"}

        logger.info("enqueuer_dispatch | task_id=%s enviando a %s", task_id, settings.external_dispatch_url)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.external_dispatch_url,
                json=enqueuer_payload,
                headers=headers
            )

            if response.status_code >= 400:
                logger.error(
                    "enqueuer_dispatch | task_id=%s HTTP %s body=%s",
                    task_id, response.status_code, response.text
                )

            response.raise_for_status()
            resp_data = response.json()
            logger.info("enqueuer_dispatch | task_id=%s encolado ok task=%s", task_id, resp_data.get("task"))

        return True

    except Exception as e:
        logger.error("enqueuer_dispatch | task_id=%s error=%s", task_id, e)
        return False


async def _sync_to_google_sheets(task_data: dict) -> bool:
    """
    Sincronización a Sheets con extracción de campos específicos desde task_name.
    """
    try:
        sheets_service = GoogleSheetsService()
        
        task_name = task_data.get("name", "")
        
        # 1. Extraer 'name' (todo antes de '|')
        # Si no hay '|', toma el nombre completo.
        extracted_name = task_name.split('|')[0].strip() if task_name else ""

        # 2. Extraer 'dvs_name' (todo después de ' with ')
        # Si no existe ' with ', se deja vacío o podrías poner un valor por defecto.
        dvs_name = "Sin DVS"
        if " with " in task_name:
            dvs_name = task_name.split(" with ")[-1].strip()

        data = {
            "task_id": task_data.get("id"),
            "task_name": task_name,
            "name": extracted_name,
            "dvs_name": dvs_name,
            "status": task_data.get("status", {}).get("status"),
            "url": task_data.get("url"),
            "date_created": task_data.get("date_created"),
            "date_updated": task_data.get("date_updated"),
        }

        # Procesamiento de campos personalizados (Custom Fields)
        for field in task_data.get("custom_fields", []):
            field_name = field.get("name", "").lower().replace(" ", "_")
            field_value = field.get("value")
            if field_value:
                data[field_name] = field_value
                
        logger.info("sheets_sync | task_id=%s escribiendo en Sheets", task_data.get("id"))
        success = sheets_service.write_row(data)
        if not success:
            logger.warning("sheets_sync | task_id=%s write_row devolvió False", task_data.get("id"))
        return success

    except Exception as e:
        logger.error("sheets_sync | task_id=%s error=%s", task_data.get("id"), e)
        return False