# app/repositories/strategy_repository.py
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.models.strategy_new_case import StrategyNewCase
import logging

logger = logging.getLogger(__name__)

class StrategyRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert(self, data: dict):
        """
        Inserta un nuevo registro o actualiza el existente si el task_id ya existe.
        """
        try:
            # Definimos la instrucción de inserción
            stmt = insert(StrategyNewCase).values(data)

            # Definimos qué pasa si hay conflicto en la Primary Key (task_id)
            update_dict = {
                c.name: c for c in stmt.excluded 
                if not c.primary_key # No actualizamos la PK
            }

            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=['task_id'],
                set_=update_dict
            )

            self.db.execute(upsert_stmt)
            self.db.commit()
            logger.info(f"✅ StrategyNewCase {data.get('task_id')} sincronizado exitosamente.")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error en upsert de StrategyNewCase: {e}")
            raise e

    def get_by_task_id(self, task_id: str):
        return self.db.query(StrategyNewCase).filter(StrategyNewCase.task_id == task_id).first()
