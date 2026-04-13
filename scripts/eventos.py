import os
import httpx
from dotenv import load_dotenv

load_dotenv()

CLICKUP_API_TOKEN = os.getenv("CLICKUP_API_TOKEN")
# Pega aquí el ID que obtuviste anteriormente
WEBHOOK_ID = "d3c4a137-8d43-4d24-98b1-102fbc2cd830" 

def auditar_webhook():
    headers = {"Authorization": CLICKUP_API_TOKEN}
    url = f"https://api.clickup.com/api/v2/webhook/{WEBHOOK_ID}"
    
    try:
        response = httpx.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()["webhook"]
        
        print(f"\n--- AUDITORÍA DE WEBHOOK: {WEBHOOK_ID} ---")
        print(f"🔗 URL Destino: {data['endpoint']}")
        print(f"✅ Estado: {data['health']['status']}") # 'active' o 'failing'
        print(f"📊 EVENTOS REGISTRADOS:")
        for event in data['events']:
            print(f"   - {event}")
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ Error al consultar el webhook: {e}")

if __name__ == "__main__":
    auditar_webhook()