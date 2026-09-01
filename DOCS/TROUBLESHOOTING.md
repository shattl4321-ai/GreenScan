# Troubleshooting GreenScan

## Backend не запускается: `Could not import module "main"`

**Причина:** uvicorn запущен не из `BACKEND/`.

**Решение:**

```powershell
cd BACKEND
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8001
```

---

## Frontend показывает список файлов вместо приложения

**Причина:** `python -m http.server` запущен из `FRONTEND/`, а `index.html` в корне проекта.

**Решение:**

```powershell
cd C:\Users\Dmitry\Projects_UII\GreenScan
python -m http.server 3000
```

Откройте `http://127.0.0.1:3000/`.

---

## Vision API недоступен (HTTP 503)

**Что видит пользователь:** «Сервис анализа временно недоступен. Попробуйте позже.»

**Что смотреть разработчику:**
- `BACKEND/logs/greenscan.log`
- Консоль uvicorn
- Корректность API-ключа в `.env`
- Доступность сети к провайдеру (OpenAI / Google / OpenRouter)
- Значение `VISION_PROVIDER`

---

## Invalid JSON from Vision (HTTP 422)

**Что видит пользователь:** «AI вернул некорректный результат. Попробуйте другие снимки.»

**Причина:** Vision вернул ответ, который не удалось распарсить как JSON (ни одно фото).

**Действия:**
- Попробовать другие фото.
- Проверить логи (warning о некорректном JSON).
- Для Gemini: проверить консоль (`print` в `gemini_provider.py`).

---

## Image is not lawn (HTTP 400)

**Что видит пользователь:** «Одно или несколько загруженных изображений не содержат газон. Замените неподходящие фотографии и попробуйте снова.»

**Причина:** Vision вернул `is_lawn = false` хотя бы для одного фото.

**Действия:** Заменить неподходящие фото. Весь набор отклоняется, даже если часть фото — газон.

---

## Missing / invalid `is_lawn` (HTTP 422)

**Что видит пользователь:** «Не удалось достоверно распознать изображение. Попробуйте загрузить другие фотографии газона.»

**Причина:** Vision не вернул `is_lawn` или вернул не-bool (например `null`).

---

## Low confidence (HTTP 422)

**Что видит пользователь:** «Не удалось выполнить достоверный анализ газона. Загрузите более чёткие фотографии газона и попробуйте снова.»

**Причина:** `max(confidence)` по всем фото `<= 0`.

---

## Wrong number of photos (HTTP 400)

**Что видит пользователь:** «Загрузите от 2 до 5 изображений газона.»

**Причина:** Отправлено меньше 2 или больше 5 файлов.

---

## API key missing

### OpenAI (`VISION_PROVIDER=openai`)

Клиент создаётся при старте. При отсутствии `OPENAI_API_KEY` вызов API завершится ошибкой → HTTP 503.

### Gemini (`VISION_PROVIDER=gemini`)

`GOOGLE_API_KEY` нужен при импорте/вызове `gemini_provider.py`. Ошибка → HTTP 503.

### Qwen (`VISION_PROVIDER=qwen`)

Отсутствие `OPENROUTER_API_KEY` → `QwenProviderError` → HTTP 503.

---

## CORS errors в браузере

Backend настроен с `allow_origins=["*"]`. Если CORS-ошибка возникает:
- Проверьте, что backend запущен на `8001`.
- Проверьте `API_URL` в `FRONTEND/app.js`.
- Frontend и backend должны быть доступны (не mixed content HTTP/HTTPS).

---

## Tests fail

```powershell
cd BACKEND
.\venv\Scripts\Activate.ps1
pip install pytest httpx
pytest -v
```

Тесты не требуют реальных API-ключей (Vision mock'ается).

---

## Unknown VISION_PROVIDER (HTTP 500)

**Причина:** `VISION_PROVIDER` не равен `openai`, `gemini` или `qwen`.

**Решение:** Исправить значение в `.env`.

---

## Frontend: «Не удалось выполнить анализ»

**Причина:** Сетевая ошибка или backend недоступен.

**Действия:**
- Убедиться, что backend запущен на порту 8001.
- Проверить консоль браузера (Network tab).
