# Data model

## Role / roles

Отдельная доменная RoleEntity (id, value: UserRole, label), ORM Role и таблица roles:

| id (PK) | value (unique) | label |
|---|---|---|
| 1 | user | Пользователь |
| 2 | admin | Администратор |

CHECK допускает только эти пары id/value; миграция создаёт обе записи. Каталог не
редактируется через API. IRoleRepository/RoleRepository возвращает записи по ID;
ListRoles читает таблицу после проверки текущего аккаунта. Новых зависимостей нет.

## User / users

Сохраняются id (UUID, PK), name, surname, username (unique), password_hash, email
(unique), phone_number (nullable, unique), created_at, updated_at (nullable).
В таблице пользователя всего 12 полей:

| Поле доступа | Тип / default | Правило |
|---|---|---|
| role_id | int, 1 | NOT NULL, FK roles.id ON DELETE RESTRICT; только 1 или 2 |
| is_blocked | bool, false | true только при role_id=1 |
| is_superadmin | bool, false | true только при role_id=2 |

ORM User.role — связь с Role; явная загрузка предотвращает неявный async IO.
UserEntity хранит UserRole (USER/ADMIN), is_blocked и is_superadmin. Репозиторий
явно преобразует фиксированные ID в enum и обратно. API выводит role как user/admin
и is_superadmin как отдельный boolean. При регистрации всегда user/false/false.

CHECK проверяют допустимость роли и обоих флагов. Частичный UNIQUE INDEX
ux_users_superadmin по is_superadmin WHERE is_superadmin гарантирует максимум
одного защищённого администратора; успешный startup обеспечивает наличие.
Индекс (created_at, id) обеспечивает порядок списка. SQL-доступ оператора вне
публичных гарантий; триггеры неизменности защищённого аккаунта не требуются.

## Переходы

| Состояние | Действие | Результат | Инициатор |
|---|---|---|---|
| Нет аккаунта | signup | user, оба флага false | Посетитель |
| Нет суперадмина | bootstrap | admin, is_superadmin=true, is_blocked=false | Startup |
| user, не blocked | назначить admin | admin, оба флага false | Защищённый admin |
| admin, не защищён | снять admin | user, оба флага false | Защищённый admin |
| user | block | user, is_blocked=true | Любой admin |
| user, blocked | повторный block | без изменений | Любой admin |
| user/admin, не защищён | та же роль | без изменений | Защищённый admin |
| admin, защищён | смена роли/block/delete | отказ | Любой |
| user, blocked | назначить admin | отказ | Любой |

No-op не обновляет updated_at. Реальная смена роли/блокировка обновляет его.
Нельзя снять блокировку сменой роли; role=superadmin недопустим в API. Регистрация
и профиль не принимают полномочия, включая is_superadmin, как изменяемые поля.

## Правила и транзакции

UserEntity immutable; переходы проверяют инварианты. Политики require_admin и
require_superadmin проверяют актуальную роль/флаг и блокировку. Административное
изменение: UoW → свежий SELECT инициатора → права → цель FOR UPDATE с
populate_existing → доменные правила → узкая запись → commit → DTO. При исключении
rollback. Профильный UPDATE не пишет role_id/is_blocked/is_superadmin. Удаление
проверяет защиту под блокировкой строки. Ранее начатые обращения могут завершиться.
JWT подтверждает личность; права не берутся из JWT или кеша. Redis и RabbitMQ
сохраняют прежние функции blacklist refresh и восстановления пароля.

## Миграции и старт

Цепочка users_roles_20260927 → role_catalog_20260927 (head). Первая — baseline
предыдущей схемы; вторая создаёт roles, переносит users.role в role_id, переводит
superadmin в admin/is_superadmin=true, удаляет строковую колонку role. Аккаунты,
UUID, профили, хеши паролей, timestamps и блокировка сохраняются. Downgrade
восстанавливает прежние роли; round trip проверяется с данными.
Startup под advisory lock применяет миграции, затем в отдельной транзакции создаёт
защищённого администратора, если его нет. Поиск существующего — по флагу, независимо
от имени. Миграции не содержат секретов и не создают аккаунт. Ошибка bootstrap не
запускает HTTP. Обновление схемы до users_roles_20260927 не поддержано этой цепочкой;
рабочая база и volumes автоматически не удаляются.
