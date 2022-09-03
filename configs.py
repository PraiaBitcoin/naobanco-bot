from os import environ

# Telegram configuration.
TELEGRAM_API_TOKEN = environ["TELEGRAM_API_TOKEN"]

# Redis configuration.
REDIS_HOST = environ.get("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(environ.get("REDIS_PORT", 6373))
REDIS_PASS = environ.get("REDIS_PASS")
