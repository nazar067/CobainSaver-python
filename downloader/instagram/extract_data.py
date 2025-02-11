import os


def extract_instagram_files(directory: str) -> list:
    """
    📌 Находит все скачанные медиафайлы (фото/видео) в папке.
    """
    if not os.path.exists(directory):
        print(f"❌ Ошибка: Папка {directory} не существует.")
        return []

    media_files = []
    for file in os.listdir(directory):
        if file.endswith((".jpg", ".mp4")):
            media_files.append(os.path.join(directory, file))

    return sorted(media_files)