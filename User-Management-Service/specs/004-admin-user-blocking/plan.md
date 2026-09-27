# Implementation Plan: Администраторы, суперадмин и блокировка

**Branch**: `fix/um` | **Date**: 2026-09-27 | **Spec**: [spec.md](spec.md)

**Input**: `specs/004-admin-user-blocking/spec.md`

Setup-plan вернул BRANCH=004-admin-user-blocking как идентификатор активной фичи; фактическая Git-ветка проверена командой git branch --show-current: fix/um. Ветка не переключалась. В рабочем дереве есть изменения предыдущих фич; они не отменяются и являются текущей базой дизайна.

## Summary

Ввести общий enum из user/admin, отдельную модель Role/таблицу roles и is_superadmin, состояние блокировки и административные действия. Только superadmin назначает и снимает admin; admin/superadmin получают список и блокируют user. Superadmin создаётся только при первой инициализации контейнера, не может быть назначен через API, понижен, заблокирован или удалён. Текущие права читаются из БД; изменение завершается commit до подтверждения. Bootstrap и миграции сериализуются для параллельного старта.

## Technical Context

**Language/Version**: Python >=3.12,<3.13, строгий mypy.

**Primary Dependencies**: Установленные в pyproject.toml FastAPI 0.135.1, Pydantic 2.12.5, SQLAlchemy async 2.0.48, Alembic 1.18.4, asyncpg 0.31.0, PyJWT 2.12.1, существующий password hasher. Новые сторонние зависимости не нужны.

**Storage**: PostgreSQL 16 (users, roles), существующие Redis для blacklist refresh и RabbitMQ для запроса восстановления пароля.

**Testing**: pytest/pytest-asyncio, HTTPX, PostgreSQL в изолированных схемах, unit fake-порты; Ruff и mypy. SQLite только вспомогательный HTTP режим.

**Target Platform**: Linux Docker; локальные проверки через PowerShell/uv.

**Project Type**: HTTP web service с DDD слоями и контейнерной инициализацией.

**Performance Goals**: Не вводится произвольный latency SLA. Пагинация ограничена 100 записями, default 50; авторизация требует актуального чтения БД. SC-004 проверяется на 125 аккаунтах.

**Constraints**: Две роли, один защищённый admin на БД, немедленное действие подтверждённой блокировки/смены роли на новые запросы; no secret logging; начальные настройки не сбрасывают существующий аккаунт. Init lock timeout 60 секунд. Новая установка на пустой БД; текущая users_roles_20260927 обновляется без потери аккаунтов.

**Scale/Scope**: Один сервис, четыре новых операции HTTP (roles, list, change role, block), изменение проверок существующих auth/me маршрутов, один startup runner. Группы, изображения и разблокировка не добавляются.

## Constitution Check

До Phase 0 выявлено противоречие с конституцией 4.0.0: запрет ролей/блокировки/списка/суперадмина. На основании явных новых требований пользователя конституция обновлена до 6.0.0; это изменение границ, а не исключение из правил. Исторические решения сохранены, изменены только относящиеся к фиче действующие положения.

| Gate | До исследования после поправки | После дизайна |
|------|--------------------------------|---------------|
| Область раздела I | PASS: запрошены две роли и защищённый admin и ограниченные операции | PASS: матрица и contracts не добавляют чужие профили/разблокировку |
| Python/FastAPI | PASS: стек сохраняется | PASS: тонкие маршруты, типизированные схемы |
| Строгие типы | PASS для дизайна | PASS для дизайна: enum, DTO, UoW и порты без Any; реальный mypy обязателен при реализации |
| DDD | PASS для дизайна | PASS: переходы/политики в домене, сценарии в application, SQL и locks в infrastructure |
| Проверяемость | PASS: определены сценарии | PASS: unit, HTTP, PostgreSQL races, startup и commit failure |
| Новая установка | PASS | PASS: baseline + forward-миграция каталога + bootstrap; существующие аккаунты сохраняются |

Прохождение design gates не утверждает успешность тестов будущего кода. Новые исключения не нужны. Полный аудит существующих нарушений типизации не выполнялся; результаты обязательных проверок должны быть записаны при реализации, не замаскированы подавлениями.

## Project Structure

### Documentation (this feature)

```text
specs/004-admin-user-blocking/
  spec.md
  plan.md
  research.md
  data-model.md
  contracts/admin-api.md
  quickstart.md
  checklists/requirements.md
  tasks.md
  validation.md
```

tasks.md сгенерирован командой speckit-tasks; результаты реализации и проверок находятся в validation.md.

### Source Code (repository root)

