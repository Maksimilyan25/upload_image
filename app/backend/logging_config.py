import json
import logging
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Форматтер для логов в формате JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись лога в формате JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }

        # Добавляем дополнительные поля, если они есть
        if hasattr(record, 'task_id'):
            log_entry['task_id'] = record.task_id

        if hasattr(record, 'image_id'):
            log_entry['image_id'] = record.image_id

        if hasattr(record, 'file_path'):
            log_entry['file_path'] = record.file_path

        # Добавляем информацию об исключении, если она есть
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Настройка логирования в формате JSON."""
    # Создаем логгер
    logger = logging.getLogger("image_service")
    logger.setLevel(level)

    # Очищаем существующие обработчики
    logger.handlers.clear()

    # Создаем обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Создаем и устанавливаем форматтер
    formatter = JSONFormatter()
    console_handler.setFormatter(formatter)

    # Добавляем обработчик к логгеру
    logger.addHandler(console_handler)

    return logger


# Глобальный экземпляр логгера
logger = setup_logging()
