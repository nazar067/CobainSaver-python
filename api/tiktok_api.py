import aiohttp


async def is_server_alive(api_url: str, timeout: int = 5) -> bool:
    """
    Проверяет, доступен ли API.
    Считаем сервер живым, если он вернул любой HTTP-ответ < 500.
    """
    try:
        client_timeout = aiohttp.ClientTimeout(total=timeout)

        async with aiohttp.ClientSession(timeout=client_timeout) as session:
            async with session.get(api_url) as resp:
                return resp.status < 500

    except (aiohttp.ClientError, TimeoutError):
        return False