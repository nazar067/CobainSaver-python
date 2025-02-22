from logs.write_server_errors import setup_logging
from utils.auto_del import delete_old_files
setup_logging()

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery
from aiogram.filters import CommandStart
from config import API_TOKEN, DATABASE_URL
from db.db import get_db_pool, init_db
from bot_settings.commands import set_bot_commands
from bot_settings.description import set_bot_description
from bot_settings.short_description import set_bot_short_description
from downloader.music_selector import select_music
from handlers.language_handler import set_language_handler
from handlers.settings_keyboard_handler import toggle_ads_callback, toggle_audio_callback
from handlers.start_handler import start_handler
from payments.end_subscribe import check_and_update_ads
from payments.payment import process_payment
from utils.pagination import playlist_pagination
from utils.select_service import choose_service

TOKEN = API_TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    """
    Команда /start
    """
    await start_handler(bot, message, dp, message.business_connection_id)

@dp.message(lambda m: m.successful_payment)
async def successful_payment_handler(message: Message):
    """
    Обработка успешной оплаты
    """
    await toggle_ads_callback(bot, message, dp)

@dp.message()
async def echo_handler(message: Message):
    await choose_service(bot, message, "", dp)

@dp.business_message()
async def business_echo_handler(message: Message):
    await choose_service(bot, message, message.business_connection_id, dp)

@dp.callback_query(lambda c: c.data.startswith("P "))
async def pagination_button(callback: CallbackQuery):
    await playlist_pagination(callback, dp)

@dp.callback_query(lambda c: c.data.startswith(("Y ", "S ")))
async def select_track(callback: CallbackQuery):
    await select_music(callback, dp)
    
@dp.callback_query(lambda c: c.data.startswith(("toggle_audio")))
async def change_audio(callback: CallbackQuery):
    await toggle_audio_callback(callback, dp)

@dp.callback_query(lambda c: c.data.startswith(("pay:")))
async def pay_stars_handler(callback: CallbackQuery):
    """
    Обработка платежей с валютой XTR
    """
    amount = int(callback.data.split(":")[1])
    provider_token = ""

    pool = dp["db_pool"]
    payment_data = await process_payment(callback, amount, provider_token, pool)
    if payment_data:
        await callback.message.answer_invoice(**payment_data)  
        
@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """
    Обработка PreCheckoutQuery
    """
    await pre_checkout_query.answer(ok=True)

@dp.callback_query(lambda callback: callback.data.startswith("set_language:"))
async def language_handler(callback: CallbackQuery):
    pool = dp["db_pool"]
    await set_language_handler(callback, pool)

async def main():
    print("Bot started")
    pool = await get_db_pool(DATABASE_URL)
    dp["db_pool"] = pool
    await init_db(pool)
    
    await set_bot_description(bot)
    await set_bot_commands(bot)
    await set_bot_short_description(bot)
    
    asyncio.create_task(check_and_update_ads(pool))
    asyncio.create_task(delete_old_files())

    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query", "pre_checkout_query", "business_message"])
    finally:
        await pool.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
