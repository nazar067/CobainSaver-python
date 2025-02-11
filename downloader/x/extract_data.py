import aiohttp
from config import TWITTER_API

TWITTER_API_URL = TWITTER_API

async def extract_twitter_data(url: str) -> dict:
    """
    🐦 Извлекает данные из Twitter API: ссылки на фото, видео, текст.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(TWITTER_API_URL + url) as response:
            if response.status != 200:
                return {"error": "Ошибка API"}

            data = await response.json()

    if "mediaURLs" not in data:
        return {"error": "Медиафайлы не найдены"}

    return {
        "media_urls": data.get("mediaURLs", []),
        "caption": data.get("text", "Twitter Post"),
    }
