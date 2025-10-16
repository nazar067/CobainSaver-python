from datetime import datetime
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from admin.check_is_admin import is_user_admin
from admin.send_gifts import send_premium
from admin.send_to_users import send_message_to_chats, send_test_message_to_admin
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
    if message.text.startswith("/topup"):
        if not is_user_admin(user_id):
            return
        
        amount = int(message.text.split(" ")[1])
        builder = InlineKeyboardBuilder()
        builder.button(
                text="topup stars",
                callback_data=f"pay:{amount}"
        )

        await bot.send_message(chat_id=chat_id, text="topup stars", reply_markup=builder.as_markup())
    if message.text.startswith("/test_premium"):
        if not is_user_admin(user_id):
            return
        await send_test_message_to_admin(bot, dp)
    if message.text.startswith("/send_premium"):
        if not is_user_admin(user_id):
            return
        parts = message.text.split(" ")
        winner_id = int(parts[1])
        months = int(parts[2])
        star = int(parts[3])
        await send_premium(bot, dp, winner_id, months, star)