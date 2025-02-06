import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from config import API_TOKEN, DATABASE_URL
from db.db import get_db_pool, init_db
from downloader.spotify import process_spotify_track
from downloader.youtube.youtube_music import process_youtube_music
from downloader.playlist import process_music_playlist
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
async def pagination_button(callback: CallbackQuery):
    _, source, content_type, playlist_id, new_page = callback.data.split()
    chat_id = callback.message.chat.id
    msg_id = callback.message.message_id
    business_connection_id = callback.message.business_connection_id
    if source == "Y":
        await process_music_playlist(callback.bot, business_connection_id, int(chat_id), f"https://music.youtube.com/playlist?list={playlist_id}", int(new_page), int(msg_id))
    elif source == "S":
        if content_type is "a":
            await process_music_playlist(callback.bot, business_connection_id, int(chat_id), f"https://open.spotify.com/album/{playlist_id}", int(new_page), int(msg_id))
        elif content_type is "p":
            await process_music_playlist(callback.bot, business_connection_id, int(chat_id), f"https://open.spotify.com/playlist/{playlist_id}", int(new_page), int(msg_id))
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith(("Y ", "S ")))
async def select_track(callback: CallbackQuery):
    """
    Обрабатывает выбор трека с YouTube Music или Spotify.
    """
    data = callback.data.split()
    source = data[0]
    track_id = data[1]
    chat_id = callback.message.chat.id
    business_connection_id = callback.message.business_connection_id

    if source == "Y":
        # YouTube трек (используем видео ID)
        track_url = f"https://music.youtube.com/watch?v={track_id}"
        asyncio.create_task(process_youtube_music(callback.bot, track_url, chat_id, business_connection_id))
    
    elif source == "S":
        # Spotify трек (поиск на YouTube по названию)
        url = "https://open.spotify.com/track/" + track_id
        asyncio.create_task(process_spotify_track(callback.bot, url, chat_id, business_connection_id))

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
