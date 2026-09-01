# Changelog

## Current MVP

### Backend

- FastAPI endpoint `POST /analyze-photo` для анализа 2–5 фотографий.
- Три Vision-провайдера: OpenAI, Gemini, Qwen (OpenRouter).
- Переключение провайдера через `VISION_PROVIDER`.
- Общий `SYSTEM_PROMPT` в `vision/prompts.py`.
- Валидация Vision-ответов (`validate_vision_results`).
- Агрегация результатов нескольких фото (`aggregate_results`).
- RuleEngine с правилами из `expert_rules.json`.
- KnowledgeBase с JSON-базами (удобрения, гербициды, семена, рекомендации).
- Логирование в консоль и `logs/greenscan.log`.

### Vision validation (regression fix)

- Добавлены поля `is_lawn` и `lawn_confidence` в Vision-схему.
- Отклонение неподходящих изображений (`is_lawn = false`) — весь набор.
- Обязательная проверка `is_lawn` (отсутствие / не-bool → HTTP 422).
- Отсечка нулевой уверенности (`max(confidence) <= 0` → HTTP 422).
- Поля `is_lawn` / `lawn_confidence` не передаются в RuleEngine.

### Frontend

- Статический UI: загрузка фото, анализ, результаты, рекомендации.
- Состояния: start / loading / results.
- Отображение ошибок из `data.detail`.

### Tests

- `test_engine.py` — RuleEngine и KnowledgeBase.
- `test_analyze_photo.py` — валидация, агрегация, `/analyze-photo` с mock.

### Not implemented

- Docker / production deployment.
- Health endpoint.
- Автоматический fallback Vision-провайдеров.
- `requirements.txt`.
- База данных.
- Аутентификация.

---

## Previous iterations

### v0.3 (2026-07-18) — мульти-провайдерный Vision

- Добавлен `BACKEND/vision/qwen_provider.py` (OpenRouter).
- Диспетчер провайдеров в `main.py` по `VISION_PROVIDER`.
- Создан `BACKEND/.env.example`.
- Модель Gemini заменена: `gemini-1.5-flash` → `gemini-flash-latest` (Google вывел старую модель из OpenAI-compatible endpoint).
- В OpenAI-ветке исправлена передача MIME (`jpeg` / `png` / `webp` вместо жёсткого `jpeg`).

> Примечание: в этой итерации также исследовались free-tier модели OpenRouter; доступность конкретных model ID может меняться. Актуальные defaults — в коде и `docs/ENVIRONMENT.md`.
