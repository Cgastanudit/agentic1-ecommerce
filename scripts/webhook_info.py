import os
import sys

from dotenv import load_dotenv
import httpx

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    print("ERROR: TELEGRAM_TOKEN no está definido en .env")
    sys.exit(1)

url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"

print(f"getWebhookInfo -> {url}")

with httpx.Client() as client:
    resp = client.get(url, timeout=30.0)
    print(f"HTTP {resp.status_code}")
    data = resp.json()
    print(resp.text)
    if data.get("ok"):
        result = data.get("result", {})
        print("\n--- Resumen ---")
        print(f"url: {result.get('url')}")
        print(f"tiene_secret_token: {'sí' if result.get('has_custom_certificate') else 'no'}")
        print(f"pending_update_count: {result.get('pending_update_count')}")
        print(f"ultimo_error: {result.get('last_error_message')}")
        print(f"ultimo_error_fecha: {result.get('last_error_date')}")
