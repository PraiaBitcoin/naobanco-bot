from dotenv import load_dotenv

# Loads the variables of environments in the .env file
# of the current directory.
load_dotenv()

from database import db
from configs import TELEGRAM_API_TOKEN
from telebot import TeleBot
from tinydb import Query

from json import loads
from cv2 import QRCodeDetector, imread
from re import search
from os import remove

import requests

bot = TeleBot(TELEGRAM_API_TOKEN)

@bot.message_handler(content_types=["photo"])
def load_qrcode(data: object):
    file_name = data.photo[-1].file_id
    file_path = bot.get_file(file_name).file_path
    file_data = bot.download_file(file_path)
    with open(f"data/{file_name}", "wb") as w:
        w.write(file_data)
    
    # Detect QRCODE using opencv library.
    data = QRCodeDetector().detectAndDecode(imread(f"data/{file_name}"))
    if (data[1] == None):
        return bot.reply_to(data, "Não foi possível ler o QRCODE.")
    else:
        data = data[0]

    # Delete temporary image.
    remove(f"data/{file_name}")

    user_id = data.from_user.id
    if not db.get(Query().id == user_id):
        if ("wallet?usr" in data):
            wallet = loads(search(r"window\.wallet = ({.*});", requests.get(data[0]).text).group(1))
            db.insert({"id": user_id, "admin_key": wallet["adminkey"], "invoice_key": wallet["inkey"]})
            return bot.reply_to(data, "Sua carteira %s foi importada com sucesso." % (wallet["id"]))
    else:
        if ("wallet?usr" in data):
            wallet = loads(search(r"window\.wallet = ({.*});", requests.get(data[0]).text).group(1))
            db.update({"admin_key": wallet["adminkey"], "invoice_key": wallet["inkey"]}, Query().id == user_id)
            return bot.reply_to(data, "Sua carteira %s foi importada com sucesso." % (wallet["id"]))

if __name__ == "__main__":
    bot.polling()

