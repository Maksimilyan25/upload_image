from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy import update

from app.backend.images.models import Image, ImageStatus
from app.backend.database.db import SessionDep

from typing import Optional


class ImageRepository:
    def __init__(self, db: SessionDep):
        self.db = db

    async def create_image(self, original_url: str) -> Image:
        """Создать новую запись изображения в БД."""

        image = Image(original_url=original_url, status=ImageStatus.NEW)
        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)
        return image

    async def get_image_by_id(self, image_id: UUID) -> Optional[Image]:
        """Получить изображение по ID."""

        result = await self.db.execute(
            select(Image).where(Image.id == image_id)
        )
        return result.scalar_one_or_none()

    async def update_image_status(
        self,
        image_id: UUID,
        status: ImageStatus
    ) -> bool:
        """Обновить статус изображения."""
        stmt = (
            update(Image)
            .where(Image.id == image_id)
            .values(status=status)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def update_image_thumbnails(
        self,
        image_id: UUID,
        thumbnails: dict
    ) -> bool:
        """Обновить thumbnails изображения."""
        stmt = (
            update(Image)
            .where(Image.id == image_id)
            .values(thumbnails=thumbnails)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0
