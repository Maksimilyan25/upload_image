from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy import update

from app.backend.images.models import Image, ImageStatus
from app.backend.database.db import SessionDep
from app.backend.logging_config import logger

from typing import Optional


class ImageRepository:
    def __init__(self, db: SessionDep):
        self.db = db

    async def create_image(self, original_url: str) -> Image:
        """Создать новую запись изображения в БД."""
        logger.info("Создание записи изображения в БД: %s", original_url)

        image = Image(original_url=original_url, status=ImageStatus.NEW)
        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)

        logger.info("Изображение успешно создано в БД с ID: %s", image.id)
        return image

    async def get_image_by_id(self, image_id: UUID) -> Optional[Image]:
        """Получить изображение по ID."""
        logger.info("Запрос изображения по ID: %s", image_id)

        result = await self.db.execute(
            select(Image).where(Image.id == image_id)
        )
        image = result.scalar_one_or_none()

        if image:
            logger.info("Изображение %s найдено", image_id)
        else:
            logger.info("Изображение %s не найдено", image_id)

        return image

    async def update_image_status(
            self,
            image_id: UUID,
            status: ImageStatus
    ) -> bool:
        """Обновить статус изображения."""
        logger.info("Обновление статуса изображения %s", image_id)

        stmt = (
            update(Image)
            .where(Image.id == image_id)
            .values(status=status)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()

        success = result.rowcount > 0
        if success:
            logger.info("Статус изображения %s успешно обновлен", image_id)
        else:
            logger.warning("Не удалось обновить статус изображения", image_id)

        return success

    async def update_image_thumbnails(
            self,
            image_id: UUID,
            thumbnails: dict
    ) -> bool:
        """Обновить thumbnails изображения."""
        logger.info("Обновление thumbnails изображения %s", image_id)

        stmt = (
            update(Image)
            .where(Image.id == image_id)
            .values(thumbnails=thumbnails)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()

        success = result.rowcount > 0
        if success:
            logger.info("Thumbnails изображения %s обновлены", image_id)
        else:
            logger.warning("Не удалось обновить thumbnails", image_id)

        return success
