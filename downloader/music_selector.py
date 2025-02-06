import asyncio
from aiogram.types import CallbackQuery
from downloader.spotify import process_spotify_track
from downloader.youtube.youtube_music import process_youtube_music


async def select_music(callback: CallbackQuery):
    data = callback.data.split()
    source = data[0]
    track_id = data[1]
    chat_id = callback.message.chat.id
    business_connection_id = callback.message.business_connection_id

    if source == "Y":
        track_url = f"https://music.youtube.com/watch?v={track_id}"
        asyncio.create_task(process_youtube_music(callback.bot, track_url, chat_id, business_connection_id))
    
    elif source == "S":
        url = "https://open.spotify.com/track/" + track_id
        asyncio.create_task(process_spotify_track(callback.bot, url, chat_id, business_connection_id))

    await callback.answer()