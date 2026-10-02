# Tasks: Администраторы, суперадмин и блокировка

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/admin-api.md](contracts/admin-api.md), [quickstart.md](quickstart.md).
**Prerequisites**: Конституция 6.0.0; активная фича `004-admin-user-blocking`; текущая ветка `fix/um`.
**Tests**: Включены по требованиям раздела V конституции и согласованного плана. Новые сценарные тесты писать до соответствующей реализации и сначала подтверждать ожидаемый отказ; затем выполнять их на завершении истории.
**Organization**: Пять историй из спецификации; пути ниже относительно корня репозитория. Новые файлы разрешено создавать. `[P]` означает независимые файлы и отсутствие зависимостей внутри указанной параллельной группы, а не разрешение пропустить предыдущую фазу. Все 56 задач выполнены; результаты проверок приведены в validation.md.

Задачи T001–T050 фиксируют первоначальную реализацию. Их прежние ссылки на три
роли и единственную baseline заменены поправкой T051–T056 ниже. Действующие
требования — две роли в отдельной таблице и защищённый статус администратора.

## Phase 1: Setup

**Цель**: Зафиксировать исходную точку и подготовить проверки без потери текущих изменений.

- [X] T001 Проверить текущие изменения, Python 3.12 и доступность uv/Docker; записать исходное состояние и доступность проверок в `specs/004-admin-user-blocking/validation.md`, сверив `pyproject.toml`; не сбрасывать изменения предыдущих фич и не менять зависимости без необходимости.
- [X] T002 Подготовить изолированные PostgreSQL-схемы и фабрики аккаунтов трёх ролей в `tests/integration/conftest.py`; добавить отдельный harness запуска runner в независимых процессах и обязательный режим PostgreSQL-проверок без ложного успеха при пропусках; не использовать рабочую БД.

## Phase 2: Foundational — общая основа

**Цель**: Создать типизированные модели, транзакции и актуальную проверку доступа. Завершить T003–T012 до реализации историй.

**Тесты**: Сначала добавить проверки T003, зафиксировать ожидаемый отказ до реализации. Здесь и далее тесты обязательны по разделу V конституции и плану проверок.

