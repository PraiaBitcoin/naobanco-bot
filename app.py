from services.redis import redis
from threading import Thread
from binascii import unhexlify
from services import bitcoin
from chatbot import bot

from database import db 
from configs import API_HOST, API_PORT, PUBLIC_URL_ENDPOINT, RSA_PRIVATE_KEY

from fastapi import FastAPI, Body, HTTPException, Request
from tinydb import Query

from secrets import token_hex
from lnbits import Lnbits
from json import dumps, loads

import uvicorn
import telebot

import rsa

# Generate random key to make it difficult
# for an attacker to find the webhook point.
WEBHOOK_TELEGRAM_TOKEN = token_hex(64)

api = FastAPI(docs_url=None, redoc_url=None)

@api.post(f"/api/webhook/telegram")
def telegram_webhook(payload: dict = Body(...), request: Request = Request):
    if (request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_TELEGRAM_TOKEN):
        raise HTTPException(401)

    bot.process_new_updates([telebot.types.Update.de_json(payload)])

@api.get("/.well-known/lnurlp/{username}")
async def lightning_address(username: str, request: Request = Request):
    callback = f"{request.base_url}lnurl/pay/{username}"
    minSendable = 1 * 1000
    maxSendable = 100000000 * 1000
    return {"status":"OK", "commentAllowed": 255, "callback": callback, "minSendable": minSendable, "maxSendable": maxSendable, "tag": "payRequest"}

@api.get("/lnurl/pay/{username}")
async def lnurl_pay_create_invoice(username: str, amount: int = 1000, comment: str = ""):
    if (amount < 1000):
        return {"status":"ERROR", "reason": "The minimum amount is 1 sat."}

    amount = round(amount / 1000)
    wallet = db.get(Query().username == username)
    if (wallet == None):
        return {"status":"ERROR", "reason": "Username does not exist."}
    
    if (wallet["admin_key"] != None):
        wallet["admin_key"] = rsa.decrypt(unhexlify(wallet["admin_key"]), RSA_PRIVATE_KEY).decode()
    
    lnbits = Lnbits(wallet["admin_key"], wallet["invoice_key"], url=wallet["api"])
    invoice = lnbits.create_invoice(amount, comment, webhook=PUBLIC_URL_ENDPOINT + "/api/webhook/lnbits")
    
    payment_hash = invoice["payment_hash"]
    payment_request = invoice["payment_request"]
    
    redis.set(f"invoice.{payment_hash}", dumps({"id": wallet["id"]}))
    redis.expire(f"invoice.{payment_hash}", 86400)
    return {"status": "OK", "routes": [], "pr": payment_request}

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

@api.post("/api/webhook/lnswap/{userid}")
def lnswap_webhook(userid: str, payload: dict = Body(...)):
    if (payload.get("type") == "loop-out"):
        txid = payload["to"]["txid"]
        address = payload["to"]["address"]
        amount = int(payload["to"]["amount"] * pow(10, 8))

        message = f"O pagamento de {amount} sats para o endereço {address} foi processado com sucesso.\n\n"
        message+= f"<b>Txid:</b> <code>{txid}</code>"
        return bot.send_message(userid, message)
    
bot.remove_webhook()

def start():
    threads = []

    thread = Thread(target=lambda: uvicorn.run(api, host=API_HOST, port=API_PORT))
    thread.start()
    threads.append(thread)

    try:
        bot.set_webhook(
            url=f"{PUBLIC_URL_ENDPOINT}/api/webhook/telegram", 
            secret_token=WEBHOOK_TELEGRAM_TOKEN,
            timeout=60 * 2,
            drop_pending_updates=True
        )
    except:
        thread = Thread(target=lambda : bot.polling(skip_pending=True))
        thread.start()
        threads.append(thread)    
    
    thread = Thread(target=bitcoin.start)
    thread.start()
    threads.append(thread)

    for t in threads:
        t.join()
    