import logging
from aiohttp import ClientSession
from config import TIKTOK_API
from constants.errors.tiktok_api_errors import API_LIMIT
from logs.write_server_errors import log_error
from utils.get_name import get_clear_name
from utils.get_settings import get_settings
import asyncio

from utils.service_identifier import identify_service
from utils.text_format import format_as_expandable_quote

api_url = TIKTOK_API

tiktok_request_queue = asyncio.Queue()
tiktok_request_lock = asyncio.Lock()

async def tiktok_request_worker():
    while True:
        job = await tiktok_request_queue.get()
        if job:
            url, session, payload, future = job
            try:
                async with session.post(api_url, data=payload) as response:
                    if response.status != 200:
                        future.set_result({"error": "Ошибка API"})
                    else:
                        result = await response.json()
                        if result.get("msg") == API_LIMIT:
                            await asyncio.sleep(1)
                            await tiktok_request_queue.put((url, session, payload, future))
                        else:
                            future.set_result(result)
            except Exception as e:
                future.set_result({"error": str(e)})
            await asyncio.sleep(1)
        tiktok_request_queue.task_done()

async def extract_tiktok_data(url: str, pool, chat_id) -> dict:
    """
    Извлекает данные TikTok из API: ссылки на видео, аудио, размеры, превью или изображения.
    Обрабатывает лимит API: 1 запрос в секунду.
    """
    payload = {"url": url, "hd": "1"}

    async with ClientSession() as session:
        future = asyncio.get_event_loop().create_future()
        await tiktok_request_queue.put((url, session, payload, future))
        data = await future

    if "data" not in data:
        log_error(url, chat_id=chat_id, service=await identify_service(url), string_error=data)
        return {"error": f"Контент не найден, {data}"}

    media_title = data["data"].get("title", "TikTok_Content")
    if media_title:
        media_title = await get_clear_name(media_title, 760)
        if len(media_title) > 174:
            media_title = await format_as_expandable_quote(media_title)

    images = data["data"].get("images", [])
    live_images = data["data"].get("live_images", [])

    merged_images = await merge_images_with_live(images, live_images)
    # 📸 Фото
    if "images" in data["data"]:
        return {
            "type": "photo",
            "images": merged_images,
            "title": media_title,
            "audio_url": data["data"].get("play", None),
            "audio_title": data["data"]["music_info"].get("title", "TikTok_Audio"),
            "audio_thumbnail_url": data["data"]["music_info"].get("cover", None),
            "audio_duration": data["data"]["music_info"].get("duration", 0),
            "audio_author": data["data"]["music_info"].get("author", "Unknown Artist"),
        }

    # 🎥 Видео
    if "play" not in data["data"]:
        return {"error": "Видео не найдено"}

    hd_size_mb = data["data"].get("hd_size", 0) / (1024 * 1024)
    play_size_mb = data["data"].get("size", 0) / (1024 * 1024)

    hd_settings = await get_settings(pool, chat_id)
    
    if hd_size_mb >= 0 and hd_size_mb < 1999 and hd_settings["hd_size"] == True:
        video_url = data["data"]["hdplay"]
    elif play_size_mb >= 0 and play_size_mb < 1999:
        video_url = data["data"]["play"]
    else:
        return "large"

    return {
        "type": "video",
        "video_url": video_url,
        "video_thumbnail_url": data["data"].get("origin_cover", None),
        "video_title": media_title,
        "video_duration": data["data"].get("duration", 0),
        "audio_url": data["data"]["music_info"].get("play", None),
        "audio_title": data["data"]["music_info"].get("title", "TikTok_Audio"),
        "audio_thumbnail_url": data["data"]["music_info"].get("cover", None),
        "audio_duration": data["data"]["music_info"].get("duration", 0),
        "audio_author": data["data"]["music_info"].get("author", "Unknown Artist"),
    }

async def merge_images_with_live(images: list, live_images: list) -> list:
    result = []

    for i, img in enumerate(images):
        live = live_images[i] if i < len(live_images) else None

        if live:
            result.append({
                "type": "live",
                "url": live
            })
        else:
            result.append({
                "type": "image",
                "url": img
            })

    return result