- [X] T003 Добавить проверки трёх ролей, defaults, недопустимых переходов и неизменяемости сущности в `tests/unit/user_access_invariants_test.py`: регистрация user/false, superadmin нельзя понизить/удалить/заблокировать, admin нельзя блокировать, заблокированного user нельзя повысить, no-op сохраняет updated_at.
- [X] T004 Создать `source/domain/value_objects/user_role.py` и расширить `source/domain/entities/user.py`: role — «Только user, admin, superadmin; одно значение на аккаунт», default user; is_blocked — bool, default false, «true допускается только для user»; сохранить immutable entity и существующие проверки профиля, реализовать проверяемые методы переходов и защиты удаления без обхода через dataclasses.replace.
- [X] T005 Описать типизированные fresh-read, get_for_update, list_page и узкие записи в `source/application/interfaces/repositories.py`; добавить `source/application/interfaces/unit_of_work.py` и `source/application/interfaces/bootstrap.py` с async enter/exit, commit/rollback и портом начального создания; экспортировать порты в `source/application/interfaces/__init__.py` без инфраструктурных импортов.
- [X] T006 Дополнить `source/application/dto/users_dto.py` и `source/application/use_cases/base.py` role/is_blocked; создать `source/application/dto/admin_dto.py` с AdminUserDTO, UserPageDTO и ChangeRoleDTO; DTO списка содержит только id/name/surname/username/email/role/is_blocked, без password_hash/телефона/токенов; обновить экспорты в `source/application/dto/__init__.py`.
- [X] T007 Обновить `source/infrastructure/database/models/users.py` и заменить текущую baseline на `source/infrastructure/database/alembic/versions/2026_09_27_users_roles_baseline.py`: итоговые 11 полей users, «NOT NULL обоих полей», «CHECK допустимой роли», «CHECK (NOT is_blocked OR role = 'user')», «UNIQUE INDEX по role WHERE role = 'superadmin'», индекс (created_at, id); сохранить «id (UUID, PK)», «username (unique)», «email (unique)», «phone_number (nullable, unique)», «updated_at (nullable)» и остальные поля; миграция не создаёт аккаунт, не переносит и не удаляет рабочие данные.
- [X] T008 Реализовать fresh SELECT и locked SELECT FOR UPDATE с populate_existing в `source/infrastructure/database/user_repository.py`, явное преобразование UserRole и новых полей; добавить узкие set_role/set_blocked и поиск superadmin; профильный update не пишет role/is_blocked, no-op не меняет updated_at, реальные изменения меняют updated_at.
- [X] T009 Реализовать адаптер UoW в `source/infrastructure/database/session.py` и его фабрику в `source/presentation/api/dependencies/adapters.py`: отдельная транзакционная сессия, явный commit до возврата результата сценария, rollback/close при исключении, без повторного commit в yield-finalizer; обеспечить совместимость с существующими обычными репозиториями.
- [X] T010 Добавить доменные ошибки в `source/domain/exceptions/user_access_exceptions.py`, их прикладное преобразование в `source/application/exceptions/user_exceptions.py` и HTTP mapping в `source/presentation/exceptions.py`: 403 forbidden/user_blocked, 409 protected_account/invalid_target_state, 503 service_unavailable; не раскрывать SQL/секреты и не менять сообщения старых маршрутов; домен не импортирует application.
- [X] T011 В `source/application/use_cases/user_use_cases.py` и `source/domain/policies/user_access.py` реализовать общую актуальную проверку аккаунта и политики прав: fresh DB read в require_user/GetCurrentUserFromToken/LoginUser/ResetTokens, отказ blocked до выдачи токенов и действий, проверка пароля до сообщения о блокировке; новые административные сценарии проверяют инициатора до чтения цели, роль не берётся из JWT/Redis.
- [X] T012 Согласовать fake с узкими production-записями в `tests/adapters/user_repository.py`, добавить rollback/commit fake в `tests/adapters/unit_of_work.py`; обновить фабрики `tests/unit/utils/shared_data.py` и `tests/unit/user_usecases_tests/conftest.py`, проверить новую схему и её ограничения в `tests/integration/settings/fresh_schema_test.py`, выполнить T003 и затронутые unit/schema checks, записать результат в `specs/004-admin-user-blocking/validation.md`.

## Phase 3: US1 — защищённый суперадмин при запуске (P1), первый инкремент

**Цель**: Создать одного superadmin при старте, сохранить его при рестартах и запретить удаление; показать отдельную третью роль.

**Независимая проверка**: Новая установка → вход суперадмина → GET /roles → три рестарта и параллельный старт → один неизменившийся аккаунт; DELETE /users/me запрещён. Полные HTTP-проверки запрета назначения/снятия и блокировки завершаются в US2/US4; возможность управления ролями US1 проверяется сквозным сценарием после US2. Это первый технический инкремент, не завершение всей фичи.

### Тесты — до реализации

