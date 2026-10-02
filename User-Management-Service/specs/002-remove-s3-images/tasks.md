# Tasks: Полное удаление изображений пользователя и AWS S3

**Input**: Документы из `specs/002-remove-s3-images/`.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/http-api.md](contracts/http-api.md), [quickstart.md](quickstart.md); конституция 4.0.0.

**Status**: Выполнено — 38/38 задач; подтверждения в [validation.md](validation.md).

**Tests**: Обязательны согласно сценариям/критериям спецификации и принципу V конституции. Новые проверки затронутого поведения писать до реализации и подтверждать ожидаемое падение, не путать его с ошибкой окружения. Общую регрессию переиспользовать; несвязанных тестов не добавлять.

**Organization**: Setup → общий тестовый фундамент → US1 (P1) → US2 (P1) → US3 (P2) → общие проверки. Сквозное удаление имеет реальные зависимости; независимый тест истории выполняется после её указанных предпосылок.

## Format: `[ID] [P?] [Story] Description`

- `[P]` означает независимые файлы внутри указанной группы после выполнения её предпосылок; не разрешает запуск до зависимости.
- `[US1]`, `[US2]`, `[US3]` соответствуют историям спецификации. Общие задачи не имеют метки истории.
- Пути ниже относительно корня `D:/course_project/pdd_ai/User-Management-Service`.
- Завершённую задачу отмечать только по фактическому результату; пропущенная проверка не равна успешной.

## Phase 1: Setup

**Purpose**: Подготовить контекст и отдельное окружение проверки без изменения основного развёртывания.

- [X] T001 Проверить согласованность `specs/002-remove-s3-images/spec.md`, `specs/002-remove-s3-images/plan.md`, `specs/002-remove-s3-images/checklists/requirements.md` и `.specify/memory/constitution.md`: изображения удаляются целиком, конституция 4.0.0, новая пустая база допустима; не менять ветку и не переписывать исторические документы 001.
- [X] T002 Создать `specs/002-remove-s3-images/validation.md` с таблицей FR-001–FR-010 и SC-001–SC-005, разделами команд/результатов/пропусков и исходным статусом «не выполнено»; использовать его для фактических результатов следующих задач.
- [X] T003 Подготовить отдельный Compose-проект `ums-no-images-validation` по `specs/002-remove-s3-images/quickstart.md` и `docker-compose.test.yaml`: найти Docker executable, проверить порты 5434/6380/5673/15673/8001, подготовить `.env.test` из `.env.test.example` без перезаписи существующих настроек и поднять только одноразовые PostgreSQL/Redis/RabbitMQ; основной Compose и его volumes не изменять.

**Checkpoint**: Подготовлены входные документы, отчёт и одноразовые сервисы. Приложение нового startup-профиля пока не запускать.

## Phase 2: Foundational — общие тестовые зависимости

**Purpose**: Убрать общий тестовый доступ к удаляемому хранилищу, чтобы сборка сценариев не зависела от FakeStorage.

- [X] T004 Удалить `tests/adapters/storage.py`, `tests/unit/user_usecases_tests/set_user_image_test.py`, `tests/unit/user_usecases_tests/get_user_image_test.py`, `tests/unit/user_usecases_tests/delete_user_image_test.py` и `tests/integration/user_tests/own_image_test.py`; убрать storage fixtures/imports/аргументы/override из `tests/unit/user_usecases_tests/conftest.py` и `tests/integration/conftest.py`, а также FakeStorage и проверки его вызовов из `tests/integration/user_tests/removed_operations_test.py`; сохранить изоляцию repository/publisher/blacklist/token provider.
- [X] T005 Выполнить сбор тестов для `tests/unit` и `tests/integration` и устранить только оставшиеся зависимости тестов от FakeStorage в `tests/`; подтвердить, что `tests/adapters/cache_service.py` с token-blacklist `.storage` сохраняется, а текущая личность и form-login fixtures в `tests/integration/conftest.py` не изменены; результаты записать в `specs/002-remove-s3-images/validation.md`.

**Checkpoint**: Тесты собираются без FakeStorage. Изменение действующего кода и выходного профиля относится к следующим историям.

