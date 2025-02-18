from aiogram.types import Message

from admin.send_to_users import send_message_to_chats
from settings.send_settings_msg import send_setting_msg
from config import ADMIN_ID

async def choose_command(bot, message: Message, dp, business_connection_id):
    pool = dp["db_pool"]
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.text.startswith("/send_users_hard"):
        if str(user_id) == ADMIN_ID:
            return await send_message_to_chats(bot, dp)
    if message.text.startswith("/settings"):
        return await send_setting_msg(pool, bot, chat_id, business_connection_id)