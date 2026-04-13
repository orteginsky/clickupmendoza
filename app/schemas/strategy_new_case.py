# app/schemas/strategy_new_case.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StrategyNewCaseBase(BaseModel):
    task_id: str
    task_name: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[str] = None
    date_created: Optional[datetime] = None
    id_cliente: Optional[str] = None
    caso: Optional[str] = None
    fecha_de_venta: Optional[datetime] = None
    fecha_consulta_original: Optional[datetime] = None
    phone: Optional[str] = None
    attorney_lsucb: Optional[str] = None
    fecha_de_asignacin: Optional[datetime] = None
    paralegal_report: Optional[str] = None
    link_de_rs: Optional[str] = None
    link_tramcase: Optional[str] = None
    open_case_type: Optional[str] = None

class StrategyNewCaseCreate(StrategyNewCaseBase):
    pass

class StrategyNewCaseResponse(StrategyNewCaseBase):
    updated_at: datetime
    
    class Config:
        from_attributes = True
