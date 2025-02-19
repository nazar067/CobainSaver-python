import asyncio
import logging
import os
import aiohttp
import requests
import yt_dlp
import time

from fake_useragent import UserAgent
from stem import Signal
from stem.control import Controller
from utils.get_name import get_random_file_name

DEFAULT_THUMBNAIL_URL = "https://github.com/TelegramBots/book/raw/master/src/docs/photo-ara.jpg"

class TorProxy:
    """Tor Proxy Manager"""

    def __init__(self, ip="127.0.0.1", port=1881, password="Passwort", control_port=9051, delay=5):
        self.ip = ip
        self.port = port
        self.password = password
        self.control_port = control_port
        self.delay = delay

        self.controller = Controller.from_port(port=self.control_port)
        self.controller.authenticate(self.password)

    @property
    def proxy(self):
        return {
            'http': f'socks5://{self.ip}:{self.port}',
            'https': f'socks5://{self.ip}:{self.port}',
        }

    def get_next(self):
        self.controller.signal(Signal.NEWNYM)
        time.sleep(self.delay)
        return self.proxy


# Используем TorProxy
proxy_manager = TorProxy()

async def fetch_youtube_data(url: str, user_folder: str, quality: str) -> dict:
    """
    Асинхронно извлекает данные видео, скачивает видео и превью.
    """
    ua = UserAgent()
    ydl_opts = {
        'format': f"bestvideo[height<={quality}]+bestaudio/best",
        'outtmpl': os.path.join(user_folder, get_random_file_name("%(ext)s")),
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'http_headers': {'User-Agent': ua.random},
        'proxy': proxy_manager.get_next()["http"],
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
    ua = UserAgent()
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(user_folder, get_random_file_name("%(ext)s")),
        'quiet': True,
        'noplaylist': True,
        'http_headers': {'User-Agent': ua.random},
        'proxy': proxy_manager.get_next()["http"],
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
            async with session.get(url, proxy=proxy_manager.get_next()["http"]) as resp:
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
