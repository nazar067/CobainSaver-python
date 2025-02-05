import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from config import API_TOKEN, DATABASE_URL
from db.db import get_db_pool, init_db
from downloader.youtube.youtube_music import process_youtube_music
from downloader.youtube.youtube_music_playlist import process_youtube_music_playlist
from handlers.start_handler import start_handler
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
    await choose_service(bot, message, "")
    
@dp.business_message()
async def echo_handler(message: Message):
    await choose_service(bot, message, message.business_connection_id)
    
@dp.callback_query(lambda c: c.data.startswith("P "))
async def previous_page(callback: CallbackQuery):
    _, chat_id, playlist_id, new_page, msg_id = callback.data.split()
    await process_youtube_music_playlist(callback.bot, int(chat_id), f"https://music.youtube.com/playlist?list={playlist_id}", int(new_page), int(msg_id))
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("N "))
async def next_page(callback: CallbackQuery):
    _, chat_id, playlist_id, new_page, msg_id = callback.data.split()
    await process_youtube_music_playlist(callback.bot, int(chat_id), f"https://music.youtube.com/playlist?list={playlist_id}", int(new_page), int(msg_id))
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("L "))
async def select_track(callback: CallbackQuery):
    _, track_id, chat_id, playlist_id, msg_id = callback.data.split()
    track_url = f"https://music.youtube.com/watch?v={track_id}"

    asyncio.create_task(process_youtube_music(callback.bot, track_url, int(chat_id)))

    await callback.answer()

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
