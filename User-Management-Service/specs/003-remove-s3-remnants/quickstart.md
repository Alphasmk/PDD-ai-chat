# Quickstart: проверка очищенного тестового набора

**Date**: 2026-09-27 | **Status**: запланированная проверка; команды приложения на этапе планирования не выполнялись.

Контракты: [HTTP](contracts/http-api.md), [тесты](contracts/test-contract.md), [модель](data-model.md). Выполнять после реализации 003. Устаревшие исполняемые примеры quickstart002 к этому моменту должны быть актуализированы; его прошлый validation остаётся историческим.

## Подготовка

Нужны Python3.12, uv, PowerShell, Docker Desktop с Linux engine и свободные порты 5434/6380/5673/15673/8001. Использовать отдельный одноразовый проект `ums-remnants-validation` с существующим test Compose и tmpfs. Если его ресурсы уже используются другой работой, выбрать другое имя и свободные TEST_* ports, согласованно изменив URL. Основной Compose и пользовательские volumes не затрагивать.

`.env.test` должен содержать одноразовые значения примера. Существующий файл автоматически не перезаписывать и не печатать его содержимое. Не добавлять специальные настройки удалённых возможностей.

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

Ошибку установки/engine считать блокировкой соответствующих проверок, не успехом. Новые зависимости и миграции не требуются.

## 1. Аудит и быстрые проверки

```powershell
rg -n -i 'image_s3_path|image_url|AWS_|aws_value|ImageResponse|ImageUploadResponse|/image|IStorage|StorageConfig|FakeStorage|UploadImage|DeleteImage|GetUserImage|SetUserImage|UserHasNoImage|ImageReceiving' tests
rg -n -i 'image|s3|aws|storage' tests
uv run ruff check source tests scripts
uv run ruff format --check source tests scripts
uv run mypy source tests scripts
uv run pytest tests/unit
```

Первый поиск должен вернуть ноль совпадений (rg exit1 при отсутствии совпадений ожидаем). Второй — обзор контекста: разрешены только исторический revision baseline и token blacklist .storage, не специальные данные/сценарии. Поиск не маскировать конкатенацией старых имён. Исторические specs/Git не включать в критерий нулевого результата.

Ruff/mypy/unit должны завершиться успешно. Сравнения точных наборов DTO/config остаются в существующих тестах; expected-набор не вычисляется из той же модели. Проверить [тестовый контракт](contracts/test-contract.md) и исполняемые примеры002 вручную на согласованность. Этот аудит — процедура проверки, не входные данные приложения.

## 2. Реальные сервисы и production startup

При повторном запуске сначала убедиться, что проект одноразовый и никем не используется. Down удалит только его временные данные; fresh startup требует пустую тестовую public.users. Это не требование очищать существующую пользовательскую установку.

```powershell
& $validationDocker compose --env-file .env.test -p ums-remnants-validation -f docker-compose.test.yaml --profile startup down
& $validationDocker compose --env-file .env.test -p ums-remnants-validation -f docker-compose.test.yaml --profile startup up -d --build --wait
$env:UMS_TEST_POSTGRES_URL = 'postgresql+asyncpg://postgres:disposable@localhost:5434/ums_test'
$env:UMS_TEST_REDIS_URL = 'redis://:disposable@localhost:6380/0'
$env:UMS_TEST_BROKER_URL = 'amqp://test:disposable@localhost:5673/'
$env:UMS_TEST_APP_URL = 'http://localhost:8001'
Invoke-RestMethod "$env:UMS_TEST_APP_URL/healthcheck"
uv run pytest tests/integration
```

Ожидание: Dockerfile frozen/no-dev build, Alembic текущего baseline и production lifespan работают. Startup не пропускается; опубликованный OpenAPI содержит ровно8 операций, GET/POST signup — profile8, PATCH —5. Login остаётся формой; refresh rotation/replay, текущий субъект, конфликты, reset publisher и удаление аккаунта проходят. Неизвестные нейтральные поля игнорируются, пустые изменения сохраняют даты и оба профиля. PostgreSQL tests проверяют users-only схему и прежний revision; Redis/RabbitMQ tests работают с настоящими сервисами.

Для диагностики:

```powershell
& $validationDocker compose --env-file .env.test -p ums-remnants-validation -f docker-compose.test.yaml --profile startup ps
& $validationDocker compose --env-file .env.test -p ums-remnants-validation -f docker-compose.test.yaml --profile startup logs --tail 100 app_test
```

