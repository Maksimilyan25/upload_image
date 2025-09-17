import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.backend.database.db import engine, Base
from app.backend.images.router import router as images_router
from app.backend.logging_config import logger


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения. Создание таблиц в базе данных.")
    await create_tables()
    logger.info("Таблицы успешно созданы. Приложение готово к работе.")
    yield
    logger.info("Завершение работы приложения.")


# Инициализация приложения
app = FastAPI(
    title="Сервис по загрузке изображений",
    description=(
        "API для загрузки и обработки изображений с возможностью "
        "создания миниатюр различных размеров"
    ),
    version="1.0.0",
    lifespan=lifespan,
)


@app.get(
    "/",
    summary="Корневой endpoint",
    description="Возвращает приветственное сообщение сервиса"
)
async def root():
    logger.info("Получен запрос к корневому endpoint'у")
    return {"message": "Сервис обработки изображений"}


# Подключаем статические файлы для отдачи изображений
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Подключаем роутеры
app.include_router(images_router)
