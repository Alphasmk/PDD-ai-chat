# HTTP contract: действующие операции

**Date**: 2026-09-27 | **Status**: существующий API; изменений в 003 нет.

## Точный набор операций

| Метод | Путь | Успех | Назначение |
|---|---|---|---|
| POST | /api/v1/auth/signup | 201 | Регистрация |
| POST | /api/v1/auth/login | 200 | Вход формой username/password |
| POST | /api/v1/auth/refresh-token | 200 | Ротация refresh из cookie; прежние требования bearer |
| POST | /api/v1/auth/reset-password | 200 | Публикация запроса восстановления |
| GET | /api/v1/users/me | 200 | Собственный профиль |
| PATCH | /api/v1/users/me | 200 | Изменение собственного профиля |
| DELETE | /api/v1/users/me | 200 | Удаление собственного профиля |
| GET | /healthcheck | 200 | Готовность |

Сравнивать набор пар path/method OpenAPI с этим списком. Любая дополнительная операция вызывает ошибку проверки. /docs и /openapi.json не являются операциями бизнес-API в OpenAPI.

## Точные формы данных

| Форма | Поля |
|---|---|
| Signup JSON | name, surname, username, password, email, phone_number |
| Полный профиль signup / GET | id, name, surname, username, email, phone_number, created_at, updated_at |
| PATCH JSON / response | name, surname, username, email, phone_number |
| DELETE response | id, username, email |
| Token response | access_token, refresh_token, token_type |
| Reset request / response | email / message |

Signup phone_number необязателен; все поля PATCH необязательны. Неизвестные поля игнорируются существующим extra="ignore". Ответы проверяются точным набором свойств.

## Сохраняемые правила

- Login принимает application/x-www-form-urlencoded; python-multipart остаётся необходимым.
- Me использует подтверждённого существующего bearer-субъекта. Неизвестный id JSON не выбирает аккаунт.
- Unknown-only и пустой PATCH не изменяют профиль и даты.
- Refresh rotation, Redis-отзыв, cookie, TTL и replay rejection сохраняются.
- Reset-password сохраняет существующую публикацию RabbitMQ без новых возможностей восстановления.
- Domain/Application ошибки сохраняют JSON `{ "error": "..." }` и текущие статусы 400/401/404/409. Стандартные HTTP/Pydantic ошибки, включая 422, сохраняют формат.

Валидация, уникальность, отсутствие auth и удалённый субъект проверяются прежними тестами. Контракты не расширяются.
