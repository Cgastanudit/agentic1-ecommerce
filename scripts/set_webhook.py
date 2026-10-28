import os
import sys

from dotenv import load_dotenv
import httpx

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
PUBLIC_URL = os.getenv("PUBLIC_URL")
SECRET = os.getenv("TELEGRAM_SECRET")

if not TOKEN:
    print("ERROR: TELEGRAM_TOKEN no está definido en .env")
    sys.exit(1)
if not PUBLIC_URL:
    print("ERROR: PUBLIC_URL no está definido en .env")
    sys.exit(1)

url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
payload = {
    "url": f"{PUBLIC_URL.rstrip('/')}/telegram",
    "secret_token": SECRET,
}

print(f"setWebhook -> {payload['url']} (secret_token configurado: {'sí' if SECRET else 'no'})")

with httpx.Client() as client:
    resp = client.post(url, json=payload, timeout=30.0)
    print(f"HTTP {resp.status_code}")
    print(resp.json())
