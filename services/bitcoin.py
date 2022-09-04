from services.redis import redis
from chatbot import bot
from bitcoin import Bitcoin
from configs import BTC_HOST, BTC_PASS, BTC_USER, BTC_ZMQ_TX
from json import loads

import zmq 

bitcoin = Bitcoin(BTC_HOST)
bitcoin.auth(BTC_USER, BTC_PASS)

def start():
    context = zmq.Context()

    subscribe = context.socket(zmq.SUB)
    subscribe.setsockopt_string(zmq.SUBSCRIBE, "rawtx")
    subscribe.connect(BTC_ZMQ_TX)
    
    while True:
        topic, body, _ = subscribe.recv_multipart()
        if (topic != b"rawtx"):
            continue
        
        # Get the transaction txid.
        txid = bitcoin.decoderawtransaction(body.hex()).get("txid")
        if (txid == None):
            continue
        
        # List last transactions.
        transactions = bitcoin.listtransactions()

        # Search for the transaction in the last transactions list.
        transaction = list(filter(lambda tx: 
            (tx["txid"] == txid) and \
                (tx["category"] == "receive") and \
                    (tx["confirmations"] >= 1) and \
                        (tx["involvesWatchonly"] == True) and \
                            (tx["amount"] >= 1e-05), transactions))
        if not (transaction):
            continue            
        else:
            transaction = transaction[0]
        
        user = redis.get(transaction["address"])
        if not (user):
            continue
        else:
            user = loads(user)["id"]
        
        amount = round(transaction["amount"] * pow(10, 8))
        bot.send_message(user, f"Você recebeu {amount} sats.")