import asyncio
import yt_dlp
import os
import requests
import math
from aiogram import Bot
from aiogram.types import FSInputFile
from downloader.media import del_media_content
from downloader.youtube.youtube import download_thumbnail
from keyboard import generate_playlist_keyboard
from typing import Optional
from user.get_user_path import get_user_path
from utils.spotify_helper import extract_spotify_id, get_spotify_client

PAGE_SIZE = 10

async def process_music_playlist(bot: Bot, chat_id: int, url: str, page: int = 1, msg_id: Optional[int] = None):
    """
    Универсальная функция обработки плейлистов с разных платформ (Spotify, YouTube Music).
    """
    user_folder = await get_user_path(chat_id)
    source = ""
    
    # 📌 Определяем источник (Spotify / YouTube)
    if "spotify" in url:
        playlist_info = await fetch_spotify_data(url, user_folder)
        source = "S"
    else:
        playlist_info = await fetch_youtube_music_playlist(url, user_folder)
        source = "Y"

    if "error" in playlist_info:
        return await bot.send_message(chat_id, playlist_info["error"])

    # 📌 Универсальный формат данных
    title = playlist_info.get("title", "Без названия")
    owner = playlist_info.get("owner", "Неизвестный")
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
        

    caption = f"🎵 <b>{title}</b>\n👤 {owner}\n📀 Плейлист\n🎧 Треков: {total_tracks}\n📃 Страница {page}/{total_pages}\n⬇ Выберите песню для скачивания"

    if msg_id is None:
        message = await bot.send_photo(chat_id, photo=FSInputFile(cover_path), caption=caption, parse_mode="HTML")
        msg_id = message.message_id

    msg_id = int(msg_id)
    print(playlist_id)
    inline_keyboard = await generate_playlist_keyboard(songs_for_current_page, chat_id, source, playlist_id, page, total_pages, msg_id, content_type)

    await bot.edit_message_caption(chat_id=chat_id, message_id=msg_id, caption=caption, reply_markup=inline_keyboard, parse_mode="HTML")

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
        'force_generic_extractor': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if "_type" in info and info["_type"] == "playlist":
            title = info.get("title", "Без названия")
            owner = info.get("uploader", "Неизвестный исполнитель")
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
                download_thumbnail(cover_url, cover_path)

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
        title = data.get("name", "Без названия")
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

            tracks.append({"title": f"{artist_name} - {track_name}", "id": track_id})

        # 📌 Загружаем обложку
        cover_path = os.path.join(user_folder, f"{spotify_id}_thumbnail.jpg")
        if cover_url:
            download_thumbnail(cover_url, cover_path)

        return {
            "title": title,
            "owner": owner,
            "playlist_id": playlist_id,  # ✅ Теперь ID плейлиста тоже возвращается
            "tracks": tracks,
            "cover_path": cover_path,
            "content_type": content_type
        }
    
    except Exception as e:
        return {"error": f"Ошибка при обработке Spotify: {str(e)}"}
