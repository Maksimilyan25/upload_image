Сервис для обработки изображений с использованием FastAPI, PostgreSQL и RabbitMQ.

## Функциональные возможности

1. Загрузка изображений через POST /images
2. Генерация thumbnails трех размеров (100x100, 300x300, 1200x1200)
3. Проверка состояния сервиса через GET /health
4. Получение информации об изображении через GET /images/{id}

## Технологии

- FastAPI - веб-фреймворк
- PostgreSQL - база данных
- RabbitMQ - очередь сообщений
- OpenCV - обработка изображений

## Установка и запуск

### Вариант 1: Запуск через Docker Compose (рекомендуется)

```bash
docker-compose up --build
```

Эта команда запустит все сервисы:
- api - на порту 8000
- worker - обработчик изображений
- db - PostgreSQL на порту 5432
- rabbit - RabbitMQ на портах 5672 и 15672

### Вариант 2: Ручная установка

#### Требования

- Python 3.10+
- PostgreSQL
- RabbitMQ

#### Установка зависимостей

```bash
pip install -r requirements.txt
```

#### Настройка переменных окружения

Создайте файл `.env` в директории `app/backend/`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/imagedb
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

#### Запуск миграций

```bash
alembic -c alembic.ini upgrade head
```

#### Запуск приложения

```bash
uvicorn app.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Запуск worker

```bash
python app/backend/worker/main.py
```

## Архитектура


- **Роутеры** (`router.py`) - обработка HTTP запросов
- **Сервисы** (`service.py`) - бизнес-логика приложения
- **Репозитории** (`repository.py`) - работа с базой данных
- **Модели** (`models.py`) - определение структуры данных
- **База данных** (`database/db.py`) - конфигурация подключения к БД

Для внедрения зависимостей используется `SessionDep` - аннотированный тип зависимости для сессии БД.

## API Endpoints

### POST /images

Загрузка изображения.

```bash
curl -X POST "http://localhost:8000/images/" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@image.jpg"
```

Ответ:
```json
{
  "id": "uuid",
  "status": "NEW"
}
```

### GET /images/{id}

Получение информации об изображении.

```bash
curl -X GET "http://localhost:8000/images/{id}" -H "accept: application/json"
```

Ответ:
```json
{
  "id": "uuid",
  "status": "NEW|PROCESSING|DONE|ERROR",
  "original_url": "string",
  "thumbnails": {
    "100x100": "url",
    "300x300": "url",
    "1200x1200": "url"
  }
}
```

### GET /health

Проверка состояния сервиса.

```bash
curl -X GET "http://localhost:8000/images/health" -H "accept: application/json"
```

Ответ:
```json
{
  "service": "ok",
  "database": "ok",
  "rabbitmq": "ok"
}