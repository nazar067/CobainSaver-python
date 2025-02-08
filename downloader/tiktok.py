import os
import requests
import json
from aiohttp import ClientSession
from aiogram import Bot, Dispatcher

from downloader.media import send_audio, send_video
from localisation.get_language import get_language
from user.get_user_path import get_user_path
from utils.fetch_data import download_file
from utils.get_name import get_random_file_name

async def fetch_tiktok_video(bot: Bot, url: str, chat_id: int, dp: Dispatcher, business_connection_id) -> dict:
    """
    Загружает видео с TikTok через API.
    Возвращает словарь с путями к видео и миниатюре.
    """
    try:
        pool = dp["db_pool"]
        chat_language = await get_language(pool, chat_id)
        api_url = "https://www.tikwm.com/api/"
        save_folder = await get_user_path(chat_id)
        async with ClientSession() as session:
            payload = {"url": url, "hd": "1"}
            async with session.post(api_url, data=payload) as response:
                if response.status != 200:
                    return {"error": "Ошибка API"}

                data = await response.json()

        if "data" not in data or "play" not in data["data"]:
            return {"error": "Видео не найдено"}

        # 📌 Проверяем размеры видео
        hd_size_mb = data["data"].get("hd_size", 0) / (1024 * 1024)
        play_size_mb = data["data"].get("size", 0) / (1024 * 1024)

        if hd_size_mb > 0 and hd_size_mb < 49:
            video_url = data["data"]["hdplay"]  # ✅ Если HD < 50MB, скачиваем HD
        elif play_size_mb > 0 and play_size_mb < 49:
            video_url = data["data"]["play"]  # ✅ Если HD > 50MB, скачиваем обычное
        else:
            return {"error": "❌ Видео больше 50MB и не может быть скачано"}
        

        video_thumbnail_url = data["data"].get("origin_cover", None)
        video_title = data["data"].get("title", "TikTok_Video")

        # 📌 Удаление хэштегов из заголовка
        video_title = video_title.split("#")[0].strip()
        video_title = video_title[:800] + "..." if len(video_title) > 800 else video_title
        
        video_duration = data["data"]["duration"]
        
        audio_url = data["data"]["music_info"]["play"]
        audio_title = data["data"]["music_info"]["title"]
        
        audio_thumbnail_url = data["data"]["music_info"]["cover"]
        
        audio_duration = data["data"]["music_info"]["duration"]
        
        audio_author = data["data"]["music_info"]["author"]

        # 📌 Пути для сохранения файлов
        os.makedirs(save_folder, exist_ok=True)
        video_path = os.path.join(save_folder, get_random_file_name("mp4"))
        video_thumbnail_path = os.path.join(save_folder, get_random_file_name("jpg"))
        audio_path = os.path.join(save_folder, get_random_file_name("mp3"))
        audio_thumbnail_path = os.path.join(save_folder, get_random_file_name("jpg"))
        
        await download_file(video_url, video_path)
        await download_file(audio_url, audio_path)
        
        # 📌 Скачивание превью (если есть)
        if video_thumbnail_url:
            await download_file(video_thumbnail_url, video_thumbnail_path, False)
        else:
            video_thumbnail_path = None
        if audio_thumbnail_url:
            await download_file(audio_thumbnail_url, audio_thumbnail_path, False)
        else:
            audio_thumbnail_path = None
        
        await send_video(bot, chat_id, chat_language, business_connection_id, video_path, video_title, video_thumbnail_path, video_duration)
        await send_audio(bot, chat_id, chat_language, business_connection_id, audio_path, audio_title, audio_thumbnail_path, audio_duration, audio_author)
        return
        

    except Exception as e:
        return print({"error": f"Ошибка обработки TikTok: {str(e)}"})
