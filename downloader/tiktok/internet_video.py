import os

from aiogram import Bot

from downloader.media import send_video
from downloader.tiktok.download_video import download_and_send_tiktok_video
from utils.fetch_data import download_file
from utils.get_name import get_random_file_name


async def send_tiktok_video(bot: Bot, chat_id: int, chat_language, business_connection_id: str, data: dict, save_folder):
    attempt = await send_video(
        bot,
        chat_id,
        chat_language,
        business_connection_id,
        data["video_url"],
        data["video_title"],
        None,
        data["video_duration"],
        1
    )

    if attempt is 2:
        await download_and_send_tiktok_video(bot, chat_id, chat_language, business_connection_id, data, save_folder)