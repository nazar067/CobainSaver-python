import mimetypes
from urllib.parse import urlparse


def detect_file_type(url: str) -> str:
    """
    🧐 Определяет тип файла (фото или видео) по URL, даже если расширение скрыто внутри параметров.
    """
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    
    # Проверяем расширение в пути URL
    image_extensions = (".jpg", ".jpeg", ".png", ".webp")
    video_extensions = (".mp4", ".m4v")

    for ext in image_extensions:
        if ext in path:
            return "photo"
    
    for ext in video_extensions:
        if ext in path:
            return "video"

    # Альтернативный метод определения MIME-типа (если URL не содержит расширения)
    mime_type, _ = mimetypes.guess_type(url)
    if mime_type:
        if mime_type.startswith("image/"):
            return "photo"
        elif mime_type.startswith("video/"):
            return "video"

    return "unknown"