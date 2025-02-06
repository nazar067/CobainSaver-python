import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from config import API_TOKEN, DATABASE_URL
from db.db import get_db_pool, init_db
from downloader.music_selector import select_music
from handlers.start_handler import start_handler
from utils.pagination import playlist_pagination
from utils.service import choose_service

TOKEN = API_TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    """
    Команда /start
    """
    await start_handler(bot, message, dp)

@dp.message()
async def echo_handler(message: Message):
    await choose_service(bot, message, "", dp)
    
@dp.business_message()
async def echo_handler(message: Message):
    await choose_service(bot, message, message.business_connection_id, dp)
    
@dp.callback_query(lambda c: c.data.startswith("P "))
async def pagination_button(callback: CallbackQuery):
    await playlist_pagination(callback)

@dp.callback_query(lambda c: c.data.startswith(("Y ", "S ")))
async def select_track(callback: CallbackQuery):
    await select_music(callback, dp)

async def main():
    print("Bot started")
    pool = await get_db_pool(DATABASE_URL)
    dp["db_pool"] = pool
    await init_db(pool)
    await dp.start_polling(bot)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=["message", "callback_query", "pre_checkout_query"])
    finally:
        await pool.close()
        await bot.session.close()

if __name__ == "__main__":
    import asyncio
    from config import DATABASE_URL
    from db.db import get_db_pool, init_db
    asyncio.run(main())
