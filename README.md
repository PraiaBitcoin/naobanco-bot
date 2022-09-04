# Lnbits Chatbot

A simple telegram wallet to use with boltcard.

## Resources:

- [x] Import Lnbits wallet via QRCode
- [x] Basic wallet resources (Balance, Transactions, Receive, Pay)
- [ ] Lightning Address support
- [ ] Watch Only Bitcoin Address (Onchain)

## Setup:

```bash
$ python3 -m virtualenv venv
$ ./venv/bin/pip install -r requirements.txt
```

Configuring the Bot:
- Create your bot using [@BotFather](https://t.me/BotFather)
- Type /newbot (Create an @ and a Name for the ChatBot)
- Take the token that was generated.

```bash
$ nano .env
```
```env
TELEGRAM_API_TOKEN = <token>
REDIS_PASS = "password"
NGROK_ACTIVE = true
```

Start your ngrok using the command below (if you don't know how to configure a Google search):
```bash
$ ngrok http 9651 &
```

Iniciando o ChatBot.

```bash
$ ./venv/bin/python __main__.py
```
