from aiogram import Bot, Dispatcher

from downloader.media import send_video
from localisation.get_language import get_language
from user.get_user_path import get_user_path
from localisation.translations.downloader import translations
from utils.quality import select_optimal_quality

MAX_SIZE_MB = 50  
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
            text=translations["live_unavaliable_content"][chat_language]
        )

    user_folder = await get_user_path(chat_id)

    quality_result = await select_optimal_quality(url, user_folder, initial_quality="360")

    if quality_result is "large":
        return await bot.send_message(
            chat_id=chat_id,
            business_connection_id=business_connection_id,
            text=translations["large_content"][chat_language]
        )
    elif "error" in quality_result:
        return await bot.send_message(
            chat_id=chat_id,
            business_connection_id=business_connection_id,
            text=translations["unavaliable_content"][chat_language]
        )

    file_path = quality_result["file_path"]
    video_title = quality_result["video_title"]
    thumbnail_path = quality_result["thumbnail_path"]
    duration = quality_result["duration"]
    return await send_video(bot, chat_id, msg_id, chat_language, business_connection_id, file_path, video_title, thumbnail_path, duration)