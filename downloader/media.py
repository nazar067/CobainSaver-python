import os
from aiogram import Bot
from aiogram.types import FSInputFile

async def send_video(bot: Bot, chat_id: int, file_path: str) -> None:
    """
    Отправляет скачанное видео в чат.
    """
    try:
        video = FSInputFile(file_path)
        await bot.send_video(chat_id, video, caption="Вот ваше видео! 🎥")
        await del_media_content(file_path)
    except Exception as e:
        await bot.send_message(chat_id, f"Ошибка при отправке видео: {str(e)}")
        
        
async def del_media_content(file_path):
    os.remove(file_path)
