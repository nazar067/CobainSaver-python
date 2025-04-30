import asyncio
from aiogram import Dispatcher
from aiogram.types import CallbackQuery
from downloader.spotify import process_spotify_track
from downloader.youtube.youtube_music import process_youtube_music


async def select_music(callback: CallbackQuery, dp: Dispatcher):
    data = callback.data.split()
    source = data[0]
    track_id = data[1]
    track_name = data[3]
    chat_id = callback.message.chat.id
    business_connection_id = callback.message.business_connection_id
    msg_id = callback.message.message_id

    if source == "Y":
        track_url = f"https://music.youtube.com/watch?v={track_id}"
        asyncio.create_task(process_youtube_music(callback.bot, track_url, chat_id, dp, business_connection_id, msg_id, track_name))
    
    elif source == "S":
        url = "https://open.spotify.com/track/" + track_id
        asyncio.create_task(process_spotify_track(callback.bot, url, chat_id, dp, business_connection_id, msg_id))

    await callback.answer()