from services.redis import redis
from chatbot import bot

from database import db 
from configs import API_HOST, API_PORT, PUBLIC_URL_ENDPOINT

from fastapi import FastAPI, Body, HTTPException
from tinydb import Query

from secrets import token_hex
from lnbits import Lnbits
from json import loads

import uvicorn
import telebot

# Generate random key to make it difficult
# for an attacker to find the webhook point.
WEBHOOK_TELEGRAM_TOKEN = token_hex(64)

api = FastAPI(docs_url=None, redoc_url=None)

@api.post(f"/api/webhook/telegram/{WEBHOOK_TELEGRAM_TOKEN}")
def telegram_webhook(payload: dict = Body(...)):
    bot.process_new_updates([telebot.types.Update.de_json(payload)])

@api.post("/api/webhook/lnbits")
def lnbits_webhook(payload: dict = Body(...)):
    payment_request = payload.get("bolt11")
    if not (payment_request):
        raise HTTPException(500)

    payment_hash = payload.get("payment_hash")

    # Get the user_id of payment_hash in redis.
    payment = redis.get(f"invoice.{payment_hash}")
    if (payment == None):
        raise HTTPException(500)
    else:
        payment = loads(payment)

    wallet = db.get(Query().id == int(payment["id"]))
    if (wallet == None):
        raise HTTPException(500)

    lnbits = Lnbits(wallet["admin_key"], wallet["invoice_key"], url=wallet["api"])
    if (lnbits.check_invoice_status(payment_hash) == False):
        raise HTTPException(500)

    decode_invoice = lnbits.decode_invoice(payment_request)
    if (payment_hash != decode_invoice["payment_hash"]):
        raise HTTPException(500)

    if (payload["amount"] != decode_invoice["amount_msat"]):
        raise HTTPException(500)
    
    redis.delete(f"invoice.{payment_hash}")
    
    amount = round(payload.get("amount") / 1000)
    bot.send_message(wallet["id"], f"Você recebeu {amount} sats.")

bot.remove_webhook()
bot.set_webhook(url=PUBLIC_URL_ENDPOINT  + f"/api/webhook/telegram/{WEBHOOK_TELEGRAM_TOKEN}")

def start():
    uvicorn.run(api, host=API_HOST, port=API_PORT)