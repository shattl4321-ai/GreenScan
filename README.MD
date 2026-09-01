# GreenScan

GreenScan — веб-приложение для анализа состояния газона по нескольким фотографиям. Vision AI извлекает визуальные признаки, а rule-based слой (`RuleEngine` + `KnowledgeBase`) формирует рекомендации по уходу.

Проект находится в стадии учебного / portfolio MVP.

---

## Что умеет GreenScan

- Загрузка **от 2 до 5** фотографий газона через веб-интерфейс.
- Проверка, является ли каждое изображение газоном (`is_lawn`, `lawn_confidence`).
- Vision-анализ визуальных признаков (сухость, сорняки, мох, проплешины и др.).
- Валидация ответов Vision до запуска правил.
- Агрегация результатов нескольких фотографий в единое состояние.
- Формирование действий через `RuleEngine`.
- Обогащение рекомендаций данными из JSON-базы знаний.
- Отображение диагноза и рекомендаций пользователю.

---

## Как работает приложение

```text
Пользователь
    ↓
Frontend (index.html + FRONTEND/app.js)
    ↓
POST /analyze-photo (FastAPI)
    ↓
Vision provider (OpenAI / Gemini / Qwen)
    ↓
JSON visual state (по фото)
    ↓
validate_vision_results
    ↓
aggregate_results
    ↓
RuleEngine.evaluate
    ↓
RuleEngine.enrich → KnowledgeBase
    ↓
JSON response
    ↓
Frontend (результаты и рекомендации)
```

Подробнее: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Архитектура

| Компонент | Расположение | Назначение |
|-----------|--------------|------------|
| Frontend | `index.html`, `FRONTEND/` | UI, загрузка фото, отображение результатов |
| Backend API | `BACKEND/main.py` | HTTP API, Vision, валидация, агрегация |
| Vision layer | `BACKEND/vision/` | Провайдеры и общий prompt |
| RuleEngine | `BACKEND/engine.py` | Правила → список действий |
| KnowledgeBase | `BACKEND/knowledge.py`, `BACKEND/knowledge/` | Рекомендации и подбор продуктов |

---

## Vision-провайдеры

В проекте реализованы три провайдера (выбор через `VISION_PROVIDER`):

| Провайдер | Значение env | Реализация |
|-----------|--------------|------------|
| OpenAI | `openai` | `BACKEND/main.py` |
| Gemini | `gemini` | `BACKEND/vision/gemini_provider.py` |
| Qwen (OpenRouter) | `qwen` | `BACKEND/vision/qwen_provider.py` |

**Автоматический fallback между провайдерами не реализован.** Используется только провайдер, указанный в `VISION_PROVIDER`.

Подробнее: [docs/VISION.md](docs/VISION.md)

---

## Проверка входных изображений

Vision возвращает для каждого фото:

- `is_lawn` — `true` / `false`
- `lawn_confidence` — число от 0.0 до 1.0

Правила:

- Если **хотя бы одно** фото имеет `is_lawn = false` → весь набор отклоняется (**HTTP 400**).
- Если `is_lawn` **отсутствует** или не является `bool` → анализ не продолжается (**HTTP 422**).
- Если у всех фото `confidence <= 0` → анализ не продолжается (**HTTP 422**).

Тексты ошибок и коды: [docs/API.md](docs/API.md)

---

## Диагностируемые признаки

Поля Vision-ответа (из `BACKEND/vision/prompts.py`):

| Поле | Тип |
|------|-----|
| `is_lawn` | bool |
| `lawn_confidence` | float 0.0–1.0 |
| `dryness` | bool |
| `pale_grass` | bool |
| `weed_presence` | bool |
| `weed_type` | `"broadleaf"` \| `"grass"` \| `"mixed"` \| `null` |
| `weed_density` | `"low"` \| `"medium"` \| `"high"` \| `null` |
| `fungal_signs` | bool |
| `thin_lawn` | bool |
| `bare_spots` | bool |
| `needs_mowing` | bool |
| `moss_presence` | bool |
| `soil_issue` | всегда `null` в текущем prompt |
| `confidence` | float 0.0–1.0 |

---

## Технологии

- **Python** — backend
- **FastAPI** — HTTP API
- **Uvicorn** — ASGI-сервер
- **OpenAI Python SDK** — OpenAI, Gemini (OpenAI-compatible endpoint), Qwen (OpenRouter)
- **python-dotenv** — переменные окружения
- **HTML / CSS / JavaScript** — статический frontend без сборки
- **pytest** — автотесты

Docker-конфигурация в репозитории **отсутствует**.

