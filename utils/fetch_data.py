import asyncio
import logging
import os
import aiohttp
import requests
import yt_dlp
from logs.write_server_errors import log_error
from utils.get_file_size import get_music_size
from utils.get_name import get_random_file_name, sanitize_filename
from utils.get_url import split_time_code_and_video
from utils.service_identifier import identify_service
from utils.text_format import remove_special_chars
from utils.time_format import format_seconds
from localisation.translations.downloader import translations

DEFAULT_THUMBNAIL_URL = "https://github.com/TelegramBots/book/raw/master/src/docs/photo-ara.jpg"

async def fetch_youtube_data(url: str, user_folder: str, quality: str, chat_language) -> dict:
    """
    Асинхронно извлекает данные видео, скачивает видео и превью.
    """
    ydl_opts = {
        "cookies_from_browser": ("firefox"),
        'format': f"bestvideo[height<={quality}]+bestaudio/best",
        'outtmpl': os.path.join(user_folder, get_random_file_name("%(ext)s")),
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        #'cookiefile': 'cookies.txt',
        #'cookies_from_browser': None,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Safari/537.36',
        },
    }
    correct_url = url
    seconds = 0
    if "&t=" in url:
        parsed_url = await split_time_code_and_video(url)
        correct_url = parsed_url["url"]
        seconds = int(parsed_url["time_code"])

    def download_video():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(correct_url, download=True)

    try:
        info_dict = await asyncio.to_thread(download_video)
        
        file_path = info_dict["requested_downloads"][0]["filepath"]
        video_title = info_dict.get("title", "")
        video_id = info_dict.get("id", None)
        duration = info_dict.get("duration", 0)

        video_title = await remove_special_chars(video_title)
        if seconds > 0:
            video_title += f"\n\n<i>{translations["time_code"][chat_language]}</i> {await format_seconds(seconds)}"

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
        log_error(url, e, 1111, await identify_service(url))
        return {"error": f"Error with download: {str(e)}"}
    
async def fetch_youtube_music_data(url: str, user_folder: str) -> dict:
    """
    Асинхронно извлекает данные аудио и скачивает его с YouTube Music.
    """
    base_ydl_opts = {
        "cookies_from_browser": ("firefox"),
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0 ... Chrome/92.0.4515.115 Safari/537.36'},
    }

    def get_metadata():
        with yt_dlp.YoutubeDL(base_ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    def download_info(yt_opts):
        with yt_dlp.YoutubeDL(yt_opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        info_for_size = await asyncio.to_thread(get_metadata)
        original_title = info_for_size.get("title", "audio")
        
        size = await get_music_size(192, info_for_size.get("duration", 0))
        if size > 49:
            return {
                "large": True,
                "audio_title": original_title
            }

        sanitized_title = sanitize_filename(original_title) or get_random_file_name("")

        ydl_opts = base_ydl_opts.copy()
        ydl_opts['outtmpl'] = os.path.join(user_folder, f"{sanitized_title}.%(ext)s")
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

        info_dict = await asyncio.to_thread(lambda: download_info(ydl_opts))

        file_extension = "mp3"
        file_path = os.path.join(user_folder, f"{sanitized_title}.{file_extension}")

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
            "audio_title": original_title,
            "audio_id": audio_id,
            "duration": duration,
            "thumbnail_path": thumbnail_path,
            "author": author,
        }

    except Exception as e:
        log_error(url, e, 1111, await identify_service(url))
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
        log_error(url, e, 1111, await identify_service(url))
        
    if isThumbnail:
        try:
            response = requests.get(DEFAULT_THUMBNAIL_URL, stream=True, timeout=10)
            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
        except Exception as e:
            log_error(url, e, 1111, await identify_service(url))
    
