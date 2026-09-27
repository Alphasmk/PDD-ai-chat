# Data Model: пользователь без изображения

**Date**: 2026-09-27
**Related**: [spec.md](spec.md), [research.md](research.md), [HTTP contracts](contracts/http-api.md).

## User

Единственная доменная сущность — UserEntity. Каждая операция профиля относится к пользователю, найденному по подтверждённому subject access-токена.

| Поле | Домен / DTO | Хранение | Правила |
|---|---|---|---|
| id | ID(UUID) / UUID | UUID primary key, NOT NULL | Создаётся сервисом; не редактируется входными полями |
| name | Name / str | String, NOT NULL | 2–20 символов; латиница/кириллица, дефис, апостроф |
| surname | Name / str | String, NOT NULL | Те же правила Name |
| username | str | String, NOT NULL | Уникален; прежние правила без новых ограничений |
| password_hash | PasswordHash | String, NOT NULL | Результат хеширования; никогда не выдаётся в UserReadDTO или HTTP |
| email | Email / str | String, NOT NULL, UNIQUE | Прежняя доменная проверка; HTTP EmailStr; уникальность |
| phone_number | str или None | String, nullable, UNIQUE | Необязателен; прежние правила без нового формата |
| created_at | datetime UTC | DateTime, NOT NULL | Фиксируется при создании; репозиторий нормализует UTC |
| updated_at | datetime UTC или None | DateTime, nullable | None до обновления; дата обновления при изменении |

`image_s3_path` полностью исключается из сущности, DTO, ORM, преобразований add/update/read и схем ответов. Не вводится `image_url`, avatar, поле замены или отдельная сущность файлов. У пользователя нет отношений с изображениями или другими пользователями.

## DTO and boundaries

- UserCreateDTO: name, surname, username, password, email, необязательный phone_number. Входной RawPassword сохраняет длину 8–20 и действующее допустимое множество символов; хранится только хеш.
- UpdateUserDTO: необязательные name, surname, username, email, phone_number. Как прежде, None означает отсутствие изменения; возможность очищать phone_number через null этой функцией не вводится.
- UserReadDTO: id, name, surname, username, email, created_at, phone_number, updated_at — 8 полей, без пароля и изображения.
- DataFromTokenDTO: user_id UUID, email. Источник — проверенный access-токен и существующий пользователь, а не идентификатор из запроса.
- TokenDTO и инфраструктура отзыва refresh не меняются.

Name и Email проверяются при создании и изменении; восстановление сохранённых данных использует существующий from_trusted. Удаление поля не изменяет остальные инварианты. Оставшиеся JSON-схемы сохраняют extra=ignore и from_attributes=True.

## State transitions

1. Регистрация создаёт пользователя без изображения; уникальность username/email/ненулевого phone_number обеспечивается прежними ограничениями.
2. Получение профиля не изменяет состояние.
3. Редактирование меняет только допустимые поля, сохраняет id/created_at/password_hash и устанавливает updated_at при изменении. Пустое редактирование сохраняет прежнее поведение.
4. Удаление собственного профиля удаляет пользователя без обращений к AWS. Последующая проверка токена требует существующего пользователя.
5. Состояний «изображение отсутствует/загружено/удалено» больше нет. Входной image_s3_path остаётся неизвестным JSON-полем, игнорируется и не входит ни в один переход.

## Fresh database contract

- Новый единственный baseline: `source/infrastructure/database/alembic/versions/2026_09_27_users_without_images_baseline.py`.
- Revision: `users_no_images_20260927`; down_revision=None; один head.
- Таблицы после установки: users и alembic_version. В users ровно 9 полей из таблицы выше, без внешних ключей.
- Сохраняются `ix_users_username` (unique), `users_email_key` и `users_phone_number_key`.
- Перед первой регистрацией users пустая; нет bootstrap аккаунтов.
- Прежний `users_only_20260926` удаляется из активного набора. Старую наполненную базу не обновлять и не stamp: новая установка использует пустую базу, существующие аккаунты могут быть утрачены.
- Физическое представление UTC сохраняется: PostgreSQL DateTime хранит naive UTC, репозиторий выдаёт datetime с timezone.utc. Эта функция не меняет тип столбцов времени.

## Removed data and external objects

Удаляемые сведения об изображениях не переносятся. Объекты, бакеты и ключи AWS не являются управляемыми сущностями новой версии; приложение не очищает их при запуске, удалении аккаунта или пересоздании базы.
