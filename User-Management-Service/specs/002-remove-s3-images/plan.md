# Implementation Plan: Полное удаление изображений пользователя и AWS S3

**Branch**: `fix/um` (текущая Git-ветка; новая не создавалась) | **Date**: 2026-09-27 | **Spec**: [spec.md](spec.md)

**Feature Directory**: `specs/002-remove-s3-images`. Значение `BRANCH=002-remove-s3-images` из setup-plan — идентификатор фичи, а не фактическая Git-ветка.

**Input**: Спецификация `specs/002-remove-s3-images/spec.md` и уточнения: изображения удаляются целиком; допустима новая пустая база после пересоздания volume.

## Summary

Удалить вертикаль изображений из всех слоёв: операции, поля пользователя, порты и адаптер S3, настройки, ошибки, файловые ограничения и ненужные зависимости. Сохранить семь операций регистрации, аутентификации и собственного профиля, включая форму входа и `python-multipart`. Заменить прежнюю базовую миграцию единственным baseline без изображений с новым revision. Перенос наполненной базы и очистка объектов AWS не выполняются.

Конституция обновлена до 4.0.0 согласно принятому пользователем сокращению области. Дизайн сохраняет Python/FastAPI, строгую типизацию и направление зависимостей DDD. Детали решений: [research.md](research.md).

## Technical Context

**Language/Version**: Python >=3.12,<3.13.

**Primary Dependencies**: FastAPI 0.135.1, Pydantic 2.12.5 / pydantic-settings 2.13.1, SQLAlchemy 2.0.48, Alembic 1.18.4, asyncpg 0.31.0, Redis 7.4.0, aio-pika 9.6.2, PyJWT 2.12.1, passlib 1.7.4, python-multipart 0.0.22. Удаляются aioboto3 15.5.0 и types-aioboto3[s3] 15.5.0; uv пересчитывает транзитивный граф.

**Storage**: PostgreSQL 16 — пользователи; Redis — отзыв refresh-токенов. RabbitMQ сохраняется для запроса восстановления пароля. Объектного и файлового хранилища изображений нет.

**Testing**: pytest / pytest-asyncio, httpx, SQLite для изолированных HTTP-тестов, отдельные PostgreSQL/Redis/RabbitMQ через Compose, production startup-профиль. Ruff и mypy strict проверяют source, tests и scripts.

**Target Platform**: Linux-контейнер с Python 3.12; рабочее окружение Windows PowerShell и Docker Desktop.

**Project Type**: Один HTTP-сервис с DDD-слоями.

**Performance Goals**: Новые численные SLO не вводятся. Целевой результат — семь оставшихся сценариев работают без интеграции изображений; функциональность не заменяется дополнительной сетевой операцией.

**Constraints**: Новая пустая база; старый revision не поддерживается; запрещены stamping и скрытый перенос старых данных. Нет новых зависимостей, хранилища, фоновых задач или операций AWS. Сохраняются проверки личности и действующие форматы входа/ошибок/токенов.

**Scale/Scope**: 7 пользовательских HTTP-операций + healthcheck; удаляются 3 текущие операции изображения и 1 поле во всех слоях. Существующие unit/integration тесты адаптируются; исходный объём аккаунтов не влияет на путь новой установки.

## Constitution Check

*GATE: Проверен до Phase 0 и повторно после Phase 1.*

Первоначальное расхождение с версией 3.0.0 разрешено поправкой до исследования: сопровождающий выбрал полное удаление изображений. Конституция 4.0.0 фиксирует причину, последствия и переход на пустую базу. Это изменение обязательной границы, а не исключение из правил типизации или DDD.

| Gate | До исследования | После проектирования | Подтверждение |
|---|---|---|---|
| Только регистрация, аутентификация и собственный профиль без изображений | PASS | PASS | 7 операций; никаких замен S3 и чужих профилей |
| Python 3.12 и FastAPI | PASS | PASS | Стек и формат входа сохраняются |
| Строгая типизация всех слоёв и тестов | PASS | PASS | Нет Any/новых suppressions; mypy strict включён; предусмотрена проверка |
| Границы DDD и направленность зависимостей | PASS | PASS | Удаление IStorage и адаптера; домен не получает инфраструктурную замену |
| Проверяемые правила и контракты | PASS | PASS | Отрицательные HTTP-проверки, точная схема БД, запуск без AWS и регрессия |
| Новая пустая users-only база | PASS | PASS | Новый единственный baseline, без обновления существующей базы |
| Согласованные зависимости и lock | PASS | PASS | uv lock + frozen установка; python-multipart остаётся |

PASS относится к согласованности дизайна. Выполнение команд и успешность проверок реализации должны быть подтверждены отдельно; прошлый результат тестов не переносится на эту функцию.

## Project Structure

### Documentation (this feature)

```text
specs/002-remove-s3-images/
├── spec.md
├── checklists/requirements.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/http-api.md
```

`tasks.md` содержит 38 выполненных задач; результаты реализации и проверок — в [validation.md](validation.md).

### Source Code (repository root)

