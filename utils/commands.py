from aiogram.types import Message

from admin.send_to_users import send_message_to_chats
from settings.send_settings_msg import send_setting_msg

async def choose_command(bot, message: Message, dp):
    pool = dp["db_pool"]
    chat_id = message.chat.id
    if message.text.startswith("/send_users_hard"):
        return await send_message_to_chats(bot, dp)
    if message.text.startswith("/settings"):
        return await send_setting_msg(pool, bot, chat_id)