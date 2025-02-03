import os
from typing import Optional
from aiogram import Bot
from aiogram.types import FSInputFile

async def send_video(bot: Bot, chat_id: int, file_path: str, title: str = None, thumbnail_path: Optional[str] = None, duration: int = None) -> None:
    """
    Отправляет скачанное видео в чат.
    """
    try:
        video = FSInputFile(file_path)
        thumbnail = FSInputFile(thumbnail_path) if thumbnail_path else None
        await bot.send_video(chat_id, video, caption=title, thumbnail=thumbnail, duration=duration)
        await del_media_content(file_path)
        if thumbnail_path:
            await del_media_content(thumbnail_path)
    except Exception as e:
        await bot.send_message(chat_id, f"Ошибка при отправке видео: {str(e)}")
        
        
async def del_media_content(file_path):
    os.remove(file_path)
