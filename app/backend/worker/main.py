import os
import sys
import cv2
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.backend.database.db import async_session
from app.backend.images.models import ImageStatus
from app.backend.images.repository import ImageRepository
from app.backend.images.rabbitmq import RabbitMQClient

# Создаем пул потоков для выполнения блокирующих операций
executor = ThreadPoolExecutor(max_workers=4)


async def process_image(message):
    """Обработать изображение и создать thumbnails."""
    task_id = message.get("task_id")
    image_id = message.get("image_id")
    file_path = message.get("file_path")

    print(f"Начинаем обработку задачи {task_id} для изображения {image_id}")

    # Открываем сессию БД
    async with async_session() as session:
        repository = ImageRepository(session)

        try:
            # Проверяем существование файла
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл {file_path} не существует")

            # Обновляем статус на PROCESSING
            await repository.update_image_status(
                uuid.UUID(image_id),
                ImageStatus.PROCESSING
            )

            # Загружаем изображение асинхронно
            loop = asyncio.get_event_loop()
            img = await loop.run_in_executor(executor, cv2.imread, file_path)
            if img is None:
                raise ValueError("Не удалось загрузить изображение. "
                                 "Файл может быть поврежден или иметь "
                                 "неподдерживаемый формат.")

            # Создаем thumbnails
            thumbnails = {}
            sizes = [(100, 100), (300, 300), (1200, 1200)]

            for width, height in sizes:
                # Изменяем размер изображения асинхронно
                resized = await loop.run_in_executor(
                    executor,
                    lambda img=img, w=width, h=height: cv2.resize(img, (w, h))
                )

                # Сохраняем thumbnail асинхронно
                # Упрощаем имя файла для thumbnail
                original_basename = os.path.basename(file_path)
                # Убираем UUID из начала имени файла если он есть
                if '_' in original_basename:
                    # Формат имени: UUID_original_filename
                    parts = original_basename.split('_', 1)
                    # Проверяем, что первая часть - это UUID
                    if len(parts) == 2 and len(parts[0]) == 36:
                        simplified_name = parts[1]
                    else:
                        simplified_name = original_basename
                else:
                    simplified_name = original_basename

                thumb_filename = (
                    f"uploads/thumb_{width}x{height}_{simplified_name}"
                )

                # Проверяем успешность сохранения
                success = await loop.run_in_executor(
                    executor,
                    lambda: cv2.imwrite(thumb_filename, resized)
                )

                if not success:
                    raise IOError(
                        f"Не удалось сохранить thumbnail {thumb_filename}. "
                        f"Проверьте права доступа к директории и "
                        f"доступное место на диске."
                    )

                thumbnails[f"{width}x{height}"] = thumb_filename

            # Обновляем запись в БД с thumbnails и статусом DONE
            await repository.update_image_thumbnails(
                uuid.UUID(image_id),
                thumbnails
            )
            await repository.update_image_status(
                uuid.UUID(image_id),
                ImageStatus.DONE
            )

            print(f"Задача {task_id} успешно завершена")

        except FileNotFoundError as e:
            print(f"Ошибка при обработке задачи {task_id}: {e}")
            # Обновляем статус на ERROR
            await repository.update_image_status(
                uuid.UUID(image_id),
                ImageStatus.ERROR
            )

        except ValueError as e:
            print(f"Ошибка при обработке задачи {task_id}: {e}")
            # Обновляем статус на ERROR
            await repository.update_image_status(
                uuid.UUID(image_id),
                ImageStatus.ERROR
            )

        except IOError as e:
            print(f"Ошибка при обработке задачи {task_id}: {e}")
            # Обновляем статус на ERROR
            await repository.update_image_status(
                uuid.UUID(image_id),
                ImageStatus.ERROR
            )

        except Exception as e:
            print(f"Неожиданная ошибка при обработке задачи {task_id}: {e}")
            # Обновляем статус на ERROR
            await repository.update_image_status(
                uuid.UUID(image_id),
                ImageStatus.ERROR
            )


def message_handler(message):
    """Обработчик сообщений из очереди."""
    import asyncio
    import nest_asyncio

    # Разрешаем вложенные циклы событий
    nest_asyncio.apply()

    # Запускаем асинхронную функцию
    loop = asyncio.get_event_loop()
    loop.run_until_complete(process_image(message))


def cleanup():
    """Очистка ресурсов при завершении работы."""
    executor.shutdown(wait=True)


if __name__ == "__main__":
    print("Запуск worker для обработки изображений...")

    # Проверяем наличие переменных окружения
    if not os.getenv("DATABASE_URL"):
        print("Ошибка: Не установлена переменная окружения DATABASE_URL")
        sys.exit(1)
    if not os.getenv("RABBITMQ_URL"):
        print("Ошибка: Не установлена переменная окружения RABBITMQ_URL")
        sys.exit(1)

    # Создаем клиента RabbitMQ
    rabbit_client = RabbitMQClient()

    try:
        # Начинаем потребление сообщений
        rabbit_client.consume_messages(message_handler)
    except KeyboardInterrupt:
        print("Остановка worker")
        rabbit_client.disconnect()
        cleanup()
    except Exception as e:
        print(f"Ошибка worker: {e}")
        rabbit_client.disconnect()
        cleanup()
        sys.exit(1)
