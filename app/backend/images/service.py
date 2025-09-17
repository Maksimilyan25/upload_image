import os
import uuid
from typing import Optional, Dict

from sqlalchemy import text

from app.backend.images.repository import ImageRepository
from app.backend.images.rabbitmq import RabbitMQClient
from app.backend.database.db import SessionDep
from app.backend.logging_config import logger


class ImageService:
    def __init__(self, db: SessionDep):
        self.db = db
        self.repository = ImageRepository(db)
        self.rabbitmq_url = os.getenv("RABBITMQ_URL")

    async def upload_image(self, file_content: bytes, filename: str) -> dict:
        """Загрузить изображение и отправить задачу в очередь."""
        # Сохраняем файл на диск
        image_id = str(uuid.uuid4())
        file_path = f"uploads/{image_id}_{filename}"

        logger.info("Начало загрузки изображения %s с ID %s",
                    filename, image_id)

        # Создаем директорию uploads если её нет
        os.makedirs("uploads", exist_ok=True)

        # Сохраняем файл
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Создаем запись в БД
        image = await self.repository.create_image(file_path)
        logger.info("Изображение %s успешно сохранено в БД", image_id)

        # Отправляем задачу в RabbitMQ
        await self.send_to_queue(image.id, file_path)
        logger.info("Задача для изображения %s отправлена в очередь",
                    image_id)

        return {
            "id": str(image.id),
            "status": image.status.value
        }

    async def send_to_queue(self, image_id: uuid.UUID, file_path: str) -> None:
        """Отправить задачу в очередь RabbitMQ."""
        task_id = str(uuid.uuid4())

        try:
            logger.info("Отправка задачи %s для изображения %s в очередь",
                        task_id, image_id)

            # Создаем клиента RabbitMQ
            rabbit_client = RabbitMQClient()
            rabbit_client.connect()

            # Отправляем сообщение
            message = {
                "task_id": task_id,
                "image_id": str(image_id),
                "file_path": file_path
            }

            rabbit_client.send_message(message)
            rabbit_client.disconnect()

            logger.info("Задача %s для изображения %s успешно отправлена",
                        task_id, image_id)
        except Exception as e:
            logger.error("Ошибка отправки задачи %s для изображения %s: %s",
                         task_id, image_id, str(e))
            # В реальном приложении здесь должна быть обработка ошибок

    async def get_image_info(self, image_id: uuid.UUID) -> Optional[Dict]:
        """Получить информацию об изображении."""
        logger.info("Запрос информации об изображении %s", image_id)

        image = await self.repository.get_image_by_id(image_id)
        if not image:
            logger.info("Изображение %s не найдено", image_id)
            return None

        logger.info("Информация об изображении %s успешно получена", image_id)
        return {
            "id": str(image.id),
            "status": image.status.value,
            "original_url": image.original_url,
            "thumbnails": image.thumbnails or {}
        }

    async def check_health(self) -> dict:
        """Проверить состояние сервиса."""
        logger.info("Начало проверки состояния сервиса")

        health_status = {
            "service": "ok",
            "database": "unknown",
            "rabbitmq": "unknown"
        }

        # Проверяем подключение к БД
        try:
            # Простая проверка подключения
            await self.db.execute(text("SELECT 1"))
            health_status["database"] = "ok"
            logger.info("Подключение к базе данных успешно")
        except Exception as e:
            health_status["database"] = f"error: {str(e)}"
            logger.error("Ошибка подключения к базе данных: %s", str(e))

        # Проверяем подключение к RabbitMQ
        try:
            rabbit_client = RabbitMQClient()
            rabbit_client.connect()
            rabbit_client.disconnect()
            health_status["rabbitmq"] = "ok"
            logger.info("Подключение к RabbitMQ успешно")
        except Exception as e:
            health_status["rabbitmq"] = f"error: {str(e)}"
            logger.error("Ошибка подключения к RabbitMQ: %s", str(e))

        logger.info("Проверка состояния сервиса завершена: %s", health_status)
        return health_status
