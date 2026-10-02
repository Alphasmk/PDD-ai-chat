# HTTP API contract: сервис без изображений

**Date**: 2026-09-27
**Status**: Реализован и проверен; результаты в [validation.md](../validation.md).
**Related**: [spec.md](../spec.md), [data model](../data-model.md).

## Supported operations

Все пользовательские операции имеют префикс `/api/v1`. Всего 7 пользовательских операций; технический healthcheck — восьмая.

| Метод и путь | Вход / доступ | Успех |
|---|---|---|
| POST `/api/v1/auth/signup` | JSON UserSignupRequest, публичный | 201 UserResponse |
| POST `/api/v1/auth/login` | Form username/password, публичный | 200 TokenResponse + HttpOnly cookie refresh_token |
| POST `/api/v1/auth/refresh-token` | Bearer-заголовок и cookie refresh_token | 200 TokenResponse + новая HttpOnly cookie |
| POST `/api/v1/auth/reset-password` | JSON email, публичный | 200 ResetPasswordResponse; публикация прежнего сообщения RabbitMQ |
| GET `/api/v1/users/me` | Проверенный bearer access-токен существующего пользователя | 200 UserResponse |
| PATCH `/api/v1/users/me` | Проверенный bearer access-токен + JSON UserEditRequest | 200 UserEditResponse |
| DELETE `/api/v1/users/me` | Проверенный bearer access-токен | 200 UserDeleteResponse |
| GET `/healthcheck` | Публичный | 200, прежний HealthcheckResponse |

Форма login сохраняется (включая прежнюю поддержку OAuth2PasswordRequestForm); не заменять её JSON. Refresh сохраняет действующую ротацию, уникальный jti и отзыв прежнего токена через Redis; access-expiration при этой операции по-прежнему не проверяется. Запрос восстановления пароля не расширяется до полного восстановления.

## Exact data shapes

| Схема | Поля |
|---|---|
| UserSignupRequest | name, surname, username, password, email; необязательный phone_number |
| UserEditRequest | необязательные name, surname, username, email, phone_number |
| UserResponse | id, name, surname, username, email, created_at, phone_number, updated_at |
| UserEditResponse | name, surname, username, email, phone_number |
| UserDeleteResponse | id, username, email |
| TokenResponse | access_token, refresh_token, token_type="bearer" |
| ResetPasswordRequest | email |
| ResetPasswordResponse | message |

Типы UUID, EmailStr, даты и nullable phone_number/updated_at сохраняются. image_s3_path и image_url не входят в выходные данные даже со значением null. Password/password_hash не входят в ответы профиля. UserEditResponse не расширяется полями id или датами.

JSON-вход сохраняет `extra="ignore"`: прежний image_s3_path, image_url или id игнорируется как неизвестное поле, не записывается и не влияет на subject. PATCH с одними неизвестными полями не меняет профиль. Нельзя возвращать присланный путь как часть ответа.

## Removed operations and schemas

POST, GET и DELETE `/api/v1/users/me/image` отсутствуют и возвращают 404 отсутствующего маршрута с действующим bearer и без него. Они не возвращают 200/null, 410 или специфические ошибки файлов/хранилища и не проверяют MIME, размер или наличие изображения. Существующее стандартное HTTP-тело 404 сохраняется; новый специальный handler не создаётся.

OpenAPI не содержит `/api/v1/users/me/image`, ImageResponse, ImageUploadResponse, свойств image_s3_path/image_url или image-only описаний ошибок. Типы UploadImageError, DeleteImageError, ImageReceivingError и UserHasNoImageError исключаются из внутреннего контракта ошибок.

Ранее удалённые операции над чужими аккаунтами и изображениями по идентификатору также остаются недоступны; их отрицательные проверки сохраняются.

## Unchanged errors and access

- Доменные и прикладные ошибки оставшихся сценариев сохраняют `{ "error": "..." }` и существующие статусы 400/401/404/409.
- Стандартные HTTP и ошибки валидации FastAPI сохраняют прежнюю форму; не унифицировать их в рамках этой функции.
- Конфликты username/email/phone_number сохраняют 409; неверные учётные данные и ошибки токенов — действующие ответы аутентификации.
- GET/PATCH/DELETE me используют подтверждённую личность. Переданный клиентом id не даёт доступ к другому аккаунту. Удалённый пользователь не получает доступ по прежнему токену.

## Runtime configuration contract

Обязательность PostgreSQL, Redis, RabbitMQ и JWT сохраняется. StorageConfig и Config.storage отсутствуют. AWS_ACCESS_KEY_ID, AWS_ACCESS_KEY, AWS_REGION_NAME и AWS_BUCKET_NAME не требуются; отсутствие, пустые или устаревшие значения не меняют поведение при корректных остальных настройках. Примеры настройки и startup окружение не объявляют их.

Приложение использует POSTGRES_NAME; production Compose уже передаёт его PostgreSQL как POSTGRES_DB. Test Compose сохраняет собственный POSTGRES_DB для тестового сервера. Эти разные имена не являются частью интеграции S3 и не меняются.

## Acceptance matrix

| Граница | Наблюдаемый результат |
|---|---|
| Signup, GET me | Ровно 8 полей UserResponse, без image-полей |
| PATCH me | Ровно 5 полей UserEditResponse; legacy image input игнорируется |
| POST/GET/DELETE me/image | 404 при обоих вариантах аутентификации |
| OpenAPI | 8 поддерживаемых операций; отсутствуют image пути/схемы/свойства |
| Form login + refresh | Вход успешен; refresh вращается; replay прежнего токена отклоняется |
| Чужой id | Не меняет другого пользователя и не даёт доступа к нему |
| Startup без AWS | Готовность, семь пользовательских сценариев и удаление аккаунта работают |
