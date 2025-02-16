from aiogram import Bot, Dispatcher

from downloader.send_album import send_social_media_album
from downloader.tiktok.download_audio import download_and_send_tiktok_audio
from downloader.tiktok.extract_tiktok_data import extract_tiktok_data
from downloader.tiktok.internet_video import send_tiktok_video
from localisation.get_language import get_language
from user.get_user_path import get_user_path
from localisation.translations.downloader import translations
from utils.get_settings import get_settings

async def fetch_tiktok_video(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id, msg_id) -> None:
    """
    Главная функция: извлекает данные, скачивает и отправляет TikTok-контент (видео или фото).
    """
    pool = dp["db_pool"]
    chat_language = await get_language(pool, chat_id)
    save_folder = await get_user_path(chat_id)
    settings = await get_settings(pool, chat_id)
    is_audio = settings["send_tiktok_music"]

    data = await extract_tiktok_data(url)
    if data is "large":
        return await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["large_content"][chat_language], reply_to_message_id=msg_id)
    elif "error" in data:
        return await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["unavaliable_content"][chat_language], reply_to_message_id=msg_id)

    if data["type"] == "photo":
        if is_audio:
            await send_social_media_album(bot, chat_id, chat_language, business_connection_id, data["images"], data["title"], msg_id, False, pool=pool)
        else: 
            await send_social_media_album(bot, chat_id, chat_language, business_connection_id, data["images"], data["title"], msg_id, True, pool=pool)
    else:
        if is_audio:
            await send_tiktok_video(bot, chat_id, chat_language, business_connection_id, data, save_folder, msg_id, pool, False)
        else: 
            await send_tiktok_video(bot, chat_id, chat_language, business_connection_id, data, save_folder, msg_id, pool, True)
    
    if is_audio:
        await download_and_send_tiktok_audio(bot, chat_id, chat_language, business_connection_id, data, save_folder, msg_id, pool)

