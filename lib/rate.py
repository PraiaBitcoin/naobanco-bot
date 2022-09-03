from cachetools import cached, TTLCache
from requests import get

@cached(cache=TTLCache(maxsize=1, ttl=30))
def get_price_bitcoin_in_brl() -> dict:
    return get("https://api.biscoint.io/v1/ticker?base=BTC&quote=BRL").json().get("data")