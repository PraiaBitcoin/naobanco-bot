# Boltcard Chatbot

A simple telegram wallet to use with boltcard.

## Resources:

- [x] Import Lnbits wallet via QRCode
- [x] Basic wallet resources (Balance, Transactions, Receive, Pay)
- [x] Lightning Address support
- [x] Watch Only Bitcoin Address (Onchain)

## Setup:

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

```bash
$ git clone https://github.com/leffw/lnbits-chatbot
$ cd ./lnbits-chatbot
$ chmod +x autopilote.sh 
$ chmod +x start.sh
$ ./autopilote.sh
$ ./start.sh
```
