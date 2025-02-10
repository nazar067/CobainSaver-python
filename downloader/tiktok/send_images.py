from aiogram.types import InputMediaPhoto
from aiogram import Bot
import re

from downloader.media import send_media_group

async def send_tiktok_images(bot: Bot, chat_id: int, chat_language, business_connection_id, images: list, title: str):
    """
    Отправляет изображения из TikTok в виде альбома.
    """
    title = re.sub(r"#\S+", "", title).strip()
    title = title[:800] + "..." if len(title) > 800 else title

    media_album = []
    for index, image_url in enumerate(images):
        if index == 0:
            media_album.append(InputMediaPhoto(media=image_url, caption=title, parse_mode="HTML"))
        else:
            media_album.append(InputMediaPhoto(media=image_url))
            
    await send_media_group(bot, chat_id, chat_language, business_connection_id, media_album)
