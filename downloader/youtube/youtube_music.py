import asyncio
import yt_dlp
import os
import requests
from typing import Optional
from aiogram import Bot, Dispatcher

from downloader.media import del_media_content, send_audio
from downloader.youtube.youtube import download_thumbnail
from downloader.playlist import process_music_playlist
from localisation.get_language import get_language
from user.get_user_path import get_user_path
from localisation.translations.downloader import translations

MAX_SIZE_MB = 50 

async def process_youtube_music(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id: Optional[str] = None) -> str:
    """
    Обрабатывает скачивание аудио с YouTube Music и отправляет его пользователю.
    """
    if "/playlist?" in url:
        await process_music_playlist(bot, business_connection_id, chat_id, url)
        return
    pool = dp["db_pool"]
    user_folder = await get_user_path(chat_id)

    data = await fetch_youtube_music_data(url, user_folder)
    
    chat_language = await get_language(pool, chat_id)

    if "error" in data:
        await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["unavaliable_content"][chat_language])

    file_path = data["file_path"]
    audio_title = data["audio_title"]
    duration = data["duration"]
    thumbnail_path = data["thumbnail_path"]
    author = data["author"]
    if os.path.exists(file_path):
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb <= MAX_SIZE_MB:
            return await send_audio(bot, chat_id, chat_language, business_connection_id, file_path, audio_title, thumbnail_path, duration, author)

        await del_media_content(file_path)
        if thumbnail_path:
            await del_media_content(thumbnail_path)

    return await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["large_content"][chat_language])


async def fetch_youtube_music_data(url: str, user_folder: str) -> dict:
    """
    Асинхронно извлекает данные аудио и скачивает его с YouTube Music.
    """
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{user_folder}/%(title)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }
        ],
    }

    def download_info():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        info_dict = await asyncio.to_thread(download_info)

        file_path = info_dict["requested_downloads"][0]["filepath"]
        audio_title = info_dict.get("title", "Аудио без названия")
        audio_id = info_dict.get("id", None)
        duration = info_dict.get("duration", 0)
        author = info_dict.get("channel", info_dict.get("uploader", "CobainSaver"))
        
        thumbnail_path = None
        if audio_id:
            thumbnail_url = f"https://img.youtube.com/vi/{audio_id}/maxresdefault.jpg"
            thumbnail_path = os.path.join(user_folder, f"{audio_id}_thumbnail.jpg")
            download_thumbnail(thumbnail_url, thumbnail_path)

        return {
            "file_path": file_path,
            "audio_title": audio_title,
            "audio_id": audio_id,
            "duration": duration,
            "thumbnail_path": thumbnail_path,
            "author": author,
        }

    except Exception as e:
        return {"error": f"{str(e)}"}