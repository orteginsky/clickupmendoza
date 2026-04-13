# app/api/webhook_strategy.py
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from typing import Optional
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.services.strategy_service import StrategyService
from app.services.clickup_service import ClickUpService
from app.repositories.strategy_repository import StrategyRepository
from app.schemas.webhook import WebhookPayload

router = APIRouter(prefix="/webhooks", tags=["strategy"])

@router.post("/strategy", response_model=None)
async def handle_strategy_webhook(
    request: Request,
    payload: WebhookPayload,
    db: Session = Depends(get_db),
    x_signature: Optional[str] = Header(None)
):
    """
    Webhook para la lista Strategy New Cases.
    """
    # 1. Validar la firma
    body = await request.body()
    body_text = body.decode("utf-8")
    
    clickup_service = ClickUpService()

    # Usamos el secret específico o el general si no está definido
    secret = settings.clickup_webhook_secret_strategy
    if secret == "REPLACE_ME":
        secret = settings.clickup_webhook_secret

    is_valid = clickup_service.verify_webhook_signature(
        body_text, 
        x_signature or "", 
        secret=secret
    )
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # 2. Obtener datos de ClickUp
    task_id = payload.task_id
    task_data = await clickup_service.get_task(task_id)
    
    if not task_data:
        # 200 para evitar reintentos infinitos si la tarea desaparece
        return {"status": "ignored", "reason": "task_not_found", "task_id": task_id}

    # 3. Transformar y Guardar
    formatted_data = StrategyService.transform_task(task_data)
    repo = StrategyRepository(db)
    repo.upsert(formatted_data)

    return {"status": "success", "task_id": task_id, "event": payload.event}
