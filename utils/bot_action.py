from aiogram import Bot
from aiogram.enums.chat_action import ChatAction

async def send_bot_action(bot: Bot, chat_id, business_connection_id, action: str):
    if action is "video":
        return await bot.send_chat_action(chat_id=chat_id, business_connection_id=business_connection_id, action=ChatAction.UPLOAD_VIDEO)
    elif action is "photo":
        return await bot.send_chat_action(chat_id=chat_id, business_connection_id=business_connection_id, action=ChatAction.UPLOAD_PHOTO)
    elif action is "text":
        return await bot.send_chat_action(chat_id=chat_id, business_connection_id=business_connection_id, action=ChatAction.TYPING)
    elif action is "document":
        return await bot.send_chat_action(chat_id=chat_id, business_connection_id=business_connection_id, action=ChatAction.UPLOAD_DOCUMENT)
    elif action is "audio":
        return await bot.send_chat_action(chat_id=chat_id, business_connection_id=business_connection_id, action=ChatAction.UPLOAD_VOICE)
    