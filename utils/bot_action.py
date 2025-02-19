from aiogram import Bot
from aiogram.enums.chat_action import ChatAction

async def send_bot_action(bot: Bot, chat_id, business_connection_id, action: str):
    if action == "video":
        return await bot.send_chat_action(chat_id=chat_id, business_connection_id=business_connection_id, action=ChatAction.UPLOAD_VIDEO)
    elif action == "photo":
        return await bot.send_chat_action(chat_id=chat_id, business_connection_id=business_connection_id, action=ChatAction.UPLOAD_PHOTO)
    elif action == "text":
        return await bot.send_chat_action(chat_id=chat_id, business_connection_id=business_connection_id, action=ChatAction.TYPING)
    elif action == "document":
        return await bot.send_chat_action(chat_id=chat_id, business_connection_id=business_connection_id, action=ChatAction.UPLOAD_DOCUMENT)
    elif action == "audio":
        return await bot.send_chat_action(chat_id=chat_id, business_connection_id=business_connection_id, action=ChatAction.UPLOAD_VOICE)
    