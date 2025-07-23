import os
import logging
import traceback

from constants.errors.telegram_errors import CANNOT_BE_FORWARDED, NOT_RIGHTS
from constants.errors.tiktok_api_errors import API_LIMIT

def setup_logging():
    """
    Настройка логирования с записью новых ошибок в начало файла.
    """
    log_file = "serverLogs.txt"
    
    if not os.path.exists(log_file):
        open(log_file, "w").close()

    class ReverseFileHandler(logging.FileHandler):
        def emit(self, record):
            log_message = self.format(record)
            with open(self.baseFilename, "r", encoding="utf-8") as f:
                existing_content = f.read()
            with open(self.baseFilename, "w", encoding="utf-8") as f:
                f.write(log_message + "\n\n" + existing_content)

    handler = ReverseFileHandler(log_file, encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    logger.addHandler(handler)

def log_error(url: str, error: Exception = None, chat_id: int = None, service: str = None, string_error: str = None):
    """
    Логирует структурированную ошибку.
    """
    logger = logging.getLogger()
    location = "Not found"
    correct_error = None
    if error:
        tb_lines = traceback.extract_tb(error.__traceback__)
        # Фильтруем только пользовательские пути (исключаем site-packages, frozen и stdlib)
        user_frame = next(
            (frame for frame in reversed(tb_lines) if "site-packages" not in frame.filename and "<frozen" not in frame.filename),
            tb_lines[-1]
        )
        # Получаем абсолютный путь, если доступен
        location = f"{user_frame.filename}:{user_frame.lineno}"
        correct_error = f"❗️Ошибка: {type(error).__name__}: {error}"
    else:
        correct_error = f"❗️Ошибка: {string_error}"

    if NOT_RIGHTS not in str(correct_error) and CANNOT_BE_FORWARDED not in str(correct_error) and API_LIMIT not in str(correct_error):
        log_message = (
            f"🧩 Ошибка в сервисе: {service or 'Неизвестно'}\n"
            f"💬 Chat ID: {chat_id or 'Неизвестно'}\n"
            f"📌 Место: {location}\n"
            f"{correct_error}\n"
            f"🌐 URL: {url or '—'}"
        )
        logger.error(log_message)