- [X] T013 [P] [US1] Добавить unit-проверки bootstrap и настроек в `tests/unit/bootstrap_use_case_test.py`: первый запуск, существующий superadmin с отсутствующими/изменёнными начальными настройками, конфликт обычного аккаунта, ошибки валидации без секретов, отсутствие сброса пароля и hash через существующий hasher.
- [X] T014 [P] [US1] Добавить startup-проверки в `tests/integration/settings/admin_startup_test.py`: новая схема, три рестарта, два независимых runner, восстановление после прерывания до commit, конфликт личности, missing/invalid data, недоступная БД, timeout lock; проверить ненулевой exit и отсутствие запуска HTTP при неудаче, не только вызов bootstrap.
- [X] T015 [P] [US1] Добавить контрактные проверки GET /roles и DELETE /users/me суперадмина в `tests/integration/admin_tests/superadmin_protection_test.py`, unit защиты удаления в `tests/unit/user_usecases_tests/delete_user_test.py`; ожидать ровно три значения и 409 protected_account без удаления.
- [X] T016 [US1] Создать `source/settings/separated_configs/bootstrap_config.py`: SUPERADMIN_USERNAME/EMAIL/PASSWORD/NAME/SURNAME обязательны только при первом создании, пароль SecretStr, телефон null; валидация после поиска existing superadmin, ошибки без входных значений; обычные импорты `source/settings/config.py` не требуют bootstrap credentials.
- [X] T017 [US1] Реализовать `source/application/use_cases/bootstrap_use_case.py`: проверить наличие superadmin по роли, при наличии ничего не менять, иначе проверить профиль/пароль текущими value objects, создать через bootstrap-порт и hasher; совпавший username/email обычного аккаунта даёт identity_conflict, без повышения; логика не зависит от HTTP/SQL.
- [X] T018 [US1] Создать `source/infrastructure/database/bootstrap.py` и `scripts/initialize_service.py`: выделенное соединение, session advisory lock 74004001 с ожиданием до 60 секунд, миграция через supplied Connection из `source/infrastructure/database/alembic/env.py`, затем bootstrap и commit; lock охватывает обе стадии, освобождение и закрытие при любой ошибке, безопасные категории diagnostics и ненулевой exit до запуска приложения.
- [X] T019 [US1] Подключить runner перед exec в `scripts/entry.sh`, проверить наличие модуля в `Dockerfile`, добавить пустые документированные bootstrap-параметры в `.env.example` и `.env.test.example`, пробросить их в `docker-compose.test.yaml` и проверить передачу через `docker-compose.yaml`; не вводить стандартный production-пароль и не требовать bootstrap данных при обычном импорте настроек.
- [X] T020 [US1] Перевести DeleteUser на UoW/locked read в `source/application/use_cases/user_use_cases.py` и `source/presentation/api/dependencies/user_deps.py`: проверка is_blocked и запрет удаления superadmin в той же транзакции, commit до успеха; сохранить удаление незаблокированных user/admin.
- [X] T021 [US1] Реализовать типизированный сценарий списка ролей в `source/application/use_cases/role_use_cases.py`, схемы в `source/presentation/api/schemas/roles.py` и GET /api/v1/roles в `source/presentation/api/routes/roles_router.py`; зарегистрировать в `source/main.py`: доступ любому вошедшему незаблокированному аккаунту, ровно user/admin/superadmin с русскими label, без изменяемого справочника.
- [X] T022 [US1] Выполнить проверки T013–T015 и обновить существующий `tests/integration/settings/startup_test.py` на новую схему и один superadmin после runner; отдельно подтвердить отсутствие пароля в логах/ошибках и неизменность аккаунта после редактирования его профиля и рестарта; результаты записать в `specs/004-admin-user-blocking/validation.md`.

## Phase 4: US2 — назначение и снятие администраторов (P1)

**Цель**: Только superadmin меняет user ↔ admin; новая роль применяется в прежних сеансах.

**Независимая проверка**: С подготовленными аккаунтами выполнить повышение/понижение, проверить сохранение профиля, права по свежему чтению и no-op. Сквозной доступ прежним токеном к списку и блокировке дополнительно проверяется после US3/US4.

### Тесты — до реализации

- [X] T023 [P] [US2] Добавить unit-сценарии смены роли в `tests/unit/admin_usecases_tests/change_role_test.py`: только superadmin, отсутствие/блокировка цели, no-op с неизменным updated_at, запрет изменения superadmin, fresh actor перед lookup target, rollback и отсутствие результата при ошибке commit.
- [X] T024 [P] [US2] Добавить HTTP contract tests в `tests/integration/admin_tests/change_role_test.py`: PATCH /users/{id}/role, строго user/admin, superadmin/unknown → 422 invalid_role, extras → 422 invalid_request, protected target → 409, отсутствие полномочий раньше поиска цели; профиль и число аккаунтов не меняются.
- [X] T025 [US2] Реализовать ChangeUserRole в `source/application/use_cases/admin_use_cases.py`: открыть UoW, fresh actor и superadmin policy, locked target, доменный переход, узкая запись и commit; user для уже blocked user оставляет блокировку; admin для blocked user запрещён; superadmin нельзя назначить даже самому себе.
- [X] T026 [US2] Добавить схемы назначения и результата в `source/presentation/api/schemas/admin.py`, PATCH /api/v1/users/{user_id}/role в `source/presentation/api/routes/admin_router.py` и DI в `source/presentation/api/dependencies/admin_deps.py`; зарегистрировать router в `source/main.py`; общий enum выходов трёхзначный, вход смены роли двухзначный, extra=forbid.
- [X] T027 [US2] Добавить локальную нормализацию валидации новых маршрутов в `source/presentation/api/routes/admin_route.py`, подключить к `source/presentation/api/routes/admin_router.py`: invalid_role/invalid_request и ErrorResponse согласно контракту, старые 422 не менять; переводить сбой проверки состояния/commit в 503 без 2xx и без секретов.
- [X] T028 [US2] Выполнить T023–T024 и проверить отсутствие новых role claims в `tests/unit/token_provider_test.py`, добавить проверку актуальных прав прежнего сеанса в `tests/unit/current_subject_test.py`; записать результат US2 в `specs/004-admin-user-blocking/validation.md`.

