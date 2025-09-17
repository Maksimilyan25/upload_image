from fastapi import APIRouter, UploadFile, File, Path, HTTPException, status

from uuid import UUID

from app.backend.database.db import SessionDep
from app.backend.images.service import ImageService
from app.backend.logging_config import logger


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
    logger.info("Получен запрос на загрузку изображения %s", file.filename)

    # Читаем содержимое файла
    file_content = await file.read()

    # Создаем сервис и обрабатываем загрузку
    service = ImageService(db)
    result = await service.upload_image(file_content, file.filename)

    logger.info("Изображение %s успешно загружено с ID %s",
                file.filename, result["id"])

    return result


@router.get(
        "/health",
        status_code=status.HTTP_200_OK,
        summary="Проверка состояния PostgreSQL и RabbitMQ"
)
async def health_check(db: SessionDep):
    """Проверить состояние сервиса."""
    logger.info("Получен запрос на проверку состояния сервиса")

    service = ImageService(db)
    result = await service.check_health()

    logger.info("Проверка состояния сервиса завершена: %s", result)
    return result


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
    logger.info("Получен запрос на получение информации об изображении %s", id)

    service = ImageService(db)
    image_info = await service.get_image_info(id)

    if not image_info:
        logger.warning("Изображение %s не найдено", id)
        raise HTTPException(status_code=404, detail="Изображение не найдено")

    logger.info("Информация об изображении %s успешно получена", id)
    return image_info
