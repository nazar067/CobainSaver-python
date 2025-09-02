import asyncio
import logging
import re
import yt_dlp
import os
import requests
import math
from aiogram import Bot, Dispatcher
from aiogram.types import FSInputFile
from downloader.media import del_media_content
from keyboard import generate_playlist_keyboard, send_log_keyboard
from typing import Optional
from localisation.get_language import get_language
from logs.write_server_errors import log_error
from user.get_user_path import get_user_path
from utils.fetch_data import download_file
from utils.get_name import get_random_file_name
from utils.spotify_helper import extract_spotify_id, get_spotify_client
from localisation.translations.downloader import translations

PAGE_SIZE = 10

async def process_music_playlist(bot: Bot, dp: Dispatcher, business_connection_id: Optional[str], chat_id: int, url: str, page: int = 1, msg_id: Optional[int] = None, user_msg_id = None):
    """
    Универсальная функция обработки плейлистов с разных платформ (Spotify, YouTube Music).
    """
    user_folder = await get_user_path(chat_id)
    source = ""
    pool = dp["db_pool"]
    chat_language = await get_language(pool, chat_id)

    if "spotify" in url:
        playlist_info = await fetch_spotify_data(url, user_folder)
        source = "S"
    elif "soundcloud" in url:
        playlist_info = await fetch_soundcloud_playlist(url, user_folder)
        source = "C"
    else:
        playlist_info = await fetch_youtube_music_playlist(url, user_folder)
        source = "Y"

    if "error" in playlist_info:
        return await bot.send_message(chat_id=chat_id, business_connection_id=business_connection_id, text=translations["unavaliable_content"][chat_language], reply_to_message_id=msg_id, reply_markup=await send_log_keyboard(translations["unavaliable_content"][chat_language], playlist_info, chat_language, chat_id, url))

    title = playlist_info.get("title", "")
    owner = playlist_info.get("owner", "")
    tracks = playlist_info.get("tracks", [])
    cover_path = playlist_info.get("cover_path", None)
    content_type = playlist_info.get("content_type", "p")
    playlist_id = playlist_info.get("playlist_id", None)
    total_tracks = len(tracks)
    total_pages = max(1, math.ceil(total_tracks / PAGE_SIZE))
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    songs_for_current_page = tracks[start_idx:end_idx]
        
    caption = translations["playlist_info"][chat_language].format(
        title=title,
        total_tracks=total_tracks,
        page=page,
        total_pages=total_pages
    )
    
    if msg_id == None:
        message = await bot.send_photo(business_connection_id=business_connection_id, chat_id=chat_id, photo=FSInputFile(cover_path), caption=caption, parse_mode="HTML", reply_to_message_id=user_msg_id)
        msg_id = message.message_id

    msg_id = int(msg_id)
    inline_keyboard = await generate_playlist_keyboard(songs_for_current_page, source, playlist_id, page, total_pages, content_type, dp, chat_id)
    await bot.edit_message_caption(business_connection_id=business_connection_id, chat_id=chat_id, message_id=msg_id, caption=caption, reply_markup=inline_keyboard, parse_mode="HTML")

    if cover_path:
        await del_media_content(cover_path)

    return msg_id
        

async def fetch_youtube_music_playlist(url: str, user_folder: str) -> dict:
    """
    Универсальная функция для получения информации о плейлисте YouTube Music.
    """
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.115 Safari/537.36'},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if "_type" in info and info["_type"] == "playlist":
            title = info.get("title", "")
            owner = info.get("uploader", "")
            playlist_id = info.get("id", None)

            # 📌 Формируем список треков
            tracks = [
                {"title": entry["title"], "id": entry["id"]}
                for entry in info.get("entries", []) if entry.get("id")
            ]

            # 📌 Обложка плейлиста (по первому видео)
            cover_url = f"https://img.youtube.com/vi/{tracks[0]['id']}/maxresdefault.jpg" if tracks else None
            cover_path = os.path.join(user_folder, f"{playlist_id}_thumbnail.jpg")

            if cover_url:
                await download_file(cover_url, cover_path)

            return {
                "title": title,
                "owner": owner,
                "tracks": tracks,
                "cover_path": cover_path,
                "content_type": "плейлист",
                "playlist_id": playlist_id
            }
        else:
            return {"error": "Ошибка: Не удалось получить информацию о плейлисте."}

    except Exception as e:
        log_error(url, e, 1111, "fetch yt playlist")
        return {"error": f"Ошибка при извлечении плейлиста: {str(e)}"}
    

