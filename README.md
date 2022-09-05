# Boltcard Chatbot

A simple telegram wallet to use with boltcard.

## Resources:

- [x] Import Lnbits wallet via QRCode
- [x] Basic wallet resources (Balance, Transactions, Receive, Pay)
- [x] Lightning Address support
- [x] Watch Only Bitcoin Address (Onchain)

## Setup:

```bash
$ python3 -m virtualenv venv
$ ./venv/bin/pip install -r requirements.txt
```

Configuring the Bot:
- Create your bot using [@BotFather](https://t.me/BotFather)
- Type /newbot (Create an @ and a Name for the ChatBot)
- Take the token that was generated.

Configuration bitcoin.conf:
- Edit the file using nano ~/.bitcoin/bitcoin.conf and configure the file and restart the bitcoind.
```env
server=1
rpcauth=username:password
zmqpubrawtx=tcp://0.0.0.0:28333
rpcbind=0.0.0.0
rpcallowip=0.0.0.0/0
rpcport=8332
listen=1
```
- Edit the .env file using nano .env

```env
TELEGRAM_API_TOKEN = "<token>"
REDIS_PASS = "password"
NGROK_ACTIVE = true

# You can get your bitcoin node credentials 
# at ~/.bitcoin/bitcoin.conf.
BTC_HOST = "http://127.0.0.1:8332"
BTC_USER = "username"
BTC_PASS = "password"

BTC_ZMQ_TX = "tcp://127.0.0.1:28333"

# Take the url of the lnbits service that you will use by default.
LNBITS_DEFAULT_URL = "https://legend.lnbits.com/api"
```

Start your ngrok using the command below (if you don't know how to configure a Google search):
```bash
$ ngrok http 9651 &
```

Starting the ChatBot.
```bash
$ docker-compose up -d
$ ./venv/bin/python __main__.py
```
