from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict

# Mapeo de etiquetas del campo "1st Outcome" a sus UUIDs de opción en ClickUp
FIRST_OUTCOME_OPTIONS: Dict[str, str] = {
    "DENIED": "53e46014-6add-4b02-9afa-f90f2e158ec1",
    "N/Q - TS": "60eaca67-5a9c-4620-bd93-4afc19b46b6e",
    "NO INFO/SOLO QUEST": "efda53a6-acc4-44e7-88c2-9b511aa6f518",
    "NON VAWA": "c4516db1-a473-4603-919e-e1f47af5b846",
    "NQ - FORCED LABOR": "ed5f8ef1-e81d-47f0-80b0-ca2aecd55961",
    "NQ - GMC": "06c87578-65d7-42af-b9b6-e019f36e0828",
    "NQ - VAWA/VISA T": "174ae76a-fb7e-47aa-a54e-bd1a649a78dd",
    "NQ - VISA U": "0c3c2a4c-83c2-4012-b2a8-8891bd784729",
    "NQ-NOT QAL RELATION": "8c98f179-ef5b-4b82-baf3-edb8d42d05c8",
    "Pass": "94dcc461-ee3c-4b07-9afa-a203344e8352",
    "POSSIBLE NON VAWA": "64433fb2-b60b-4f43-9a06-6c463f9c1755",
    "POTENTIAL VAWA": "77c293fc-f305-42f0-924d-f1345bac054d",
    "POTENTIAN VISA T": "199e41b1-9d64-4f18-8e8c-e8afd17d6b72",
    "Reactivation": "544e383e-3f39-4d75-ba4c-1d343e6680fb",
    "REESCREENING": "8511a7e2-4354-435f-ad13-1f006a3aa594",
    "VAWA - NEA": "f09c6265-61f8-40fa-a42d-687f6849255b",
    "VAWA SPOUSE": "06ea9e6f-150b-42cd-b840-9c58051d9662",
    "VISA U": "dbff9536-51a0-4d5a-924d-26eda89bce99",
}

class ArtifactsInfo(BaseModel):
    doc_id: str
    doc_url: str

class DiagnosticsInfo(BaseModel):
    processing_time_ms: int
    version: str

class FiltrosCallbackPayload(BaseModel):
    """Payload recibido desde el servicio FILTROS."""
    task_id: str
    status: str
    outcome: Optional[str] = None
    first_outcome: Optional[str] = None
    artifacts: Optional[ArtifactsInfo] = None
    diagnostics: Optional[DiagnosticsInfo] = None
    error: Optional[str] = None

    @field_validator("first_outcome")
    @classmethod
    def validate_first_outcome(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in FIRST_OUTCOME_OPTIONS:
            valid = list(FIRST_OUTCOME_OPTIONS.keys())
            raise ValueError(f"first_outcome '{v}' no es válido. Opciones: {valid}")
        return v
