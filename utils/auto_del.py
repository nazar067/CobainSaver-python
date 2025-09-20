import logging
import os
import time
import asyncio
from datetime import datetime, timedelta

from logs.write_server_errors import log_error

DOWNLOADS_FOLDER = "downloads"
CHECK_INTERVAL = 1800

async def delete_old_files():
    """
    Функция, которая каждые 1 час проверяет папки в 'downloads/' и удаляет файлы старше 1 часа.
    """
    while True:
        now = datetime.now()

        if not os.path.exists(DOWNLOADS_FOLDER):
            os.makedirs(DOWNLOADS_FOLDER)

        for folder_name in os.listdir(DOWNLOADS_FOLDER):
            folder_path = os.path.join(DOWNLOADS_FOLDER, folder_name)

            if not os.path.isdir(folder_path):
                continue

            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)

                file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path))

                if now - file_creation_time > timedelta(minutes=30):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        log_error("url", e, 1111, "del old files")

        await asyncio.sleep(CHECK_INTERVAL)

