import os
import httpx
from dotenv import load_dotenv

# 1. Cargar variables
load_dotenv()

# --- CONFIGURACIÓN ---
API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
LIST_ID = "901412734772"
TARGET_FIELD_ID = "f18ca98e-67b0-4f93-8dc3-a863d6c7cb8d"

headers = {
    "Authorization": API_TOKEN, 
    "Content-Type": "application/json"
}

def map_dropdown_options(list_id, field_id):
    print(f"🔍 Analizando opciones del Dropdown en la Lista: {list_id}...")
    
    url = f"https://api.clickup.com/api/v2/list/{list_id}/field"
    
    try:
        response = httpx.get(url, headers=headers)
        response.raise_for_status()
        
        fields = response.json().get("fields", [])
        
        # Buscar el campo específico por su ID
        target_field = next((f for f in fields if f["id"] == field_id), None)
        
        if not target_field:
            print(f"❌ No se encontró el campo con ID: {field_id}")
            return

        print(f"\n--- Campo: {target_field['name']} ---")
        
        # Los dropdowns guardan sus opciones en 'type_config'
        options = target_field.get("type_config", {}).get("options", [])
        
        if not options:
            print("⚠️ El campo no tiene opciones configuradas.")
            return

        print(f"{'VALOR (LABEL)':<30} | {'ID DE LA OPCIÓN (UUID)'}")
        print("-" * 70)
        
        for opt in options:
            label = opt.get("name", "N/A")
            opt_id = opt.get("id", "N/A")
            print(f"{label:<30} | {opt_id}")
    except Exception as e:
        print(f"❌ Error al consultar la API: {e}")

if __name__ == "__main__":
    if not API_TOKEN:
        print("❌ Error: Falta CLICKUP_API_TOKEN en el .env")
    else:
        map_dropdown_options(LIST_ID, TARGET_FIELD_ID)