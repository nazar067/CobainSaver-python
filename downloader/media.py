import os
from typing import Optional
from aiogram import Bot
from aiogram.types import FSInputFile

async def send_video(bot: Bot, chat_id: int, business_connection_id, file_path: str, title: str = None, thumbnail_path: Optional[str] = None, duration: int = None) -> None:
    """
    Отправляет скачанное видео в чат.
    """
    try:
        video = FSInputFile(file_path)
        thumbnail = FSInputFile(thumbnail_path) if thumbnail_path else None
        await bot.send_video(
            business_connection_id=business_connection_id, 
            chat_id=chat_id, 
            video=video, 
            caption=title, 
            thumbnail=thumbnail, 
            duration=duration)
        await del_media_content(file_path)
        if thumbnail_path:
            await del_media_content(thumbnail_path)
    except Exception as e:
        await bot.send_message(chat_id, f"Ошибка при отправке видео: {str(e)}")
        
async def send_audio(bot: Bot, chat_id: int, business_connection_id: Optional[str], file_path: str, title: str, thumbnail_path: Optional[str], duration: int, author) -> str:
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
            duration=duration,
            thumbnail=thumbnail,
            performer=author
        )
        await del_media_content(file_path)
        if thumbnail_path:
            await del_media_content(thumbnail_path)

        return "Аудио успешно отправлено!"
    except Exception as e:
        return f"Ошибка при отправке аудио: {str(e)}"       
        
async def del_media_content(file_path):
    os.remove(file_path)
