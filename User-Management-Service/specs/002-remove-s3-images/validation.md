# Validation: полное удаление изображений пользователя и AWS S3

**Date**: 2026-09-27
**Status**: Выполнено — 38/38 задач, итоговые проверки успешны.
**Related**: [spec.md](spec.md), [plan.md](plan.md), [tasks.md](tasks.md), [contracts](contracts/http-api.md), [quickstart](quickstart.md).

## Result

Удалены три операции изображения, поле image_s3_path во всех активных слоях, image схемы/ошибки/константы, IStorage, S3 адаптер и его сборка, StorageConfig, AWS-примеры и фиктивное startup окружение. uv lock удалил 23 S3-only пакета без добавления пакетов или обновления остальных версий. python-multipart сохранён для form-login.

Новый единственный baseline `users_no_images_20260927` создаёт пустую users без изображения; остаются 9 столбцов, прежние ограничения уникальности и UTC. Открытая поверхность — 7 пользовательских операций и healthcheck. Старые операции изображений возвращают обычный 404 с bearer и без него; legacy JSON-поля игнорируются и не возвращаются.

## Commands and Evidence

| Проверка | Результат |
|---|---|
| Checklist gate | requirements.md 16/16; файл и маркеры при реализации не изменялись |
| Context / ignores | Конституция 4.0.0 согласована; .gitignore/.dockerignore покрывают Python caches, .venv, секреты и служебные документы |
| `uv run pytest tests/unit tests/integration --collect-only -q` после удаления FakeStorage | 106 тестов собраны без ошибок |
| RED config tests | 3 ожидаемых падения на обязательном StorageConfig и сохранявшемся атрибуте storage |
| `uv lock`, `uv sync --frozen` | Успех; 23 пакета удалены, 0 добавлено, 0 изменений оставшихся версий |
| Config + auth/profile checkpoint | 37 passed; конфигурация без AWS и с пустыми/устаревшими значениями |
| RED DTO / HTTP / OpenAPI | 5 ожидаемых падений из-за сохранившегося поля изображения до изменения моделей |
| US2 regression checkpoint | 104 passed / 1 failed: устаревший позиционный image аргумент make_user в update_user_test; исправлен, 4 теста этого файла прошли |
| RED fresh schema | 2 ожидаемых падения на старом image столбце и revision до замены baseline |
| PostgreSQL schema + real Redis/RabbitMQ | 4 passed, 0 skipped; случайные схемы, constraints/UTC, refresh blacklist/TTL и reset publication |
| `uv run ruff format source tests scripts` | 5 файлов отформатировано; остальные 117 без изменений |
| `uv run ruff check source tests scripts` | All checks passed |
| `uv run mypy source tests scripts` | Success, 122 source files, strict включён |
| Compose startup build | Production Dockerfile frozen/no-dev, entry.sh/Alembic и lifespan успешны без AWS |
| `uv run pytest tests/integration/settings/startup_test.py -q` с test APP/PG URL | 1 passed, 0 skipped; реальные bearer/form/token/profile/reset сценарии и удалённые маршруты |
| Container runtime inspection | AWS variables=False; aioboto3/boto3/botocore installed=False |
| Persistence guide section 4 | Создание, изменение и повторный login после restart только app_test успешны; UUID сохранён, имя Jane сохранено, image поля отсутствуют, тестовый аккаунт удалён |
| `uv run pytest tests/unit tests/integration -q --tb=short --cov=source --cov-report=term --cov-report=json:.coverage-report.tmp` | **125 passed, 0 failed, 0 skipped**, 59.08 s; реальные PostgreSQL/Redis/RabbitMQ и production startup включены |
| Coverage | 87% overall (704/806 statements), user_use_cases 98% (100/102); покрытие pytest процесса, контейнерный lifespan отдельно подтверждён HTTP-проверкой |
| Narrow legacy audit | Нет совпадений в source, pyproject.toml, uv.lock, env примерах и startup Compose для удалённых портов/SDK/полей/настроек/ошибок |
| Documentation | Локальные ссылки корректны; README содержит новый контракт, пустую базу, потерю аккаунтов и ограниченный переход |
| Cleanup | Только ums-no-images-validation завершён; 0 контейнеров этого проекта осталось, tmpfs данные удалены |
| `git diff --check` | Успех; предупреждение Git о будущем LF→CRLF uv.lock не является ошибкой whitespace |

Одноразовый проект использовал PostgreSQL 16, Redis 7 и RabbitMQ 4 на localhost:5434/6380/5673, приложение :8001. Файл .env.test совпадал с одноразовым примером; реальные секреты не выводились. Стандартные sandbox ограничения запуска uv/docker преодолены разрешённой escalation; отказа автоматической проверки действий не было.

## Requirements Traceability

| Requirement | Evidence / Outcome |
|---|---|
| FR-001 | Image use cases, IStorage и адаптер удалены; нет альтернативного хранилища; removed_operations/OpenAPI проверки проходят |
| FR-002 | Три me/image метода возвращают 404 с bearer и без; HTTP integration и production startup |
| FR-003 | Точный состав signup/GET — 8 полей, PATCH — 5; нет nullable image поля |
| FR-004 | Entity/DTO/ORM/repository без поля; чистая PG users без image столбца; legacy JSON input не меняет профиль |
| FR-005 | 3 config сценария и production startup без AWS; внутри контейнера отсутствуют AWS variables и S3 SDK |
| FR-006 | Нет image-only runtime компонентов, fixtures/адаптера, настройки или S3 roots; lock/frozen build успешны |
| FR-007 | Итоговые 125 тестов включают 7 оставшихся сценариев, form login, token replay/TTL, конфликты, инварианты и собственный subject |
| FR-008 | Один root/head users_no_images_20260927; users+alembic_version, 0 начальных аккаунтов, 9 столбцов; перенос не выполняется |
| FR-009 | README/env/Compose обновлены; инструкция явно описывает новую пустую базу, потерю аккаунтов и только подтверждённый PG volume |
| FR-010 | Нет SDK/адаптера/конфигурации или пути вызовов AWS; удаление аккаунта в production без AWS успешно; внешние объекты не изменялись |
| SC-001 | Config и стандартный production контейнер стартуют без настройки хранилища; тестовый startup healthy |
| SC-002 | Все итоговые проверки успешны; 7 оставшихся сценариев подтверждены без image интеграции |
| SC-003 | Ровно 8 опубликованных HTTP операций; все 3 image операции недоступны; 0 image атрибутов в профиле |
| SC-004 | Чистая PG установка и restart только приложения сохраняют созданный аккаунт/изменённый профиль без изображения |
| SC-005 | Актуальные инструкции запуска/env примеры без настройки хранилища; потеря старых аккаунтов явно описана |

## Limits and Transition

- Не выполненных обязательных проверок нет; финальный прогон без skips. RED-падения и исправленная устаревшая фикстура выше относятся к промежуточным этапам, не к итоговому результату.
- Production Compose и основной PostgreSQL volume не изменены и не пересоздавались. Новая версия требует пустую базу; перенос старых аккаунтов или stamping прежней схемы не поддерживаются согласно решению пользователя.
- Старые объекты AWS не очищались; интеграция отсутствует в приложении. Это не скрытый перенос в другое хранилище.
- Исторические документы 001, конституционные решения прежней даты и отрицательные legacy тесты сохранены. Docker image и token-blacklist storage не относятся к изображениям пользователя.
- Commit/PR не создавались. Проверка post-implement hooks выполнена: .specify/extensions.yml отсутствует.
