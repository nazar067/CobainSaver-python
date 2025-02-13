import asyncio
import os
from aiogram import Bot, Dispatcher
import aiohttp
import yt_dlp
from downloader.media import send_video

from localisation.get_language import get_language
from user.get_user_path import get_user_path
from utils.fetch_data import download_file
from utils.get_name import get_random_file_name
from localisation.translations.downloader import translations



async def fetch_pornhub_video(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id):
    """
    Загружает видео с PornHub через yt-dlp, ограничивая размер файла до 50MB.
    """
    pool = dp["db_pool"]
    chat_language = await get_language(pool, chat_id)
    save_folder = await get_user_path(chat_id)
    random_name = get_random_file_name("")

    ydl_opts = {
        'quiet': True
    }

    def extract_info():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    def download_video(options):
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([video_url])

    try:
        info = await asyncio.to_thread(extract_info)
        
        video_url = info["formats"][0]["url"]
        video_title = info.get("title", "")
        video_duration = info.get("duration", 0)
        video_thumbnail = info.get("thumbnail", None)
        if video_duration > 1101:
            return await bot.send_message(
                chat_id=chat_id,
                business_connection_id=business_connection_id,
                text="Video more than 50MB"
            ) 

        video_path = os.path.join(save_folder, f"{random_name}mp4")
        thumbnail_path = os.path.join(save_folder, f"{random_name}jpg") if video_thumbnail else None

        ydl_opts["outtmpl"] = video_path
        await download_file(video_url, video_path)

        if video_thumbnail:
            await download_file(video_thumbnail, thumbnail_path)

        await send_video(bot, chat_id, chat_language, business_connection_id, video_path, video_title, thumbnail_path, video_duration)

    except Exception as e:
        return await bot.send_message(
            chat_id=chat_id,
            business_connection_id=business_connection_id,
            text=f"❌ Ошибка скачивания: {str(e)}"
        )