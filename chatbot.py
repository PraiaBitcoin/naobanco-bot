from middlewares import checkIfExistWallet
from lib.rate import get_price_bitcoin_in_brl
from database import db
from configs import TELEGRAM_API_TOKEN
from telebot import TeleBot
from tinydb import Query
from lnbits import Lnbits

from json import loads
from cv2 import QRCodeDetector, imread
from re import search
from os import remove

import requests
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
    if not db.get(Query().id == user_id):
        if ("wallet?usr" in qr):
            service = qr.split("/wallet")[0] + "/api"
            wallet = loads(search(r"window\.wallet = ({.*});", requests.get(qr).text).group(1))
            db.insert({"id": user_id, "api": service, "admin_key": wallet["adminkey"], "invoice_key": wallet["inkey"]})
            return bot.reply_to(data, "Sua carteira %s foi importada com sucesso." % (wallet["id"]))
    else:
        if ("wallet?usr" in qr):
            service = qr.split("/wallet")[0] + "/api"
            wallet = loads(search(r"window\.wallet = ({.*});", requests.get(qr).text).group(1))
            db.update({"api": service, "admin_key": wallet["adminkey"], "invoice_key": wallet["inkey"]}, Query().id == user_id)
            return bot.reply_to(data, "Sua carteira %s foi importada com sucesso." % (wallet["id"]))

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
    message+= f"<b>BTC:</b> {balance_in_sat}\n"
    message+= f"<b>BRL:</b> {locale.currency(balance_in_brl, symbol=None)}"
    return bot.reply_to(data, message)