## Phase 3: User Story 1 — Запуск без хранилища изображений (Priority: P1)

**Goal**: Устранить runtime зависимость от AWS, сохранив регистрацию, аутентификацию и операции собственного профиля.

**Independent Test**: Config создаётся без AWS и с устаревшими пустыми AWS-полями; приложение импортируется без S3-клиента; form-login и оставшиеся сценарии работают. Окончательная production startup проверка выполняется T031 после новой базовой миграции US3.

### Tests for User Story 1

- [X] T006 [US1] Добавить `tests/unit/settings_config_test.py`: в изолированном временном рабочем каталоге с корректными настройками оставшихся зависимостей проверить Config/get_settings без AWS, с пустыми и устаревшими AWS-полями и отсутствие Config.storage; очищать/восстанавливать lru_cache и окружение через типизированные fixtures, не читать реальные секреты `.env`; подтвердить падение на существующем StorageConfig.

### Implementation for User Story 1

- [X] T007 [US1] Удалить POST/GET/DELETE `/me/image` и связанные imports/Depends из `source/presentation/api/routes/user_router.py`; сохранить GET/PATCH/DELETE `/me`, подтверждённый subject и неизменные статусы; не вводить заглушки, redirects или новый файловый маршрут.
- [X] T008 [US1] Удалить SetUserImage/GetUserImage/DeleteUserImage из `source/application/use_cases/user_use_cases.py`, их импорты/экспорты в `source/application/use_cases/__init__.py`, `source/application/interfaces/storage.py` и экспорт IStorage в `source/application/interfaces/__init__.py`; сохранить require_user, токены и остальные use case.
- [X] T009 [US1] Удалить get_storage, импорты S3 Session/адаптера и три image use case factories из `source/presentation/api/dependencies/adapters.py`, `source/presentation/api/dependencies/user_deps.py`, `source/presentation/api/dependencies/__init__.py`; сохранить сборку repo/hasher/token/cache/broker и доступ через текущую личность.
- [X] T010 [P] [US1] Удалить UploadImageError/DeleteImageError/UserHasNoImageError/ImageReceivingError и exports из `source/application/exceptions/user_exceptions.py` и `source/application/exceptions/__init__.py`; убрать их imports и image-only maps из `source/presentation/exceptions.py`, сохранив общий ERROR_STATUS для оставшихся ошибок и прежний handler.
- [X] T011 [P] [US1] Удалить `source/infrastructure/storage/__init__.py`, `source/infrastructure/storage/session.py`, `source/infrastructure/storage/storage_adapter.py`; удалить только MAX_FILE_SIZE и ALLOWED_MIME_TYPES из `source/settings/constansts.py`, сохранив константы очередей и exchange RabbitMQ; не добавлять очистку объектов AWS.
- [X] T012 [P] [US1] Удалить `source/settings/separated_configs/storage_config.py`, экспорт StorageConfig в `source/settings/separated_configs/__init__.py` и Config.storage/import в `source/settings/config.py`; сохранить общий `extra="ignore"` в `source/settings/separated_configs/base.py` и обязательность PostgreSQL/Redis/RabbitMQ/JWT.
- [X] T013 [US1] Удалить только aioboto3==15.5.0 и types-aioboto3[s3]==15.5.0 из `pyproject.toml`, пересчитать `uv.lock` через uv lock и проверить frozen установку; сохранить python-multipart==0.0.22 для OAuth2PasswordRequestForm в `source/presentation/api/routes/auth_router.py`, общие транзитивные зависимости и остальные версии без сопутствующего upgrade (после T009–T012).
- [X] T014 [P] [US1] Удалить четыре AWS-настройки и комментарии из `.env.example`, а также фиктивные AWS-переменные app_test из `docker-compose.test.yaml`; проверить отсутствие AWS в `.env.test.example`, сохранив PostgreSQL/Redis/RabbitMQ/JWT, tmpfs и startup профиль; локальные секреты `.env` не публиковать.
- [X] T015 [US1] Обновить `README.md`: убрать S3-настройки, image endpoints, форматы/лимиты файлов и обслуживание изображения; сохранить инструкции form-login, refresh и reset-password; согласовать сетевые инструкции с фактическим `docker-compose.yaml`, где shared_net закомментирована и POSTGRES_DB получает POSTGRES_NAME.
- [X] T016 [US1] Проверить T006, импорт `source/main.py` и оставшиеся сценарии тестами из `tests/integration/auth_tests` и `tests/integration/user_tests/get_current_user_test.py`, `tests/integration/user_tests/edit_current_user_test.py`, `tests/integration/user_tests/delete_current_user_test.py` без AWS-зависимости; подтвердить удаление аккаунта без AWS и записать результат в `specs/002-remove-s3-images/validation.md` (после T007–T015).

