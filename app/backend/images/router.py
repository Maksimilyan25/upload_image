from fastapi import APIRouter, UploadFile, File, Path, HTTPException, status

from uuid import UUID

from app.backend.database.db import SessionDep
from app.backend.images.service import ImageService


router = APIRouter(prefix="/images", tags=["images"])


@router.post(
        "/", status_code=status.HTTP_200_OK,
        summary="Загрузка изображений"
)
async def upload_image(
    db: SessionDep,
    file: UploadFile = File(...)
):
    """Загрузить изображение."""

    # Читаем содержимое файла
    file_content = await file.read()

    # Создаем сервис и обрабатываем загрузку
    service = ImageService(db)
    result = await service.upload_image(file_content, file.filename)

    return result


@router.get(
        "/health",
        status_code=status.HTTP_200_OK,
        summary="Проверка состояния PostgreSQL и RabbitMQ"
)
async def health_check(db: SessionDep):
    """Проверить состояние сервиса."""

    service = ImageService(db)
    return await service.check_health()


@router.get(
        "/{id}",
        status_code=status.HTTP_200_OK,
        summary="Получение инфомарции об изображении по ID"
)
async def get_image_info(
    db: SessionDep,
    id: UUID = Path(...)
):
    """Получить информацию об изображении."""

    service = ImageService(db)
    image_info = await service.get_image_info(id)

    if not image_info:
        raise HTTPException(status_code=404, detail="Изображение не найдено")

    return image_info
