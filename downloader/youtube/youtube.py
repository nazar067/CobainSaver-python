from aiogram import Bot, Dispatcher

from downloader.media import send_video
from keyboard import send_log_keyboard
from localisation.get_language import get_language
from user.get_user_path import get_user_path
from localisation.translations.downloader import translations
from utils.fetch_data import get_video_duration
from utils.quality import select_optimal_quality

MAX_SIZE_MB = 1999  
QUALITIES = ["1080", "720", "480", "360", "240", "144"]  

async def process_youtube_video(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id, msg_id) -> str:
    """
    Обрабатывает скачивание и отправку видео пользователю с выбором оптимального качества.
    """
    pool = dp["db_pool"]
    chat_language = await get_language(pool, chat_id)

    if "/live/" in url:
        return await bot.send_message(
            chat_id=chat_id,
            business_connection_id=business_connection_id,
            text=translations["live_unavaliable_content"][chat_language],
            reply_to_message_id=msg_id
        )

    video_duration = await get_video_duration(url)
    if video_duration > 5400:
        return await bot.send_message(
            chat_id=chat_id,
            business_connection_id=business_connection_id,
            text=translations["large_content"][chat_language],
            reply_to_message_id=msg_id
        )
    
    user_folder = await get_user_path(chat_id)

    quality_result = await select_optimal_quality(url, user_folder, initial_quality="360", chat_language=chat_language)

    if quality_result == "large":
        return await bot.send_message(
            chat_id=chat_id,
            business_connection_id=business_connection_id,
            text=translations["large_content"][chat_language],
            reply_to_message_id=msg_id
        )
    elif "error" in quality_result:
        return await bot.send_message(
            chat_id=chat_id,
            business_connection_id=business_connection_id,
            text=translations["unavaliable_content"][chat_language],
            reply_to_message_id=msg_id,
            reply_markup=await send_log_keyboard(translations["unavaliable_content"][chat_language], quality_result["error"], chat_language, chat_id, url)
        )

    file_path = quality_result["file_path"]
    video_title = quality_result["video_title"]
    thumbnail_path = quality_result["thumbnail_path"]
    duration = quality_result["duration"]
    return await send_video(bot, chat_id, msg_id, chat_language, business_connection_id, file_path, video_title, thumbnail_path, duration, parse_mode="HTML")