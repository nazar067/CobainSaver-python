import asyncio
from aiogram import Bot
from localisation.get_language import get_language
from localisation.translations.general import translations

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
            print(f"Failed to send message to chat {chat_id}: {e}")