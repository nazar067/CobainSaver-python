import os
import re
from aiogram.types import InputMediaPhoto, InputMediaVideo, FSInputFile
from downloader.media import send_media_group
from utils.detect_type import detect_file_type
from utils.get_name import get_clear_name

async def send_social_media_album(bot, chat_id, chat_language, business_connection_id, media_list: list, caption: str, msg_id, isAds = True, pool = None):
    """
    📩 Отправляет альбом из фото и видео (по 10 файлов за раз).
    Поддерживает TikTok и Twitter.
    """
    if caption:
        caption = await get_clear_name(caption, 800) 
    media_album = []
    count = 0

    for media_url in media_list:
        file_type = detect_file_type(media_url)
        
        if os.path.exists(media_url):
            media_url = FSInputFile(media_url)
        else:
            media_url = media_url

        if file_type == "photo":
            if count == 0:
                media_album.append(InputMediaPhoto(media=media_url, caption=caption, parse_mode="HTML"))
                count += 1
            else:
                media_album.append(InputMediaPhoto(media=media_url))
        
        elif file_type == "video":
            if count == 0:
                media_album.append(InputMediaVideo(media=media_url, caption=caption, parse_mode="HTML"))
                count += 1
            else:
                media_album.append(InputMediaVideo(media=media_url))

    batch_size = 10
    is_success = False
    for i in range(0, len(media_album), batch_size):
        batch = media_album[i:i + batch_size]
        is_success = await send_media_group(bot, chat_id, msg_id, chat_language, business_connection_id, batch, media_list)
    
    return is_success