# User Management Service

Сервис на Python 3.12 и FastAPI для регистрации, входа, собственного профиля
и ограниченного администрирования аккаунтов. В отдельной таблице `roles` ровно две
роли: Пользователь (`user`) и Администратор (`admin`). Пользователь связан с ролью
через `role_id`. Суперадмин — защищённый администратор с `is_superadmin=true`.

## API

Все пользовательские маршруты имеют префикс `/api/v1`.

| Метод | Маршрут | Назначение |
|---|---|---|
| POST | /auth/signup | Регистрация |
| POST | /auth/login | Вход: форма username/password |
| POST | /auth/refresh-token | Ротация токенов |
| POST | /auth/reset-password | Публикация запроса восстановления пароля |
| GET, PATCH, DELETE | /users/me | Собственный профиль |
| GET | /roles | Две роли из таблицы roles и их подписи; любой вошедший незаблокированный аккаунт |
| GET | /users?limit=50&offset=0 | Постраничный список; admin/superadmin |
| PATCH | /users/{user_id}/role | Тело {"role":"user"} или {"role":"admin"}; только superadmin |
| POST | /users/{user_id}/block | Блокировка обычного пользователя без тела; admin/superadmin |

Профиль требует действующий bearer access-токен существующего
пользователя. Refresh использует HttpOnly cookie `refresh_token` и наличие bearer
заголовка; срок access-токена при этой операции не проверяется. Старый refresh
отзывается через Redis, новый получает уникальный `jti`.

PATCH принимает name, surname, username, email и phone_number. Неизвестные JSON-поля
игнорируются, включая role/is_blocked/is_superadmin. Идентификатор не принимается для изменения.
Ответы регистрации, просмотра и изменения профиля содержат актуальные role/is_blocked/is_superadmin.
Запрос восстановления пароля публикует существующее сообщение RabbitMQ;
дальнейшие этапы восстановления в этом сервисе не реализованы.

OpenAPI: `/docs`; техническая проверка: `/healthcheck`.

Администратор сохраняет права на свой профиль и может удалить себя. Суперадминистратор
дополнительно назначает/снимает обычных администраторов. Его нельзя назначить через API,
снять с роли, заблокировать или удалить, включая удаление собственного аккаунта.
Блокировать admin нельзя: сначала superadmin должен снять роль. Разблокировки нет.
Повторная допустимая смена роли или блокировка успешна без изменения updated_at.

Права читаются из БД на каждом защищённом обращении. После подтверждённой смены роли
прежние сеансы используют новые права; после блокировки запрещены login, refresh
и защищённые действия всех сеансов. Уже начатые запросы могут завершиться.
Неверный пароль даёт прежний 401, верный пароль заблокированного — 403 user_blocked.
Восстановление пароля остаётся публичным и не меняет блокировку.

Список включает все роли/состояния, содержит только id/name/surname/username/email/role/is_blocked/is_superadmin.
Порядок created_at ASC, id ASC; limit 1..100 (default 50), offset >=0 (default 0).
Пустая страница успешна; total и snapshot при изменениях между страницами не обещаются.

Новые ошибки имеют формат {"error":"..."}: 403 forbidden/user_blocked;
404 user_not_found (цель проверяется после полномочий); 409 protected_account/invalid_target_state;
422 invalid_role/invalid_request; 503 service_unavailable. Ошибки прежних маршрутов сохраняются.
Входная схема смены роли допускает только user/admin и запрещает дополнительные поля.

## Новая установка

Для новой установки нужна пустая PostgreSQL-база. Цепочка миграций
`users_roles_20260927` → `role_catalog_20260927` создаёт `users` (12 столбцов),
`roles` (две записи) и служебную `alembic_version`. Startup создаёт единственного
защищённого администратора до готовности HTTP.

Если база уже находится на `users_roles_20260927`, запуск runner применит новую
миграцию без удаления аккаунтов: прежний `superadmin` станет `admin` с
`is_superadmin=true`. UUID, профили, хеши паролей и блокировка сохраняются.
Пересоздавать volume для этого обновления не требуется. Переход с более старых
схем этой цепочкой не поддерживается. Ограничения запрещают третью роль,
блокировку администратора, защищённый статус пользователя и второго суперадмина.