## Phase 5: US3 — список всех пользователей (P1)

**Цель**: Admin/superadmin получают полный безопасный постраничный список.

**Независимая проверка**: Подготовить 125 аккаунтов всех ролей и допустимых состояний, обойти страницы и получить 125 уникальных id; user/посетитель/blocked не получают записи или количество.

### Тесты — до реализации

- [X] T029 [P] [US3] Добавить unit-проверки списка в `tests/unit/admin_usecases_tests/list_users_test.py`: права до чтения списка, безопасный DTO, пустая страница, ошибка проверки текущего состояния не даёт разрешения.
- [X] T030 [P] [US3] Добавить контрактные проверки GET /users в `tests/integration/admin_tests/list_users_test.py`: 125 аккаунтов, limit 50/100, default 50/offset 0, границы 1..100 и offset >=0, сортировка created_at/id, пустая страница; роли и block видны, password_hash/телефон/токены отсутствуют.
- [X] T031 [US3] Реализовать list_page в `source/infrastructure/database/user_repository.py` и `tests/adapters/user_repository.py`: сортировка created_at ASC, id ASC, limit/offset; расширить `source/application/use_cases/admin_use_cases.py` сценарием ListUsers с fresh actor и admin/superadmin policy; не возвращать total и не обещать snapshot между запросами.
- [X] T032 [US3] Добавить схемы UserPageResponse в `source/presentation/api/schemas/admin.py`, GET /api/v1/users в `source/presentation/api/routes/admin_router.py` и DI в `source/presentation/api/dependencies/admin_deps.py`: items/limit/offset, ограничения параметров и локальные ошибки из T027; сохранить маршруты /users/me.
- [X] T033 [US3] Выполнить T029–T030 и добавить promotion/demotion со старым access token → GET /users в `tests/integration/admin_tests/list_users_test.py`; сразу после подтверждённого снятия роли ожидать 403, собственный профиль доступен; результат записать в `specs/004-admin-user-blocking/validation.md`.

## Phase 6: US4 — блокировка пользователя (P1)

**Цель**: Admin/superadmin блокируют user; все последующие входы, refresh и защищённые запросы заблокированного прекращаются.

**Независимая проверка**: Заблокировать известный user по id, проверить несколько прежних сеансов, новый login, refresh и GET/PATCH/DELETE /users/me; другой аккаунт продолжает работать.

### Тесты — до реализации

