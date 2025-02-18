from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from keyboard import generate_settings_keyboard
from localisation.get_language import get_language
from settings.change_settings import upsert_settings
from localisation.translations.ads import translations

async def toggle_audio_callback(callback: CallbackQuery, dp):
    _, chat_id, new_state = callback.data.split()
    pool = dp["db_pool"]
    chat_id = int(chat_id)
    new_state = bool(int(new_state))

    await upsert_settings(pool, chat_id, send_tiktok_music=new_state)

    updated_keyboard = await generate_settings_keyboard(chat_id, new_state, send_ads=True, pool=pool)
    await callback.message.edit_reply_markup(reply_markup=updated_keyboard)

async def toggle_ads_callback(bot: Bot, message: Message, dp):
    pool = dp["db_pool"]
    chat_id = message.chat.id
    chat_language = await get_language(pool, chat_id)
    await upsert_settings(pool, chat_id, send_ads=False)
    
    await bot.send_message(chat_id, translations["success_disable"][chat_language])