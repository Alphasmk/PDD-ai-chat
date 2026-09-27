# Quickstart: проверка удаления изображений и AWS S3

**Date**: 2026-09-27
**Status**: Руководство проверено при реализации; результаты в [validation.md](validation.md). При планировании команды не выполнялись.

Подробности: [план](plan.md), [модель данных](data-model.md), [контракты](contracts/http-api.md).

## Prerequisites

- Реализован план 002; обновлены pyproject.toml, uv.lock, baseline и тесты.
- Python 3.12, uv, Docker Desktop с доступным Linux engine.
- PowerShell из корня репозитория. Все проверки используют одноразовый проект `ums-no-images-validation` и `docker-compose.test.yaml`, не основной Compose.
- Свободны localhost:5434,6380,5673,15673,8001. При необходимости измените TEST_* ports и соответствующие URL согласованно.
- `.env.test` содержит одноразовые значения из `.env.test.example` (postgres/disposable/ums_test, Redis disposable, RabbitMQ test/disposable). При существующем файле проверьте его соответствие примеру, не перезаписывая пользовательские настройки вслепую. AWS не нужен.

```powershell
Set-Location 'D:/course_project/pdd_ai/User-Management-Service'
if (-not (Test-Path .env.test)) { Copy-Item .env.test.example .env.test }
$validationDocker = 'docker'
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    $validationDocker = 'C:/Users/yomi/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe'
}
& $validationDocker version
uv sync --frozen
```

Если версии/установка недоступны, зафиксировать блокировку, не считать дальнейшие проверки выполненными. Frozen установка должна проходить без S3-клиента; python-multipart остаётся установленным для login.

## 1. Static and isolated validation

```powershell
uv run ruff check source tests scripts
uv run ruff format --check source tests scripts
uv run mypy source tests scripts
uv run pytest tests/unit
```

Ожидание: все проверки проходят. Модульные тесты не требуют AWS, PostgreSQL, Redis или RabbitMQ. Тестов трёх удалённых image use case и FakeStorage нет; проверки остальных правил сохраняются.

Проверить оставшиеся упоминания в актуальной поставке:

```powershell
rg -n -i 'image_s3_path|image_url|IStorage|StorageConfig|aioboto|botocore|AWS_|UploadImage|DeleteImage|GetUserImage|SetUserImage|UserHasNoImage|ImageReceiving|MAX_FILE_SIZE|ALLOWED_MIME_TYPES' source pyproject.toml uv.lock .env.example .env.test.example docker-compose.test.yaml README.md
```

Ожидание: нет ссылок на действующую интеграцию или поля изображения; код возврата rg=1 при отсутствии совпадений нормален. Упоминание удаления в инструкции перехода допустимо после проверки контекста. Исторические specs и отрицательные тесты могут содержать прежние имена. Docker `image:` и `.storage` в blacklist токенов не считаются пользовательскими изображениями.

Проверки конфигурации должны создавать Config без AWS-полей и с устаревшими пустыми AWS-полями при корректных остальных параметрах; ни один вариант не требует StorageConfig. Файл с реальными секретами не выводить.

## 2. Real PostgreSQL, Redis and RabbitMQ

Для новой проверки начать с остановки только одноразового проекта. tmpfs данные этого проекта будут утрачены; основные volumes не затрагиваются.

```powershell
& $validationDocker compose --env-file .env.test -p ums-no-images-validation -f docker-compose.test.yaml --profile startup down
& $validationDocker compose --env-file .env.test -p ums-no-images-validation -f docker-compose.test.yaml up -d --wait postgres_test redis_test rabbitmq_test
$env:UMS_TEST_POSTGRES_URL = 'postgresql+asyncpg://postgres:disposable@localhost:5434/ums_test'
$env:UMS_TEST_REDIS_URL = 'redis://:disposable@localhost:6380/0'
$env:UMS_TEST_BROKER_URL = 'amqp://test:disposable@localhost:5673/'
Remove-Item Env:UMS_TEST_APP_URL -ErrorAction SilentlyContinue
uv run pytest tests/integration
```

Ожидаемые результаты:

- PostgreSQL-тесты применяют новый единственный baseline в случайных схемах; в users ровно 9 столбцов и нет image_s3_path, а tables — users+alembic_version.
- До signup пользователей нет; ограничения уникальности и UTC round-trip сохранены.
- HTTP-ответы имеют точный состав полей из контракта; legacy image input игнорируется.
- POST/GET/DELETE `/api/v1/users/me/image` возвращают 404 с bearer и без него; OpenAPI не содержит пути, image-схем или полей.
- Реальные Redis/RabbitMQ проверки не пропускаются: refresh отзывается, TTL работает, запрос восстановления публикуется.
- Startup-тест на этой стадии может пропускаться из-за отсутствия UMS_TEST_APP_URL; он выполняется отдельно ниже. Остальные skips анализировать и отражать в результате.

## 3. Production entrypoint without AWS

После реализации app_test не содержит четырёх фиктивных AWS-переменных. Не добавлять их обратно для прохождения startup.

```powershell
& $validationDocker compose --env-file .env.test -p ums-no-images-validation -f docker-compose.test.yaml --profile startup up -d --build --wait
$env:UMS_TEST_APP_URL = 'http://localhost:8001'
Invoke-RestMethod "$env:UMS_TEST_APP_URL/healthcheck"
uv run pytest tests/integration/settings/startup_test.py
```

