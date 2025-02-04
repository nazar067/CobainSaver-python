import yt_dlp
import os
import requests
import math
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from typing import Optional
from downloader.youtube.youtube import download_thumbnail
from user.get_user_path import get_user_path

PAGE_SIZE = 10


async def process_youtube_music_playlist(bot: Bot, chat_id: int, url: str, page: int = 1, msg_id: Optional[int] = None):
    """
    Обрабатывает скачивание и отображение плейлиста YouTube Music.
    """
    user_folder = await get_user_path(chat_id)

    playlist_info = fetch_youtube_music_playlist(url, user_folder)

    if "error" in playlist_info:
        return await bot.send_message(chat_id, playlist_info["error"])

    playlist_title = playlist_info["playlist_title"]
    playlist_id = playlist_info["playlist_id"]
    videos = playlist_info["videos"]
    thumbnail_path = playlist_info["thumbnail_path"]

    total_videos = len(videos)
    total_pages = math.ceil(total_videos / PAGE_SIZE)

    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    songs_for_current_page = videos[start_idx:end_idx]

    buttons_list = [
        [InlineKeyboardButton(text=track["title"], callback_data=f"L {track['id']} {chat_id}")]
        for track in songs_for_current_page
    ]

    navigation_buttons = []
    if total_pages > 1:
        if page > 1:
            navigation_buttons.append(
                InlineKeyboardButton(text="◀️ Назад", callback_data=f"P {chat_id} {playlist_id} {page - 1} {msg_id}")
            )
        if page < total_pages:
            navigation_buttons.append(
                InlineKeyboardButton(text="Вперед ▶️", callback_data=f"N {chat_id} {playlist_id} {page + 1} {msg_id}")
            )
    if navigation_buttons:
        buttons_list.append(navigation_buttons)

    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=buttons_list)

    caption = f"🎵 <b>{playlist_title}</b>\n\nТреков: {total_videos}\nСтраница {page}/{total_pages}\n⬇ Выберите песню для скачивания"

    if msg_id:
        await bot.edit_message_caption(chat_id, msg_id, caption=caption, reply_markup=inline_keyboard, parse_mode="HTML")
    else:
        with open(thumbnail_path, "rb") as thumb:
            message = await bot.send_photo(
                chat_id=chat_id,
                photo=FSInputFile(thumbnail_path),
                caption=caption,
                reply_markup=inline_keyboard,
                parse_mode="HTML"
            )
        msg_id = message.message_id

    return msg_id


def fetch_youtube_music_playlist(url: str, user_folder: str) -> dict:
    """
    Извлекает информацию о плейлисте YouTube Music.
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
            playlist_title = info.get("title", "Плейлист без названия")
            playlist_id = info.get("id", None)
            videos = [
                {"title": entry["title"], "id": entry["id"]}
                for entry in info["entries"] if entry.get("id")
            ]

            thumbnail_url = f"https://img.youtube.com/vi/{videos[0]['id']}/maxresdefault.jpg" if videos else None
            thumbnail_path = os.path.join(user_folder, f"{playlist_id}_thumbnail.jpg")

            if thumbnail_url:
                download_thumbnail(thumbnail_url, thumbnail_path)

            return {
                "playlist_title": playlist_title,
                "playlist_id": playlist_id,
                "videos": videos,
                "thumbnail_path": thumbnail_path
            }
        else:
            return {"error": "Ошибка: Не удалось получить информацию о плейлисте."}

    except Exception as e:
        return {"error": f"Ошибка при извлечении плейлиста: {str(e)}"}