**Checkpoint / MVP**: Runtime больше не требует AWS или S3, удалённые image-маршруты не вызывают отсутствующие зависимости. Это минимальный проверяемый технический срез; nullable image-поля старой модели до US2 и старый baseline до US3 означают, что функция целиком ещё не готова к выпуску.

## Phase 4: User Story 2 — Учётная запись без изображения (Priority: P1)

**Goal**: Удалить изображение из домена, данных и контрактов регистрации/профиля; сохранить общие правила доступа и валидации.

**Independent Test**: Проверить точные ключи signup/GET/PATCH, игнорирование legacy image input, 404 трёх image операций с bearer и без него, отсутствие image-схем в OpenAPI и прежние правила текущей личности. Физический состав новой базы дополнительно проверяется US3.

### Tests for User Story 2

- [X] T017 [P] [US2] Расширить `tests/integration/user_tests/removed_operations_test.py`: POST/GET/DELETE `/api/v1/users/me/image` возвращают 404 с bearer и без, не меняют оба профиля; ожидать ровно 8 HTTP-операций (7 пользовательских+healthcheck) и отсутствие ImageResponse/ImageUploadResponse/image_s3_path/image_url в OpenAPI; сохранить прежние отрицательные проверки чужих операций и групп (после T016).
- [X] T018 [P] [US2] Обновить `tests/integration/auth_tests/signup_user_test.py`, `tests/integration/user_tests/get_current_user_test.py`, `tests/integration/user_tests/edit_current_user_test.py`: signup/GET имеют ровно 8 ключей UserResponse, PATCH — 5 UserEditResponse, ни одного image-поля даже null; сохранить legacy image_s3_path/id inputs как проверки игнорирования, дополнить PATCH только неизвестными полями проверкой неизменного профиля (после T016).
- [X] T019 [P] [US2] Обновить `tests/unit/user_usecases_tests/register_user_test.py` и `tests/unit/user_usecases_tests/get_current_user_from_db_test.py`: проверять UserReadDTO без атрибута изображения и с прежними данными; убрать создание пользователей с image_s3_path, сохранив проверки личности и валидации (после T016).

### Implementation for User Story 2

