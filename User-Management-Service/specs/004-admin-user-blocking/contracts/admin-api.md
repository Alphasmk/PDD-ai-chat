# HTTP и startup contracts

Префикс `/api/v1`. Формат ошибок сохраняется: `{"error":"..."}`; новые стабильные значения error перечислены ниже. Вход: существующий Bearer access token. Актуальные права проверяются в сценарии до поиска цели. Ошибки синтаксиса могут возвращаться до проверки прав, но не раскрывают существование цели.

## Общий перечень ролей

`GET /roles`, любой вошедший незаблокированный аккаунт, 200:

```json
{"items":[{"value":"user","label":"Пользователь"},{"value":"admin","label":"Администратор"}]}
```

UserRole в общих выходных схемах включает только user/admin. Суперадмин имеет role=admin и is_superadmin=true. GET /roles читает две записи таблицы roles. Перечень не является редактируемым справочником. Наличие значения в нём не даёт права назначать эту роль.

## Список

`GET /users?limit=50&offset=0`, только admin/superadmin. limit: integer 1..100, offset: integer >=0. Порядок created_at ASC, id ASC. 200:

```json
{"items":[{"id":"fba73eea-1f75-4f9a-9a9e-100000000001","name":"Иван","surname":"Иванов","username":"ivan","email":"ivan@example.com","role":"user","is_blocked":false,"is_superadmin":false}],"limit":50,"offset":0}
```

Полный набор полей записи показан выше. Нет телефона, password_hash и токенов. Пустая страница возвращает items=[]. Не обещается snapshot при изменениях между страницами.

## Назначение и снятие администратора

`PATCH /users/{user_id}/role`, только superadmin. UUID цели; тело строго `{"role":"admin"}` или `{"role":"user"}`. Extra fields запрещены. 200: `{"id":"<uuid>","role":"admin","is_blocked":false,"is_superadmin":false}` (фактические значения).

role=superadmin и неизвестное значение: 422 `invalid_role`; никакая операция назначения superadmin не существует. Цель superadmin при запросе user/admin: 409 `protected_account`. Назначение admin заблокированному user: 409 `invalid_target_state`. Повторное допустимое значение успешно, включая user для заблокированного user; блокировка сохраняется. Эффект действует после commit, новые обращения прежних сеансов используют новые права.

## Блокировка

`POST /users/{user_id}/block`, только admin/superadmin, без тела. 200: `{"id":"<uuid>","role":"user","is_blocked":true,"is_superadmin":false}`. Повторная блокировка успешна. Цель admin: 409 `invalid_target_state`; цель superadmin: 409 `protected_account`. Разблокировки нет.

## Общие ошибки новых операций

| HTTP | error | Условие |
|------|-------|---------|
| 401 | существующая ошибка аутентификации | Нет/невалидный/истёкший токен |
| 403 | forbidden | Недостаточно прав |
| 403 | user_blocked | Инициатор заблокирован |
| 404 | user_not_found | Цель отсутствует, только после проверки прав |
| 409 | protected_account / invalid_target_state | Запрещённое состояние цели |
| 422 | invalid_role / invalid_request | Недопустимое новое тело, UUID или параметры страницы |
| 503 | service_unavailable | Невозможно проверить актуальное состояние или завершить транзакцию |

Существующие сообщения старых маршрутов сохраняются. Новые ошибки валидации нормализовать локально для новых контрактов, не менять глобально старые 422. Не возвращать SQL, параметры подключения и секреты в error. Ошибка commit не должна давать 2xx.

## Существующие маршруты

Signup и PATCH /users/me продолжают игнорировать неизвестные поля согласно существующему Base; role/is_blocked/is_superadmin из запроса не применяются. В ответы signup, GET /users/me и PATCH /users/me добавить role/is_blocked/is_superadmin с общей двухзначной схемой роли; существующие профильные поля сохранить. DELETE /users/me суперадмина: 409 protected_account. Для заблокированного аккаунта все защищённые действия и refresh: 403 user_blocked. Login: неверные credentials — прежний 401; корректные credentials заблокированного — 403 user_blocked. Формат токенов и cookie refresh остаётся прежним. Запрос восстановления пароля публичный и не меняет состояние.

## Инициализация контейнера

`python -m scripts.initialize_service` — команда startup runner; entry.sh вызывает её вместо отдельного alembic upgrade head, после успеха выполняет exec приложения. Runner использует существующее подключение PostgreSQL и собственные настройки bootstrap. Обязательные при первом создании переменные: SUPERADMIN_USERNAME, SUPERADMIN_EMAIL, SUPERADMIN_PASSWORD, SUPERADMIN_NAME, SUPERADMIN_SURNAME. Значения профиля и пароля проходят текущие доменные проверки. Телефон null. Пароль не принимается в argv, не печатается и не сохраняется открытым текстом в БД.

Lock 74004001 охватывает миграции и bootstrap на выделенном соединении, timeout 60 секунд. Код 0 — схема готова и ровно один superadmin существует; ненулевой код — приложение не запускается. Категории диагностики: missing_initial_data, invalid_initial_data, identity_conflict, database_unavailable, initialization_timeout. Ошибки не включают входные значения. Существующий superadmin сохраняется; переменные bootstrap могут отсутствовать или измениться, они не применяются. Переименование его профиля не приводит к созданию нового аккаунта: поиск идёт по is_superadmin=true.
