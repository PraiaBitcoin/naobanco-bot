from os.path import exists
from os import environ

import rsa

# API configuration.
API_HOST = environ.get("API_HOST", "0.0.0.0")
API_PORT = int(environ.get("API_PORT", 80))

# Telegram configuration.
TELEGRAM_API_TOKEN = environ.get("TELEGRAM_API_TOKEN")

# Redis configuration.
REDIS_HOST = environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(environ.get("REDIS_PORT", 6379))
REDIS_PASS = environ.get("REDIS_PASS")

# PUBLIC URL ENDPOINT
PUBLIC_URL_ENDPOINT = environ.get("PUBLIC_URL_ENDPOINT", f"http://127.0.0.1:{API_PORT}")

# Lnbits configuration.
LNBITS_DEFAULT_URL = environ.get("LNBITS_DEFAULT_URL", "https://legend.lnbits.com/api")

# Bitcoin configuration.
BTC_HOST = environ.get("BTC_HOST", "http://127.0.0.1:8332") 
BTC_USER = environ.get("BTC_USER")
BTC_PASS = environ.get("BTC_PASS")

BTC_ZMQ_TX = environ.get("BTC_ZMQ_TX", "tcp://127.0.0.1:28333")
BTC_NETWORK = environ.get("BTC_NETWORK", "main")

# RSA configuration keys.
RSA_PUB_KEY = environ.get("RSA_PUB_KEY")
RSA_PRIVATE_KEY = environ.get("RSA_PRIVATE_KEY")
if (RSA_PUB_KEY == None) and (RSA_PRIVATE_KEY == None):
    if exists("./data/rsa_private_key.key") == False:
        RSA_PUB_KEY, RSA_PRIVATE_KEY = rsa.newkeys(512)
        with open("./data/rsa_private_key.key", "wb") as w:
            w.write(RSA_PRIVATE_KEY.save_pkcs1())

        with open("./data/rsa_pub_key.pub", "wb") as w:
            w.write(RSA_PUB_KEY.save_pkcs1())
    else:
        with open("./data/rsa_private_key.key", "rb") as r:
            RSA_PRIVATE_KEY = r.read()

        with open("./data/rsa_pub_key.pub", "rb") as r:
            RSA_PUB_KEY = r.read()

if (type(RSA_PRIVATE_KEY) == bytes) and (type(RSA_PUB_KEY) == bytes):
    RSA_PUB_KEY = rsa.PublicKey.load_pkcs1(RSA_PUB_KEY)
    RSA_PRIVATE_KEY = rsa.PrivateKey.load_pkcs1(RSA_PRIVATE_KEY)

LOOP_OUT_ACTIVE = environ.get("LOOP_OUT_ACTIVE", False)
if (LOOP_OUT_ACTIVE == "true"):
    LOOP_OUT_ACTIVE = True
else:
    LOOP_OUT_ACTIVE = False

LN_SWAP_HOST = environ.get("LN_SWAP_HOST", "http://127.0.0.1:1536")