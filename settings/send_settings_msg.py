from keyboard import generate_settings_keyboard
from aiogram import Bot

from localisation.get_language import get_language
from utils.get_settings import get_settings
from localisation.translations.general import translations

async def send_setting_msg(pool, bot: Bot, chat_id, business_connection_id):
    chat_language = await get_language(pool, chat_id)
    settings = await get_settings(pool, chat_id)
    send_tiktok_music = settings["send_tiktok_music"]
    send_ads = settings["send_ads"]
    hd_size = settings["hd_size"]
    keyboard = await generate_settings_keyboard(chat_id=chat_id, send_tiktok_music=send_tiktok_music, send_ads=send_ads, hd_size=hd_size, pool=pool, business_connection_id=business_connection_id)
    await bot.send_message(chat_id=chat_id, text=translations["settings"][chat_language], reply_markup=keyboard, business_connection_id=business_connection_id)