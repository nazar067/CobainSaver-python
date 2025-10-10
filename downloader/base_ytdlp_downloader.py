import asyncio
import os
from aiogram import Bot, Dispatcher
import yt_dlp
import subprocess

from downloader.media import del_media_content, send_video, send_audio
from downloader.playlist import process_music_playlist
from keyboard import send_log_keyboard
from localisation.get_language import get_language
from logs.write_server_errors import log_error
from user.get_user_path import get_user_path
from utils.fetch_data import download_file
from utils.get_name import get_random_file_name
from localisation.translations.downloader import translations
from utils.service_identifier import identify_service
from utils.task_queue import enqueue

async def fetch_base_media(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id, msg_id):
    # НИЖЕ — просто перенесём ТВОЮ текущую логику в отдельную корутину и выполним её через очередь
    async def _process():
        pool = dp["db_pool"]
        chat_language = await get_language(pool, chat_id)
        save_folder = await get_user_path(chat_id)
        random_name = await get_random_file_name("")

        video_extensions = ["mp4", "mov", "avi", "webm", "mkv", "flv"]
        audio_extensions = ["mp3", "wav", "m4a", "aac", "ogg", "flac", "opus"]

        ydl_opts = {
            'quiet': True,
            'http_headers': {'User-Agent': 'Mozilla/5.0'},
            'outtmpl': os.path.join(save_folder, random_name + "%(ext)s"),
        }

        def extract_music_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)
        def extract_info():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        def download_video():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=True)

        try:
            video_info = await asyncio.to_thread(extract_info)

            file_ext = video_info.get("ext", "").lower()
            is_audio = file_ext in audio_extensions
            is_video = file_ext in video_extensions
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
            if is_video:
                await bot.send_message(
                    chat_id=chat_id,
                    business_connection_id=business_connection_id,
                    text=translations["downloading"][chat_language],
                    reply_to_message_id=msg_id
                )

            file_path = os.path.join(save_folder, f"{random_name}{file_ext}")
            if is_video:
                await asyncio.to_thread(download_video)
            else:
                audio_info = await asyncio.to_thread(extract_music_info)

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

            if is_audio and file_ext == "opus":
                mp3_path = os.path.join(save_folder, f"{random_name}.mp3")
                ffmpeg_command = [
                    "ffmpeg", "-y", "-i", file_path,
                    "-vn", "-ab", "192k", "-ar", "44100", "-f", "mp3", mp3_path
                ]
                # оставим как у тебя (блокирующий run), логика не меняется
                subprocess.run(ffmpeg_command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                await del_media_content(file_path)
                file_path = mp3_path
            
            if is_audio:
                return await send_audio(
                    bot, chat_id, msg_id, chat_language,
                    business_connection_id, file_path, title,
                    thumbnail_path, int(duration), author=audio_info.get("uploader", "CobainSaver")
                )

            if is_video:
                return await send_video(
                    bot, chat_id, msg_id, chat_language,
                    business_connection_id, file_path, title,
                    thumbnail_path, int(duration)
                )

            # fallback
            await del_media_content(file_path)
            if thumbnail_path:
                await del_media_content(thumbnail_path)
            return await bot.send_message(
                chat_id=chat_id,
                business_connection_id=business_connection_id,
                text=translations["unsupport_format"][chat_language],
                reply_to_message_id=msg_id
            )

        except Exception as e:
            service = await identify_service(url)
            if service == "PornHub":
                await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["unavaliable_content"][chat_language], reply_to_message_id=msg_id, reply_markup=await send_log_keyboard(translations["unavaliable_content"][chat_language], e, chat_language, chat_id, url))
            log_error(url, e, chat_id, await identify_service(url))

    # 👇 ВАЖНО: теперь вся тяжёлая работа идёт ЧЕРЕЗ ОЧЕРЕДЬ
    return await enqueue(_process)