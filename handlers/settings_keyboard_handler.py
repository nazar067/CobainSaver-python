from aiogram.types import CallbackQuery
from keyboard import generate_settings_keyboard
from settings.change_settings import upsert_settings


async def toggle_audio_callback(callback: CallbackQuery, dp):
    _, chat_id, new_state = callback.data.split()
    pool = dp["db_pool"]
    chat_id = int(chat_id)
    new_state = bool(int(new_state))

    await upsert_settings(pool, chat_id, send_tiktok_music=new_state)

    updated_keyboard = await generate_settings_keyboard(chat_id, new_state, send_ads=True)
    await callback.message.edit_reply_markup(reply_markup=updated_keyboard)

async def toggle_ads_callback(callback: CallbackQuery, dp):
    _, chat_id, new_state = callback.data.split()
    pool = dp["db_pool"]
    chat_id = int(chat_id)
    new_state = bool(int(new_state))

    await upsert_settings(pool, chat_id, send_ads=new_state)

    updated_keyboard = await generate_settings_keyboard(chat_id, send_tiktok_music=True, send_ads=new_state)
    await callback.message.edit_reply_markup(reply_markup=updated_keyboard)