- [X] T020 [US2] Удалить image_s3_path из `source/domain/entities/user.py` и `source/application/dto/users_dto.py`; сохранить «2–20 символов; латиница/кириллица, дефис, апостроф» для name/surname, «8–20» и действующее множество символов RawPassword, email «Прежняя доменная проверка; HTTP EmailStr; уникальность», username «Уникален; прежние правила без новых ограничений», phone_number «Необязателен; прежние правила без нового формата», id «Создаётся сервисом; не редактируется входными полями» и updated_at «None до обновления; дата обновления при изменении» из `specs/002-remove-s3-images/data-model.md`; не добавлять новые ограничения (после T017–T019).
- [X] T021 [US2] Удалить преобразование image_s3_path из `source/application/use_cases/base.py` и аргумент/значение image_s3_path из `tests/unit/utils/shared_data.py`; сохранить typed преобразование UserEntity → UserReadDTO с 8 полями и существующие from_trusted/UTC правила (после T020).
- [X] T022 [P] [US2] Удалить image_s3_path из `source/infrastructure/database/models/users.py` и read/add/update mappings в `source/infrastructure/database/user_repository.py`; сохранить «UUID primary key, NOT NULL», «String, NOT NULL» для обязательных строк, «String, nullable, UNIQUE» для phone_number, «DateTime, NOT NULL» для created_at и «DateTime, nullable» для updated_at, уникальные username/email и UTC-преобразования (после T020–T021).
- [X] T023 [P] [US2] Удалить image_s3_path из UserResponse в `source/presentation/api/schemas/auth.py` и UserEditResponse в `source/presentation/api/schemas/user.py`, удалить ImageResponse/ImageUploadResponse и их exports в `source/presentation/api/schemas/__init__.py`, если имеются; сохранить nullable phone_number/updated_at, `extra="ignore"`, from_attributes=True и прежние входные JSON-схемы из `source/presentation/api/schemas/base.py` (после T020–T021).
- [X] T024 [US2] Выполнить затронутые unit/HTTP проверки T017–T019 и прежнюю регрессию `tests/unit/current_subject_test.py`, `tests/unit/domain_invariants_test.py`, `tests/unit/token_provider_test.py`, `tests/integration/user_tests/delete_current_user_test.py`; подтвердить отсутствие полей и сохранение формата ошибок/идентичности, записать результаты в `specs/002-remove-s3-images/validation.md` (после T022–T023).
- [X] T025 [US2] Проверить `source/presentation/api/routes/auth_router.py`, `source/presentation/api/dependencies/auth.py` и `source/application/use_cases/user_use_cases.py` по `specs/002-remove-s3-images/contracts/http-api.md`: form-login и HttpOnly refresh-cookie сохранены, вращение/replay действуют, id из запроса не заменяет subject, удалённый пользователь не получает доступ по прежнему токену; подтвердить существующими тестами `tests/integration/auth_tests` и `tests/integration/user_tests`, без несвязанных изменений (после T024).

**Checkpoint**: Публичный профиль и все активные модели не содержат изображений; отсутствующие маршруты дают 404. Старый baseline ещё не является контрактом новой установки: закончить US3 перед выпуском.

## Phase 5: User Story 3 — Чистая установка (Priority: P2)

**Goal**: Создать пустую базу без изображения и подтвердить реальные startup/persistence сценарии без AWS.

**Independent Test**: На отдельном PostgreSQL применить новый baseline, проверить 9 столбцов и ноль исходных аккаунтов, выполнить регистрацию/редактирование, перезапустить только приложение и проверить прежние учётные данные и сохранённый профиль.

### Tests for User Story 3

- [X] T026 [P] [US3] Обновить `tests/integration/settings/fresh_schema_test.py`: ровно 9 столбцов users без image_s3_path, таблицы users+alembic_version, единственный root/head revision users_no_images_20260927, 0 пользователей до регистрации, username/email/phone_number уникальны, phone_number/updated_at nullable, сохранены UTC round-trip и отсутствуют bootstrap данные; подтвердить падение проверки схемы на прежнем baseline (после T025).
- [X] T027 [P] [US3] Обновить `tests/integration/settings/startup_test.py`: без storage overrides/AWS проверить production entrypoint, отсутствие image-полей signup/GET/PATCH и OpenAPI, 404 трёх удалённых image операций с bearer и без, прежние form-login/refresh-replay/reset-password и очистку двух тестовых аккаунтов; исключить ожидание nullable image-поля (после T025).

### Implementation for User Story 3

