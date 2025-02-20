import os
import random

proxy_list = [
    "socks4://127.0.0.1:9050",
    "socks5://127.0.0.1:9050",
    None
]

async def get_random_proxy():
    return random.choice(proxy_list)

async def restart_tor():
    os.system("sudo systemctl restart tor")