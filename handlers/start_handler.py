from aiogram.types import Message
from aiogram import Dispatcher, Bot
from downloader.media import send_video
from localisation.get_language import get_language
from localisation.set_language import set_language
from localisation.translations.general import translations
from asyncpg import Record

async def start_handler(bot: Bot, message: Message, dp: Dispatcher, business_connection_id):
    """
    Обработка команды /start
    """
    pool = dp["db_pool"]
    chat_id = message.chat.id
    language_code = message.from_user.language_code or "en"
    msg_id = message.message_id

    async with pool.acquire() as connection:
        existing_language: Record = await connection.fetchrow("""
            SELECT language_code FROM chat_languages WHERE chat_id = $1
        """, chat_id)

    if not existing_language:
        if not language_code:
            language_code = "en"
        await set_language(pool, chat_id, language_code)
        chat_language = await get_language(pool, chat_id)
    else:
        chat_language = await get_language(pool, chat_id)
    if message.from_user.is_premium and message.chat.type == "private":    
        await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["premium_welcome"][chat_language], reply_to_message_id=msg_id, parse_mode="HTML")
        await send_video(bot=bot, chat_id=chat_id, msg_id=msg_id, chat_language=chat_language, business_connection_id=business_connection_id, file_path_or_url="premium_guide.mp4", title="", duration=8)
    else:
        await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["welcome"][chat_language], reply_to_message_id=msg_id)  