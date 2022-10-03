# Lnbits Chatbot

A simple telegram wallet to use with lnbits.

## Resources:

- [x] Import Lnbits wallet via QRCode
- [x] Basic wallet resources (Balance, Transactions, Receive, Pay)
- [x] Lightning Address support
- [x] Watch Only Bitcoin Address (Onchain)
- [x] Recharge via LNURLw

## Setup:

1) Configuring the Bot:
- Create your bot using [@BotFather](https://t.me/BotFather)
- Type /newbot (Create an @ and a Name for the ChatBot)
- Take the token that was generated.

2) Configuration bitcoin.conf:
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
3) Create an account on [Ngrok](https://ngrok.com/).

4) Install the bot and configure with few commands.
```bash
$ git clone https://github.com/leffw/lnbits-chatbot
$ cd ./lnbits-chatbot
$ chmod +x autopilote.sh 
$ chmod +x start.sh
$ ./autopilote.sh
$ ./start.sh
```
