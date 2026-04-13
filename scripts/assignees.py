import os
import httpx
import json
from dotenv import load_dotenv

# 1. Cargar variables
load_dotenv()

# --- CONFIGURACIÓN ---
API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
LIST_ID = "901403238634" 

headers = {
    "Authorization": API_TOKEN, 
    "Content-Type": "application/json"
}

def analyze_system_fields(list_id):
    print(f"🔍 Obteniendo tareas de la lista {list_id} para analizar metacampos...\n")
    
    # Consultamos las tareas de la lista para ver su estructura real
    url = f"https://api.clickup.com/api/v2/list/{list_id}/task"
    
    try:
        response = httpx.get(url, headers=headers)
        response.raise_for_status()
        tasks = response.json().get("tasks", [])
        
        if not tasks:
            print("⚠️ No hay tareas en esta lista para analizar.")
            return

        # Tomamos la primera tarea como muestra
        sample_task = tasks[0]
        
        print("=== ANÁLISIS DE METACAMPOS (SYSTEM FIELDS) ===")
        
        # 1. Analizar Asignados (Assignees)
        assignees = sample_task.get("assignees", [])
        print(f"\n📌 CAMPO: 'assignees' (Encargados)")
        print(f"   Tipo: {type(assignees).__name__} de objetos")
        if assignees:
            print(f"   Estructura del primer encargado:")
            print(json.dumps(assignees[0], indent=4))
        else:
            print("   ⚠️ Esta tarea no tiene nadie asignado.")

        # 2. Analizar Fechas
        print(f"\n📌 CAMPO: 'date_created'")
        print(f"   Valor: {sample_task.get('date_created')} (Unix Timestamp en milisegundos)")
        
        # 3. Analizar Estatus
        status_info = sample_task.get("status", {})
        print(f"\n📌 CAMPO: 'status'")
        print(f"   Nombre: {status_info.get('status')} | ID: {status_info.get('id')}")

    except Exception as e:
        print(f"❌ Error al consultar la API: {e}")

if __name__ == "__main__":
    if not API_TOKEN:
        print("❌ Error: Falta CLICKUP_API_TOKEN en el .env")
    else:
        analyze_system_fields(LIST_ID)