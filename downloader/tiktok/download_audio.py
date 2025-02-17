import os
from aiogram import Bot

from downloader.media import send_audio
from utils.fetch_data import download_file
from utils.get_name import get_random_file_name


async def download_and_send_tiktok_audio(bot: Bot, chat_id: int, chat_language, business_connection_id: str, data: dict, save_folder: str, msg_id, pool):
    """
    Скачивает TikTok-аудио и отправляет его в чат.
    """
    if not data["audio_url"]:
        return

    audio_path = os.path.join(save_folder, get_random_file_name("mp3"))
    audio_thumbnail_path = os.path.join(save_folder, get_random_file_name("jpg"))

    await download_file(data["audio_url"], audio_path)

    await download_file(data["audio_thumbnail_url"], audio_thumbnail_path)

    return await send_audio(
        bot,
        chat_id,
        msg_id,
        chat_language,
        business_connection_id,
        audio_path,
        data["audio_title"],
        audio_thumbnail_path,
        data["audio_duration"],
        data["audio_author"],
    )
