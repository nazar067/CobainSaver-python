from aiogram.types import InputMediaPhoto
from aiogram import Bot
import re

from downloader.media import send_media_group

async def send_tiktok_images(bot: Bot, chat_id: int, chat_language, business_connection_id, images: list, title: str):
    """
    Отправляет изображения из TikTok в виде альбома (по 10 фото за раз).
    """
    title = re.sub(r"#\S+", "", title).strip()
    title = title[:800] + "..." if len(title) > 800 else title

    media_album = []
    count = 0

    for image_url in images:
        if count == 0:
            media_album.append(InputMediaPhoto(media=image_url, caption=f"{title}", parse_mode="HTML"))
            count += 1
        else:
            media_album.append(InputMediaPhoto(media=image_url))

    batch_size = 10
    for i in range(0, len(media_album), batch_size):
        batch = media_album[i:i + batch_size]
        await send_media_group(bot, chat_id, chat_language, business_connection_id, batch)
