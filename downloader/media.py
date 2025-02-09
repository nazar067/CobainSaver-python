import os
from typing import Optional
from aiogram import Bot
from aiogram.types import FSInputFile
from localisation.translations.erros import translations
from utils.media_source import get_media_source

async def send_video(bot: Bot, chat_id: int, chat_language, business_connection_id, file_path_or_url: str, title: str = None, thumbnail_path_or_url: Optional[str] = None, duration: int = None, attempt = None) -> None:
    """
    Отправляет скачанное видео в чат (по ссылке или из файла).
    """
    try:
        video = get_media_source(file_path_or_url)
        thumbnail = get_media_source(thumbnail_path_or_url)

        await bot.send_video(
            business_connection_id=business_connection_id,
            chat_id=chat_id,
            video=video,
            caption=title,
            thumbnail=thumbnail,
            duration=duration
        )

        if not file_path_or_url.startswith("http"):
            await del_media_content(file_path_or_url)

        if thumbnail_path_or_url and not thumbnail_path_or_url.startswith("http"):
            await del_media_content(thumbnail_path_or_url)

    except Exception as e:
        if attempt:
            return 2
        else:
            print(f"Ошибка при отправке видео: {str(e)}")
            return await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["send_content_error"][chat_language])
        
async def send_audio(bot: Bot, chat_id: int, chat_language, business_connection_id: Optional[str], file_path: str, title: str, thumbnail_path: Optional[str], duration: int, author) -> str:
    """
    Отправляет аудио в чат.
    """
    try:
        audio = FSInputFile(file_path)
        thumbnail = FSInputFile(thumbnail_path) if thumbnail_path else None

        await bot.send_audio(
            business_connection_id=business_connection_id,
            chat_id=chat_id,
            audio=audio,
            title=title,
            duration=0,
            thumbnail=thumbnail,
            performer=author
        )
        await del_media_content(file_path)
        if thumbnail_path:
            await del_media_content(thumbnail_path)

        return
    except Exception as e:
        print(e)
        return await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["send_content_error"][chat_language])     
        
async def del_media_content(file_path):
    os.remove(file_path)
