from aiogram.types import Message

from admin.send_to_users import send_message_to_chats

async def choose_command(bot, message: Message, dp):
    if message.text.startswith("/send_users_hard"):
        return await send_message_to_chats(bot, dp)