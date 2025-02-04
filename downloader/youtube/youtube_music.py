import yt_dlp
import os
import requests
from typing import Optional
from aiogram import Bot
from aiogram.types import FSInputFile

from downloader.media import del_media_content, send_audio
from downloader.youtube.youtube import download_thumbnail
from downloader.youtube.youtube_music_playlist import process_youtube_music_playlist
from user.get_user_path import get_user_path

MAX_SIZE_MB = 50 

async def process_youtube_music(bot: Bot, url: str, chat_id: int, business_connection_id: Optional[str] = None) -> str:
    """
    Обрабатывает скачивание аудио с YouTube Music и отправляет его пользователю.
    """
    if "/playlist?" in url:
        await process_youtube_music_playlist(bot, chat_id, url)
        return
    user_folder = await get_user_path(chat_id)

    data = fetch_youtube_music_data(url, user_folder)

    if "error" in data:
        return data["error"]

    file_path = data["file_path"]
    audio_title = data["audio_title"]
    duration = data["duration"]
    thumbnail_path = data["thumbnail_path"]
    if os.path.exists(file_path):
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb <= MAX_SIZE_MB:
            return await send_audio(bot, chat_id, business_connection_id, file_path, audio_title, thumbnail_path, duration)

        await del_media_content(file_path)
        if thumbnail_path:
            await del_media_content(thumbnail_path)

    return "Ошибка: даже в минимальном качестве аудио превышает 50MB."


def fetch_youtube_music_data(url: str, user_folder: str) -> dict:
    """
    Извлекает данные аудио и скачивает его с YouTube Music.
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

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)

            file_path = ydl.prepare_filename(info_dict).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            audio_title = info_dict.get("title", "Аудио без названия")
            audio_id = info_dict.get("id", None)
            duration = info_dict.get("duration", 0)

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
                "thumbnail_path": thumbnail_path
            }

    except Exception as e:
        return {"error": f"Ошибка при скачивании: {str(e)}"}