- [X] T034 [P] [US4] Добавить unit-сценарии block в `tests/unit/admin_usecases_tests/block_user_test.py`: actor permissions до target lookup, protected/admin цели, отсутствующая цель, повторный успех без изменения updated_at, сохранение профиля/роли и rollback при commit failure.
- [X] T035 [P] [US4] Добавить HTTP contract tests в `tests/integration/admin_tests/block_user_test.py`: POST /users/{id}/block без тела, успешный ответ id/role/is_blocked, 401/403/404/409/422/503, запрет блокировки себя/admin/superadmin, повторная блокировка успешна.
- [X] T036 [P] [US4] Добавить PostgreSQL race tests с двумя независимыми сессиями в `tests/integration/admin_tests/concurrent_changes_test.py`: promotion↔block, delete↔block, profile-update↔role-change, два block, stale ORM; синхронизировать операции барьерами, проверить актуальную цель после ожидания и отсутствие недопустимого финального состояния; SQLite не заменяет эти проверки.
- [X] T037 [US4] Реализовать BlockUser в `source/application/use_cases/admin_use_cases.py`: UoW, fresh actor, admin/superadmin policy до locked target, доменный переход, узкая запись is_blocked, commit до результата; отказ для административных ролей и успех для повторной блокировки user.
- [X] T038 [US4] Подключить POST /api/v1/users/{user_id}/block и DI в `source/presentation/api/routes/admin_router.py` и `source/presentation/api/dependencies/admin_deps.py`, схему ответа в `source/presentation/api/schemas/admin.py`; сохранить общий error contract, не добавлять unblock.
- [X] T039 [US4] Добавить проверки ранее выданных access/refresh нескольких сеансов после block в `tests/integration/admin_tests/blocked_sessions_test.py`, а также неверного пароля (401), верного пароля blocked (403), запроса восстановления без снятия блокировки, сохранения доступа другого аккаунта и отказа БД; при обнаруженных обходах исправить общую проверку в `source/application/use_cases/user_use_cases.py`.
- [X] T040 [US4] Выполнить T034–T036/T039; дополнить `tests/integration/admin_tests/block_user_test.py` сквозным сценарием superadmin снимает admin → может блокировать бывшего admin, прежний токен снятого admin блокировать не может; проверить commit failure на HTTP и сохранение блокировки после рестарта, записать результат в `specs/004-admin-user-blocking/validation.md`.

## Phase 7: US5 — регистрация и собственный профиль (P2)

**Цель**: Сохранить самообслуживание, исключить повышение прав через профиль и регистрацию.

**Независимая проверка**: Передать role/is_blocked в signup и PATCH /me, подтвердить неизменность полномочий; выполнить сохранённые операции user/admin/superadmin с единственным исключением удаления superadmin.

### Тесты — до реализации

- [X] T041 [P] [US5] Расширить `tests/integration/auth_tests/signup_user_test.py` и `tests/unit/user_usecases_tests/register_user_test.py`: дополнительные role=admin/superadmin и is_blocked игнорируются, новый аккаунт всегда user/false, обычная регистрация не создаёт второй superadmin; выход включает действительные role/is_blocked.
- [X] T042 [P] [US5] Расширить `tests/integration/user_tests/edit_current_user_test.py`, `tests/integration/user_tests/get_current_user_test.py` и `tests/integration/user_tests/delete_current_user_test.py`: подмена роли/блокировки через профиль не работает, все три роли читаются корректно, user/admin удаляют себя, superadmin получает 409; сохранить уникальность и валидацию профиля.
- [X] T043 [US5] В `source/application/use_cases/user_use_cases.py` явно закрепить signup user/false и профильный whitelist; обновить `source/presentation/api/schemas/auth.py`, `source/presentation/api/schemas/user.py` и `source/presentation/api/routes/user_router.py` для выходных role/is_blocked с общим enum; сохранить extra=ignore на существующих входах и текущие поля ответов.
- [X] T044 [US5] Актуализировать `tests/integration/user_tests/removed_operations_test.py` под разрешённые role/list/block, сохранить отрицательные проверки чужих профилей, групп, изображений и разблокировки; согласовать прежние unit assertions в `tests/unit/user_usecases_tests/update_user_test.py` и `tests/unit/user_usecases_tests/get_current_user_from_db_test.py` с новыми полями, не ослабляя проверок безопасности.
- [X] T045 [US5] Выполнить T041–T042 и существующие auth/me regression tests, включая `tests/integration/auth_tests/reset_tokens_test.py` и `tests/integration/auth_tests/reset_password_test.py`; подтвердить прежние JWT/cookie/blacklist и публикацию восстановления, записать результаты US5 в `specs/004-admin-user-blocking/validation.md`.

## Phase 8: Polish & Cross-Cutting Concerns

**Цель**: Подтвердить весь контракт и подготовить эксплуатационные инструкции. Начинать после всех историй.

