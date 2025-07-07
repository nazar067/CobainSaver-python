import os
import re
from aiogram import Bot, Dispatcher
from downloader.media import del_media_group
from downloader.send_album import send_social_media_album
from downloader.x.extract_data import extract_twitter_data
from keyboard import send_log_keyboard
from localisation.get_language import get_language
from localisation.translations.downloader import translations
from user.get_user_path import get_user_path
from utils.fetch_data import download_file
from utils.get_name import get_clear_name, get_random_file_name


async def fetch_twitter_content(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id, msg_id) -> None:
    """
    📩 Загружает и отправляет контент из Twitter.
    """
    pool = dp["db_pool"]
    chat_language = await get_language(pool, chat_id)
    directory = await get_user_path(chat_id)
    uniq_id = get_random_file_name("")
    
    ext = ""

    data = await extract_twitter_data(url)
    if "error" in data:
        return await bot.send_message(chat_id, text=translations["unavaliable_content"][chat_language], reply_to_message_id=msg_id, business_connection_id=business_connection_id, reply_markup=await send_log_keyboard(translations["unavaliable_content"][chat_language], data["error"], chat_language, chat_id, url))
    
    media_urls = data["media_urls"]
    if not media_urls:
        return await bot.send_message(chat_id, text=translations["unavaliable_content"][chat_language], reply_to_message_id=msg_id, business_connection_id=business_connection_id, reply_markup=await send_log_keyboard(translations["unavaliable_content"][chat_language], "media urls is null", chat_language, chat_id, url))
    
    caption = await get_clear_name(data["caption"], 800)
    result = await send_social_media_album(bot, chat_id, chat_language, business_connection_id, media_urls, caption, msg_id, pool=pool, attempt=1)
    
    if result is False:
        count_media = 0
        for media_url in media_urls:
            type = data["types"][count_media]
            if type == "video":
                ext = "mp4"
            elif type == "image":
                ext = "jpg"
                
            random_name = f"twitter {uniq_id}" + get_random_file_name(ext)
            save_path = f"{directory}/{random_name}"
            await download_file(media_url, save_path)
            count_media += 1
        
        matching_files = [
            os.path.join(directory, file) for file in os.listdir(directory) if f"twitter {uniq_id}" in file
        ]
        
        result = await send_social_media_album(bot, chat_id, chat_language, business_connection_id, matching_files, caption, msg_id, pool=pool)
        
    return result
