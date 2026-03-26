# app/api/drive_sync.py
"""
Endpoint para sincronizar archivos PDF de Google Drive con tareas de ClickUp.
Recibe metadatos del archivo, busca el lead por nombre y actualiza el campo
"Drive PDF" en ClickUp con la URL del archivo.
"""

import re
import unicodedata
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.repositories.lead_repository import LeadRepository
from app.services.clickup_service import ClickUpService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drive", tags=["Drive Sync"])

# UUID del campo "Link Intake" en ClickUp
FIELD_ID_LINK_INTAKE = "1c35f9be-9fe2-4a0c-b0af-9f4f92dd4554"

# ---------------------------------------------------------------------------
# Stopwords y helper de normalización
# ---------------------------------------------------------------------------

STOPWORDS = {
    "intake", "pdf", "archivo", "mp3", "interview", "appointment",
    "new", "with", "for",
    "2026", "2025", "2024", "2023",
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    "january", "february", "march", "april", "june", "july",
    "august", "september", "october", "november", "december",
    "lunes", "martes", "miercoles", "jueves", "viernes",
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "am", "pm", "mendoza", "firm", "law", "legal",
}


def _normalize_filename(raw: str) -> str:
    """
    Convierte un nombre de archivo crudo en un query limpio para búsqueda:
    1. Normaliza a NFC (unifica caracteres con acento).
    2. Reemplaza todo lo que no sea letra o espacio por espacio.
    3. Elimina tokens que sean stopwords o secuencias de 4+ dígitos.
    4. Colapsa espacios y convierte a UPPERCASE.
    """
    # 1. Unicode NFC
    text = unicodedata.normalize("NFC", raw)

    # 2. Reemplaza no-letras (excepto espacios) por espacio
    text = re.sub(r"[^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ\s]", " ", text)

    # 3. Tokenizar, filtrar stopwords y números de 4+ dígitos
    tokens = [
        t for t in text.split()
        if t.lower() not in STOPWORDS and not re.fullmatch(r"\d{4,}", t)
    ]

    # 4. Colapsar, strip y uppercase
    return " ".join(tokens).strip().upper()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DriveSyncRequest(BaseModel):
    filename_raw: str
    file_url: str
    folder_date: Optional[str] = None  # para logging


class DriveSyncResponse(BaseModel):
    status: str
    query: str
    task_id: str
    nombre_clickup: str
    field_updated: bool
    file_url: str


# ---------------------------------------------------------------------------
# Dependencia de autenticación
# ---------------------------------------------------------------------------

def verify_bearer(authorization: Optional[str] = Header(default=None)) -> None:
    """
    Valida el header Authorization: Bearer <DRIVE_SYNC_SECRET>.
    Lanza 401 si falta o no coincide.
    """
    expected = f"Bearer {settings.drive_sync_secret}"
    if not authorization or authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/sync",
    response_model=DriveSyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Sincronizar PDF de Drive con tarea de ClickUp",
)
async def drive_sync(
    payload: DriveSyncRequest,
    db: Session = Depends(get_db),
    _auth: None = Depends(verify_bearer),
):
    """
    Recibe metadatos de un PDF subido a Google Drive, busca el lead
    correspondiente por nombre y actualiza el campo Drive PDF en ClickUp.

    - **filename_raw**: nombre del archivo sin extensión (ej. "Ma Guadalupe Garay - INTAKE - 25032026")
    - **file_url**: URL pública/compartida del archivo en Drive
    - **folder_date**: nombre de la carpeta padre (opcional, solo para logging)
    """

    # 1. Normalizar nombre ---------------------------------------------------
    nombre_clean = _normalize_filename(payload.filename_raw)
    logger.info(
        "drive_sync | raw=%r clean=%r folder_date=%s",
        payload.filename_raw,
        nombre_clean,
        payload.folder_date,
    )

    if not nombre_clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "empty_query_after_normalization",
                "filename_raw": payload.filename_raw,
            },
        )

    # 2. Buscar lead ---------------------------------------------------------
    repo = LeadRepository(db)
    results = repo.search_by_name(nombre_clean, limit=1)

    if not results:
        logger.warning("drive_sync | lead_not_found query=%r", nombre_clean)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "lead_not_found", "query": nombre_clean},
        )

    lead = results[0]
    task_id: str = lead.task_id
    nombre_clickup: str = lead.nombre_clickup or ""
    logger.info("drive_sync | lead encontrado task_id=%s nombre=%s", task_id, nombre_clickup)

    # 3. Actualizar campo en ClickUp -----------------------------------------
    field_updated = False
    try:
        clickup = ClickUpService()
        field_updated = await clickup.set_custom_field_value(
            task_id=task_id,
            field_id=FIELD_ID_LINK_INTAKE,
            value=payload.file_url,
        )
        if field_updated:
            logger.info(
                "drive_sync | campo actualizado task_id=%s url=%s",
                task_id,
                payload.file_url,
            )
        else:
            logger.warning(
                "drive_sync | fallo al actualizar campo ClickUp task_id=%s", task_id
            )
    except Exception as exc:
        # Non-blocking: logeamos pero no lanzamos excepción
        logger.error(
            "drive_sync | excepcion actualizando ClickUp task_id=%s error=%s",
            task_id,
            exc,
        )

    # 4. Respuesta -----------------------------------------------------------
    return DriveSyncResponse(
        status="ok",
        query=nombre_clean,
        task_id=task_id,
        nombre_clickup=nombre_clickup,
        field_updated=field_updated,
        file_url=payload.file_url,
    )
