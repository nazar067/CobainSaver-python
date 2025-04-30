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

async def get_clear_name(name: str, max_symbols: int):
    name = re.sub(r"#\S+", "", name).strip()
    name = name[:max_symbols] + "..." if len(name) > max_symbols else name 
    return name

def sanitize_filename(filename: str) -> str:
    invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
    sanitized_name = re.sub(invalid_chars, "", filename).strip()

    return sanitized_name if sanitized_name else get_random_file_name("")

async def get_name_for_button_data(name: str, max_symbols: int = 10):
    name = re.sub(r"#\S+", "", name).strip()
    name = name.replace(" ", "_")
    name = name[:max_symbols] + "" if len(name) > max_symbols else name
    return name
