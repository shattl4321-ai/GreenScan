# Локальная разработка GreenScan

## Requirements

Версия Python **не зафиксирована** в репозитории (нет `pyproject.toml`, `.python-version`, `runtime.txt`).

Проект тестировался на Python 3.14 (по окружению разработки). Минимальная версия не определена в текущей версии проекта.

## Installation

### Backend

```powershell
cd BACKEND
python -m venv venv
.\venv\Scripts\Activate.ps1    # Windows
# source venv/bin/activate      # Linux/macOS

pip install fastapi uvicorn openai python-dotenv python-multipart pytest httpx
```

Файл `requirements.txt` **отсутствует**. Список пакетов основан на фактических импортах и venv.

### Frontend

Сборка не требуется. Статические файлы: `index.html`, `FRONTEND/`.

## Environment

```powershell
cd BACKEND
copy .env.example .env
```

Заполните переменные. См. [ENVIRONMENT.md](ENVIRONMENT.md).

Минимальная конфигурация для OpenAI:

```env
VISION_PROVIDER=openai
OPENAI_API_KEY=your_key_here
```

## Start backend

```powershell
cd BACKEND
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8001
```

- API: `http://127.0.0.1:8001`
- Swagger: `http://127.0.0.1:8001/docs`

## Start frontend

```powershell
cd C:\Users\Dmitry\Projects_UII\GreenScan
python -m http.server 3000
```

Откройте: `http://127.0.0.1:3000/`

> Запускать из **корня** проекта, не из `FRONTEND/`. `index.html` ссылается на `FRONTEND/styles.css` и `FRONTEND/app.js`.

Frontend обращается к backend по адресу `http://127.0.0.1:8001/analyze-photo` (захардкожено в `FRONTEND/app.js`).

## Tests

```powershell
cd BACKEND
.\venv\Scripts\Activate.ps1
pytest
```

Подробнее: [TESTING.md](TESTING.md)

## Logs

| Расположение | Описание |
|--------------|----------|
| Консоль | stdout через `StreamHandler` |
| `BACKEND/logs/greenscan.log` | Ротация 5 MB, 3 backup |

Logger name: `greenscan`, уровень: `INFO`.

Дополнительно: `BACKEND/server.log` — не определено в текущей версии проекта, может быть артефактом ручного запуска.

## Добавление Vision-провайдера

Текущий интерфейс:

1. Создать модуль в `BACKEND/vision/` с функцией `analyze_image(base64_image, mime_type=...) -> dict | None`.
2. Использовать `SYSTEM_PROMPT` из `vision/prompts.py`.
3. Добавить провайдер в `ALLOWED_PROVIDERS` и lazy-import в `main.py`.
4. Добавить ветку в `_analyze_one_image`.
5. Добавить env-переменные в `.env.example` и `docs/ENVIRONMENT.md`.
6. Добавить тесты с mock.

Единый prompt обязателен для совместимости с `validate_vision_results` и `aggregate_results`.

## Структура IDE

Рекомендуется открывать корень `GreenScan/` как workspace. Backend запускать из `BACKEND/`.

## Полезные ссылки

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [API.md](API.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
