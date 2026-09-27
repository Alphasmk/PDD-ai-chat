# Implementation Plan: очистка остаточной логики изображений в тестах

**Feature**: `003-remove-s3-remnants` | **Git branch**: `fix/um` | **Date**: 2026-09-27 | **Spec**: [spec.md](spec.md)

**Input**: `specs/003-remove-s3-remnants/spec.md`; новая Git-ветка не создавалась.

## Summary

Удалить из семи тестовых файлов специальную логику изображений и AWS: устаревшие входные поля, индивидуальные проверки отсутствия атрибутов, запросы прежних маршрутов и варианты конфигурации. Сохранить текущие контракты через точные наборы полей/операций, нейтральные неизвестные поля и сравнение профилей. Актуализировать исполняемые инструкции quickstart 002 и указатель README на руководство 003. Runtime, зависимости, схема и revision baseline не меняются; основную БД не пересоздавать.

## Technical Context

**Language/Version**: Python 3.12 (`>=3.12,<3.13`); PowerShell для проверки.

**Primary Dependencies**: существующие FastAPI 0.135.1, Pydantic 2.12.5, pydantic-settings 2.13.1, SQLAlchemy 2.0.48, Alembic 1.18.4, asyncpg 0.31.0, Redis client 7.4.0, aio-pika 9.6.2, PyJWT 2.12.1. `python-multipart` 0.0.22 сохраняется для формы login. Изменений pyproject.toml/uv.lock нет.

**Storage**: действующая users-only PostgreSQL схема, Redis blacklist, RabbitMQ publisher. Новые таблицы/миграции не нужны; SQLite/fakes сохраняются в быстром тестовом режиме.

**Testing**: pytest 9.0.3, pytest-asyncio 1.3.0, httpx 0.28.1, Ruff 0.15.7, strict mypy 1.19.1. PostgreSQL 16/Redis 7/RabbitMQ 4 через docker-compose.test.yaml; production Dockerfile/entrypoint для startup.

**Target Platform**: Linux-контейнеры; Windows PowerShell/Docker Desktop для локальной проверки.

**Project Type**: HTTP web service с DDD слоями; изменение тестов/документации.

**Performance Goals**: новые latency/throughput цели не вводятся; runtime не меняется. Число тестов может уменьшиться после удаления параметризации.

**Constraints**: сохранить 7 сценариев и строгую типизацию без Any/suppressions; не модифицировать основной volume, revision и аккаунты. Сохранить незакоммиченные изменения 002 и исторические требования/отчёты.

**Scale/Scope**: 7 тестовых файлов, актуальные примеры quickstart 002 и README. Общие фикстуры/конфигурации меняются только при обнаружении относящегося к FR-001–003 остатка. Новые модули приложения не создаются.

## Constitution Check

Конституция [4.0.0](../../.specify/memory/constitution.md). Gate до Phase 0: **PASS**; после Phase 1: **PASS**.

| Принцип / ограничение | До исследования | После проектирования |
|---|---|---|
| I. Users-only | PASS: область ограничена тестовой очисткой | PASS: 7 пользовательских операций и healthcheck |
| II. Python/FastAPI | PASS: стек прежний | PASS: существующие pytest/httpx |
| III. Строгая типизация | PASS: без ослабления требований | PASS: object с сужением для OpenAPI, dataclasses.fields для DTO; без Any/suppressions |
| IV. DDD | PASS: source не меняется | PASS: DTO/HTTP проверяются на своих границах; без новой бизнес-логики |
| V. Проверяемость | PASS: специальные проверки заменяются общими | PASS: точные наборы, no-op, subject, реальные сервисы/startup |
| Зависимости и схема | PASS: обновления не нужны | PASS: users-only baseline/revision прежний; свежая БД лишь у одноразового startup-теста |
| Данные и история | PASS: FR-009/010 соблюдены | PASS: история сохраняется; restart приложения проверяет persistence |

Нарушений/исключений нет; поправка конституции не нужна. PASS относится к дизайну, не подтверждает выполнение будущих Ruff/mypy/pytest.

## Project Structure

### Documentation (this feature)

```text
specs/003-remove-s3-remnants/
├── spec.md
├── checklists/requirements.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/
│   ├── http-api.md
│   └── test-contract.md
└── quickstart.md
```

`tasks.md` создаётся следующим `$speckit-tasks`, validation.md — при реализации.

### Source Code (repository root)

```text
source/                                      # без изменений
tests/unit/settings_config_test.py
tests/unit/user_usecases_tests/register_user_test.py
tests/unit/user_usecases_tests/get_current_user_from_db_test.py
tests/integration/auth_tests/signup_user_test.py
tests/integration/user_tests/edit_current_user_test.py
tests/integration/user_tests/removed_operations_test.py
tests/integration/settings/startup_test.py
tests/integration/settings/fresh_schema_test.py  # revision сохраняется
specs/002-remove-s3-images/quickstart.md        # текущие инструкции
README.md                                    # указатель на quickstart003
docker-compose.test.yaml                     # повторно используется
```

**Structure Decision**: исправить существующие проверки, не создавать параллельный набор или новый слой. Expected-наборы определяются контрактом независимо от проверяемых моделей.

## Phase 0: Research

Завершено: [research.md](research.md). Исследователь подтвердил семь файлов и границу исторических идентификаторов. Нерешённых вопросов нет.

## Phase 1: Design

Модель: [data-model.md](data-model.md). API: [contracts/http-api.md](contracts/http-api.md). Правила проверок и FR/SC: [contracts/test-contract.md](contracts/test-contract.md). Порядок проверки: [quickstart.md](quickstart.md).

Последовательность реализации для генерации задач:

1. Очистить unit DTO/settings, сохранить точные формы и lifecycle кеша.
2. Заменить signup/PATCH данные нейтральными. Сохранить no-op и полное равенство профилей/дат при unknown-only/empty PATCH, чужой id и текущую личность.
3. Убрать шесть image пар method/path и четыре image термина OpenAPI; сохранить прочие отрицательные сценарии и allowlist8.
4. Очистить startup, проверить опубликованные операции8/поля8/5, сохранить login, rotation/replay, publisher и cleanup.
5. Актуализировать исполняемые инструкции quickstart002 и README; исторические результаты002 сохранить.
6. Выполнить аудит, Ruff, strict mypy, unit, интеграции с реальными сервисами, production startup и persistence. Записать фактические результаты003, ошибки/пропуски и соответствие требованиям.

**Acceptance**: FR-001–FR-010 и SC-001–SC-004. Прежнее число тестов не является целевым. Все оставшиеся проверки должны проходить; отсутствие opt-in URL не подтверждает реальные интеграции.

## Complexity Tracking

Не применяется: новых компонентов/зависимостей или исключений нет.

## Planning validation

Проверены относительные ссылки восьми Markdown-файлов функции и синтаксис шести PowerShell-блоков quickstart; ошибок нет. В проектных артефактах нет незаполненных шаблонных полей или нерешённых вопросов. Тесты приложения на этом этапе не выполнялись. `.specify/extensions.yml` отсутствует; before_plan/after_plan hooks пропущены согласно workflow.
