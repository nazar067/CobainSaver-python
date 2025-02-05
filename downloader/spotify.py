import os
import yt_dlp
import asyncio
import requests
import json
from aiogram import Bot
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from downloader.youtube.youtube_music import process_youtube_music

def get_spotify_credentials():
    return "cdae9ddf2d664afcbda097fe95c4ee4f", "63a589c3bb794462bdf587df6d9125a9"

def get_spotify_client():
    client_id, client_secret = get_spotify_credentials()
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return Spotify(auth_manager=auth_manager)

def extract_track_id(url: str) -> str:
    return url.split("/")[-1].split("?")[0]

async def find_song_on_ytmusic(query: str) -> str:
    ydl_opts = {
        "quiet": True,
        "default_search": "ytsearch1",
        "format": "bestaudio/best",
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info and len(info["entries"]) > 0:
            video_id = info["entries"][0]["id"]
            return f"https://music.youtube.com/watch?v={video_id}"
        return None

async def process_spotify_track(bot: Bot, url: str, chat_id: int, business_connection_id: str = None):
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
