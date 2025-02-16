from keyboard import generate_settings_keyboard
from aiogram import Bot

from utils.get_settings import get_settings

async def send_setting_msg(pool, bot: Bot, chat_id):
    settings = await get_settings(pool, chat_id)
    send_tiktok_music = settings["send_tiktok_music"]
    send_ads = settings["send_ads"]
    keyboard = await generate_settings_keyboard(chat_id=chat_id, send_tiktok_music=send_tiktok_music, send_ads=send_ads)

    await bot.send_message(chat_id=chat_id, text="Настройки:", reply_markup=keyboard)