- [X] T028 [US3] Заменить `source/infrastructure/database/alembic/versions/2026_09_26_users_baseline.py` новым `source/infrastructure/database/alembic/versions/2026_09_27_users_without_images_baseline.py`: revision users_no_images_20260927, down_revision=None, единственный root/head, users без image_s3_path, прежние NOT NULL/nullable, PK и ix_users_username/users_email_key/users_phone_number_key; не добавлять update старой базы, stamping или вызовы AWS (после T026–T027).
- [X] T029 [US3] Дополнить `README.md` инструкцией новой пустой базы и допустимой потери аккаунтов; согласовать с `specs/002-remove-s3-images/quickstart.md` новый revision и процедуру определения/удаления только подтверждённого PostgreSQL volume при реальном переходе, без общего down -v, удаления Redis volume или очистки AWS; сам основной volume этой задачей не пересоздавать (после T028).
- [X] T030 [US3] Проверить `tests/integration/settings/fresh_schema_test.py` и `tests/integration/settings/real_services_test.py` на одноразовых PostgreSQL/Redis/RabbitMQ из `docker-compose.test.yaml`: новый baseline, constraints/UTC, реальный отзыв/TTL refresh и публикация reset-password без обязательного AWS; пропуски реальных сервисов не объявлять успехом, результат записать в `specs/002-remove-s3-images/validation.md` (после T028–T029).
- [X] T031 [US3] Собрать и поднять startup-профиль `docker-compose.test.yaml` в отдельном проекте через текущие `Dockerfile` и `scripts/entry.sh` без AWS-переменных; проверить healthcheck и выполнить `tests/integration/settings/startup_test.py` с UMS_TEST_APP_URL и UMS_TEST_POSTGRES_URL, без skip и S3 overrides; записать результат в `specs/002-remove-s3-images/validation.md` (после T030).
- [X] T032 [US3] Выполнить persistence сценарий раздела 4 `specs/002-remove-s3-images/quickstart.md`: создать аккаунт, изменить профиль с legacy image input, перезапустить только app_test, повторно войти и подтвердить UUID/имя/отсутствие изображения; удалить созданный аккаунт и записать фактический результат в `specs/002-remove-s3-images/validation.md` (после T031).

**Checkpoint**: Новая установка соответствует модели, production lifespan не требует AWS, изменённый профиль сохраняется после restart приложения. Существующая наполненная база остаётся неподдерживаемым путём.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Подтвердить полноту удаления и готовность изменения с единым отчётом.

- [X] T033 Выполнить контекстный аудит `source/`, `tests/`, `pyproject.toml`, `uv.lock`, `.env.example`, `.env.test.example`, `docker-compose.test.yaml`, `docker-compose.yaml`, `Dockerfile`, `scripts/entry.sh` и `README.md`: нет активных S3/image imports, полей, настроек, SDK, fake adapter или orphan exports; legacy термины допустимы в отрицательных тестах/инструкции перехода/исторических specs, Docker image и token-blacklist storage сохраняются; результат записать в `specs/002-remove-s3-images/validation.md`.
- [X] T034 Выполнить Ruff format/check и mypy strict для `source/`, `tests/`, `scripts/` согласно `pyproject.toml`; исправить только относящиеся к удалению ошибки без Any/новых suppressions и зафиксировать команды и исходы в `specs/002-remove-s3-images/validation.md`.
- [X] T035 Выполнить итоговую полную регрессию `tests/unit` и `tests/integration` с реальными одноразовыми PostgreSQL/Redis/RabbitMQ; startup тест запускать на пустой public.users с корректным UMS_TEST_APP_URL, при необходимости отдельной командой по `specs/002-remove-s3-images/quickstart.md`; учесть изменения после T034 и записать фактические passed/failed/skipped в `specs/002-remove-s3-images/validation.md`, не переносить старое число 122.
- [X] T036 Сверить реализованное поведение с `specs/002-remove-s3-images/spec.md`, `specs/002-remove-s3-images/plan.md`, `specs/002-remove-s3-images/contracts/http-api.md`, `specs/002-remove-s3-images/data-model.md`, `specs/002-remove-s3-images/quickstart.md` и `.specify/memory/constitution.md`; обновить статусы/устаревшие инструкции по факту, сохранить историю 001 и не менять отмеченный пользователем объём функции.
- [X] T037 Завершить только одноразовый проект по `docker-compose.test.yaml` и очистить UMS_TEST_* переменные согласно `specs/002-remove-s3-images/quickstart.md`; убедиться, что основной Compose, Redis volume и внешние AWS объекты не изменены, результат зафиксировать в `specs/002-remove-s3-images/validation.md`.
- [X] T038 Завершить `specs/002-remove-s3-images/validation.md`: связать каждый FR/SC с фактическими тестами/аудитом, указать оставшиеся риски и непроведённые проверки; отметить задачи `specs/002-remove-s3-images/tasks.md` только по выполненным результатам и выполнить git diff --check для изменённых файлов, не создавать commit/PR автоматически.

## Dependencies & Execution Order

### Phase Dependencies

```text
Setup T001–T003
  → Foundational T004–T005
    → US1 T006–T016 (P1)
      → US2 T017–T025 (P1)
        → US3 T026–T032 (P2)
          → Polish T033–T038
```

