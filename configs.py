from lib.ngrok import get_ngrok_url
from os import environ

# API configuration.
API_HOST = environ.get("API_HOST", "0.0.0.0")
API_PORT = int(environ.get("API_PORT", 9651))

# Telegram configuration.
TELEGRAM_API_TOKEN = environ["TELEGRAM_API_TOKEN"]

# Redis configuration.
REDIS_HOST = environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(environ.get("REDIS_PORT", 6379))
REDIS_PASS = environ.get("REDIS_PASS")

# Ngrok configuration.
NGROK_ACTIVE = environ.get("NGROK_ACTIVE")
if (NGROK_ACTIVE == None):
    NGROK_ACTIVE = False
else:
    if (NGROK_ACTIVE == "true"):
        NGROK_ACTIVE = True
    else:
        NGROK_ACTIVE = False

PUBLIC_URL_ENDPOINT = environ.get("PUBLIC_URL_ENDPOINT", f"http://127.0.0.1:{API_PORT}")
if (NGROK_ACTIVE == True) and (PUBLIC_URL_ENDPOINT == f"http://127.0.0.1:{API_PORT}"):
    PUBLIC_URL_ENDPOINT = get_ngrok_url()
