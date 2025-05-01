from datetime import datetime
from aiogram.types import Message

from admin.check_is_admin import is_user_admin
from admin.send_to_users import send_message_to_chats
from admin.statistics import send_statistics, send_user_reviews
from keyboard import language_keyboard
from localisation.get_language import get_language
from logs.send_server_errors import send_server_logs
from settings.send_settings_msg import send_setting_msg
from config import ADMIN_ID
from localisation.translations.general import translations

async def choose_command(bot, message: Message, dp, business_connection_id):
    pool = dp["db_pool"]
    chat_id = message.chat.id
    user_id = message.from_user.id
    chat_language = await get_language(pool, chat_id)
    if message.text.startswith("/send_users_hard"):
        if not is_user_admin(user_id):
            return
        return await send_message_to_chats(bot, dp)
    if message.text.startswith("/settings"):
        return await send_setting_msg(pool, bot, chat_id, business_connection_id)
    if message.text.startswith("/changelang"):
        return await message.reply(
            translations["choose_lang"][chat_language],
            reply_markup=language_keyboard(message)
        )
    if message.text.startswith("/serverLogs"):
        await send_server_logs(message, dp)
    if message.text.startswith("/stats"):
        if not is_user_admin(user_id):
            return
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            date = datetime.strptime(parts[1], "%Y-%m-%d").date()
        else:
            date = datetime.now().date()
        await send_statistics(bot, pool, date=date)
    if message.text.startswith("/reviews"):
        if not is_user_admin(user_id):
            return
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            date = datetime.strptime(parts[1], "%Y-%m-%d").date()
        else:
            date = datetime.now().date()
        await send_user_reviews(bot, pool, date)