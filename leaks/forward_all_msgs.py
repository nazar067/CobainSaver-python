import logging
from aiogram import Bot
from aiogram.types import Message

from leaks.create_thread import get_forum_thread
from config import THREAD_GROUP_ID
import random

EMOJI_LIST = ["🤖", "👽"]

user_emojis = {}

async def forward_message_to_thread(message: Message, bot: Bot, dp):
    try:
        thread_id = await get_forum_thread(bot, dp, message)
        
        user_id = message.from_user.id

        if user_id not in user_emojis:
            available_emojis = list(set(EMOJI_LIST) - set(user_emojis.values()))
            if available_emojis:
                user_emojis[user_id] = random.choice(available_emojis)
            else:
                user_emojis[user_id] = random.choice(EMOJI_LIST)

        user_emoji = user_emojis[user_id]

        user_info = (
            f"{user_emoji} <b><a href='https://t.me/{message.from_user.username if message.from_user.username else ''}'>"
            f"{message.from_user.first_name if message.from_user.first_name else 'не указан'}</a></b>\n"
        )

        if not message.business_connection_id:
            await message.forward(chat_id=THREAD_GROUP_ID, message_thread_id=thread_id)
            return

        if message.content_type == "text":
            await bot.send_message(
                chat_id=THREAD_GROUP_ID, 
                message_thread_id=thread_id, 
                text=user_info + message.text, 
                parse_mode="HTML", 
                disable_web_page_preview=True
            )
            
        elif message.photo:
            await bot.send_photo(
                chat_id=THREAD_GROUP_ID, 
                message_thread_id=thread_id, 
                caption=user_info + f" {message.caption if message.caption else ''}", 
                photo=message.photo[-1].file_id, 
                parse_mode="HTML"
            )  
            
        elif message.video:
            await bot.send_video(
                chat_id=THREAD_GROUP_ID, 
                message_thread_id=thread_id, 
                caption=user_info, 
                video=message.video.file_id, 
                parse_mode="HTML"
            )
            
        elif message.voice:
            await bot.send_voice(
                chat_id=THREAD_GROUP_ID, 
                message_thread_id=thread_id, 
                caption=user_info, 
                voice=message.voice.file_id, 
                parse_mode="HTML"
            )

        elif message.document:
            await bot.send_document(
                chat_id=THREAD_GROUP_ID, 
                message_thread_id=thread_id, 
                caption=user_info, 
                document=message.document.file_id, 
                parse_mode="HTML"
            )

        elif message.audio:
            await bot.send_audio(
                chat_id=THREAD_GROUP_ID, 
                message_thread_id=thread_id, 
                caption=user_info, 
                audio=message.audio.file_id,  
                parse_mode="HTML"
            )
            
        elif message.video_note:
            video_note = await bot.send_video_note(
                chat_id=THREAD_GROUP_ID, 
                message_thread_id=thread_id, 
                video_note=message.video_note.file_id
            )
            await bot.send_message(
                chat_id=THREAD_GROUP_ID, 
                message_thread_id=thread_id, 
                text=user_info, 
                reply_to_message_id=video_note.message_id, 
                parse_mode="HTML", 
                disable_web_page_preview=True
            )
            
        elif message.sticker:
            sticker = await bot.send_sticker(
                chat_id=THREAD_GROUP_ID, 
                message_thread_id=thread_id, 
                sticker=message.sticker.file_id
            )
            await bot.send_message(
                chat_id=THREAD_GROUP_ID, 
                message_thread_id=thread_id, 
                text=user_info, 
                reply_to_message_id=sticker.message_id, 
                parse_mode="HTML", 
                disable_web_page_preview=True
            )
    except Exception as e:
        logging.error("Error in forward_message_to_thread", e)