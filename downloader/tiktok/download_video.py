import os

from aiogram import Bot

from downloader.media import send_video
from utils.fetch_data import download_file
from utils.get_name import get_random_file_name


async def download_and_send_tiktok_video(bot: Bot, chat_id: int, chat_language, business_connection_id: str, data: dict, save_folder: str, msg_id, pool, is_Ads = False):
    """
    Скачивает TikTok-видео и отправляет его в чат.
    """
    video_path = os.path.join(save_folder, get_random_file_name("mp4"))
    video_thumbnail_path = os.path.join(save_folder, get_random_file_name("jpg"))

    await download_file(data["video_url"], video_path)

    if data["video_thumbnail_url"]:
        await download_file(data["video_thumbnail_url"], video_thumbnail_path, False)
    else:
        video_thumbnail_path = None
    
    return await send_video(
        bot,
        chat_id,
        msg_id,
        chat_language,
        business_connection_id,
        video_path,
        data["video_title"],
        video_thumbnail_path,
        data["video_duration"],
    )
