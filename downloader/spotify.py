import yt_dlp
import asyncio
from aiogram import Bot
from downloader.youtube.youtube_music import process_youtube_music
from downloader.playlist import process_music_playlist
from utils.spotify_helper import extract_track_id, get_spotify_client

async def find_song_on_ytmusic(query: str) -> str:
    ydl_opts = {
        "quiet": True,
        "default_search": "ytsearch1",
        "format": "bestaudio/best",
        "noplaylist": True,
    }
    def search():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(query, download=False)

    try:
        info = await asyncio.to_thread(search)  # Асинхронный вызов
        if "entries" in info and len(info["entries"]) > 0:
            video_id = info["entries"][0]["id"]
            return f"https://music.youtube.com/watch?v={video_id}"
        return None
    except Exception as e:
        print(f"❌ Ошибка при поиске YouTube Music: {str(e)}")
        return None

async def process_spotify_track(bot: Bot, url: str, chat_id: int, business_connection_id: str = None):
    if "/playlist/" in url or "/album/" in url:
        if business_connection_id is "":
            await process_music_playlist(bot, chat_id, url)
        return
    spotify = get_spotify_client()
    track_id = extract_track_id(url)

    try:
        track = spotify.track(track_id)
        artist = track["artists"][0]["name"]
        track_name = track["name"]
        search_query = f"{artist} {track_name} audio"
        print(f"🔍 Ищем на YouTube Music: {search_query}")

        youtube_music_url = await find_song_on_ytmusic(search_query)

        if youtube_music_url:
            print(f"✅ Найдено: {youtube_music_url}")
            asyncio.create_task(process_youtube_music(bot, youtube_music_url, chat_id, business_connection_id))
        else:
            await bot.send_message(chat_id, "❌ Не удалось найти трек на YouTube Music.")
    
    except Exception as e:
        await bot.send_message(chat_id, f"❌ Ошибка при обработке Spotify трека: {str(e)}")
