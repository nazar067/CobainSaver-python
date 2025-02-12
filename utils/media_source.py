from aiogram.types import InputMediaPhoto, InputMediaVideo
from aiogram.types.input_file import FSInputFile
from typing import Optional, Union, List
import os

def get_media_source(media_input: Optional[Union[str, List[str], List[Union[InputMediaPhoto, InputMediaVideo]]]]) -> Optional[Union[str, FSInputFile, List[Union[InputMediaPhoto, InputMediaVideo]]]]:
    """
    Определяет тип переданных данных: одиночный файл/ссылку или список файлов/ссылок.
    - Если передана строка, возвращает либо URL, либо FSInputFile.
    - Если передан список `InputMediaPhoto` или `InputMediaVideo`, возвращает его без изменений.
    - Если передан список путей или ссылок, возвращает список объектов `InputMediaPhoto` или `InputMediaVideo`.
    """

    if not media_input:
        return None

    if isinstance(media_input, list) and all(isinstance(item, (InputMediaPhoto, InputMediaVideo)) for item in media_input):
        return media_input

    if isinstance(media_input, str):
        if media_input.startswith("http"):
            return media_input
        return FSInputFile(media_input) if os.path.exists(media_input) else None

    elif isinstance(media_input, list):
        media_album = []

        for media_path in media_input:
            if isinstance(media_path, str):
                if media_path.startswith("http"):
                    if any(media_path.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                        media_album.append(InputMediaPhoto(media=media_path))
                    elif any(media_path.lower().endswith(ext) for ext in [".mp4", ".mov", ".mkv"]):
                        media_album.append(InputMediaVideo(media=media_path))
                elif os.path.exists(media_path):
                    if any(media_path.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                        media_album.append(InputMediaPhoto(media=FSInputFile(media_path)))
                    elif any(media_path.lower().endswith(ext) for ext in [".mp4", ".mov", ".mkv"]):
                        media_album.append(InputMediaVideo(media=FSInputFile(media_path)))

        return media_album if media_album else None
