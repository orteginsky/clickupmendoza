import os
import httpx
from dotenv import load_dotenv

# Cargar variables de entorno para obtener el TOKEN
load_dotenv()

# Configuración
CLICKUP_API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
WEBHOOK_ID_TO_DELETE = "d3c4a137-8d43-4d24-98b1-102fbc2cd830"

def delete_specific_webhook():
    if not CLICKUP_API_TOKEN:
        print("❌ Error: No se encontró CLICKUP_API_TOKEN en el archivo .env")
        return

    url = f"https://api.clickup.com/api/v2/webhook/{WEBHOOK_ID_TO_DELETE}"
    headers = {
        "Authorization": CLICKUP_API_TOKEN,
        "Content-Type": "application/json"
    }

    print(f"🗑️  Intentando eliminar el webhook ID: {WEBHOOK_ID_TO_DELETE}...")

    try:
        response = httpx.delete(url, headers=headers)
            
        # 200 OK significa borrado exitoso
        # 204 No Content también es común en DELETE
        if response.status_code in [200, 204]:
            print("\n" + "="*50)
            print("✅ ¡ÉXITO! El webhook antiguo ha sido eliminado.")
            print("="*50)
        else:
            print(f"\n❌ Algo salió mal. Código de estado: {response.status_code}")
            print(f"Respuesta de ClickUp: {response.text}")
                
    except httpx.HTTPStatusError as e:
        print(f"❌ Error de conexión o http: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    delete_specific_webhook()