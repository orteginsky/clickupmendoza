#!/usr/bin/env python3
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.config import settings
from app.models.strategy_new_case import StrategyNewCase
from app.models import Base

def init_database():
    """Crea la tabla strategy_new_cases"""
    print("🗄️  Inicializando tabla Strategy New Cases...")
    engine = create_engine(settings.database_dsn)

    try:
        # Esto creará solo las tablas que no existan
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas sincronizadas exitosamente")
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database()