async def fetch_spotify_data(url: str, user_folder: str) -> dict:
    """
    Универсальная функция получения информации о плейлисте или альбоме Spotify.
    """
    spotify = get_spotify_client()
    spotify_id = extract_spotify_id(url)

    try:
        if "album" in url:
            data = spotify.album(spotify_id)
            content_type = "a"
        elif "playlist" in url:
            data = spotify.playlist(spotify_id)
            content_type = "p"
        else:
            return {"error": "❌ Неверный URL Spotify"}

        # 📌 Получаем информацию
        title = data.get("name", "")
        owner = data["owner"]["display_name"] if "playlist" in url else data["artists"][0]["name"]
        playlist_id = data["id"]  # ✅ Теперь сохраняем ID плейлиста/альбома
        cover_url = data["images"][0]["url"] if data.get("images") else None
        track_items = data["tracks"]["items"]

        # 📌 Список треков
        tracks = []
        for item in track_items:
            track = item["track"] if "playlist" in url else item
            track_name = track["name"]
            artist_name = track["artists"][0]["name"]
            track_id = track["id"]

            tracks.append({"title": f"{track_name} - {artist_name}", "id": track_id})

        # 📌 Загружаем обложку
        cover_path = os.path.join(user_folder, f"{spotify_id}_thumbnail.jpg")
        if cover_url:
            await download_file(cover_url, cover_path)

        return {
            "title": title,
            "owner": owner,
            "playlist_id": playlist_id,  # ✅ Теперь ID плейлиста тоже возвращается
            "tracks": tracks,
            "cover_path": cover_path,
            "content_type": content_type
        }
    
    except Exception as e:
        log_error(url, e, 1111, "fetch spotify data")
        return {"error": f"Ошибка при обработке Spotify: {str(e)}"}

async def fetch_soundcloud_playlist(url: str, user_folder: str) -> dict:
    """
    Универсальная функция для получения информации о плейлисте YouTube Music.
    """
    random_name = get_random_file_name("")
    ydl_opts = {
        'quiet': True,
        'http_headers': {'User-Agent': 'Mozilla/5.0'},
        'outtmpl': os.path.join(user_folder, random_name + "%(ext)s"),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if "_type" in info and info["_type"] == "playlist":
            title = info.get("title", "")
            owner = info.get("uploader", "")
            playlist_id = info.get("id", None)

            # 📌 Формируем список треков
            tracks = [
                {"title": entry["title"], "id": entry["id"]}
                for entry in info.get("entries", []) if entry.get("id")
            ]

            # 📌 Обложка плейлиста (по первому видео)
            cover_url = "https://github.com/TelegramBots/book/raw/master/src/docs/photo-ara.jpg"
            cover_path = os.path.join(user_folder, f"{playlist_id}_thumbnail.jpg")

            if cover_url:
                await download_file(cover_url, cover_path)

            return {
                "title": title,
                "owner": owner,
                "tracks": tracks,
                "cover_path": cover_path,
                "content_type": "плейлист",
                "playlist_id": playlist_id
            }
        else:
            return {"error": "Ошибка: Не удалось получить информацию о плейлисте."}

    except Exception as e:
        log_error(url, e, 1111, "fetch yt playlist")
        return {"error": f"Ошибка при извлечении плейлиста: {str(e)}"}
