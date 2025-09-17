import os
import uuid
from typing import Optional, Dict

from app.backend.images.repository import ImageRepository
from app.backend.images.rabbitmq import RabbitMQClient
from app.backend.database.db import SessionDep


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

        # Создаем директорию uploads если её нет
        os.makedirs("uploads", exist_ok=True)

        # Сохраняем файл
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Создаем запись в БД
        image = await self.repository.create_image(file_path)

        # Отправляем задачу в RabbitMQ
        await self.send_to_queue(image.id, file_path)

        return {
            "id": str(image.id),
            "status": image.status.value
        }

    async def send_to_queue(self, image_id: uuid.UUID, file_path: str) -> None:
        """Отправить задачу в очередь RabbitMQ."""
        task_id = str(uuid.uuid4())

        try:
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
        except Exception as e:
            print(f"Ошибка при отправке в очередь: {e}")
            # В реальном приложении здесь должна быть обработка ошибок

    async def get_image_info(self, image_id: uuid.UUID) -> Optional[Dict]:
        """Получить информацию об изображении."""
        image = await self.repository.get_image_by_id(image_id)
        if not image:
            return None

        return {
            "id": str(image.id),
            "status": image.status.value,
            "original_url": image.original_url,
            "thumbnails": image.thumbnails or {}
        }

    async def check_health(self) -> dict:
        """Проверить состояние сервиса."""
        health_status = {
            "service": "ok",
            "database": "unknown",
            "rabbitmq": "unknown"
        }

        # Проверяем подключение к БД
        try:
            # Простая проверка подключения
            await self.db.execute("SELECT 1")
            health_status["database"] = "ok"
        except Exception as e:
            health_status["database"] = f"error: {str(e)}"

        # Проверяем подключение к RabbitMQ
        try:
            rabbit_client = RabbitMQClient()
            rabbit_client.connect()
            rabbit_client.disconnect()
            health_status["rabbitmq"] = "ok"
        except Exception as e:
            health_status["rabbitmq"] = f"error: {str(e)}"

        return health_status