```text
source/domain/
  entities/user.py                 # role, is_superadmin, blocked, переходы
  entities/role.py                 # отдельная модель роли
  value_objects/                  # UserRole
source/application/
  interfaces/                     # repository, UoW, bootstrap ports
  dto/                            # list/role/block DTO
  exceptions/                     # forbidden/blocked/protected/conflict
  use_cases/user_use_cases.py      # проверки auth/me
  use_cases/admin_use_cases.py     # новые сценарии
  use_cases/bootstrap_use_case.py  # создание superadmin
source/infrastructure/database/
  models/users.py                  # role_id FK, is_superadmin, blocked, constraints/indexes
  user_repository.py              # fresh/locked reads, narrow writes, list
  models/roles.py                  # каталог двух ролей
  role_repository.py               # чтение каталога
  session.py                      # UoW adapter, commit lifecycle
  alembic/versions/                # baseline и forward-миграция каталога
source/presentation/
  api/routes/                     # roles/admin + существующие auth/me
  api/schemas/                    # общий UserRole и ограниченная смена роли
  api/dependencies/               # сборка сценариев и UoW
  exceptions.py                  # новые HTTP ошибки
source/settings/separated_configs/ # bootstrap config, секреты
scripts/initialize_service.py     # новый startup composition runner
scripts/entry.sh                  # runner перед exec
.env.example
.env.test.example
docker-compose.test.yaml
README.md
tests/unit/                      # домен, сценарии, настройки
tests/adapters/                  # fake repository/UoW
tests/integration/               # HTTP, схема, конкуренция, startup
```

**Structure Decision**: Расширить существующие четыре слоя. Новые файлы в дереве — планируемые; бизнес-правила не переносятся в routes или scripts. scripts только собирает инфраструктуру и вызывает сценарий. Каталог подключается через отдельный типизированный репозиторий; новая БД и кеш полномочий не нужны.

## Phase 0 — Research

Завершено: [research.md](research.md). Проверены текущие auth/read/write/session/startup и результаты отдельного исследовательского агента. Выбраны свежие DB reads, UoW с явным commit, row locks, уникальный superadmin и serialized startup. Неразрешённых технических вопросов нет.

## Phase 1 — Design

Завершено: [data-model.md](data-model.md), [контракты](contracts/admin-api.md), [проверки](quickstart.md). Матрица spec сохраняется; общий перечень содержит только user/admin; superadmin — отдельный признак, но контракт назначения допускает только user/admin.

Порядок будущей реализации:

1. Доменная роль и переходы, DTO/ошибки/порты; unit tests и согласованные fake-адаптеры.
2. Итоговая baseline, ограничения, fresh/locked reads и узкие записи, UoW; PostgreSQL tests инвариантов и гонок.
3. Bootstrap и startup runner с общей блокировкой миграций и создания; настройки и повторный/параллельный запуск.
4. Актуальные проверки LoginUser, ResetTokens, GetCurrentUserFromToken, require_user; защищённое удаление; новые административные сценарии.
5. HTTP контракты, DI и ошибки; список двух ролей из БД и поля профиля; запрет superadmin во входной схеме смены роли.
6. Актуализировать тесты прежнего отсутствия ролей/списка и нулевого числа пользователей после старта; сохранить негативные тесты групп, изображений и чужих профилей. Обновить README и env examples, выполнить quickstart и обязательные проверки.

## Transition and risks

Baseline users_no_images_20260927 заменена итоговой users_roles_20260927 для чистой установки, без цепочки создания старых удалённых возможностей. Сохранена как базовая ревизия; новая role_catalog_20260927 обновляет её с сохранением аккаунтов. README и tests используют новый head. Не выполнять downgrade/stamp/автоудаление рабочей базы. Проверки выполняются в выделенных тестовых схемах; штатный runner обновляет существующую users_roles_20260927 без пересоздания базы.

Критические риски: commit после ответа, stale identity map, гонка admin/block, параллельные миграции, перезапись прав профильным update и выдача секрета из ошибки настроек. Для каждого предусмотрены архитектурное ограничение и проверка в quickstart. Отказ БД не разрешает действие; неуспешный bootstrap не запускает приложение.

## Complexity Tracking

Нарушений конституции в дизайне нет. UoW и startup runner нужны для обещаний о подтверждённом изменении и параллельном старте; они локализуют транзакции без добавления новых внешних сервисов.

## Поправка: отдельный каталог двух ролей

Последний запрос заменяет представление третьей роли. RoleEntity и RoleRepository
отделены от пользователя; ListRoles читает каталог через IRoleRepository. ORM
User.role_id ссылается на roles.id, связь User.role загружается явно. Домен
использует UserRole и is_superadmin. Каталог содержит (1, user, Пользователь) и
(2, admin, Администратор), без API редактирования. Head role_catalog_20260927
следует за users_roles_20260927 и сохраняет профили, пароли и идентификаторы.
Startup применяет обе миграции под lock. Bootstrap сохраняет матрицу доступа.
Проверки: каталог/FK/ORM связь, upgrade-downgrade-upgrade с данными, запрет третьей
роли, защита флага при signup/PATCH me, матрица доступа и PostgreSQL startup.
Схема до users_roles_20260927 за пределами поддержанного перехода.
