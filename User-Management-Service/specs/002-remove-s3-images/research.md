# Research: удаление изображений и AWS S3

**Date**: 2026-09-27
**Scope**: [spec.md](spec.md), FR-001–FR-010.

Исследование основано на текущих файлах репозитория, без изменения кода и запуска инфраструктуры. Новая технология или интеграция не вводится. Неопределённостей `NEEDS CLARIFICATION` не осталось.

## 1. Граница функции и конституция

**Decision**: Полностью удалить изображения пользователя без замены хранилища. Конституция приведена к версии 4.0.0 на основании уточнений пользователя от 2026-09-27; изображения и их хранение исключены из обязанностей сервиса.

**Rationale**: Пользователь выбрал «Полностью убрать изображения пользователя». Отмена обязательства обслуживать изображения — несовместимое изменение границы, поэтому используется MAJOR. Правила Python, FastAPI, строгой типизации и DDD сохраняются.

**Alternatives considered**: Замена S3 локальными файлами или другим сервисом противоречит выбранному объёму; пустые реализации операций сохраняли бы ложный контракт.

**Evidence**: `spec.md`, `.specify/memory/constitution.md`, `source/presentation/api/routes/user_router.py`.

## 2. Удаление сквозной вертикали изображений

**Decision**: Удалить три маршрута `/api/v1/users/me/image`, три прикладных сценария, `IStorage`, инфраструктурный каталог storage, сборку зависимостей, схемы ответов изображения, ошибки и ограничения файлов. Удалить `image_s3_path` из сущности, DTO, преобразований, ORM и ответов регистрации/профиля.

**Rationale**: S3 встроен во все слои; удаление только адаптера оставит сломанные импорты, обязательные настройки или неработающие контракты. Общие операции пользователя и обработки ошибок остаются.

**Alternatives considered**: Депрекация с ответом 410, заглушки 200/null и сохранение nullable поля отвергнуты: требуются отсутствующие операции и отсутствующие поля. Удаление регистрации или механизмов токенов не связано с функцией.

**Evidence**: `source/application/use_cases/user_use_cases.py`, `source/application/use_cases/base.py`, `source/application/interfaces/storage.py`, `source/infrastructure/storage/`, `source/infrastructure/database/user_repository.py`, `source/presentation/api/dependencies/`, `source/presentation/exceptions.py`, `source/settings/constansts.py`.

## 3. Зависимости и настройки

**Decision**: Удалить прямые зависимости `aioboto3==15.5.0` и `types-aioboto3[s3]==15.5.0`, затем пересчитать `uv.lock` штатным `uv lock`. Сохранить `python-multipart==0.0.22`, потому что вход использует `OAuth2PasswordRequestForm`. Удалить `StorageConfig`, `Config.storage`, AWS-переменные из `.env.example` и окружения `app_test`. Не публиковать содержимое локального `.env`; устаревшие AWS-поля могут игнорироваться общим `extra="ignore"`.

**Rationale**: Удаляются исключительно ненужные зависимости. Общие транзитивные пакеты, в том числе используемые `aio-pika`, нельзя удалять вручную по сходству с прежним деревом S3. Пустые AWS-значения не должны мешать созданию `Config`.

**Alternatives considered**: Удаление `python-multipart` сломает вход; ручная зачистка lock-файла может удалить общие пакеты. Фиктивные AWS credentials сохраняют ошибочную обязательность интеграции.

**Evidence**: `pyproject.toml`, `uv.lock`, `source/presentation/api/routes/auth_router.py`, `source/settings/config.py`, `source/settings/separated_configs/base.py`, `storage_config.py`, `docker-compose.test.yaml`.

## 4. Новая установка и миграция

**Decision**: Заменить единственную базовую миграцию новой `2026_09_27_users_without_images_baseline.py`, revision `users_no_images_20260927`, `down_revision=None`. Она создаёт только `users` без изображения; служебную `alembic_version` ведёт Alembic. Удалить прежний baseline из активного каталога. Не добавлять миграцию наполненной базы или stamping.

**Rationale**: Пользователь разрешил пересоздание volume с нуля. Новый revision отличает неподдерживаемую старую установку от новой; существующая база со старым revision не должна считаться обновлённой. Сохраняются ограничения уникальности и UTC-преобразования оставшихся полей.

**Alternatives considered**: Изменение старого baseline с прежним revision оставляет риск ложного успешного upgrade на старой базе. Добавление drop-column upgrade создаёт незаказанный путь переноса. Удаление всей инфраструктуры или всех volumes не требуется.

**Evidence**: `source/infrastructure/database/alembic/versions/2026_09_26_users_baseline.py`, `source/infrastructure/database/models/users.py`, `tests/integration/settings/fresh_schema_test.py`, `scripts/entry.sh`, уточнение пользователя о volume.

## 5. Контракт лишних полей и ошибок

**Decision**: Сохранить `extra="ignore"` для входных JSON-схем. Прежнее `image_s3_path`, как и другие неизвестные поля, игнорируется, но никогда не сохраняется и не возвращается. Удалённые маршруты получают стандартный 404 отсутствующего маршрута; проверки выполняются с bearer и без него. Общий формат доменных и прикладных ошибок `{ "error": ... }` сохраняется; стандартные HTTP/validation ошибки не переопределяются этой функцией.

**Rationale**: Сокращение возможностей не должно менять оставшуюся валидацию или аутентификацию. Для отсутствующего маршрута не запускаются зависимости изображений и проверки файлов.

**Alternatives considered**: `extra="forbid"` меняет прежнее поведение регистрации/редактирования; специальный обработчик удалённого маршрута сохраняет сам маршрут.

**Evidence**: `source/presentation/api/schemas/base.py`, `source/main.py`, `source/presentation/exceptions.py`, `tests/integration/auth_tests/signup_user_test.py`, `tests/integration/user_tests/edit_current_user_test.py`.

## 6. Проверка завершённости

**Decision**: Удалить позитивные image-only тесты и FakeStorage. Добавить негативные проверки отсутствия маршрутов и схем, обновить точный состав полей ответов и схемы БД. Проверить конфигурацию без AWS, PostgreSQL/Redis/RabbitMQ и реальный контейнерный entrypoint без overrides storage. Сохранить тесты подтверждённой личности, токенов, форм входа, уникальности и удалённых ранее возможностей.

**Rationale**: HTTP-тесты с ASGITransport и подменами не подтверждают production lifespan или отсутствие обязательного StorageConfig. Чистая PostgreSQL-схема и production контейнер проверяют разные границы. Повторная регистрация после удаления не доказывает сохранение данных при перезапуске — нужен отдельный сценарий сохранённого аккаунта.

**Alternatives considered**: Только unit-тесты, только SQLite, поиск слова image без анализа контекста или прежний успех 122 тестов не доказывают новую функцию. Упоминания удаления в негативных тестах и исторических документах допустимы; Docker `image:` не относится к изображениям пользователя.

**Evidence**: `tests/integration/conftest.py`, `tests/integration/settings/startup_test.py`, `real_services_test.py`, `fresh_schema_test.py`, `docker-compose.test.yaml`.
