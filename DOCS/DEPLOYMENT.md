# Deployment GreenScan

## Текущий статус

**Deployment not completed yet.**

Проект работает локально. Production-окружение не развёрнуто.

## Предполагаемая архитектура

На основе текущей структуры проекта (статический frontend + FastAPI backend):

```text
Internet
    ↓
Nginx (reverse proxy, TLS)
    ↓
├── Static files (index.html, FRONTEND/)
└── FastAPI (Uvicorn) — /analyze-photo
        ↓
    Vision API (OpenAI / Gemini / OpenRouter)
```

Это **план**, а не описание работающего production.

## Почему отдельный сервер

VPS должен иметь **стабильный сетевой доступ** к используемым Vision API (OpenAI, Google Gemini, OpenRouter).

Конкретная страна или регион как техническое требование в коде **не зафиксированы**.

## Docker

**Docker configuration is not yet present / not finalized.**

В репозитории отсутствуют:

- `Dockerfile`
- `docker-compose.yml`

Создание Docker-конфигурации — отдельная задача.

## Nginx

Конфигурация Nginx в репозитории **отсутствует**.

Предполагаемая роль:

- раздача статики frontend;
- reverse proxy для backend API;
- TLS termination.

Готовые production-команды и конфиги **не задокументированы как факт**.

## ENV

- `.env` хранится в `BACKEND/` и **не должен** попадать в Git.
- На сервере переменные задаются через `.env` или secrets manager.
- Пример: `BACKEND/.env.example`.

## Health check

**Dedicated health endpoint is not currently implemented.**

Для мониторинга можно временно использовать `/docs` (доступность FastAPI), но это не полноценный health check.

## Порты (локальная разработка)

| Сервис | Порт | Где задан |
|--------|------|-----------|
| Backend | `8001` | Команда запуска + `FRONTEND/app.js` (`API_URL`) |
| Frontend | `3000` | Команда `python -m http.server 3000` |

В `main.py` порт **не захардкожен**.

## Логи на сервере

При деплое учитывать `BACKEND/logs/greenscan.log` — ротация 5 MB, 3 backup.

## Чеклист перед деплоем

- [ ] Заполнить `.env` на сервере
- [ ] Настроить CORS (сейчас `allow_origins=["*"]`)
- [ ] Настроить HTTPS
- [ ] Ограничить размер загружаемых файлов (сейчас не ограничен)
- [ ] Добавить health endpoint (опционально)
- [ ] Создать Docker-конфигурацию (опционально)
- [ ] Обновить `API_URL` во frontend для production-домена
