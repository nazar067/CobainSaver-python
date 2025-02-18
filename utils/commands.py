from aiogram.types import Message

from admin.send_to_users import send_message_to_chats
from keyboard import language_keyboard
from localisation.get_language import get_language
from settings.send_settings_msg import send_setting_msg
from config import ADMIN_ID
from localisation.translations.general import translations

async def choose_command(bot, message: Message, dp, business_connection_id):
    pool = dp["db_pool"]
    chat_id = message.chat.id
    user_id = message.from_user.id
    chat_language = await get_language(pool, chat_id)
    if message.text.startswith("/send_users_hard"):
        if str(user_id) == ADMIN_ID:
            return await send_message_to_chats(bot, dp)
    if message.text.startswith("/settings"):
        return await send_setting_msg(pool, bot, chat_id, business_connection_id)
    if message.text.startswith("/changelang"):
        return await message.reply(
            translations["choose_lang"][chat_language],
            reply_markup=language_keyboard(message)
        )