Файл `requirements.txt` в репозитории **отсутствует**.

---

## Структура проекта

```text
GreenScan/
├── index.html              # Точка входа frontend
├── README.md
├── BACKEND/
│   ├── main.py             # FastAPI, /analyze-photo
│   ├── engine.py           # RuleEngine
│   ├── knowledge.py        # KnowledgeBase
│   ├── vision/
│   │   ├── prompts.py      # Общий SYSTEM_PROMPT
│   │   ├── gemini_provider.py
│   │   └── qwen_provider.py
│   ├── knowledge/          # JSON-базы знаний и expert_rules.json
│   ├── test_engine.py
│   ├── test_analyze_photo.py
│   └── .env.example
├── FRONTEND/
│   ├── app.js
│   ├── styles.css
│   └── assets/
└── docs/                   # Техническая документация
```

---

## Локальный запуск

### 1. Backend

```powershell
cd BACKEND
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install fastapi uvicorn openai python-dotenv python-multipart pytest httpx
copy .env.example .env
# Заполните .env (см. docs/ENVIRONMENT.md)
uvicorn main:app --reload --port 8001
```

Backend: `http://127.0.0.1:8001`  
Swagger UI: `http://127.0.0.1:8001/docs`

### 2. Frontend

```powershell
cd C:\Users\Dmitry\Projects_UII\GreenScan
python -m http.server 3000
```

Откройте: `http://127.0.0.1:3000/`

> Frontend должен запускаться из **корня** проекта, потому что `index.html` ссылается на `FRONTEND/styles.css` и `FRONTEND/app.js`.

Подробнее: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

---

## Переменные окружения

| Variable | Required | Purpose |
|----------|----------|---------|
| `VISION_PROVIDER` | optional (default: `openai`) | Выбор Vision-провайдера: `openai`, `gemini`, `qwen` |
| `OPENAI_API_KEY` | required при `openai` | API-ключ OpenAI |
| `OPENAI_VISION_MODEL` | optional (default: `gpt-4o-mini`) | Модель OpenAI Vision |
| `GOOGLE_API_KEY` | required при `gemini` | API-ключ Google Gemini |
| `OPENROUTER_API_KEY` | required при `qwen` | API-ключ OpenRouter |
| `QWEN_VISION_MODEL` | optional (default в коде: `qwen/qwen-2.5-vl-7b-instruct:free`) | Модель Qwen через OpenRouter |

Полное описание: [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md)

---

## API

| Method | Path | Описание |
|--------|------|----------|
| `POST` | `/analyze-photo` | Анализ 2–5 фотографий газона |

Подробности: [docs/API.md](docs/API.md)

---

## Тестирование

Из каталога `BACKEND`:

```bash
pytest
```

или:

```bash
python -m pytest test_analyze_photo.py test_engine.py -v
```

Группы тестов: RuleEngine, валидация Vision, агрегация, endpoint `/analyze-photo` (с mock).

Подробнее: [docs/TESTING.md](docs/TESTING.md)

---

## Ограничения MVP

- Результат зависит от качества и ракурса фотографий.
- Vision AI может ошибаться; возможны false positive и false negative.
- Проект **не является** профессиональной агрономической экспертизой.
- Анализ основан только на **видимых** признаках.
- Состояние почвы, корней, скрытые болезни без визуальных признаков надёжно определить нельзя.
- Качество результата зависит от выбранного Vision-провайдера и модели.
- Автоматический fallback между провайдерами отсутствует.
- Часть правил в `expert_rules.json` ссылается на признаки, которых нет в Vision-схеме (см. [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md)).

---

## Статус проекта

Учебный / portfolio MVP. Backend и frontend работают локально. Production deployment **не завершён**.

---

## Документация

| Документ | Содержание |
|----------|------------|
| [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md) | Контекст проекта для разработчика / AI |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Техническая архитектура |
| [docs/API.md](docs/API.md) | API endpoints |
| [docs/VISION.md](docs/VISION.md) | Vision-слой |
| [docs/RULE_ENGINE.md](docs/RULE_ENGINE.md) | RuleEngine и KnowledgeBase |
| [docs/TESTING.md](docs/TESTING.md) | Тестирование |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | План деплоя |
| [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) | Переменные окружения |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Локальная разработка |
| [docs/SECURITY.md](docs/SECURITY.md) | Базовая безопасность |
| [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) | Ограничения |
| [docs/ADR.md](docs/ADR.md) | Архитектурные решения |
| [docs/AI_ROLE.md](docs/AI_ROLE.md) | Правила для AI-агента |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | FAQ по ошибкам |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Changelog MVP |
