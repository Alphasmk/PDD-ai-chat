# User Management Service

Сервис на Python 3.12 и FastAPI для регистрации, входа и управления собственной
учётной записью и изображением.

## API

Все пользовательские маршруты имеют префикс `/api/v1`.

| Метод | Маршрут | Назначение |
|---|---|---|
| POST | /auth/signup | Регистрация |
| POST | /auth/login | Вход: форма username/password |
| POST | /auth/refresh-token | Ротация токенов |
| POST | /auth/reset-password | Публикация запроса восстановления пароля |
| GET, PATCH, DELETE | /users/me | Собственный профиль |
| POST, GET, DELETE | /users/me/image | Собственное изображение |

Профиль и изображение требуют действующий bearer access-токен существующего
пользователя. Refresh использует HttpOnly cookie `refresh_token` и наличие bearer
заголовка; срок access-токена при этой операции не проверяется. Старый refresh
отзывается через Redis, новый получает уникальный `jti`.

PATCH принимает name, surname, username, email и phone_number. Неизвестные JSON-поля
игнорируются. Идентификатор и ключ изображения не принимаются для изменения.
Форматы изображения: JPEG, PNG, WebP; максимум 5 MiB. Удаление изображения возвращает
`200 null`. Запрос восстановления пароля публикует существующее сообщение RabbitMQ;
дальнейшие этапы восстановления в этом сервисе не реализованы.

OpenAPI: `/docs`; техническая проверка: `/healthcheck`.

## Новая установка

Требуется новая пустая PostgreSQL-база. Единственная базовая миграция создаёт таблицу
users и служебную alembic_version. До регистрации пользователей нет. Обновление
старой базы, перенос данных и stamping старой схемы не поддерживаются.

1. Установите Python 3.12 и uv; выполните `uv sync --frozen`.
2. Скопируйте `.env.example` в `.env` и задайте PostgreSQL, Redis, RabbitMQ,
   JWT и S3-настройки.
3. Выполните `uv run alembic upgrade head` и
   `uv run uvicorn source.main:app --host 0.0.0.0 --port 8000`.

В контейнере `scripts/entry.sh` выполняет базовую миграцию и запускает приложение.
Для основного `docker-compose.yaml` требуется внешняя сеть `shared_net`.
Первый аккаунт создаётся обычной регистрацией.

## Проверки

```powershell
uv run ruff check source tests scripts
uv run ruff format --check source tests scripts
uv run mypy source tests scripts
uv run pytest tests/unit
```

Модульные тесты не требуют сервисов. Для интеграционных проверок:

```powershell
Copy-Item .env.test.example .env.test
docker compose --env-file .env.test -p ums-users-only -f docker-compose.test.yaml up -d --wait
$env:UMS_TEST_POSTGRES_URL = "postgresql+asyncpg://postgres:disposable@localhost:5434/ums_test"
$env:UMS_TEST_REDIS_URL = "redis://:disposable@localhost:6380/0"
$env:UMS_TEST_BROKER_URL = "amqp://test:disposable@localhost:5673/"
uv run pytest tests/integration
docker compose --env-file .env.test -p ums-users-only -f docker-compose.test.yaml --profile startup up -d --build --wait
```

Профиль startup запускает приложение через entry.sh на порту 8001 с тестовыми
настройками. После проверки `/healthcheck` завершите одноразовый проект:

```powershell
docker compose --env-file .env.test -p ums-users-only -f docker-compose.test.yaml --profile startup down -v
```

Compose использует временные данные, без фиксированных имён контейнеров.
Каждый PostgreSQL-тест применяет миграцию в отдельной случайной схеме и удаляет
только эту схему. Используйте отдельный тестовый экземпляр RabbitMQ: проверка
публикации использует и удаляет очереди восстановления пароля.
Без переменных UMS_TEST_* HTTP-тесты используют временную SQLite-базу и
изолированные адаптеры; две проверки Redis/RabbitMQ пропускаются.

Подробные сценарии: [quickstart](specs/001-remove-groups-roles/quickstart.md).
Результаты реализации: [validation](specs/001-remove-groups-roles/validation.md).
