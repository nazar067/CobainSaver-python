from typing import Optional, Union
from aiogram.types import FSInputFile

def get_media_source(media_path_or_url: Optional[str]) -> Optional[Union[str, FSInputFile]]:
    """
    Определяет, является ли переданный путь ссылкой или файлом.
    Возвращает либо URL, либо FSInputFile, либо None, если пусто.
    """
    if not media_path_or_url:
        return None
    if media_path_or_url.startswith("http"):
        return media_path_or_url
    return FSInputFile(media_path_or_url)
