import re
from aiogram.types import InputMediaPhoto, InputMediaVideo
from downloader.media import send_media_group
from utils.detect_type import detect_file_type

async def send_social_media_album(bot, chat_id, chat_language, business_connection_id, media_list: list, caption: str):
    """
    📩 Отправляет альбом из фото и видео (по 10 файлов за раз).
    Поддерживает TikTok и Twitter.
    """
    caption = re.sub(r"#\S+", "", caption).strip()  # Удаляем хэштеги
    caption = caption[:800] + "..." if len(caption) > 800 else caption  # Ограничение 800 символов

    media_album = []
    count = 0  # Контроль первой подписи

    for media_url in media_list:
        file_type = detect_file_type(media_url)

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

    # 🔹 Отправка альбома по 10 файлов за раз
    batch_size = 10
    for i in range(0, len(media_album), batch_size):
        batch = media_album[i:i + batch_size]
        await send_media_group(bot, chat_id, chat_language, business_connection_id, batch)
