from embit.networks import NETWORKS
from embit.script import p2wpkh
from embit.bip32 import HDKey

from services.bitcoin import bitcoin
from services.redis import redis
from middlewares import checkIfExistWallet
from lib.rate import get_price_bitcoin_in_brl

from database import db
from configs import PUBLIC_URL_ENDPOINT, TELEGRAM_API_TOKEN
from telebot import TeleBot

from tinydb import Query
from lnbits import Lnbits
from qrcode import make as MakeQR

from time import time
from json import dumps, loads
from cv2 import QRCodeDetector, imread

from io import BytesIO
from re import search
from os import remove

import requests
import timeago
import locale

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

bot = TeleBot(TELEGRAM_API_TOKEN, parse_mode="HTML")

@bot.message_handler(content_types=["photo"])
def load_qrcode(data: object):
    file_name = data.photo[-1].file_id
    file_path = bot.get_file(file_name).file_path
    file_data = bot.download_file(file_path)
    with open(f"data/{file_name}", "wb") as w:
        w.write(file_data)
    
    # Detect QRCODE using opencv library.
    qr = list(QRCodeDetector().detectAndDecode(imread(f"data/{file_name}")))
    if not (qr[0]):
        return bot.reply_to(data, "Não foi possível ler o QRCODE.")
    else:
        qr = qr[0]

    # Delete temporary image.
    remove(f"data/{file_name}")

    user_id = data.from_user.id
    username = data.from_user.username
    if ("wallet?usr" in qr):
        wallet = loads(search(r"window\.wallet = ({.*});", requests.get(qr).text).group(1))
        api = qr.split("/wallet")[0] + "/api"
        if not db.get(Query().id == user_id):
            db.insert({"id": user_id, "username": username, "api": api, "admin_key": wallet["adminkey"], "invoice_key": wallet["inkey"], "type": "full-acess"})
        else:
            db.update({"api": api, "username": username, "admin_key": wallet["adminkey"], "invoice_key": wallet["inkey"], "type": "full-acess"}, Query().id == user_id)
        return bot.reply_to(data, "Sua carteira %s foi importada com sucesso." % (wallet["id"]))
    
    elif (qr[:4].upper() in ["ZPUB"]):
        try:
            zpub = HDKey.from_string(qr)
            zpub.version = NETWORKS["main"]["zpub"]
        except:
            return bot.reply_to(data, "Não foi possível importar sua carteira de apenas visualização.")
        
        for path in range(0, 20):
            address = p2wpkh(zpub.derive(f"m/0/{path}").key).address(NETWORKS["main"])
            bitcoin.importaddress(address)
            redis.set(address, dumps({"id": user_id}))
        
        if not db.get(Query().id == user_id):
            db.insert({"id": user_id, "zpub": qr, "path": 0})
        else:
            db.update({"zpub": qr, "path": 0}, Query().id == user_id)
        return bot.reply_to(data, "Sua carteira de apenas visualização foi importado com sucesso.")
    
@bot.message_handler(commands=["me"])
@checkIfExistWallet
def me(data: object):
    address = data.from_user.username + "@" + PUBLIC_URL_ENDPOINT.split("//")[-1].replace("/", "")
    message = f"Você pode receber bitcoins usando este endereço <code>{address}</code>."
    return bot.reply_to(data, message)

@bot.message_handler(commands=["balance", "saldo"])
@checkIfExistWallet
def balance(data: object):
    wallet = db.get(Query().id == data.from_user.id)
    lnbits = Lnbits(wallet["admin_key"], wallet["invoice_key"], url=wallet["api"])

    get_price_btc_in_brl = get_price_bitcoin_in_brl()["bid"]

    # Get bitcoin balance from wallet.
    balance_in_sat = lnbits.get_wallet()["balance"]
    balance_in_brl = balance_in_sat * get_price_btc_in_brl

    message = "<b>Saldos disponíveis:</b>\n\n"
    message+= f"<b>BTC:</b> {locale.currency(balance_in_sat, symbol=None)}\n"
    message+= f"<b>BRL:</b> {locale.currency(balance_in_brl, symbol=None)}"
    return bot.reply_to(data, message)

@bot.message_handler(commands=["receive", "receber", "invoice"], regexp="/receber|/receive|/invoice [0-9]")
@checkIfExistWallet
def receive(data: object):
    wallet = db.get(Query().id == data.from_user.id)
    lnbits = Lnbits(wallet["admin_key"], wallet["invoice_key"], url=wallet["api"])

    amount = int(data.text.split()[-1])
    invoice = lnbits.create_invoice(amount, webhook=PUBLIC_URL_ENDPOINT)
    payment_hash = invoice["payment_hash"]
    payment_request = invoice["payment_request"]
    
    redis.set(f"invoice.{payment_hash}", dumps({"id": data.from_user.id}))
    redis.expire(f"invoice.{payment_hash}", 86400)

    create_qrcode = MakeQR(f"lightning:{payment_request}")
    qrcode_bytes = BytesIO()
    create_qrcode.save(qrcode_bytes)
    qrcode_bytes.seek(0)

    caption = f"<code>{payment_request}</code>"
    return bot.send_photo(data.from_user.id, qrcode_bytes, caption=caption)