```text
source/
├── domain/entities/user.py
├── application/
│   ├── dto/users_dto.py
│   ├── interfaces/                 # убрать storage.py и экспорт IStorage
│   ├── exceptions/                 # убрать ошибки изображения и экспорты
│   └── use_cases/                  # убрать три сценария, поля и экспорты
├── infrastructure/
│   ├── storage/                    # удалить целиком
│   └── database/
│       ├── models/users.py
│       ├── user_repository.py
│       └── alembic/versions/        # новый единственный baseline
├── presentation/
│   ├── api/routes/user_router.py
│   ├── api/schemas/{auth,user}.py
│   ├── api/dependencies/           # убрать factories, get_storage и экспорты
│   └── exceptions.py
└── settings/
    ├── config.py
    ├── constansts.py               # файловые лимиты убрать; broker-константы оставить
    └── separated_configs/         # убрать StorageConfig и экспорт

tests/
├── adapters/storage.py            # удалить
├── unit/user_usecases_tests/      # удалить 3 image-only теста, обновить fixtures/assertions
├── unit/utils/shared_data.py
└── integration/
    ├── conftest.py                # убрать FakeStorage и dependency override
    ├── auth_tests/signup_user_test.py
    ├── user_tests/                # own_image удалить; отрицательные проверки оставить
    └── settings/                 # schema, startup, отсутствие AWS, реальные сервисы

pyproject.toml / uv.lock
.env.example / docker-compose.test.yaml
README.md
.specify/memory/constitution.md
```

**Structure Decision**: Сохранить существующие слои одного сервиса. Удалять возможности вместе с импортами и экспортами; не создавать новый порт хранения, замену поля или общий файловый сервис.

## Design and Implementation Sequence

1. **Governance — выполнено при планировании**: конституция 4.0.0 соответствует принятым уточнениям; спецификация и checklist синхронизируются с поправкой. Исторические документы 001 не переписываются.
2. **Сократить модель и сценарии**: убрать image_s3_path из UserEntity, UserReadDTO и UseCaseBase; удалить три image use case, IStorage, ошибки изображения и их exports. Создание/изменение доменных значений и доступ через подтверждённого subject сохраняются.
3. **Сократить хранение и сборку**: убрать поле из ORM и репозитория, заменить baseline новым `users_no_images_20260927`, удалить storage каталог, StorageConfig/Config.storage/get_storage и зависимые factories. Прикладные и общие ошибки продолжают использовать существующий handler.
4. **Сократить HTTP-контракты**: убрать POST/GET/DELETE `/api/v1/users/me/image`, ImageResponse/ImageUploadResponse, image_s3_path в UserResponse/UserEditResponse и file-only imports/limits. Не менять `extra="ignore"`, форму login, refresh-cookie и bearer-субъект.
5. **Сократить поставку**: удалить 2 прямые S3-зависимости, пересчитать lock без сопутствующих upgrades, убрать AWS-примеры и фиктивные параметры startup. Обновить действующий README; описание запуска согласовать с реальным Compose, где shared_net уже закомментирована. Текущий POSTGRES_DB → POSTGRES_NAME mapping сохраняется.
6. **Адаптировать проверки**: удалить image-only tests и FakeStorage, убрать override из fixtures и обновить точные поля ответов и схемы. Добавить наблюдаемые отрицательные проверки и настройки без AWS; переиспользовать регрессию семи сценариев, токенов, конфликтов и доступа.
7. **Подтвердить результат**: Ruff, mypy strict, unit/integration, реальные PostgreSQL/Redis/RabbitMQ, startup production entry и сохранение профиля при restart. Инфраструктура проверки одноразовая; production volume на этом этапе не удаляется.

## Validation and Traceability

| Requirements / Outcomes | Проверка |
|---|---|
| FR-001–002 / SC-003 | POST, GET, DELETE `/users/me/image` → 404 с bearer и без; OpenAPI не содержит пути и image-схем |
| FR-003–004 / SC-003–004 | Точные ключи signup/GET/PATCH; legacy image input игнорируется; Entity/DTO/ORM и мигрированная схема без поля |
| FR-005–006 / SC-001–002 | Config без AWS и с устаревшими пустыми AWS; startup-профиль без AWS; отсутствие S3 roots в поставке и ненужных imports |
| FR-007 / SC-002 | Все семь сценариев, form login, токены/replay, конфликты данных, текущая личность и недоступность чужого профиля |
| FR-008 / SC-004 | Один baseline с новым revision, только users+alembic_version; 0 аккаунтов до signup; restart сохраняет аккаунт и изменённый профиль |
| FR-009 / SC-005 | README и env/Compose примеры без настройки изображений; инструкция явно описывает пустую базу и потерю аккаунтов |
| FR-010 | В поставке нет пути к AWS; удаление аккаунта работает без S3; нет cleanup объектов/бакетов/ключей |

Поиск legacy-терминов применяется к действующему коду, настройкам, графу зависимостей и README. Отрицательные тесты и исторические specs разрешают такие строки; Docker `image:` и token-blacklist `.storage` не являются пользовательскими изображениями. Код реализации не добавляет искусственный сетевой монитор AWS: отсутствие адаптера и зависимостей плюс реальные сценарии запуска подтверждают отсутствие интеграции.

## Transition and Risks

- Клиенты, использующие изображения или ожидающие их поля, должны принять сокращённый контракт. Обратная совместимость этих возможностей не требуется.
- Новая версия устанавливается на пустую базу. Старый volume может быть пересоздан по решению пользователя; удалять следует только проверенный PostgreSQL volume выбранного проекта. Redis/RabbitMQ и сторонние проекты не требуется удалять.
- Старые изображения AWS остаются вне приложения; их очистка — отдельная работа.
- Нельзя случайно удалить `python-multipart`, общие транзитивные async пакеты или broker-константы.
- Нельзя считать ASGITransport доказательством production lifespan. Compose startup и PostgreSQL обязательны для окончательной проверки.
- Нет дополнительных архитектурных сложностей или исключений из конституции, поэтому Complexity Tracking не требуется.