Если есть skips/failures, записать причины. Запуск без UMS_TEST_* с SQLite/fakes не заменяет этот этап. Полные секреты/настройки в отчёт не выводить.

## 3. Сохранение аккаунта после restart приложения

Проводить после успешного startup, который удаляет созданные им аккаунты. Перезапускается только app_test; PostgreSQL и tmpfs остаются работающими.

```powershell
$validationUsername = 'persist' + [Guid]::NewGuid().ToString('N').Substring(0, 8)
$validationBody = @{
    name='Alice'; surname='Smith'; username=$validationUsername
    password='Test1234'; email="$validationUsername@example.com"
} | ConvertTo-Json
$validationUser = Invoke-RestMethod "$env:UMS_TEST_APP_URL/api/v1/auth/signup" -Method Post -ContentType 'application/json' -Body $validationBody
$validationTokens = Invoke-RestMethod "$env:UMS_TEST_APP_URL/api/v1/auth/login" -Method Post -ContentType 'application/x-www-form-urlencoded' -Body @{ username=$validationUsername; password='Test1234' }
$validationHeaders = @{ Authorization="Bearer $($validationTokens.access_token)" }
try {
    Invoke-RestMethod "$env:UMS_TEST_APP_URL/api/v1/users/me" -Method Patch -Headers $validationHeaders -ContentType 'application/json' -Body '{"name":"Jane","unsupported_field":"ignored"}' | Out-Null
    & $validationDocker compose --env-file .env.test -p ums-remnants-validation -f docker-compose.test.yaml --profile startup restart app_test
    if ($LASTEXITCODE -ne 0) { throw 'Restart завершился ошибкой' }
    $validationReady = $false
    for ($validationAttempt=0; $validationAttempt -lt 30; $validationAttempt++) {
        try {
            Invoke-RestMethod "$env:UMS_TEST_APP_URL/healthcheck" -TimeoutSec 2 | Out-Null
            $validationReady = $true
            break
        } catch { Start-Sleep -Seconds 1 }
    }
    if (-not $validationReady) { throw 'Приложение не готово после restart' }
    $validationTokens = Invoke-RestMethod "$env:UMS_TEST_APP_URL/api/v1/auth/login" -Method Post -ContentType 'application/x-www-form-urlencoded' -Body @{ username=$validationUsername; password='Test1234' }
    $validationHeaders = @{ Authorization="Bearer $($validationTokens.access_token)" }
    $validationProfile = Invoke-RestMethod "$env:UMS_TEST_APP_URL/api/v1/users/me" -Headers $validationHeaders
    if ($validationProfile.id -ne $validationUser.id -or $validationProfile.name -ne 'Jane') { throw 'Данные аккаунта не сохранились' }
    $validationExpected = @('id','name','surname','username','email','phone_number','created_at','updated_at')
    if (Compare-Object ($validationExpected | Sort-Object) (@($validationProfile.PSObject.Properties.Name) | Sort-Object)) { throw 'Состав профиля изменился' }
} finally {
    Invoke-RestMethod "$env:UMS_TEST_APP_URL/api/v1/users/me" -Method Delete -Headers $validationHeaders | Out-Null
}
```

Ожидание: тот же UUID, изменённое имя, действующий вход и точные восемь полей. При сбое cleanup зафиксировать его; down одноразового проекта ниже удалит его временные данные.

## 4. Очистка и отчёт

```powershell
& $validationDocker compose --env-file .env.test -p ums-remnants-validation -f docker-compose.test.yaml --profile startup down
'UMS_TEST_APP_URL','UMS_TEST_POSTGRES_URL','UMS_TEST_REDIS_URL','UMS_TEST_BROKER_URL' | ForEach-Object { Remove-Item "Env:$_" -ErrorAction SilentlyContinue }
```

В новом отчёте003 указать команды, фактические passed/failed/skipped, аудит и соответствие FR-001–010 / SC-001–004. Прежнее число тестов125 относится к002; уменьшение числа из-за удалённых сценариев ожидаемо. Обзор diff должен подтвердить неизменность source/baseline/revision/зависимостей и сохранность исторических документов относительно исходного рабочего состояния этого этапа. Основные аккаунты/volumes не изменяются.
