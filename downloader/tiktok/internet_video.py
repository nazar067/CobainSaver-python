from aiogram import Bot

from downloader.media import send_video
from downloader.tiktok.download_video import download_and_send_tiktok_video


async def send_tiktok_video(bot: Bot, chat_id: int, chat_language, business_connection_id: str, data: dict, save_folder, msg_id):
    attempt = await send_video(
        bot,
        chat_id,
        msg_id,
        chat_language,
        business_connection_id,
        data["video_url"],
        data["video_title"],
        None,
        data["video_duration"],
        1
    )

    if attempt is 2:
        await download_and_send_tiktok_video(bot, chat_id, chat_language, business_connection_id, data, save_folder, msg_id)