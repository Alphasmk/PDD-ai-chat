# Test contract: очистка без ослабления проверок

**Date**: 2026-09-27 | **API**: [http-api.md](http-api.md) | **Model**: [../data-model.md](../data-model.md)

## Изменения существующих проверок

| Файл относительно корня | Очистка | Сохраняемая проверка |
|---|---|---|
| tests/unit/settings_config_test.py | Специальный обход env, тройная параметризация, устаревший dotenv и атрибут | Точные 5 секций Config, значения, кеширование, cache_clear и временный cwd |
| tests/unit/user_usecases_tests/register_user_test.py | Специальный hasattr | dataclasses.fields(result) соответствует фиксированным 8 полям DTO; hash/email прежние |
| tests/unit/user_usecases_tests/get_current_user_from_db_test.py | Специальный hasattr | DTO8; id текущего субъекта; ошибка после его удаления |
| tests/integration/auth_tests/signup_user_test.py | Устаревшее поле заменить нейтральным | Поля8, значения и ошибки регистрации |
| tests/integration/user_tests/edit_current_user_test.py | Специальные данные/assertions, переименование сценариев | PATCH5, Alice.id; Bob прежний; unknown-only/empty PATCH сохраняют полные профили/даты |
| tests/integration/user_tests/removed_operations_test.py | 6 image пар method/path и 4 image термина | Allowlist8, signup/PATCH inputs6/5; прочие отрицательные запросы с/без auth и оба профиля |
| tests/integration/settings/startup_test.py | Специальные термины и цикл старых запросов | Опубликованные операции8, профили8/5, subject isolation, login, rotation/replay, publisher, cleanup |

Unit expected-наборы фиксируются требованиями, не вычисляются из той же проверяемой модели. Для OpenAPI используются object и isinstance; без Any, type: ignore и новых suppressions.

Unknown-only сценарий создаёт Alice/Bob, сохраняет два профиля, передаёт unsupported_field с id/user_id Bob и сравнивает оба полных профиля после запроса. Mixed PATCH дополнительно подтверждает Alice.id. Пустой PATCH проверяет равенство профиля/дат, а не только статус.

## Границы аудита

Проверяются тесты, фикстуры, имена сценариев и данные. Специальных понятий FR-001–003 не должно оставаться. Запрещено обходить аудит аббревиатурами/сборкой удалённых строк.

Разрешены исторические migration filename/revision и проверки их стабильности, исторические specs/validation, Docker image: и token blacklist .storage. Совпадения классифицируются по контексту; целый файл теста не исключается из аудита.

В quickstart002 обновить активные ожидаемые результаты, PATCH/persistence и оговорку про старые названия в действующих тестах. Исторические отчёты/требования сохранить. Новый guide003 не требует новой схемы/reset; README направляет на него.

## Соответствие требованиям

| Требования / критерии | Доказательство при реализации |
|---|---|
| FR-001–003, SC-001 | Аудит активных тестов, 7 файлов; нет специальных данных/сценариев |
| FR-004–005, SC-002 | Фиксированные profile8/PATCH5/operations8, включая production OpenAPI |
| FR-006–007, SC-003 | Neutral unknown/empty, даты/чужой профиль; регрессия 7 сценариев |
| FR-008, SC-004 | Актуальные примеры, Config, startup с реальными сервисами |
| FR-009–010 | Stable baseline/revision, persistence после app restart, обзор diff/истории |

Все оставшиеся проверки должны проходить. Фактическое число может уменьшиться. Skips/failures и недоступные интеграции отражаются в отчёте003, не выдаются за успех.