- [X] T046 [P] Обновить `README.md` и `.env.example`: три роли, endpoints/errors, initial-only bootstrap, повторный/параллельный старт, настройки без реальных секретов, новая ревизия схемы, запуск через runner и новая пустая БД; убрать текущие утверждения об отсутствии ролей и первом аккаунте через signup, не переписывать исторические specs 001–003.
- [X] T047 [P] Добавить общую проверку OpenAPI и матрицы доступа в `tests/integration/admin_tests/access_contract_test.py`: четыре новых операции, output enum из трёх ролей и input смены из двух, ошибки, отсутствие секретов и запрещённых операций; покрыть все FR-001–FR-017 и SC-001–SC-008 ссылками на тесты в `specs/004-admin-user-blocking/validation.md`.
- [X] T048 Выполнить `uv run ruff check source tests scripts`, `uv run ruff format --check source tests scripts`, `uv run mypy source tests scripts` и unit suite из `specs/004-admin-user-blocking/quickstart.md`; исправить связанные ошибки в `source/`, `tests/`, `scripts/` без подавлений ради обхода проверок, записать команды/результаты и отдельно существующие нерешённые нарушения в `specs/004-admin-user-blocking/validation.md`.
- [X] T049 Выполнить весь `specs/004-admin-user-blocking/quickstart.md` на изолированном Compose/PostgreSQL, включая параллельные процессы, реальные Redis/RabbitMQ, контейнерный entrypoint, restart и негативные bootstrap случаи; записать pass/fail/skip и причины в `specs/004-admin-user-blocking/validation.md`, не объявлять пропущенные PostgreSQL проверки успешными и не очищать рабочие volumes.
- [X] T050 Сверить итоговые `specs/004-admin-user-blocking/spec.md`, `specs/004-admin-user-blocking/plan.md`, `specs/004-admin-user-blocking/contracts/admin-api.md`, `specs/004-admin-user-blocking/quickstart.md` и `.specify/memory/constitution.md` с реализацией, обновить только фактические детали и отчёт `specs/004-admin-user-blocking/validation.md`; отметить задачи завершёнными только при наличии результата и проверок.

## Dependencies & Execution Order

```text
Setup T001–T002
  → Foundation T003–T012
    → US1 T013–T022
    → US2 T023–T028
    → US3 T029–T033
    → US4 T034–T040
    → US5 T041–T045
  → Final verification T046–T050
```

Стрелки между US задают рекомендуемый интеграционный порядок, не зависимость всех unit tests от всех предыдущих историй. Тестовые фабрики позволяют проверять каждую историю с подготовленными аккаунтами. Production end-to-end требует US1 для создания superadmin. US2 проверяет переход роли самостоятельно; его влияние на GET /users завершает T033, на block — T040. US1 полностью проходит защитные HTTP acceptance scenarios после T024/T035; до этого переходы проверены доменными тестами T003, а удаление — T015/T020. Полную фичу нельзя объявлять готовой после одного первого инкремента.

- В Phase 2 порядок последовательный: T004 даёт enum/entity, T005–T006 — порты/DTO, T007 — storage, T008–T009 — adapter/UoW, T010–T011 — ошибки и gate, T012 закрывает общий checkpoint.
- В US1 T013/T014/T015 независимы после Foundation; T016 → T017 → T018 → T019; T020 и T021 используют готовую Foundation; T022 после всех задач US1.
- В US2 T023/T024 независимы; T025 после них, затем T026 → T027 → T028.
- В US3 T029/T030 независимы; T031 → T032 → T033 после них и готового локального error handler T027.
- В US4 T034/T035/T036 независимы; T037 → T038 → T039 → T040 после них; race tests T036 завершаются только с обеими операциями US2/US4.
- В US5 T041/T042 независимы; T043 → T044 → T045 после них. Изменения общих auth/DTO файлов согласовывать с US1/US4, не редактировать их параллельно.
- T046/T047 независимы после всех историй; затем T048 → T049 → T050. Любые исправления в итоговой фазе требуют повторения затронутых проверок, без необоснованного повторения всего набора.

## Parallel Execution Examples

| История | Группа после её предпосылок | Разделение работы |
|---------|----------------------------|------------------|
| US1 | T013 + T014 + T015 | Unit bootstrap, process startup, roles/delete contracts |
| US2 | T023 + T024 | Unit change-role и HTTP change-role |
| US3 | T029 + T030 | Unit list и HTTP pagination |
| US4 | T034 + T035 + T036 | Unit block, HTTP block, PostgreSQL races |
| US5 | T041 + T042 | Signup tests и profile tests |
| Final | T046 + T047 | README/env и contract matrix/validation |

