import os

from downloader.media import del_media_content
from utils.fetch_data import download_file, fetch_youtube_data


async def select_optimal_quality(url: str, user_folder: str, initial_quality: str, chat_language) -> dict:
    """
    Универсальная функция выбора оптимального качества для скачивания.
    Поддерживает любую платформу, где есть градация качества.
    """
    quality_upgrades = {
        "360": "1080",
        "1080": "720",
        "720": "480",
        "480": "360",
        "240": "144"
    }

    quality_downgrades = ["240", "144"]
    current_quality = initial_quality

    data = await fetch_youtube_data(url, user_folder, current_quality, chat_language)

    if "error" in data:
        return {"error": data["error"]}

    file_path = data["file_path"]
    video_title = data["video_title"]
    duration = data["duration"]
    thumbnail_path = data["thumbnail_path"]

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"Размер {current_quality}p: {file_size_mb}MB")  # Лог для отладки

    # 🔹 Первый этап: проверяем, можно ли улучшить качество
    if file_size_mb <= 10:
        next_quality = "1080"
    elif 11 <= file_size_mb <= 25:
        next_quality = "720"
    elif 26 <= file_size_mb <= 45:
        next_quality = "480"
    elif 51 <= file_size_mb <= 120:
        next_quality = "240"
    elif 121 <= file_size_mb <= 180:
        next_quality = "144"
    else:
        next_quality = None  # Если 360p > 180MB, сразу понижаем качество

    if next_quality:
        print(f"⚡ Переход к {next_quality}p")
        await del_media_content(file_path)
        await del_media_content(thumbnail_path)
        current_quality = next_quality

        data = await fetch_youtube_data(url, user_folder, current_quality, chat_language)
        if "error" in data:
            return {"error": data["error"]}

        file_path = data["file_path"]
        thumbnail_path = data["thumbnail_path"]
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        print(f"Размер {current_quality}p: {file_size_mb}MB")

    if file_size_mb <= 50:
        return {
            "file_path": file_path,
            "file_size_mb": file_size_mb,
            "quality": current_quality,
            "video_title": video_title,
            "thumbnail_path": thumbnail_path,
            "duration": duration,
            "success": True
        }

    quality_downgrades = [q for q in quality_upgrades.values() if int(q) < int(current_quality)]
    for next_quality in quality_downgrades:
        print(f"🔻 Понижение до {next_quality}p")
        await del_media_content(file_path)
        await del_media_content(thumbnail_path)
        current_quality = next_quality

        data = await fetch_youtube_data(url, user_folder, current_quality, chat_language)
        if "error" in data:
            return {"error": data["error"]}

        file_path = data["file_path"]
        thumbnail_path = data["thumbnail_path"]
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        print(f"Размер {current_quality}p: {file_size_mb}MB")

        if file_size_mb <= 50:
            return {
                "file_path": file_path,
                "file_size_mb": file_size_mb,
                "quality": current_quality,
                "video_title": video_title,
                "thumbnail_path": thumbnail_path,
                "duration": duration,
                "success": True
            }

    await del_media_content(file_path)
    await del_media_content(thumbnail_path)
    return "large"
