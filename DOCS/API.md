# API GreenScan

## Endpoints

### `POST /analyze-photo`

Анализ состояния газона по нескольким фотографиям.

#### Request

- **Content-Type:** `multipart/form-data`
- **Поле:** `files` (массив файлов)
- **Количество:** от 2 до 5 включительно

Поддерживаемые MIME (backend, `_detect_mime`):

- `image/jpeg` / `image/jpg` → `jpeg`
- `image/png` → `png`
- `image/webp` → `webp`
- Если тип не распознан → default `jpeg`

Frontend принимает: `image/jpeg`, `image/png`, `image/jpg`, `image/webp`.

Ограничения размера файла в коде **не заданы**.

#### Successful response — `200 OK`

```json
{
  "individual_results": [
    {
      "is_lawn": true,
      "lawn_confidence": 0.95,
      "dryness": false,
      "pale_grass": false,
      "weed_presence": true,
      "weed_type": "broadleaf",
      "weed_density": "low",
      "fungal_signs": false,
      "thin_lawn": true,
      "bare_spots": false,
      "needs_mowing": true,
      "moss_presence": false,
      "soil_issue": null,
      "confidence": 0.9
    }
  ],
  "final_state": {
    "dryness": false,
    "pale_grass": false,
    "weed_presence": true,
    "weed_type": "broadleaf",
    "weed_density": "low",
    "fungal_signs": false,
    "thin_lawn": true,
    "bare_spots": false,
    "needs_mowing": true,
    "moss_presence": false,
    "soil_issue": null,
    "confidence": 0.9
  },
  "actions": [
    "apply_fertilizer",
    "mow_lawn",
    "overseed",
    "spot_weed_control"
  ],
  "recommendations": [
    {
      "id": "apply_fertilizer",
      "name": "Внести удобрение",
      "category": "fertilization",
      "description": "Подкормить газон удобрением в зависимости от сезона и состояния",
      "related_to": ["nutrient_deficiency", "pale_grass", "slow_growth"],
      "knowledge_items": []
    }
  ]
}
```

Примечания:

- `individual_results` — сырые ответы Vision по каждому фото (включая `is_lawn`, `lawn_confidence`).
- `final_state` — агрегированное состояние **без** `is_lawn` и `lawn_confidence`.
- `actions` — список строковых ID действий.
- `recommendations` — обогащённые объекты; `knowledge_items` присутствует только для части действий (`apply_fertilizer`, `spot_weed_control`, `full_weed_control`, `overseed`).

#### Ошибки

| HTTP | Причина | `detail` |
|------|---------|----------|
| 400 | Меньше 2 или больше 5 файлов | `Загрузите от 2 до 5 изображений газона.` |
| 400 | Хотя бы одно фото с `is_lawn = false` | `Одно или несколько загруженных изображений не содержат газон. Замените неподходящие фотографии и попробуйте снова.` |
| 422 | `is_lawn` отсутствует или не `bool` | `Не удалось достоверно распознать изображение. Попробуйте загрузить другие фотографии газона.` |
| 422 | У всех фото `confidence <= 0` | `Не удалось выполнить достоверный анализ газона. Загрузите более чёткие фотографии газона и попробуйте снова.` |
| 422 | Ни один JSON от Vision не распарсился | `AI вернул некорректный результат. Попробуйте другие снимки.` |
| 500 | `VISION_PROVIDER` не в списке допустимых | `Сервис анализа временно недоступен. Попробуйте позже.` |
| 503 | Ошибка вызова Vision API | `Сервис анализа временно недоступен. Попробуйте позже.` |

Формат ошибки FastAPI:

```json
{
  "detail": "Текст ошибки"
}
```

Frontend отображает `data.detail` при `!response.ok`.

---

## Автоматические endpoints FastAPI

| Path | Описание |
|------|----------|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc |
| `/openapi.json` | OpenAPI schema |

Dedicated `/health` endpoint **отсутствует**.
