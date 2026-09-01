# Architecture Decision Record

Ключевые архитектурные решения GreenScan.

---

## ADR-001 — FastAPI backend

**Status:** Accepted

**Decision:** HTTP backend реализован на FastAPI.

**Context:** Current implementation uses FastAPI as HTTP backend with a single endpoint `/analyze-photo`.

**Consequences:**
- Автоматическая OpenAPI-документация (`/docs`).
- Async endpoint для загрузки файлов.
- CORS middleware для локального frontend.

---

## ADR-002 — Vision + RuleEngine

**Status:** Accepted

**Decision:** Разделение Vision (извлечение признаков) и RuleEngine (принятие решений).

**Context:**
- Vision возвращает JSON с визуальными признаками.
- RuleEngine применяет правила из `expert_rules.json` и формирует действия.
- KnowledgeBase обогащает действия текстами и продуктами.

**Consequences:**
- Изменение рекомендаций не требует переобучения Vision.
- Vision prompt не содержит агрономических рекомендаций.

---

## ADR-003 — Multiple Vision providers

**Status:** Accepted

**Decision:** Три провайдера (OpenAI, Gemini, Qwen) с переключением через `VISION_PROVIDER`.

**Context:** Каждый провайдер реализован отдельным модулем. Lazy-import при старте.

**Important:** Наличие нескольких провайдеров **не означает** автоматический fallback. При ошибке одного провайдера переключение на другой **не происходит**.

---

## ADR-004 — Shared Vision prompt

**Status:** Accepted

**Decision:** Единый `SYSTEM_PROMPT` в `BACKEND/vision/prompts.py` для всех провайдеров.

**Context:** Одинаковая JSON-схема необходима для `validate_vision_results`, `aggregate_results` и RuleEngine.

**Consequences:**
- Изменение схемы требует обновления одного файла.
- Все провайдеры должны импортировать `SYSTEM_PROMPT`.

---

## ADR-005 — Reject entire batch when one image is not lawn

**Status:** Accepted

**Decision:** Если хотя бы одно фото имеет `is_lawn = false`, весь набор отклоняется (HTTP 400).

**Context:** Пользователь загружает 2–5 фото. Смешанный набор (газон + мебель) не должен анализироваться частично.

**Consequences:**
- Хорошие фото в смешанном наборе не анализируются отдельно.
- RuleEngine не вызывается при отклонении.

---

## ADR-006 — `is_lawn` is mandatory

**Status:** Accepted

**Decision:** Поле `is_lawn` обязательно в ответе Vision. Отсутствие или некорректный тип → HTTP 422.

**Context:** Без `is_lawn` невозможно отличить «идеальный газон» от «не газон с нулевой уверенностью».

**Consequences:**
- Отсутствие `is_lawn` не трактуется как `true`.
- Анализ останавливается до агрегации и RuleEngine.

---

## ADR-007 — Confidence gate at zero

**Status:** Accepted

**Decision:** Если `max(confidence)` по всем фото `<= 0`, анализ отклоняется (HTTP 422).

**Context:** Нулевая уверенность не должна приводить к положительному диагнозу «газон в идеальном состоянии».

**Consequences:** Порог выше нуля (0.2, 0.5) **не задан** — только отсечка нулевой уверенности.

---

## ADR-008 — Static frontend without build

**Status:** Accepted

**Decision:** Frontend — статические HTML/CSS/JS без сборщика.

**Context:** `index.html` в корне проекта, ресурсы в `FRONTEND/`.

**Consequences:**
- Нет npm/webpack.
- `API_URL` захардкожен в `app.js`.
