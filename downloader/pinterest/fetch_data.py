import asyncio
import os
import requests
import yt_dlp

from aiogram import Bot, Dispatcher

from downloader.media import send_video
from downloader.send_album import send_social_media_album
from localisation.get_language import get_language
from user.get_user_path import get_user_path
from utils.fetch_data import download_file
from utils.get_name import get_random_file_name


MAX_VIDEO_SIZE_MB = 50


async def fetch_pinterest_content(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id, msg_id):
    """
    Загружает контент (видео/фото) с Pinterest и отправляет пользователю.
    """
    pool = dp["db_pool"]
    chat_language = await get_language(pool, chat_id)
    save_folder = await get_user_path(chat_id)
    random_name = get_random_file_name("mp4")

    video_info = await fetch_pinterest_video(url, save_folder, random_name)

    if video_info:
        video_path = video_info["file_path"]
        thumbnail_path = video_info["thumbnail_path"]
        video_title = video_info["video_title"]
        video_size_mb = video_info["file_size_mb"]

        if video_size_mb > MAX_VIDEO_SIZE_MB:
            return await bot.send_message(
                chat_id=chat_id,
                text="❌ Видео больше 50MB и не может быть отправлено."
            )

        await send_video(bot, chat_id, msg_id, chat_language, business_connection_id, video_path, video_title, thumbnail_path)
        return

    image_urls = await fetch_pinterest_images(url)

    if image_urls:
        await send_social_media_album(bot, chat_id, chat_language, business_connection_id, image_urls, "", msg_id)
        return

    await bot.send_message(chat_id=chat_id, text="❌ Контент не найден или недоступен.")


async def fetch_pinterest_video(url: str, save_folder: str, random_name: str) -> dict:
    """
    Загружает видео с Pinterest.
    """
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(save_folder, f"{random_name}"),
        'quiet': True,
        'noplaylist': True,
        'merge_output_format': 'mp4',
    }

    def download_video():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        info_dict = await asyncio.to_thread(download_video)
        file_path = info_dict["requested_downloads"][0]["filepath"]
        video_title = info_dict.get("title", "Pinterest Video")
        thumbnail_url = info_dict.get("thumbnail", None)

        thumbnail_path = None
        if thumbnail_url:
            thumbnail_path = os.path.join(save_folder, get_random_file_name("jpg"))
            await download_file(thumbnail_url, thumbnail_path)

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        return {
            "file_path": file_path,
            "file_size_mb": file_size_mb,
            "video_title": video_title,
            "thumbnail_path": thumbnail_path
        }

    except Exception as e:
        print(f"Ошибка при скачивании видео: {str(e)}")
        return None


async def fetch_pinterest_images(url: str) -> list:
    """
    Извлекает ссылки на изображения с Pinterest.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        html_content = response.text
        image_urls = []

        for line in html_content.split('"'):
            if line.startswith("https://i.pinimg.com/originals/"):
                image_urls.append(line)
                break

        return image_urls if image_urls else None

    except Exception as e:
        print(f"Ошибка при скачивании изображений: {str(e)}")
        return None

