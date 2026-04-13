import polars as pl
from sqlalchemy import text
from app.database import engine
from app.models.case_assignment import CaseAssignment
import os

# --- CONFIGURACIÓN ---
CSV_FILE = "subsanar.csv" # Asegúrate de que el nombre coincida

def clean_assignees(val: str) -> str:
    """Limpia los corchetes y comillas de la columna assignee del CSV"""
    if not val: return None
    return val.replace("[", "").replace("]", "").replace('"', "").strip()

def run_migration():
    if not os.path.exists(CSV_FILE):
        print(f"❌ Error: No se encuentra el archivo {CSV_FILE}")
        return

    print("📖 Cargando y limpiando datos con Polars...")
    
    # 1. Leer CSV
    # Nota: Ajustamos los nombres de columnas para que coincidan con el CSV
    df = pl.read_csv(CSV_FILE)
    
    # 2. Limpieza de datos
    df = df.with_columns([
        pl.col("assignee").map_elements(clean_assignees, return_dtype=pl.Utf8),
        pl.col("abogado_asignado").fill_null("N/A")
    ])

    print(f"✅ Datos listos. {len(df)} filas preparadas.")

    # 3. Conexión y Update Masivo
    with engine.begin() as conn:
        print("🚀 Creando tabla temporal en Cloud SQL...")
        
        # Convertimos a Pandas solo para el método to_sql (es el puente más estable con SQLAlchemy)
        df.to_pandas().to_sql('temp_fix_assignments', conn, if_exists='replace', index=False)

        print("⚡ Ejecutando UPDATE masivo mediante JOIN...")
        
        # SQL nativo para máxima velocidad
        query = text("""
            UPDATE case_assignments AS target
            SET 
                assignee = temp.assignee,
                abogado_asignado = temp.abogado_asignado,
                proyecto = temp.proyecto,
                synced_at = NOW()
            FROM temp_fix_assignments AS temp
            WHERE target.task_id = temp.task_id;
        """)
        
        result = conn.execute(query)
        print(f"✨ ¡Éxito! Se actualizaron {result.rowcount} registros en la base de datos.")

        # Limpiar rastro
        conn.execute(text("DROP TABLE temp_fix_assignments;"))

if __name__ == "__main__":
    run_migration()