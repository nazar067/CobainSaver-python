import asyncio
import logging
from aiogram import Bot
from config import ANGRON_ID
from aiogram.types import FSInputFile
from downloader.media import send_video
from localisation.get_language import get_language
from localisation.translations.general import translations
from logs.write_server_errors import log_error

async def send_message_to_chats(bot: Bot, dp):
    pool = dp["db_pool"]
    file_path = "users.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        chat_ids = [line.strip() for line in file.readlines() if line.strip()]

    for chat_id in chat_ids:
        chat_language = await get_language(pool, int(chat_id))
        try:
            await bot.send_message(chat_id=chat_id, text=translations["update"][chat_language], parse_mode="HTML", disable_web_page_preview=True)
            await asyncio.sleep(0.5)
        except Exception as e:
            log_error("url", e, chat_id, "send message to users")

async def send_video_to_angron(bot: Bot):
    video = FSInputFile('happy_birthday.mp4')
    await bot.send_video(chat_id=ANGRON_ID, video=video, caption="Happy birthday, GOY!")