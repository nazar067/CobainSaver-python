from aiogram.types import InputMediaPhoto, InputMediaVideo
from aiogram.types.input_file import FSInputFile
from typing import Optional, Union, List
from PIL import Image
import os
from logs.write_server_errors import log_error


def get_media_source(media_input: Optional[Union[str, List[str], List[Union[InputMediaPhoto, InputMediaVideo]]]]) -> Optional[Union[str, FSInputFile, List[Union[InputMediaPhoto, InputMediaVideo]]]]:
    """
    Обрабатывает медиа: строку (ссылка/путь) или список.
    - Если строка: возвращает URL или FSInputFile.
    - Если список объектов InputMediaPhoto/InputMediaVideo — возвращает как есть.
    - Если список строк (путь/ссылка) — собирает InputMediaPhoto/InputMediaVideo.
      При обработке локальных изображений ресайзит до 320x320.
    """

    if not media_input:
        return None

    if isinstance(media_input, list) and all(isinstance(item, (InputMediaPhoto, InputMediaVideo)) for item in media_input):
        return media_input

    if isinstance(media_input, str):
        if media_input.startswith("http"):
            return media_input
        if os.path.exists(media_input):
            if media_input.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                resize_thumbnail(media_input)
            return FSInputFile(media_input)
        return None

    elif isinstance(media_input, list):
        media_album = []

        for media_path in media_input:
            if isinstance(media_path, str):
                if media_path.startswith("http"):
                    if media_path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                        media_album.append(InputMediaPhoto(media=media_path))
                    elif media_path.lower().endswith((".mp4", ".mov", ".mkv")):
                        media_album.append(InputMediaVideo(media=media_path))
                elif os.path.exists(media_path):
                    if media_path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                        resize_thumbnail(media_path)
                        media_album.append(InputMediaPhoto(media=FSInputFile(media_path)))
                    elif media_path.lower().endswith((".mp4", ".mov", ".mkv")):
                        media_album.append(InputMediaVideo(media=FSInputFile(media_path)))

        return media_album if media_album else None

    return None


def resize_thumbnail(path: str):
    try:
        with Image.open(path) as img:
            img = img.convert("RGB")
            img = img.resize((320, 320))
            img.save(path, "JPEG", quality=80)
    except Exception as e:
        log_error("url", e, 1111, "resize thumbnail")