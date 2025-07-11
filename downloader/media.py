import logging
import os
from typing import Optional
from aiogram import Bot
from aiogram.types import FSInputFile, InputMediaPhoto
from constants.errors.telegram_errors import NOT_RIGHTS
from keyboard import send_log_keyboard
from localisation.translations.errors import translations
from logs.write_server_errors import log_error
from utils.bot_action import send_bot_action
from utils.get_name import get_clear_name
from utils.media_source import get_media_source
from utils.service_identifier import identify_service

async def send_video(bot: Bot, chat_id: int, msg_id, chat_language, business_connection_id, file_path_or_url: str, title: str = None, thumbnail_path_or_url: Optional[str] = None, duration: int = None, attempt = None, parse_mode = None) -> None:
    """
    Отправляет скачанное видео в чат (по ссылке или из файла).
    """
    try:
        await send_bot_action(bot, chat_id, business_connection_id, "video")
        video = get_media_source(file_path_or_url)
        thumbnail = get_media_source(thumbnail_path_or_url)
        title = await get_clear_name(title, 800)
        if parse_mode == None:
            parse_mode = "HTML" if len(title) > 174 else None
        await bot.send_video(
            business_connection_id=business_connection_id,
            chat_id=chat_id,
            video=video,
            caption=title,
            thumbnail=thumbnail,
            duration=duration,
            reply_to_message_id=msg_id,
            parse_mode=parse_mode
        )
        return True
    except Exception as e:
        if attempt:
            return False
        else:
            log_error("url", e, chat_id, "send video")
            if NOT_RIGHTS in str(e):
                return False
            await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["send_content_error"][chat_language], reply_to_message_id=msg_id, reply_markup=await send_log_keyboard(translations["send_content_error"][chat_language], str(e), chat_language, chat_id, file_path_or_url))
            return False
    finally:
        if file_path_or_url != "premium_guide.mp4":
            if not file_path_or_url.startswith("http"):
                await del_media_content(file_path_or_url)

        if thumbnail_path_or_url and not thumbnail_path_or_url.startswith("http"):
            await del_media_content(thumbnail_path_or_url) 
        
async def send_audio(bot: Bot, chat_id: int, msg_id, chat_language, business_connection_id: Optional[str], file_path: str, title: str, thumbnail_path: Optional[str], duration: int, author) -> str:
    """
    Отправляет аудио в чат.
    """
    try:
        await send_bot_action(bot, chat_id, business_connection_id, "audio")

        audio = FSInputFile(file_path, filename=os.path.basename(file_path))
        thumbnail = FSInputFile(thumbnail_path) if thumbnail_path and os.path.exists(thumbnail_path) else None

        await bot.send_audio(
            business_connection_id=business_connection_id,
            chat_id=chat_id,
            audio=audio,
            title=title,
            duration=duration,
            thumbnail=thumbnail,
            performer=author,
            reply_to_message_id=msg_id,
            caption='<a href="https://t.me/cobainSaver_bot"><i>by CobainSaver</i></a>',
            parse_mode="HTML"
        )
        return True

    except Exception as e:
        log_error("url", e, chat_id, "send audio")
        if NOT_RIGHTS in str(e):
            return False    
        await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["send_content_error"][chat_language], reply_to_message_id=msg_id, reply_markup=await send_log_keyboard(translations["send_content_error"][chat_language], str(e), chat_language, chat_id, file_path)) 
        return False
    finally:
        await del_media_content(file_path)
        if thumbnail_path:
            await del_media_content(thumbnail_path)
            
async def send_media_group(bot: Bot, chat_id: int, msg_id, chat_language, business_connection_id: Optional[str], media_album: str, file_path, attempt = None):
    try:
        await send_bot_action(bot, chat_id, business_connection_id, "photo")
        media = get_media_source(media_album)
        await bot.send_media_group(
            chat_id=chat_id, 
            business_connection_id=business_connection_id, 
            media=media,
            reply_to_message_id=msg_id
            )
        return True
    except Exception as e:
        log_error("url", e, chat_id, "send media group")
        if NOT_RIGHTS in str(e):
            return False
        if attempt != 1:
            await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["send_content_error"][chat_language], reply_to_message_id=msg_id, reply_markup=await send_log_keyboard(translations["send_content_error"][chat_language], str(e), chat_language, chat_id, "no url"))     
        return False
    finally:
        await del_media_group(file_path)
        
async def del_media_content(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
    
async def del_media_group(media):
    try:
        for file in media:
            if os.path.exists(file):
                os.remove(file)
    except Exception as e:
        log_error("url", e, 1111, "del media group")
