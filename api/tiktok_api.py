import aiohttp


async def is_server_alive(api_url: str, timeout: int = 3) -> bool:
    """
    Проверяет, отвечает ли сервер (жив ли).
    Делает HEAD-запрос для минимальной нагрузки.
    Возвращает True, если сервер ответил статусом < 500.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(api_url, timeout=timeout) as resp:
                return resp.status < 500
    except Exception:
        return False