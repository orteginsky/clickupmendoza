# app/models/strategy_new_case.py
from sqlalchemy import Column, String, Text, DateTime, func
from app.models.lead import Base

class StrategyNewCase(Base):
    """
    Modelo para la lista 'Strategy New Cases'.
    """
    __tablename__ = "strategy_new_cases"

    task_id = Column(String(100), primary_key=True, index=True)
    task_name = Column(Text, nullable=True)
    status = Column(String(255), nullable=True)
    assignee = Column(Text, nullable=True)
    priority = Column(String(255), nullable=True)
    date_created = Column(DateTime(timezone=True), nullable=True)
    
    # Custom Fields
    id_cliente = Column(Text, nullable=True)
    caso = Column(Text, nullable=True)
    fecha_de_venta = Column(DateTime(timezone=True), nullable=True)
    fecha_consulta_original = Column(DateTime(timezone=True), nullable=True)
    phone = Column(Text, nullable=True)
    attorney_lsucb = Column(Text, nullable=True)
    fecha_de_asignacin = Column(DateTime(timezone=True), nullable=True)
    paralegal_report = Column(Text, nullable=True)
    link_de_rs = Column(Text, nullable=True)
    link_tramcase = Column(Text, nullable=True)
    open_case_type = Column(Text, nullable=True)
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<StrategyNewCase(task_id={self.task_id}, task_name={self.task_name})>"
