import os
import httpx
from dotenv import load_dotenv

# Cargar variables
load_dotenv()

# --- CONFIGURACIÓN ---
API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
LIST_ID_X = "901412734772" 

headers = {
    "Authorization": API_TOKEN, 
    "Content-Type": "application/json"
}

def verify_list():
    print(f"🔍 1. Analizando campos en la Lista X ({LIST_ID_X})...")
    
    try:
        url_fields = f"https://api.clickup.com/api/v2/list/{LIST_ID_X}/field"
        resp = httpx.get(url_fields, headers=headers)
        resp.raise_for_status()
        fields = resp.json().get("fields", [])
        
        print("\n--- Campos encontrados en Lista X ---")
        for f in fields:
            print(f" > Campo: '{f['name']}' | ID: {f['id']}")
        print("-------------------------------------")

    except Exception as e:
        print(f"❌ Error verificando campos: {e}")
        return


if __name__ == "__main__":
    verify_list()