import asyncio
import requests
import yt_dlp
import os
from aiogram import Bot, Dispatcher

from downloader.media import del_media_content, send_video
from localisation.get_language import get_language
from user.get_user_path import get_user_path
from localisation.translations.downloader import translations

MAX_SIZE_MB = 50  
DEFAULT_THUMBNAIL_URL = "https://github.com/TelegramBots/book/raw/master/src/docs/photo-ara.jpg"
QUALITIES = ["1080", "720", "480", "360", "240", "144"]  

async def process_youtube_video(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id) -> str:
    """
    Обрабатывает скачивание и отправку видео пользователю.
    """
    pool = dp["db_pool"]
    chat_language = await get_language(pool, chat_id)
    if "/live/" in url:
        return await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["live_unavaliable_content"][chat_language])
    user_folder = await get_user_path(chat_id)

    for quality in QUALITIES:
        data = await fetch_youtube_data(url, user_folder, quality)

        if "error" in data:
            return await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["unavaliable_content"][chat_language])

        file_path = data["file_path"]
        video_title = data["video_title"]
        duration = data["duration"]
        thumbnail_path = data["thumbnail_path"]

        if os.path.exists(file_path):
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb <= MAX_SIZE_MB:
                return await send_video(bot, chat_id, chat_language, business_connection_id, file_path, video_title, thumbnail_path, duration)

            await del_media_content(file_path)
            if thumbnail_path:
                await del_media_content(thumbnail_path)

    return await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["large_content"][chat_language])

async def fetch_youtube_data(url: str, user_folder: str, quality: str) -> dict:
    """
    Асинхронно извлекает данные видео, скачивает видео и превью.
    """
    ydl_opts = {
        'format': f"bestvideo[height<={quality}]+bestaudio/best",
        'outtmpl': f'{user_folder}/%(title)s.%(ext)s',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
    }

    def download_video():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        info_dict = await asyncio.to_thread(download_video)

        file_path = info_dict["requested_downloads"][0]["filepath"]
        video_title = info_dict.get("title", "Видео без названия")
        video_id = info_dict.get("id", None)
        duration = info_dict.get("duration", 0)

        thumbnail_path = None
        if video_id:
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            thumbnail_path = os.path.join(user_folder, f"{video_id}_thumbnail.jpg")
            download_thumbnail(thumbnail_url, thumbnail_path)

        return {
            "file_path": file_path,
            "video_title": video_title,
            "video_id": video_id,
            "duration": duration,
            "thumbnail_path": thumbnail_path
        }

    except Exception as e:
        return {"error": f"Ошибка при скачивании: {str(e)}"}


def download_thumbnail(thumbnail_url: str, save_path: str) -> None:
    """
    Скачивает превью по URL. В случае ошибки загружает резервное изображение.
    """
    try:
        response = requests.get(thumbnail_url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return
    except:
        print()

    try:
        response = requests.get(DEFAULT_THUMBNAIL_URL, stream=True, timeout=10)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
    except Exception as e:
        print()
