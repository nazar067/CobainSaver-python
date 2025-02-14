import re
from aiogram import Bot, Dispatcher
from downloader.send_album import send_social_media_album
from downloader.x.extract_data import extract_twitter_data
from localisation.get_language import get_language
from localisation.translations.downloader import translations


async def fetch_twitter_content(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id, msg_id) -> None:
    """
    📩 Загружает и отправляет контент из Twitter.
    """
    pool = dp["db_pool"]
    chat_language = await get_language(pool, chat_id)

    data = await extract_twitter_data(url)
    if "error" in data:
        return await bot.send_message(chat_id, text=translations["unavaliable_content"][chat_language])

    media_urls = data["media_urls"]
    caption = re.sub(r"#\S+", "", data["caption"]).strip() 

    await send_social_media_album(bot, chat_id, chat_language, business_connection_id, media_urls, caption, msg_id, pool=pool)