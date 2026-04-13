import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv("CLICKUP_API_TOKEN")

def list_webhooks():
    if not API_TOKEN:
        print("❌ Falta CLICKUP_API_TOKEN")
        return

    headers = {"Authorization": API_TOKEN}
    
    try:
        r = httpx.get("https://api.clickup.com/api/v2/team", headers=headers)
        teams = r.json().get("teams", [])
        if not teams:
            print("❌ No se encontraron equipos asociados a este Token.")
            return
        team_id = teams[0]["id"]
    except Exception as e:
        print(f"❌ Error conectando a ClickUp: {e}")
        return

    print(f"🔍 Buscando webhooks para el equipo {team_id}...\n")
    url = f"https://api.clickup.com/api/v2/team/{team_id}/webhook"
    
    try:
        resp = httpx.get(url, headers=headers)
        webhooks = resp.json().get("webhooks", [])
        
        if not webhooks:
            print("⚠️ No se encontraron webhooks activos.")
            return

        for w in webhooks:
            # Extraemos datos de forma segura usando .get() para evitar el error 'KeyError'
            webhook_id = w.get('id')
            endpoint = w.get('endpoint')
            user_id = w.get('userid')
            events = w.get('events', [])
            
            # El estado real suele estar en health -> status
            health = w.get('health', {})
            status = health.get('status', 'unknown') 
            fail_count = health.get('fail_count', 0)

            print("-" * 60)
            print(f"🆔 ID:       {webhook_id}")
            print(f"📋 Creado por User ID: {user_id}")
            print(f"🔗 Endpoint: {endpoint}")
            print(f"🚦 Estado:   {status.upper()}")
            
            if fail_count > 0:
                print(f"⚠️ Alerta:   Tiene {fail_count} fallos acumulados.")
                print(f"             (Si llega a 5, ClickUp lo suspende)")

            print(f"📢 Eventos registrados ({len(events)}):")
            for event in events:
                print(f"   • {event}")
            print("-" * 60)

    except Exception as e:
        print(f"❌ Error procesando la lista: {e}")

if __name__ == "__main__":
    list_webhooks()