@bot.message_handler(commands=["pay", "pagar"], func=lambda data: len(data.text.split()) >= 2)
@checkIfExistWallet
def pay(data: object):
    command = data.text.split()[1:]
    try:
        amount = int(command[0])
    except:
        amount = None
    
    address = command[-1]

    from_wallet = db.get(Query().id == data.from_user.id)
    if (from_wallet["type"] != "full-acess"):
        return bot.reply_to(data, "Sua carteira é apenas de visualização, não é possível acessar este recurso.")
    
    from_lnbits = Lnbits(from_wallet["admin_key"], from_wallet["invoice_key"], url=from_wallet["api"])
    if ("lnbc" in address):
        pay_invoice = from_lnbits.pay_invoice(address)
        payment_hash = pay_invoice.get("payment_hash")
        if (payment_hash == None):
            return bot.reply_to(data, "Não foi possível pagar á fatura.")
        else:
            decode_invoice = from_lnbits.decode_invoice(address)
            amount = round(decode_invoice.get("amount") / 1000)
            return bot.reply_to(data, f"Fatura <code>{payment_hash}</code> de {amount} sats paga.")
    
    elif (address[0] == "@") and (amount != None):
        to_wallet = db.get(Query().username == address[1:])
        to_lnbits = Lnbits(to_wallet["admin_key"], to_wallet["invoice_key"], url=to_wallet["api"])

        # Generate lightning invoice.
        invoice = to_lnbits.create_invoice(amount)["payment_request"]
    
        pay_invoice = from_lnbits.pay_invoice(invoice)
        payment_hash = pay_invoice.get("payment_hash")
        if (payment_hash == None):
            return bot.reply_to(data, f"Não foi possível pagar {address}.")
        else:
            return bot.reply_to(data, f"{amount} sats foi pagao {address}.")
    
    elif ("@" in address) and (amount != None):
        username, service = address.split("@")[-1]
        try:
            callback = requests.get(f"http://{service}/.well-known/lnurlp/{username}").json()["callback"]   
            invoice = requests.get(callback, params={"amount": amount}).json()["pr"]
        except:
            return bot.reply_to(data, "Não foi possível identificar o Lightning Address.")
        
        pay_invoice = from_lnbits.pay_invoice(invoice)
        payment_hash = pay_invoice.get("payment_hash")
        if (payment_hash == None):
            return bot.reply_to(data, f"Não foi possível pagar {address}.")
        else:
            return bot.reply_to(data, f"{amount} sats foi pagao {address}.")

@bot.message_handler(commands=["transactions", "extrato", "txs", "transacoes"])
@checkIfExistWallet
def transactions(data: object):
    wallet = db.get(Query().id == data.from_user.id)
    lnbits = Lnbits(wallet["admin_key"], wallet["invoice_key"], url=wallet["api"])

    timestamp = time()
    message = "<b>Transações:</b>\n"
    count = 0
    for tx in lnbits.list_payments(limit=5):
        if (count >= 5):
            break
            
        if (tx["pending"] == True):
            continue
        
        count += 1
        settled_at = int(tx["time"])
        amount_sat = int(tx["amount"] / 1000)
        
        amount_sat_format = locale.currency(amount_sat, symbol=None)
        if (amount_sat > 0):
            amount_sat_format = f"+{amount_sat_format}"
        
        settled_at_format = timeago.format(settled_at, timestamp, locale='pt_BR')
        message += f"<i>{amount_sat_format} sats {settled_at_format}</i>\n"
    
    return bot.reply_to(data, message)

@bot.message_handler(commands=["onchain", "address", "addr"])
@checkIfExistWallet
def onchain(data: object):
    user_id = data.from_user.id
    wallet = db.get(Query().id == user_id)
    if (wallet.get("zpub") == None):
        return bot.reply_to(data, "Você precisa importar sua carteira de visualização primeiro, para gerar uma carteira onchain.") 
    
    zpub = HDKey.from_string(wallet["zpub"])
    zpub.version = NETWORKS["main"]["zpub"]
    path = wallet["path"]

    address = p2wpkh(zpub.derive(f"m/0/{path}").key).address(NETWORKS["main"])
    if (redis.get(address) == None):
        redis.set(address, dumps({"id": user_id}))

    create_qrcode = MakeQR(f"bitcoin:{address}")
    qrcode_bytes = BytesIO()

    create_qrcode.save(qrcode_bytes)
    qrcode_bytes.seek(0)
    
    caption = f"Você pode receber bitcoins usando endereço <code>{address}</code>"
    return bot.send_photo(user_id, qrcode_bytes, caption=caption)