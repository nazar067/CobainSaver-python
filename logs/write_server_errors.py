import os
import logging

def setup_logging():
    """
    Настройка логирования с записью новых ошибок в начало файла.
    """
    log_file = "serverLogs.txt"
    
    if not os.path.exists(log_file):
        open(log_file, "w").close()
    
    class ReverseFileHandler(logging.FileHandler):
        """
        Кастомный FileHandler для записи новых логов в начало файла.
        """
        def emit(self, record):
            log_message = self.format(record)
            
            with open(self.baseFilename, "r", encoding="utf-8") as f:
                existing_content = f.read()
            
            with open(self.baseFilename, "w", encoding="utf-8") as f:
                f.write(log_message + "\n" + existing_content)

    handler = ReverseFileHandler(log_file, encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)
    logger.addHandler(handler)

def log_error(url: str, error_message: str):
    """
    Логирует ошибку с указанием URL, вызвавшего проблему.
    """
    logger = logging.getLogger()
    logger.error(f"Ошибка при обработке URL: {url}\nСообщение об ошибке: {error_message}")
