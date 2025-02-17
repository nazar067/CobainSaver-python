import asyncio
import yt_dlp
import os
import requests
from typing import Optional
from aiogram import Bot, Dispatcher

from downloader.media import del_media_content, send_audio
from downloader.playlist import process_music_playlist
from localisation.get_language import get_language
from user.get_user_path import get_user_path
from localisation.translations.downloader import translations
from utils.fetch_data import fetch_youtube_music_data

MAX_SIZE_MB = 50 

async def process_youtube_music(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id: Optional[str] = None, msg_id = None) -> str:
    """
    Обрабатывает скачивание аудио с YouTube Music и отправляет его пользователю.
    """
    if "/playlist?" in url:
        await process_music_playlist(bot, dp, business_connection_id, chat_id, url, user_msg_id=msg_id)
        return
    pool = dp["db_pool"]
    user_folder = await get_user_path(chat_id)

    data = await fetch_youtube_music_data(url, user_folder)
    
    chat_language = await get_language(pool, chat_id)

    if "error" in data:
        await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["unavaliable_content"][chat_language], reply_to_message_id=msg_id)

    file_path = data["file_path"]
    audio_title = data["audio_title"]
    duration = data["duration"]
    thumbnail_path = data["thumbnail_path"]
    author = data["author"]
    if os.path.exists(file_path):
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb <= MAX_SIZE_MB:
            return await send_audio(bot, chat_id, msg_id, chat_language, business_connection_id, file_path, audio_title, thumbnail_path, duration, author)

        await del_media_content(file_path)
        if thumbnail_path:
            await del_media_content(thumbnail_path)

    return await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["large_content"][chat_language], reply_to_message_id=msg_id)