Параллельность относится к подготовке задач группы; запуск новых тестов до появления реализации должен показать ожидаемый отказ. Общие файлы `admin_use_cases.py`, `admin_router.py`, `admin.py`, `user_use_cases.py` редактируются последовательно; межисторийная параллельная правка этих файлов не запланирована.

## Requirement Coverage

| Требования | Реализация / проверки |
|------------|-----------------------|
| FR-001, SC-002: две роли, каталог, защищённый статус | T003–T007, T015, T021, T024–T027, T035, T047, T051–T056 |
| FR-002–004, SC-001/008: начальная установка | T013–T019, T022, T046, T049 |
| FR-005: запреты superadmin | T003–T004, T015, T020, T023–T027, T034–T038 |
| FR-006–007, SC-003: назначение/снятие | T023–T028, T033, T040 |
| FR-008–010, SC-004: список и доступ | T029–T033, T034–T038 |
| FR-011–012, SC-006: блокировка и сеансы | T008–T012, T034–T040 |
| FR-013: актуальные права | T008–T011, T028, T033, T036, T039–T040 |
| FR-014/016, SC-007: auth и профиль | T011, T020, T039, T041–T045 |
| FR-015, SC-005: ошибки и матрица | T010, T023–T024, T027, T030, T035, T047 |
| FR-017: документация | T019, T046, T049–T050 |

## Implementation Strategy

Первый технический MVP — Setup + Foundation + US1: контейнер создаёт защищённого суперадмина, допускает вход и показывает две роли. Минимальный полезный административный набор — добавить US2 и US3: назначение администраторов и список. Для выполнения всего запроса обязательны также US4, US5 и итоговые проверки.

После каждой истории выполнить её независимые тесты и записать результат. Общий checkpoint — проверка старых сеансов после подтверждённых изменений, PostgreSQL races, параллельного старта и отсутствия обходов через регистрацию/профиль. Задания не требуют деплоя, удаления рабочей БД, коммита или переключения ветки.

## Summary

56 задач: поправка каталога — 6; первоначальный план — 50 (Setup — 2, Foundation — 10, US1 — 10, US2 — 6, US3 — 5, US4 — 7, US5 — 5, завершение — 5). 14 задач помечены `[P]` в шести независимых группах. У каждой задачи есть ID и пути файлов; все задачи историй имеют метку US. Всего с поправкой 56 задач. Статус чекбоксов отражает выполнение реализации, а не готовность этого документа.

## Phase 8: Поправка пользователя — отдельная таблица и две роли

Зависимости: T051 → T052 → T053 → T054 → T055 → T056. FR-001/005/014,
SC-002 и прежняя матрица доступа; предыдущие задачи сохраняются как история.

- [X] T051 Обновить UserRole, UserEntity, политики и bootstrap для двух ролей и защищённого администратора; добавить RoleEntity, IRoleRepository; проверить доменные инварианты в tests/unit/user_access_invariants_test.py.
- [X] T052 Добавить ORM Role, users.role_id FK, is_superadmin и ограничения; forward-миграцию 2026_09_27_role_catalog.py; проверить две записи, запрет третьей роли и сохранение данных при upgrade/downgrade в tests/integration/settings/role_catalog_test.py.
- [X] T053 Добавить RoleRepository и DI; перевести ListRoles на чтение БД, user repository на ID/флаг, дополнить ответы API; проверить ORM связь и чтение каталога в role_catalog_test.py.
- [X] T054 Актуализировать fixtures и матрицу HTTP/startup/schema тестов для двух ролей; проверить защиту флага при signup/PATCH me и сохранение прежних полномочий суперадмина.
- [X] T055 Выполнить Ruff format/check, strict mypy и полный suite с реальными PostgreSQL/Redis/RabbitMQ и контейнерным startup, записать фактический результат в validation.md.
- [X] T056 Согласовать README, spec/plan/data-model/research/contracts/quickstart и конституцию 6.0.0 с поправкой; сохранить исторические решения и убрать изолированные тестовые контейнеры.
