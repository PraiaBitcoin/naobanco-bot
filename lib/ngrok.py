from os import environ

import requests

NGROK_WEB_INTERFACE = environ.get("NGROK_WEB_INTERFACE", "http://127.0.0.1:4040")

def get_ngrok_url() -> dict:
    return requests.get(f"{NGROK_WEB_INTERFACE}/api/tunnels/").json()["tunnels"][0]["public_url"]