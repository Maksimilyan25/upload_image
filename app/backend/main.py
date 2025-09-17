import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.backend.database.db import engine, Base
from app.backend.images.router import router as images_router


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


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
    return {"message": "Сервис обработки изображений"}


# Подключаем статические файлы для отдачи изображений
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Подключаем роутеры
app.include_router(images_router)
