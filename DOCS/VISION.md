# Vision-слой GreenScan

## Назначение

Vision-слой извлекает **визуальные признаки** из фотографий газона. Он возвращает структурированный JSON (LawnState).

Vision **не формирует** агрономические рекомендации. Рекомендации создаёт `RuleEngine` + `KnowledgeBase`.

## Провайдеры

Выбор через переменную `VISION_PROVIDER` (default: `openai`).

### OpenAI

| Параметр | Значение |
|----------|----------|
| Файл | `BACKEND/main.py` (`_analyze_one_image`) |
| API | OpenAI Chat Completions |
| Модель | `OPENAI_VISION_MODEL` (default: `gpt-4o-mini`) |
| Env | `OPENAI_API_KEY`, `OPENAI_VISION_MODEL` |
| Temperature | `0` |
| Timeout | `60` сек |
| MIME | передаётся в data URL (`jpeg` / `png` / `webp`) |
| Ошибки | Exception → HTTP 503 |

### Gemini

| Параметр | Значение |
|----------|----------|
| Файл | `BACKEND/vision/gemini_provider.py` |
| API | OpenAI-compatible endpoint Google: `https://generativelanguage.googleapis.com/v1beta/openai/` |
| Модель | `gemini-flash-latest` (захардкожено в коде) |
| Env | `GOOGLE_API_KEY` |
| MIME | всегда отправляет `data:image/jpeg;base64,...` независимо от реального типа |
| Ошибки | Exception → HTTP 503; невалидный JSON → `None` (пропуск фото) |

> **История модели:** ранее использовалась `gemini-1.5-flash`; заменена на `gemini-flash-latest`, потому что Google вывел старую модель из OpenAI-compatible endpoint (`v1beta/openai`). Google может периодически ротировать доступные model ID.

### Qwen (OpenRouter)

| Параметр | Значение |
|----------|----------|
| Файл | `BACKEND/vision/qwen_provider.py` |
| API | `https://openrouter.ai/api/v1` |
| Модель | `QWEN_VISION_MODEL` (default: `qwen/qwen-2.5-vl-7b-instruct:free`) |
| Env | `OPENROUTER_API_KEY`, `QWEN_VISION_MODEL` |
| MIME | `jpeg`, `png`, `webp` |
| Валидация | `_validate()` проверяет наличие обязательных bool-полей диагностики |
| Ошибки | `QwenProviderError` → HTTP 503; отсутствие `OPENROUTER_API_KEY` → `QwenProviderError` при вызове |

## Общий SYSTEM_PROMPT

Файл: `BACKEND/vision/prompts.py`

Один prompt для всех провайдеров. Это гарантирует:

- одинаковую JSON-схему;
- одинаковые правила `is_lawn`;
- одинаковую диагностику признаков.

Импортируется в `main.py`, `gemini_provider.py`, `qwen_provider.py`.

## Output schema

```json
{
  "is_lawn": true,
  "lawn_confidence": 0.95,
  "dryness": false,
  "pale_grass": false,
  "weed_presence": false,
  "weed_type": null,
  "weed_density": null,
  "fungal_signs": false,
  "thin_lawn": false,
  "bare_spots": false,
  "needs_mowing": false,
  "moss_presence": false,
  "soil_issue": null,
  "confidence": 0.85
}
```

### `is_lawn`

- `true` — на фото виден газон / травяной участок, пригодный для диагностики.
- `false` — мебель, интерьер, человек, авто и т.п.

Если `is_lawn = false`:
- все диагностические bool = `false`;
- `weed_type`, `weed_density`, `soil_issue` = `null`;
- `confidence` = `0.0`.

### `lawn_confidence`

Уверенность, что на фото именно газон (0.0–1.0). Используется для валидации входа; **не передаётся** в RuleEngine.

### `confidence`

Уверенность в диагностике состояния газона (0.0–1.0).

При валидации: если `max(confidence)` по всем фото `<= 0` → анализ отклоняется.

## Обработка ответа

1. Удаление markdown-обёртки `` ```json `` (если есть).
2. Извлечение первого JSON-объекта из строки.
3. `json.loads`.
4. Валидация в `main.py` (`validate_vision_results`).

Qwen дополнительно проверяет наличие bool-полей диагностики на уровне провайдера. `is_lawn` на уровне Qwen **не проверяется** — проверка в `main.py`.

## Fallback

**Автоматический fallback между провайдерами не реализован.**

Наличие трёх провайдеров означает возможность **ручного** переключения через `VISION_PROVIDER`, а не автоматическую смену при ошибке.

## Ограничения Vision

- Качество зависит от модели и провайдера.
- Модель может ошибочно принять не-газон за газон или наоборот.
- `soil_issue` в prompt всегда `null` — почвенные проблемы не диагностируются.
- Gemini игнорирует реальный MIME и всегда шлёт JPEG.
- Разные модели могут давать разные результаты на одних и тех же фото.
