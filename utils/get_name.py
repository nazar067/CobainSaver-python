import random
import re
import time


def get_random_file_name(extension: str) -> str:
    """
    Генерирует случайное имя файла с текущим временем в миллисекундах + случайным числом.
    """
    timestamp = int(time.time() * 1000)
    random_number = random.randint(1, 1000)
    return f"{timestamp}_{random_number}.{extension}"

async def get_clear_name(name: str):
    name = re.sub(r"#\S+", "", name).strip()
    name = name[:800] + "..." if len(name) > 800 else name 
    return name

def sanitize_filename(filename: str) -> str:
    invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
    sanitized_name = re.sub(invalid_chars, "", filename).strip()

    return sanitized_name if sanitized_name else get_random_file_name("")