from aiohttp import ClientSession


async def extract_tiktok_data(url: str) -> dict:
    """
    Извлекает данные TikTok из API: ссылки на видео, аудио, размеры, превью.
    """
    api_url = "https://www.tikwm.com/api/"
    
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

    return {
        "video_url": video_url,
        "video_thumbnail_url": data["data"].get("origin_cover", None),
        "video_title": data["data"].get("title", "TikTok_Video"),
        "video_duration": data["data"].get("duration", 0),
        "audio_url": data["data"]["music_info"].get("play", None),
        "audio_title": data["data"]["music_info"].get("title", "TikTok_Audio"),
        "audio_thumbnail_url": data["data"]["music_info"].get("cover", None),
        "audio_duration": data["data"]["music_info"].get("duration", 0),
        "audio_author": data["data"]["music_info"].get("author", "Unknown Artist")
    }
