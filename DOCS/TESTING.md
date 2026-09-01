# Тестирование GreenScan

## Как запускать

Из каталога `BACKEND` с активированным venv:

```bash
pytest
```

или с подробным выводом:

```bash
python -m pytest test_analyze_photo.py test_engine.py -v
```

Запуск отдельного файла:

```bash
python -m pytest test_engine.py -v
python -m pytest test_analyze_photo.py -v
```

`test_engine.py` также можно запустить напрямую как скрипт (содержит `if __name__ == "__main__"` блок — не определено в текущей версии проекта, проверьте файл).

## Зависимости для тестов

- `pytest`
- `httpx` (для `fastapi.testclient.TestClient`)

Файл `requirements.txt` в репозитории **отсутствует**.

## Группы тестов

### `test_engine.py` — RuleEngine / KnowledgeBase

| Тест | Что проверяет |
|------|---------------|
| `test_weeds_without_mowing` | `weed_presence` без `needs_mowing` → сорняки есть, `mow_lawn` нет |
| `test_mowing_when_needed` | `needs_mowing=true` → `mow_lawn` |
| `test_overseed_with_seeds` | `bare_spots` → `overseed` + семена в knowledge |
| `test_fertilizer_enrichment` | `apply_fertilizer` → удобрения в knowledge |
| `test_herbicides_low_density_no_type` | низкая плотность без типа → commercial_product |
| `test_herbicides_low_density_broadleaf` | broadleaf → селективные препараты |
| `test_herbicides_grass_no_broadleaf_products` | злаковые сорняки → без broadleaf-препаратов |

### `test_analyze_photo.py` — API и валидация

| Группа | Тесты |
|--------|-------|
| `validate_vision_results` | принятие валидных газонов; отклонение non-lawn; zero confidence; missing is_lawn; non-bool is_lawn |
| `aggregate_results` | `is_lawn` через `all()`; `confidence` из первого фото |
| `/analyze-photo` (mock) | успешный анализ; all furniture → 400; mixed set → 400; zero confidence → 422; missing is_lawn → 422 |
| Shared prompt | один `SYSTEM_PROMPT` для всех провайдеров |

## Mocking

Тесты `/analyze-photo` **не вызывают** реальные Vision API.

Используется `monkeypatch` на `main._analyze_one_image` — функция возвращает заранее подготовленные dict.

## Критические regression cases

| Сценарий | Ожидаемое поведение |
|----------|---------------------|
| 2–3 нормальных фото газона | HTTP 200, RuleEngine вызывается, есть recommendations |
| Все фото — не газон | HTTP 400, `NOT_LAWN_MESSAGE` |
| Смешанный набор (газон + не-газон) | HTTP 400, весь набор отклоняется |
| `is_lawn` отсутствует | HTTP 422, `UNRECOGNIZED_IMAGE_MESSAGE` |
| `is_lawn = null` (не bool) | HTTP 422 |
| `confidence = 0` у всех фото | HTTP 422, `LOW_CONFIDENCE_MESSAGE` |

Числовой порог confidence (например 0.2) в коде **не задан** — отклоняется только `<= 0`.

## Что не покрыто тестами

- Реальные вызовы OpenAI / Gemini / Qwen API.
- Frontend (нет e2e / browser tests).
- Интеграционные тесты с реальными изображениями.
