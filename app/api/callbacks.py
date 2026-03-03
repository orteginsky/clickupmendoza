# app/api/callbacks.py
from fastapi import APIRouter, HTTPException, status
from app.schemas.filtros import FiltrosCallbackPayload, FIRST_OUTCOME_OPTIONS
from app.services.clickup_service import ClickUpService
from app.config import settings

router = APIRouter()

# UUID del campo "1st Outcome" (drop_down) en ClickUp
FIELD_ID_1ST_OUTCOME = "5c636462-8610-417f-a71d-e0fb27a20579"


@router.post("/filtros", status_code=status.HTTP_200_OK)
async def handle_filtros_callback(payload: FiltrosCallbackPayload):
    """
    Recibe el resultado del análisis de Filtros AI y actualiza ClickUp.

    Campos que puede actualizar:
    - Link AI Filtro (url): URL del documento generado por Filtros IA.
    - 1st Outcome (drop_down, opcional): resultado clasificado del filtro.
    """
    print(f"📥 Callback recibido para Task {payload.task_id} - Status: {payload.status}")

    # 1. Validar que el proceso fue exitoso
    if payload.status != "success":
        print(f"⚠️ El proceso en Filtros falló: {payload.error}")
        return {"received": True, "action": "ignored_due_to_error"}

    if not payload.artifacts or not payload.artifacts.doc_url:
        print("⚠️ Payload incompleto: No hay URL del documento")
        return {"received": True, "action": "ignored_no_url"}

    # 2. Inicializar servicio
    clickup_service = ClickUpService()

    # 3. Actualizar campo "Link AI Filtro" (url)
    success = await clickup_service.set_custom_field_value(
        task_id=payload.task_id,
        field_id=settings.clickup_field_id_ai_link,
        value=payload.artifacts.doc_url
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error actualizando campo Link AI Filtro en ClickUp"
        )

    print(f"✅ Link AI Filtro actualizado: Task {payload.task_id} -> {payload.artifacts.doc_url}")

    # 4. Actualizar campo "1st Outcome" (drop_down) si se proporcionó
    if payload.first_outcome:
        option_uuid = FIRST_OUTCOME_OPTIONS[payload.first_outcome]
        outcome_success = await clickup_service.set_custom_field_value(
            task_id=payload.task_id,
            field_id=FIELD_ID_1ST_OUTCOME,
            value=option_uuid
        )
        if not outcome_success:
            # Logueamos pero no fallamos — el link principal ya fue guardado
            print(f"⚠️ No se pudo actualizar '1st Outcome' en Task {payload.task_id}")
        else:
            print(f"✅ 1st Outcome actualizado: Task {payload.task_id} -> {payload.first_outcome}")

    return {"received": True, "action": "clickup_updated"}