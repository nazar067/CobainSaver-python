import random
import time


def get_random_file_name(extension: str) -> str:
    """
    Генерирует случайное имя файла с текущим временем в миллисекундах + случайным числом.
    """
    timestamp = int(time.time() * 1000)
    random_number = random.randint(1, 1000)
    return f"{timestamp}_{random_number}.{extension}"