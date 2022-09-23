from services.redis import redis
from embit.networks import NETWORKS
from embit.script import p2wpkh
from embit.bip32 import HDKey
from middlewares import checkIfExistWallet
from binascii import unhexlify

from lib.rate import get_price_bitcoin_in_brl
from database import db
from bitcoin import Bitcoin
from configs import BTC_HOST, BTC_NETWORK, BTC_PASS, BTC_USER, LNBITS_DEFAULT_URL, PUBLIC_URL_ENDPOINT, RSA_PRIVATE_KEY, TELEGRAM_API_TOKEN, RSA_PUB_KEY
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
import rsa

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

bitcoin = Bitcoin(BTC_HOST)
bitcoin.auth(BTC_USER, BTC_PASS)

bot = TeleBot(TELEGRAM_API_TOKEN, parse_mode="HTML")

@bot.message_handler(content_types=["photo", "document"])
def load_qrcode(data: object):    
    if (data.content_type == "photo"):
        file_name = data.photo[-1].file_id

    if (data.content_type == "document"):
        file_name = data.document.file_id

    file_path = bot.get_file(file_name).file_path
    file_data = bot.download_file(file_path)
    with open(f"data/{file_name}", "wb") as w:
        w.write(file_data)

    # Detect QRCODE using opencv library.
    qr = list(QRCodeDetector().detectAndDecode(imread(f"data/{file_name}")))
    if (qr[0] == None):
        return bot.reply_to(data, "Não foi possível ler o QRCode.")
    else:
        qr = qr[0].replace("\n", "").strip()

    if not (qr):
        return bot.reply_to(data, "Não foi possível ler o QRCode.")
    
    # Delete temporary image.
    remove(f"data/{file_name}")

    user_id = data.from_user.id
    username = data.from_user.username
    if ("wallet?usr" in qr):
        wallet = loads(search(r"window\.wallet = ({.*});", requests.get(qr).text).group(1))
        wallet["adminkey"] = rsa.encrypt(wallet["adminkey"].encode(), RSA_PUB_KEY).hex()

        api = qr.split("/wallet")[0] + "/api"
        if not db.get(Query().id == user_id):
            db.insert({"id": user_id, "username": username, "api": api, "admin_key": wallet["adminkey"], "invoice_key": wallet["inkey"]})
        else:
            db.update({"api": api, "username": username, "admin_key": wallet["adminkey"], "invoice_key": wallet["inkey"]}, Query().id == user_id)

        try:
            balance = Lnbits(wallet["adminkey"], wallet["inkey"], url=api).get_wallet()
            if (balance.get("detail") != None):
                raise Exception(balance["detail"])
            
            message = "Sua carteira %s foi importada com sucesso." % (wallet["id"])
            message+= "\n\nℹ️ É recomendável apagar o QRCODE que você enviou."
            return bot.reply_to(data, message)
        except:
            return bot.reply_to(data, "Sua carteira invalida.")

    elif ("admin_key" in qr) or ("invoice_key" in qr):
        invoice_key = None
        admin_key = None
        if not db.get(Query().id == user_id):
            if ("admin_key" in qr):
                admin_key = qr.replace("admin_key:", "")
                qr = rsa.encrypt(admin_key.encode(), RSA_PUB_KEY).hex()
                db.insert({"id": user_id, "api": LNBITS_DEFAULT_URL, "username": username, "admin_key": qr, "invoice_key": None})
            else:
                qr = qr.replace("invoice_key:", "")
                db.insert({"id": user_id, "api": LNBITS_DEFAULT_URL, "username": username, "admin_key": None, "invoice_key": qr})
        else:
            if ("admin_key" in qr):
                admin_key = qr.replace("admin_key:", "") 
                qr = rsa.encrypt(admin_key.encode(), RSA_PUB_KEY).hex()
                db.update({"username": username, "admin_key": qr}, Query().id == user_id)
            else:
                invoice_key = qr.replace("invoice_key:", "")
                db.update({"username": username, "invoice_key": invoice_key}, Query().id == user_id)
        try:
            balance = Lnbits(admin_key, invoice_key, url=LNBITS_DEFAULT_URL).get_wallet()
            if (balance.get("detail") != None):
                raise Exception(balance["detail"])
            
            message = "Sua carteira foi importada com sucesso."
            message+= "\n\nℹ️ É recomendável apagar o QRCODE que você enviou."
            return bot.reply_to(data, message)
        except:
            return bot.reply_to(data, "Sua carteira invalida.")

    elif (qr[1:4].upper() in ["PUB"]):
        try:
            zpub = HDKey.from_string(qr)
            zpub.version = NETWORKS[BTC_NETWORK]["zpub"]
        except:
            return bot.reply_to(data, "Não foi possível importar á carteira de visualização.")
        
        for path in range(0, 20):
            address = p2wpkh(zpub.derive(f"m/0/{path}").key).address(NETWORKS[BTC_NETWORK])
            redis.set(address, dumps({"id": user_id}))
        
        if not db.get(Query().id == user_id):
            db.insert({"id": user_id, "zpub": qr, "path": 0})
        else:
            db.update({"zpub": qr, "path": 0}, Query().id == user_id)
        
        message = "Sua carteira de visualização foi importado com sucesso."
        message+= "\n\nℹ️ É recomendável apagar o QRCODE que você enviou."
        return bot.reply_to(data, message)
    else:
        return bot.reply_to("QRCode invalido.")

