# Переменные окружения GreenScan

Файл `.env` располагается в `BACKEND/` и загружается через `python-dotenv` (`load_dotenv()` в `main.py`).

При запуске backend рабочая директория должна быть `BACKEND/`.

Пример: `BACKEND/.env.example`

---

## `VISION_PROVIDER`

| | |
|---|---|
| **Required** | optional |
| **Default** | `openai` |
| **Где используется** | `BACKEND/main.py` |
| **Назначение** | Выбор Vision-провайдера |
| **Допустимые значения** | `openai`, `gemini`, `qwen` |

```env
VISION_PROVIDER=openai
```

При неизвестном значении → HTTP 500.

---

## `OPENAI_API_KEY`

| | |
|---|---|
| **Required** | да, при `VISION_PROVIDER=openai` |
| **Где используется** | `BACKEND/main.py` |
| **Назначение** | API-ключ OpenAI |

```env
OPENAI_API_KEY=your_key_here
```

Клиент OpenAI создаётся при старте приложения независимо от выбранного провайдера.

---

## `OPENAI_VISION_MODEL`

| | |
|---|---|
| **Required** | optional |
| **Default** | `gpt-4o-mini` |
| **Где используется** | `BACKEND/main.py` |
| **Назначение** | Модель OpenAI Vision |

```env
OPENAI_VISION_MODEL=gpt-4o-mini
```

---

## `GOOGLE_API_KEY`

| | |
|---|---|
| **Required** | да, при `VISION_PROVIDER=gemini` |
| **Где используется** | `BACKEND/vision/gemini_provider.py` |
| **Назначение** | API-ключ Google Gemini |

```env
GOOGLE_API_KEY=your_key_here
```

Модуль импортируется только при `VISION_PROVIDER=gemini`.

---

## `OPENROUTER_API_KEY`

| | |
|---|---|
| **Required** | да, при `VISION_PROVIDER=qwen` |
| **Где используется** | `BACKEND/vision/qwen_provider.py` |
| **Назначение** | API-ключ OpenRouter |

```env
OPENROUTER_API_KEY=your_key_here
```

Если не задан → `QwenProviderError` при вызове анализа.

---

## `QWEN_VISION_MODEL`

| | |
|---|---|
| **Required** | optional |
| **Default в коде** | `qwen/qwen-2.5-vl-7b-instruct:free` |
| **Где используется** | `BACKEND/vision/qwen_provider.py` |
| **Назначение** | Модель Qwen через OpenRouter |

```env
QWEN_VISION_MODEL=qwen/qwen-2.5-vl-7b-instruct:free
```

> В `BACKEND/.env.example` указана другая модель (`qwen/qwen3-vl-8b-instruct`). Фактический default определяется кодом в `qwen_provider.py`.

---

## Переменные, которых нет в коде

Следующие переменные **не используются** текущей версией:

- `PORT` — порт задаётся командой uvicorn
- `LOG_LEVEL` — уровень логирования захардкожен (`INFO`)
- Database URL — БД отсутствует

---

## Безопасность

- Не коммитьте `.env` в Git.
- `BACKEND/.gitignore` исключает `.env`.
- Корневой `.gitignore` **отсутствует** (только `BACKEND/.gitignore`).
