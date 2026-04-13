import os
import httpx
from dotenv import load_dotenv

# 1. Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN ---
API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
TASK_ID = "86b8dx1y1" 

headers = {
    "Authorization": API_TOKEN, 
    "Content-Type": "application/json"
}

def inspect_task_custom_fields(task_id):
    print(f"🔍 Analizando campos personalizados de la Tarea: {task_id}...\n")
    
    # Endpoint para obtener los detalles de una tarea específica
    # Incluimos custom_task_ids=true por si usas IDs personalizados en tu espacio
    url = f"https://api.clickup.com/api/v2/task/{task_id}"
    
    try:
        response = httpx.get(url, headers=headers)
        response.raise_for_status()
        
        task_data = response.json()
        custom_fields = task_data.get("custom_fields", [])

        if not custom_fields:
            print("⚠️ No se encontraron campos personalizados en esta tarea.")
            return

        print(f"{'NOMBRE DEL CAMPO':<25} | {'ID':<20} | {'TIPO'}")
        print("-" * 70)

        for field in custom_fields:
            name = field.get("name", "N/A")
            f_id = field.get("id", "N/A")
            f_type = field.get("type", "N/A")
            
            # Algunos tipos comunes: 'url', 'drop_down', 'short_text', 'number'
            print(f"{name:<25} | {f_id:<20} | {f_type}")

    except httpx.HTTPStatusError as e:
        print(f"❌ Error de HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    # Asegúrate de que el TOKEN esté configurado
    if not API_TOKEN:
        print("❌ Error: No se encontró CLICKUP_API_TOKEN en el archivo .env")
    else:
        inspect_task_custom_fields(TASK_ID)