@bot.message_handler(commands=["me", "conta", "account"])
@checkIfExistWallet
def me(data: object):
    address = data.from_user.username + "@" + PUBLIC_URL_ENDPOINT.split("//")[-1].replace("/", "")
    message = f"Você pode receber bitcoins usando este endereço <code>{address}</code>."
    return bot.reply_to(data, message)

@bot.message_handler(commands=["balance", "saldo"])
@checkIfExistWallet
def balance(data: object):
    wallet = db.get(Query().id == data.from_user.id)
    if (wallet["admin_key"] != None):
        wallet["admin_key"] = rsa.decrypt(unhexlify(wallet["admin_key"]), RSA_PRIVATE_KEY).decode()
    
    lnbits = Lnbits(wallet["admin_key"], wallet["invoice_key"], url=wallet["api"])

    get_price_btc_in_brl = get_price_bitcoin_in_brl()["bid"]

    # Get bitcoin balance from wallet.
    balance = lnbits.get_wallet()

    balance_in_sat = round(balance["balance"] / 1000)
    balance_in_btc = balance_in_sat / pow(10, 8)
    balance_in_brl = balance_in_btc * get_price_btc_in_brl

    message = "<b>Saldo disponível:</b> "
    message+= f"{balance_in_sat} sats (~ R$ {locale.currency(balance_in_brl, symbol=None)})\n"
    return bot.reply_to(data, message)

@bot.message_handler(commands=["receive", "receber", "invoice"], regexp="/receber|/receive|/invoice [0-9]")
@checkIfExistWallet
def receive(data: object):
    wallet = db.get(Query().id == data.from_user.id)
    if (wallet["admin_key"] != None):
        wallet["admin_key"] = rsa.decrypt(unhexlify(wallet["admin_key"]), RSA_PRIVATE_KEY).decode()
    
    lnbits = Lnbits(wallet["admin_key"], wallet["invoice_key"], url=wallet["api"])

    amount = int(data.text.split()[-1])
    invoice = lnbits.create_invoice(amount, webhook=PUBLIC_URL_ENDPOINT + "/api/webhook/lnbits")

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

    from_wallet = db.get((Query().id == data.from_user.id) & (Query().admin_key != None))
    if (from_wallet == None):
        return bot.reply_to(data, "Sua carteira é apenas de visualização, não é possível acessar este recurso.")

    from_wallet["admin_key"] = rsa.decrypt(unhexlify(from_wallet["admin_key"]), RSA_PRIVATE_KEY).decode()
    from_lnbits = Lnbits(from_wallet["admin_key"], from_wallet["invoice_key"], url=from_wallet["api"])
    if ("lnbc" in address):
        pay_invoice = from_lnbits.pay_invoice(address)
        payment_hash = pay_invoice.get("payment_hash")
        if (payment_hash == None):
            return bot.reply_to(data, "Não foi possível pagar á fatura.")
        else:
            decode_invoice = from_lnbits.decode_invoice(address)
            amount = round(decode_invoice.get("amount_msat") / 1000)
            return bot.reply_to(data, f"Fatura <code>{payment_hash}</code> de {amount} sats paga.")
    
    elif (address[0] == "@") and (amount != None):
        to_wallet = db.get(Query().username == address[1:])
        if (to_wallet == None) or (to_wallet["id"] == from_wallet["id"]):
            return bot.reply_to(data, "Não foi possível pagar á fatura.")
        
        to_lnbits = Lnbits(to_wallet["admin_key"], to_wallet["invoice_key"], url=to_wallet["api"])

        # Generate lightning invoice.
        invoice = to_lnbits.create_invoice(amount, webhook=PUBLIC_URL_ENDPOINT + "/api/webhook/lnbits")["payment_request"]

        pay_invoice = from_lnbits.pay_invoice(invoice)
        payment_hash = pay_invoice.get("payment_hash")
        if (payment_hash == None):
            return bot.reply_to(data, f"Não foi possível pagar {address}.")
        else:
            return bot.reply_to(data, f"{amount} sats foi pago {address}.")
    
    elif ("@" in address) and (amount != None):
        username, service = address.split("@")
        try:
            callback = requests.get(f"http://{service}/.well-known/lnurlp/{username}").json()["callback"]   
            invoice = requests.get(callback, params={"amount": amount * 1000}).json()["pr"]
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
    if (wallet["admin_key"] != None):
        wallet["admin_key"] = rsa.decrypt(unhexlify(wallet["admin_key"]), RSA_PRIVATE_KEY).decode()
    
    lnbits = Lnbits(wallet.get("admin_key"), wallet.get("invoice_key"), url=wallet.get("api"))

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
    zpub.version = NETWORKS[BTC_NETWORK]["zpub"]
    path = wallet["path"]

    address = p2wpkh(zpub.derive(f"m/0/{path}").key).address(NETWORKS[BTC_NETWORK])
    if (redis.get(address) == None):
        redis.set(address, dumps({"id": user_id}))
        bitcoin.importaddress(address)

    create_qrcode = MakeQR(f"bitcoin:{address}")
    qrcode_bytes = BytesIO()

    create_qrcode.save(qrcode_bytes)
    qrcode_bytes.seek(0)

    caption = f"Você pode receber bitcoins usando endereço <code>{address}</code>."
    return bot.send_photo(user_id, qrcode_bytes, caption=caption)