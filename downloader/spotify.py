import logging
import yt_dlp
import asyncio
from aiogram import Bot, Dispatcher
from downloader.youtube.youtube_music import process_youtube_music
from downloader.playlist import process_music_playlist
from keyboard import send_log_keyboard
from localisation.get_language import get_language
from logs.write_server_errors import log_error
from utils.spotify_helper import extract_track_id, get_spotify_client
from localisation.translations.downloader import translations

async def find_song_on_ytmusic(query: str) -> str:
    ydl_opts = {
        "quiet": True,
        "default_search": "ytsearch1",
        "format": "bestaudio/best",
        "noplaylist": True,
        'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Safari/537.36'},

    }
    def search():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(query, download=False)

    try:
        info = await asyncio.to_thread(search)
        if "entries" in info and len(info["entries"]) > 0:
            video_id = info["entries"][0]["id"]
            return f"https://music.youtube.com/watch?v={video_id}"
        return None
    except Exception as e:
        log_error("url", e, 1111, "find song on ytmusic")
        return None

async def process_spotify_track(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id: str = None, msg_id = None):
    if "/playlist/" in url or "/album/" in url:
        await process_music_playlist(bot, dp, business_connection_id, chat_id, url, user_msg_id=msg_id)
        return
    pool = dp["db_pool"]
    chat_language = await get_language(pool, chat_id)
    spotify = get_spotify_client()
    track_id = extract_track_id(url)

    track = spotify.track(track_id)
    artist = track["artists"][0]["name"]
    track_name = track["name"]
    search_query = f"{artist} {track_name} audio"
    print(f"🔍 Ищем на YouTube Music: {search_query}")

    youtube_music_url = await find_song_on_ytmusic(search_query)

    if youtube_music_url:
        print(f"✅ Найдено: {youtube_music_url}")
        return await process_youtube_music(bot, youtube_music_url, chat_id, dp, business_connection_id, msg_id)
    else:
        await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["unavaliable_content"][chat_language], reply_to_message_id=msg_id, reply_markup=await send_log_keyboard(translations["unavaliable_content"][chat_language], "Not found in YouTube", chat_language, chat_id, url))
    
