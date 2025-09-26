import asyncio
import os
from aiogram import Bot, Dispatcher
import yt_dlp
import subprocess

from constants.errors.tiktok_api_errors import UNSUPPORTED_URL
from downloader.media import del_media_content, send_video, send_audio
from downloader.playlist import process_music_playlist
from downloader.tiktok.gallerydl.download_photo import download_photo_gallerydl
from keyboard import send_log_keyboard
from localisation.get_language import get_language
from logs.write_server_errors import log_error
from user.get_user_path import get_user_path
from utils.fetch_data import download_file
from utils.get_name import get_random_file_name
from localisation.translations.downloader import translations
from utils.service_identifier import identify_service

async def download_video_ytdlp(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id, msg_id):
    pool = dp["db_pool"]
    chat_language = await get_language(pool, chat_id)
    save_folder = await get_user_path(chat_id)
    random_name = await get_random_file_name("")

    ydl_opts = {
        'quiet': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0'},
        'outtmpl': os.path.join(save_folder, random_name + "%(ext)s"),
    }

    def download_video():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        video_info = await asyncio.to_thread(download_video)

        file_ext = video_info.get("ext", "").lower()
        type = video_info.get("_type", "")

        if type == "playlist":
            await process_music_playlist(bot, dp, business_connection_id, chat_id, url, user_msg_id=msg_id)
            return

        file_url = video_info.get("url", "")
        title = video_info.get("title", "")
        duration = video_info.get("duration", 0)
        thumbnail = video_info.get("thumbnail", None)

        if duration > 20000:
            return await bot.send_message(
                chat_id=chat_id,
                business_connection_id=business_connection_id,
                text=translations["large_content"][chat_language],
                reply_to_message_id=msg_id
            )

        file_path = os.path.join(save_folder, f"{random_name}{file_ext}")

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb >= 1999:
            await del_media_content(file_path)
            return await bot.send_message(
                chat_id=chat_id,
                business_connection_id=business_connection_id,
                text=translations["large_content"][chat_language],
                reply_to_message_id=msg_id
            )

        if thumbnail:
            thumbnail_path = os.path.join(save_folder, f"{random_name}.jpg")
            await download_file(thumbnail, thumbnail_path)
        else:
            thumbnail_path = None

        return await send_video(
            bot, chat_id, msg_id, chat_language,
            business_connection_id, file_path, title,
            thumbnail_path, int(duration)
        )

    except Exception as e:
        if UNSUPPORTED_URL in str(e) and "/photo/" in str(e):
            return await download_photo_gallerydl(bot, url, chat_id, dp, business_connection_id, msg_id)

        await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["unavaliable_content"][chat_language], reply_to_message_id=msg_id, reply_markup=await send_log_keyboard(translations["unavaliable_content"][chat_language], e, chat_language, chat_id, url))
        log_error(url, e, chat_id, await identify_service(url))
        return False
