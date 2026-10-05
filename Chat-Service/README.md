# Chat Service

Создайте `.env` с параметрами `SECRET_KEY`, `ALGORITHM`, `GEMINI_MODELS`,
`GEMINI_API_KEY`, `GEMINI_TEMPERATURE` и `GEMINI_MAX_RETRIES`.

Для анализа изображений по умолчанию используются `GEMINI_THINKING_LEVEL=low`
и `GEMINI_MEDIA_RESOLUTION=medium`. Эти параметры можно переопределить в `.env`:
для обоих поддерживаются значения `low`, `medium` и `high`.

Запуск:

```sh
docker compose up --build
```

Сервис будет доступен на `http://localhost:8000`.
