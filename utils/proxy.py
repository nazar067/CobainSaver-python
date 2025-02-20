import random

PROXIES = [
    "socks5://127.0.0.1:9050",
    "socks4://127.0.0.1:9050",
    "http://proxy2.com:3128",
    None
]

def get_random_proxy():
    proxy = random.choice(PROXIES)
    return proxy if proxy else None