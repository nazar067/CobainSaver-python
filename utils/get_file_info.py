import os
import subprocess
from typing import Optional, Tuple, Union, List
from aiogram.types import InputMediaPhoto, InputMediaVideo, FSInputFile

async def get_music_size(bit_rate_kbps: int, duration_seconds: int) -> float:
    size_mb = (bit_rate_kbps * duration_seconds) / (8 * 1024)
    return size_mb
    
async def get_video_width_height(
    media: Optional[Union[str, FSInputFile, List[Union[InputMediaPhoto, InputMediaVideo]]]]
) -> Optional[Tuple[int, int]]:
    """
    Определяет (width, height) видео.
    Поддерживает:
      - str: путь к видео
      - FSInputFile: локальный файл
      - список InputMediaVideo: берём первый элемент
    Требует установленного ffprobe (часть ffmpeg).
    """
    if media is None:
        return None

    path = None

    # Список
    if isinstance(media, list) and media:
        first = media[0]
        if isinstance(first, InputMediaVideo):
            if isinstance(first.media, str) and os.path.exists(first.media):
                path = first.media
        elif isinstance(first, InputMediaPhoto):
            return None  # это фото, не видео

    # Строка
    if isinstance(media, str) and os.path.exists(media):
        path = media

    # FSInputFile
    if isinstance(media, FSInputFile) and os.path.exists(media.path):
        path = media.path

    if not path:
        return None

    try:
        # вызываем ffprobe
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0",
                path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        w, h = result.stdout.strip().split("x")
        return int(w), int(h)
    except Exception:
        return None
    