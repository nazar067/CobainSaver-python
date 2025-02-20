import asyncio
import logging
import os
import aiohttp
import requests
import yt_dlp
from utils.get_name import get_random_file_name
from config import YT_USERNAME, YT_PASSWORD

DEFAULT_THUMBNAIL_URL = "https://github.com/TelegramBots/book/raw/master/src/docs/photo-ara.jpg"

async def fetch_youtube_data(url: str, user_folder: str, quality: str) -> dict:
    """
    Асинхронно извлекает данные видео, скачивает видео и превью.
    """
    ydl_opts = {
        'username': YT_USERNAME,
        'password': YT_PASSWORD,
        "cookies_from_browser": ("firefox"),
        'format': f"bestvideo[height<={quality}]+bestaudio/best",
        'outtmpl': os.path.join(user_folder, get_random_file_name("%(ext)s")),
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Safari/537.36'},
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
            thumbnail_path = os.path.join(user_folder, get_random_file_name("jpg"))
            await download_file(thumbnail_url, thumbnail_path)

        return {
            "file_path": file_path,
            "video_title": video_title,
            "video_id": video_id,
            "duration": duration,
            "thumbnail_path": thumbnail_path
        }

    except Exception as e:
        logging.error(e)
        return {"error": f"Error with download: {str(e)}"}
    
async def fetch_youtube_music_data(url: str, user_folder: str) -> dict:
    """
    Асинхронно извлекает данные аудио и скачивает его с YouTube Music.
    """
    ydl_opts = {
        'username': YT_USERNAME,
        'password': YT_PASSWORD,
        "cookies_from_browser": ("firefox"),
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(user_folder, get_random_file_name("%(ext)s")),
        'quiet': True,
        'noplaylist': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Safari/537.36'},
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
            thumbnail_path = os.path.join(user_folder, get_random_file_name("jpg"))
            await download_file(thumbnail_url, thumbnail_path)

        return {
            "file_path": file_path,
            "audio_title": audio_title,
            "audio_id": audio_id,
            "duration": duration,
            "thumbnail_path": thumbnail_path,
            "author": author,
        }

    except Exception as e:
        logging.error(e)
        return {"error": f"{str(e)}"}

async def download_file(url: str, save_path: str, isThumbnail: bool = True) -> None:
    """
    Скачивает превью по URL. В случае ошибки загружает резервное изображение.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    with open(save_path, "wb") as f:
                        f.write(await resp.read())
            return
    except Exception as e:
        logging.error(e)
        
    if isThumbnail:
        try:
            response = requests.get(DEFAULT_THUMBNAIL_URL, stream=True, timeout=10)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
        except Exception as e:
            logging.error(e)
    
