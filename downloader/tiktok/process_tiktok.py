import os
from aiogram import Bot, Dispatcher

from api.tiktok_api import is_server_alive
from config import TIKTOK_API
from constants.errors.tiktok_api_errors import URL_PARSING_FAILED
from downloader.send_album import send_social_media_album
from downloader.tiktok.download_audio import download_and_send_tiktok_audio
from downloader.tiktok.extract_tiktok_data import extract_tiktok_data
from downloader.tiktok.gallerydl.download_auido import download_audio_gallerydl
from downloader.tiktok.internet_video import send_tiktok_video
from downloader.tiktok.ytdlp.download_audio import download_audio_ytdlp
from downloader.tiktok.ytdlp.download_video import download_video_ytdlp
from keyboard import send_log_keyboard
from localisation.get_language import get_language
from user.get_user_path import get_user_path
from localisation.translations.downloader import translations
from utils.fetch_data import download_file
from utils.get_file_info import extract_index
from utils.get_name import get_random_file_name
from utils.get_settings import get_settings

async def fetch_tiktok_video(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id, msg_id) -> None:
    """
    Главная функция: извлекает данные, скачивает и отправляет TikTok-контент (видео или фото).
    """
    pool = dp["db_pool"]
    chat_language = await get_language(pool, chat_id)
    save_folder = await get_user_path(chat_id)
    settings = await get_settings(pool, chat_id)
    uniq_id = await get_random_file_name("")
    is_audio = settings["send_tiktok_music"]
    is_media_success = False
    is_audio_success = False

    is_tikwm_alive = await is_server_alive(TIKTOK_API, 1)
    if is_tikwm_alive:
        data = await extract_tiktok_data(url, pool, chat_id)
        if data == "large":
            await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["large_content"][chat_language], reply_to_message_id=msg_id)
            return "large"
        elif "error" in data:
            if URL_PARSING_FAILED in data["error"]:
                return await transfer_to_yt_dlp(is_audio, bot, url, chat_id, dp, business_connection_id, msg_id)
            return await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["unavaliable_content"][chat_language], reply_to_message_id=msg_id, reply_markup=await send_log_keyboard(translations["unavaliable_content"][chat_language], data["error"], chat_language, chat_id, url))
        
        if data["type"] == "photo":
            count_images = 0
            for image in data["images"]:
                random_name = f"{count_images} tiktok {uniq_id}" + await get_random_file_name("jpeg")
                save_path = f"{save_folder}/{random_name}"
                await download_file(image, save_path)
                count_images += 1
            matching_files = [
                os.path.join(save_folder, file) for file in os.listdir(save_folder) if f"tiktok {uniq_id}" in file
            ]
            matching_files.sort(key=extract_index)
            is_media_success = await send_social_media_album(bot, chat_id, chat_language, business_connection_id, matching_files, data["title"], msg_id, False, pool=pool)
        else:
            is_media_success = await send_tiktok_video(bot, chat_id, chat_language, business_connection_id, data, save_folder, msg_id, pool, False)

        if is_audio:
            is_audio_success = await download_and_send_tiktok_audio(bot, chat_id, chat_language, business_connection_id, data, save_folder, msg_id, pool)
            if is_audio_success == "No audio":
                is_audio_success = await download_audio_ytdlp(bot, url, chat_id, dp, business_connection_id, msg_id)
        else:
            is_audio_success = True
        
        if is_media_success == True and is_audio_success == True:
            return True
    else:
        return await transfer_to_yt_dlp(is_audio, bot, url, chat_id, dp, business_connection_id, msg_id)
        
async def transfer_to_yt_dlp(
    is_audio: bool,
    bot: Bot,
    url: str,
    chat_id: int,
    dp: Dispatcher,
    business_connection_id,
    msg_id
):
    raw_res = await download_video_ytdlp(bot, url, chat_id, dp, business_connection_id, msg_id)

    if isinstance(raw_res, dict):
        media_ok = bool(raw_res.get("is_success") or raw_res.get("success") or raw_res.get("ok"))
        media_type = raw_res.get("type")
    else:
        media_ok = bool(raw_res)
        media_type = None

    audio_ok = True 

    if is_audio:
        if media_type == "Photo":
            audio_ok = bool(await download_audio_gallerydl(bot, url, chat_id, dp, business_connection_id, msg_id))
        else:
            audio_ok = bool(await download_audio_ytdlp(bot, url, chat_id, dp, business_connection_id, msg_id))

    return media_ok and audio_ok

        