- US1 включает удаление image-маршрутов и их прикладной сборки: без этого удаление S3-клиента оставляет сломанные импорты. Проверка профиля без image-полей относится к US2.
- US2 использует согласованную сборку без storage из US1. Её HTTP/доменные результаты проверяются отдельно; физическая схема новой базы зависит от US3.
- US3 использует модель US2 и поставку US1. T031 одновременно завершает проверку production части US1, а T032 подтверждает SC-004.
- Замена baseline не переносится в setup: это явная работа US3. До неё не запускать новую production установку как готовый результат функции.
- Сначала писать соответствующие отрицательные тесты и фиксировать ожидаемое падение; затем реализация; затем green-проверка. Удаление импортов внутри одной последовательной группы может временно нарушить collection — не объявлять такую промежуточную точку готовой историей.

### Parallel Opportunities and Examples

Параллельность описывает допустимое распределение файлов при реализации; текущий шаг не запускает исполнителей.

| История | Предпосылки | Задачи для параллельного выполнения | Почему безопасно |
|---|---|---|---|
| US1 | T009 завершена | T010 + T011 + T012 + T014 | Ошибки, удаляемые storage/константы, настройки и env/Compose — разные файлы; T013 ждёт завершения удаления импортов |
| US2 | T016 завершена | T017 + T018 + T019 | Разные файлы HTTP и unit проверок; каждый тестовый набор фиксирует свою границу |
| US2 | T020–T021 завершены | T022 + T023 | ORM/репозиторий и HTTP-схемы — разные файлы; оба используют уже сокращённые домен/DTO |
| US3 | T025 завершена | T026 + T027 | Проверки схемы и production startup находятся в разных файлах |

Общие fixtures (T004), README (T015/T029), dependency exports и `validation.md` менять последовательно. В параллельных задачах результаты собирать в память/отдельные выводы; единый отчёт обновлять после группы. Реальные DB/startup проверки выполнять последовательно, чтобы не нарушить требование пустой public.users.

## Requirements Coverage

| Требования / критерии | Основные задачи |
|---|---|
| FR-001–002 / SC-003 | T007–T011, T017, T027, T031 |
| FR-003–004 / SC-003–004 | T018–T024, T026–T028, T032 |
| FR-005–006 / SC-001 | T004–T016, T031, T033 |
| FR-007 / SC-002 | T016, T019–T025, T027, T030–T031, T035 |
| FR-008 / SC-004 | T026, T028–T032 |
| FR-009 / SC-005 | T014–T015, T029, T036 |
| FR-010 | T008–T013, T016, T030–T033, T037 |

## Implementation Strategy

### MVP First

Закончить setup/foundation и US1, подтвердить запуск конфигурации и оставшиеся сценарии без AWS. Это первый полезный внутренний результат. Полный выпуск функции требует US2 и US3: нельзя объявлять удаление изображений завершённым при остающихся nullable полях или прежнем baseline.

### Incremental Delivery

1. Общие fixtures перестают зависеть от FakeStorage.
2. US1 убирает runtime/S3 и обязательность AWS.
3. US2 сокращает доменные/публичные данные и закрепляет 404/ignore контракты.
4. US3 создаёт правильную пустую базу и подтверждает production startup/persistence.
5. Общие проверки и отчёт подтверждают весь объём. Не разворачивать новый основной Compose и не пересоздавать его volume автоматически в рамках задачи генерации.

## Notes

- Всего 38 задач: setup 3, foundation 2, US1 11, US2 9, US3 7, polish 6.
- Восемь поддерживаемых HTTP-операций — семь пользовательских и healthcheck; login остаётся формой.
- Для отсутствия атрибута недостаточно значения None: он должен исчезнуть из моделей, схем и ответов.
- Новый baseline использует другой revision; не stamp старую базу и не сохранять старый revision под изменённой схемой.
- Изменение библиотек ограничено S3; `python-multipart`, `aio-pika` и token-blacklist storage сохраняются.
- Каждая история имеет наблюдаемые критерии проверки, но порядок реализации определяется реальными сквозными зависимостями выше.
