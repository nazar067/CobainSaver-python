import os

from downloader.media import del_media_content
from utils.fetch_data import fetch_youtube_data

MAX_MB = 1999  # новый лимит

async def select_optimal_quality(url: str, user_folder: str, initial_quality: str, chat_language) -> dict | str:
    """
    Скачивает видео, начиная с 1080p. Если файла нет/качество недоступно/размер > 2000MB —
    понижает качество: 720 -> 480 -> 360 -> 240 -> 144.
    Если даже 144p > 2000MB (или вообще не получилось) — возвращает "large".
    """
    # Порядок попыток — от высокого к низкому
    qualities = ["1080", "720", "480", "360", "240", "144"]

    last_file_path = None
    last_thumb_path = None

    for q in qualities:
        # Загружаем в текущем качестве
        data = await fetch_youtube_data(url, user_folder, q, chat_language)

        # Если формат недоступен/вернулся error — пробуем следующее качество
        if isinstance(data, dict) and "error" in data:
            continue

        # Ожидаем поля из твоего fetch_youtube_data
        file_path = data["file_path"]
        video_title = data["video_title"]
        duration = data["duration"]
        thumbnail_path = data["thumbnail_path"]

        # Размер в MB
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        except FileNotFoundError:
            # на всякий пожарный: если файл не появился — понижаем качество
            await del_media_content(file_path)
            if thumbnail_path:
                await del_media_content(thumbnail_path)
            continue

        # Если вписываемся в лимит — возвращаем успех
        if file_size_mb <= MAX_MB:
            return {
                "file_path": file_path,
                "file_size_mb": file_size_mb,
                "quality": q,
                "video_title": video_title,
                "thumbnail_path": thumbnail_path,
                "duration": duration,
                "success": True,
            }

        # Слишком большой — чистим и идём ниже
        await del_media_content(file_path)
        if thumbnail_path:
            await del_media_content(thumbnail_path)

        # запомним последний путь (для финальной уборки, если нужно)
        last_file_path = file_path
        last_thumb_path = thumbnail_path

    # Если добрались до конца (даже 144p не уложилось / не вышло скачать) — вернём "large"
    if last_file_path:
        await del_media_content(last_file_path)
    if last_thumb_path:
        await del_media_content(last_thumb_path)
    return "large"