Ожидание: Dockerfile с `uv sync --frozen --no-dev`, entry.sh с `alembic upgrade head` и production lifespan работают без AWS. Startup-тест проходит без skip и подмен зависимостей: создаёт две учётные записи, проверяет собственный профиль, форму login, обновление токенов/replay, публикацию запроса восстановления, недоступность чужих операций и удалённых image операций, затем удаляет тестовые аккаунты.

При неудаче диагностировать только этот проект:

```powershell
& $validationDocker compose --env-file .env.test -p ums-no-images-validation -f docker-compose.test.yaml --profile startup ps
& $validationDocker compose --env-file .env.test -p ums-no-images-validation -f docker-compose.test.yaml --profile startup logs --tail 100 app_test
```

Логи могут содержать диагностические сведения; не выводить полные настройки или секреты окружения.

## 4. Persistence after application restart

Этот сценарий дополняет startup-тест: PostgreSQL остаётся запущенным, перезапускается только app_test. После автоматического startup-теста public.users снова пустая.

```powershell
$validationUsername = 'persist' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$validationBody = @{
    name = 'Alice'; surname = 'Smith'; username = $validationUsername
    password = 'Test1234'; email = "$validationUsername@example.com"
} | ConvertTo-Json
$validationUser = Invoke-RestMethod "$env:UMS_TEST_APP_URL/api/v1/auth/signup" -Method Post -ContentType 'application/json' -Body $validationBody
$validationTokens = Invoke-RestMethod "$env:UMS_TEST_APP_URL/api/v1/auth/login" -Method Post -ContentType 'application/x-www-form-urlencoded' -Body @{ username=$validationUsername; password='Test1234' }
$validationHeaders = @{ Authorization = "Bearer $($validationTokens.access_token)" }
try {
    Invoke-RestMethod "$env:UMS_TEST_APP_URL/api/v1/users/me" -Method Patch -Headers $validationHeaders -ContentType 'application/json' -Body '{"name":"Jane","image_s3_path":"legacy-input"}' | Out-Null
    & $validationDocker compose --env-file .env.test -p ums-no-images-validation -f docker-compose.test.yaml --profile startup restart app_test
    $validationReady = $false
    for ($validationAttempt = 0; $validationAttempt -lt 30; $validationAttempt++) {
        try {
            Invoke-RestMethod "$env:UMS_TEST_APP_URL/healthcheck" -TimeoutSec 2 | Out-Null
            $validationReady = $true
            break
        } catch { Start-Sleep -Seconds 1 }
    }
    if (-not $validationReady) { throw 'Приложение не стало готово после restart' }
    $validationTokens = Invoke-RestMethod "$env:UMS_TEST_APP_URL/api/v1/auth/login" -Method Post -ContentType 'application/x-www-form-urlencoded' -Body @{ username=$validationUsername; password='Test1234' }
    $validationHeaders = @{ Authorization = "Bearer $($validationTokens.access_token)" }
    $validationProfile = Invoke-RestMethod "$env:UMS_TEST_APP_URL/api/v1/users/me" -Headers $validationHeaders
    if ($validationProfile.id -ne $validationUser.id -or $validationProfile.name -ne 'Jane') { throw 'Профиль не сохранился' }
    if ($validationProfile.PSObject.Properties.Name -contains 'image_s3_path' -or $validationProfile.PSObject.Properties.Name -contains 'image_url') { throw 'Поле изображения осталось в профиле' }
    $validationProfile | Select-Object id, name, username
} finally {
    Invoke-RestMethod "$env:UMS_TEST_APP_URL/api/v1/users/me" -Method Delete -Headers $validationHeaders | Out-Null
}
```

Ожидание: UUID, изменённое имя и учётные данные сохранены; изображение не появилось из legacy input. Если очистка после сбоя невозможна, завершение одноразового проекта ниже удаляет его временные данные.

## 5. Cleanup and completion record

```powershell
& $validationDocker compose --env-file .env.test -p ums-no-images-validation -f docker-compose.test.yaml --profile startup down
'UMS_TEST_APP_URL','UMS_TEST_POSTGRES_URL','UMS_TEST_REDIS_URL','UMS_TEST_BROKER_URL' | ForEach-Object { Remove-Item "Env:$_" -ErrorAction SilentlyContinue }
```

Записать фактические результаты Ruff, mypy, unit/integration, startup, persistence и аудита зависимостей/документации. Пропуски и ошибки не объявлять успехом. Сопоставить результаты FR-001–FR-010 и SC-001–SC-005 из плана. Предыдущие 122 успешных теста относятся к функции 001 и не подтверждают эту реализацию.

## Transition of an existing installation

Пользователь разрешил пересоздать PostgreSQL volume с нуля. Существующие аккаунты при этом теряются; перенос базы и stamping старого revision не поддерживаются.

Перед реальным переходом определить фактический Compose-проект, контейнер PostgreSQL и подключённый к `/var/lib/postgresql/data` named volume; проверить его имя и labels. Остановить приложение и PostgreSQL, удалить только этот контейнер и подтверждённый PostgreSQL volume, затем запустить новую установку. Не использовать общий `down -v` для основного проекта: он также затронет Redis volume. Не удалять объекты AWS или volumes других проектов. Эти действия не выполняются этапом планирования.

Production Compose уже содержит `POSTGRES_DB: ${POSTGRES_NAME}`; сохранять это соответствие. Новая база создаётся при первой инициализации нового volume. Изменение имени в окружении не превращает существующую базу в новую установку.