1. Установите Python 3.12 и uv; выполните `uv sync --frozen`.
2. Скопируйте `.env.example` в `.env` и задайте PostgreSQL, Redis, RabbitMQ,
   JWT-настройки. Для первого создания обязательны SUPERADMIN_USERNAME,
   SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD, SUPERADMIN_NAME, SUPERADMIN_SURNAME.
   Общедоступного пароля нет; пароль проходит прежние правила (8–20 допустимых символов).
3. Выполните `uv run python -m scripts.initialize_service` и
   `uv run uvicorn source.main:app --host 0.0.0.0 --port 8000`.

В контейнере `scripts/entry.sh` запускает runner и только после успеха — приложение.
Session advisory lock 74004001 охватывает миграции и bootstrap в общей БД;
ожидание ограничено 60 секундами. Параллельные запуски не создают дубликатов.
Повторный запуск ищет superadmin по is_superadmin=true, сохраняет профиль и пароль даже после
переименования; начальные настройки могут отсутствовать или измениться.
Оператор получает уведомление `superadmin_exists: initial settings are not applied`.
Начальные настройки не являются механизмом смены пароля.

Неуспешная инициализация возвращает ненулевой exit и не запускает HTTP.
Диагностика без входных значений: missing_initial_data — обязательные данные отсутствуют;
invalid_initial_data — профиль/пароль некорректны; identity_conflict — username/email
занят обычным аккаунтом (автоповышения нет); database_unavailable — БД/схема недоступна;
initialization_timeout — превышено ожидание lock. После устранения причины повторите запуск.
Основной `docker-compose.yaml` использует сеть своего Compose-проекта; внешняя сеть закомментирована.
Все последующие обычные регистрации создают только user/is_blocked=false/is_superadmin=false.

## Проверки

```powershell
uv run ruff check source tests scripts
uv run ruff format --check source tests scripts
uv run mypy source tests scripts
uv run pytest tests/unit
```

Модульные тесты не требуют сервисов. Для интеграционных проверок:

```powershell
if (-not (Test-Path .env.test)) { Copy-Item .env.test.example .env.test }
# Заполните отдельные тестовые SUPERADMIN_* перед запуском startup.
docker compose --env-file .env.test -p ums-admin-test -f docker-compose.test.yaml up -d --wait
$env:UMS_TEST_POSTGRES_URL = "postgresql+asyncpg://postgres:disposable@localhost:5434/ums_test"
$env:UMS_TEST_REDIS_URL = "redis://:disposable@localhost:6380/0"
$env:UMS_TEST_BROKER_URL = "amqp://test:disposable@localhost:5673/"
$env:UMS_REQUIRE_POSTGRES = "1"
uv run pytest tests/integration
docker compose --env-file .env.test -p ums-admin-test -f docker-compose.test.yaml --profile startup up -d --build --wait
$env:UMS_TEST_APP_URL = "http://localhost:8001"
uv run pytest tests/integration/settings/startup_test.py
```

Профиль startup запускает приложение через entry.sh на порту 8001 с тестовыми
настройками. После проверки `/healthcheck` завершите одноразовый проект:

```powershell
docker compose --env-file .env.test -p ums-admin-test -f docker-compose.test.yaml --profile startup down
```

Compose использует временные данные, без фиксированных имён контейнеров.
Каждый PostgreSQL-тест применяет миграцию в отдельной случайной схеме и удаляет
только эту схему. Используйте отдельный тестовый экземпляр RabbitMQ: проверка
публикации использует и удаляет очереди восстановления пароля.
Без переменных UMS_TEST_* HTTP-тесты используют временную SQLite-базу и
изолированные адаптеры; PostgreSQL гонки, startup и реальные Redis/RabbitMQ пропускаются.
UMS_REQUIRE_POSTGRES=1 запрещает незаметную замену PostgreSQL на SQLite.
UMS_TEST_ENV_FILE позволяет явно выбрать отдельный env-файл disposable Compose.

Подробные сценарии: [quickstart](specs/004-admin-user-blocking/quickstart.md).
Результаты реализации: [validation](specs/004-admin-user-blocking/validation.md).
