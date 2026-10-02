# Quickstart: проверка после реализации

Команды и маршруты реализованы. Контракты: [admin-api.md](contracts/admin-api.md); модель: [data-model.md](data-model.md).

## Подготовка

Нужны Python 3.12, uv, Docker Compose и отдельная тестовая БД. Запускать из корня репозитория. Не использовать рабочий PostgreSQL и не удалять его volume. Временный Compose использует tmpfs.

```powershell
uv sync --frozen
if (-not (Test-Path .env.test)) { Copy-Item .env.test.example .env.test }
```

Копирование выполнять только при отсутствии локального .env.test. В тестовом файле задать существующие PostgreSQL/Redis/RabbitMQ параметры и SUPERADMIN_USERNAME, SUPERADMIN_EMAIL, SUPERADMIN_NAME, SUPERADMIN_SURNAME, SUPERADMIN_PASSWORD с отдельным тестовым паролем, удовлетворяющим существующим правилам. app_test передаёт эти переменные runner без стандартного production-пароля. Для локального старта аналогично заполнить .env.

```powershell
docker compose --env-file .env.test -p ums-admin-test -f docker-compose.test.yaml --profile startup up -d --build --wait
$env:UMS_TEST_POSTGRES_URL = "postgresql+asyncpg://postgres:disposable@localhost:5434/ums_test"
$env:UMS_TEST_REDIS_URL = "redis://:disposable@localhost:6380/0"
$env:UMS_TEST_BROKER_URL = "amqp://test:disposable@localhost:5673/"
$env:UMS_REQUIRE_POSTGRES = "1"
$env:UMS_TEST_APP_URL = "http://localhost:8001"
$env:UMS_TEST_DOCKER = (Get-Command docker).Source
$env:UMS_TEST_COMPOSE_PROJECT = "ums-admin-test"
$env:UMS_TEST_COMPOSE_ENV_FILE = ".env.test"
# Значения должны совпадать с отдельными тестовыми SUPERADMIN_* из .env.test.
$env:UMS_TEST_SUPERADMIN_USERNAME = "<test username>"
$env:UMS_TEST_SUPERADMIN_PASSWORD = "<test password>"
uv run pytest tests/unit tests/integration
uv run ruff check source tests scripts
uv run ruff format --check source tests scripts
uv run mypy source tests scripts
```

Ожидается успешная инициализация, один superadmin и доступный http://localhost:8001/healthcheck. Интеграционные тесты работают в отдельных случайных схемах. PostgreSQL тесты конкурентности нельзя считать пройденными, если они пропущены из-за отсутствия подключения.

## Проверка HTTP вручную

Войти через POST /api/v1/auth/login (форма username/password), использовать возвращённый access_token как Bearer. Для refresh хранить выданную HttpOnly cookie; прежнее требование bearer заголовка сохраняется. Не печатать пароль и токены в отчёте.

1. Под superadmin получить GET /api/v1/roles: ровно user/admin. GET /api/v1/users показывает у суперадмина role=admin и is_superadmin=true.
2. Создать через signup двух user, войти обоими и сохранить их сеансы. PATCH /api/v1/users/{id}/role с role=admin повышает первого. Его прежний access теперь позволяет список и блокировку, но не смену роли.
3. Под superadmin вернуть первому role=user: тот же access теперь получает 403 на список, собственный профиль остаётся доступным. Повторное снятие успешно и не меняет профиль.
4. Назначить admin снова; от него заблокировать второго POST /api/v1/users/{id}/block. Проверить login, refresh и GET/PATCH/DELETE /users/me второго — 403; повторная блокировка — 200. Запрос восстановления пароля не снимает блокировку.
5. Попытаться назначить role=superadmin — 422; поменять существующему суперадмину роль на user/admin — 409; заблокировать или удалить его аккаунт — 409. Повторить от обычных участников: отказ по правам без раскрытия цели.
6. Signup и PATCH /users/me с дополнительными role/is_blocked не меняют полномочия. Общие выходные схемы профиля отражают реальную роль.

## Обязательные автоматизированные сценарии

| Область | Проверка | Ожидаемый результат |
|---------|----------|---------------------|
| Startup | Новая пустая схема, три рестарта | Один и тот же superadmin; пароль/профиль неизменны |
| Startup concurrency | Два независимых startup runner одновременно на одной новой тестовой схеме | Миграции не конфликтуют, одна итоговая схема и один superadmin |
| Startup failure | Отсутствующие/невалидные параметры, занятые username/email, недоступная БД, timeout lock | Ненулевой exit, приложение не запускается, секретов в диагностике нет |
| Existing bootstrap | Сменить начальные настройки, убрать их, изменить профиль суперадмина | Идентичность/пароль не сбрасываются, новый аккаунт не создаётся |
| Recovery | Прервать startup до commit создания, запустить снова | Rollback и успешное единственное создание при повторе |
| DB constraints | Вставить второго защищённого admin, третью роль, заблокированного admin и user с is_superadmin=true | Ограничения отвергают каждый недопустимый набор |
| Commit failure | Принудительная ошибка commit при block/role/delete | Нет 2xx и нет частичного изменения |
| Races | Две PostgreSQL сессии: promotion/block, delete/block, profile-update/role-change | Один допустимый итог; повторная проверка после ожидания; профиль не затирает роль |
| Stale ORM | Загрузить аккаунт, изменить его другой сессией, перечитать для изменения | Проверяется обновлённое состояние, не identity map |
| Pagination | 125 аккаунтов всех ролей, limit 50 и 100, все offsets, пустая последняя страница | 125 уникальных id, стабильный порядок, никаких секретов |
| Access | Все ячейки матрицы, missing/expired token, wrong role, blocked actor, absent target | Успех и ошибки по контракту; target не раскрывается до проверки прав |
| Session changes | Несколько access/refresh до block; старый access до promotion/demotion | Следующее обращение отражает актуальное состояние |
| Regression | Регистрация, собственный профиль, refresh rotation, сообщение восстановления | Сохранено прежнее поведение кроме явных новых ограничений |

Startup parallel тесты должны использовать отдельные процессы и схему/БД, а не только два вызова use case. Для проверки HTTP отсутствия готовности запускать entrypoint, а не только bootstrap. Не запускать runner на общей БД разработчика.

## Завершение и отчёт

Записать результаты команд, количество pass/fail/skip и причины пропусков в validation.md при реализации. На стадии планирования проверки приложения не запускались.

После проверки удалить только одноразовый проект ums-admin-test:

```powershell
docker compose --env-file .env.test -p ums-admin-test -f docker-compose.test.yaml --profile startup down
```

Основной Compose-проект и его данные эта команда не затрагивает.
