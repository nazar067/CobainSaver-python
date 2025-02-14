import asyncio
import os
from aiogram import Bot, Dispatcher
import aiohttp
import yt_dlp
from downloader.media import del_media_content, send_video

from localisation.get_language import get_language
from user.get_user_path import get_user_path
from utils.fetch_data import download_file
from utils.get_name import get_random_file_name
from localisation.translations.downloader import translations



async def fetch_base_video(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id, msg_id):
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
                text=translations["large_content"][chat_language],
                reply_to_message_id=msg_id
            ) 

        video_path = os.path.join(save_folder, f"{random_name}mp4")
        thumbnail_path = os.path.join(save_folder, f"{random_name}jpg") if video_thumbnail else None

        ydl_opts["outtmpl"] = video_path
        await bot.send_message(
                chat_id=chat_id,
                business_connection_id=business_connection_id,
                text=translations["downloading"][chat_language],
                reply_to_message_id=msg_id
            ) 
        await download_file(video_url, video_path)
        
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if file_size_mb >= 50:
            await del_media_content(video_path)
            return await bot.send_message(
                chat_id=chat_id,
                business_connection_id=business_connection_id,
                text=translations["large_content"][chat_language],
                reply_to_message_id=msg_id
            )

        if video_thumbnail:
            await download_file(video_thumbnail, thumbnail_path)

        await send_video(bot, chat_id, msg_id, chat_language, business_connection_id, video_path, video_title, thumbnail_path, video_duration, pool=pool)

    except Exception as e:
        return 