from dotenv import load_dotenv
import os

load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import base64
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Optional

from engine import RuleEngine
from vision.prompts import SYSTEM_PROMPT

provider_name = os.getenv("VISION_PROVIDER", "openai").strip().lower()
openai_vision_model = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini").strip()

# Lazy-импорт провайдеров, чтобы не падать на отсутствующих зависимостях,
# если выбран другой VISION_PROVIDER.
gemini_analyze_image = None
qwen_analyze_image = None
QwenProviderError = None

if provider_name == "gemini":
    from vision.gemini_provider import analyze_image as gemini_analyze_image
elif provider_name == "qwen":
    from vision.qwen_provider import analyze_image as qwen_analyze_image
    from vision.qwen_provider import QwenProviderError

ALLOWED_PROVIDERS = ("openai", "gemini", "qwen")

# Поля только для валидации входа; в RuleEngine не передаём.
_VALIDATION_ONLY_KEYS = ("is_lawn", "lawn_confidence")

# --- LOGGING ---
LOGS_DIR = Path(__file__).resolve().parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

log_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] endpoint=%(endpoint)s provider=%(provider)s model=%(model)s %(message)s"
)

logger = logging.getLogger("greenscan")
logger.setLevel(logging.INFO)
# Предотвращаем дублирование при повторных импортах/перезагрузках.
logger.handlers = []

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

file_handler = RotatingFileHandler(
    LOGS_DIR / "greenscan.log",
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# --- APP ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = RuleEngine()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

logger.info(
    "GreenScan backend started. provider=%s model=%s",
    provider_name,
    openai_vision_model,
    extra={"endpoint": "startup", "provider": provider_name, "model": openai_vision_model},
)

# --- UTILS ---
def encode_image(file_bytes):
    return base64.b64encode(file_bytes).decode("utf-8")


def _detect_mime(upload: UploadFile) -> str:
    """
    Возвращает короткий MIME (jpeg/png/webp) по content_type загруженного файла.
    По умолчанию — 'jpeg', как и раньше.
    """
    ct = (upload.content_type or "").lower()
    if ct.startswith("image/"):
        sub = ct.split("/", 1)[1]
        if sub == "jpg":
            return "jpeg"
        if sub in ("jpeg", "png", "webp"):
            return sub
    return "jpeg"


# --- ERROR HELPERS ---
def _log_provider_error(exc: Exception):
    """Логирует техническую причину ошибки провайдера без раскрытия секретов."""
    type_name = type(exc).__name__
    msg = str(exc)
    # Подчищаем возможные следы ключа из сообщения об ошибке.
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key:
        msg = msg.replace(api_key, "***")
    msg = msg[:400]
    logger.error(
        "Ошибка провайдера: %s: %s",
        type_name,
        msg,
        extra={
            "endpoint": "/analyze-photo",
            "provider": provider_name,
            "model": openai_vision_model,
        },
    )


# --- AGGREGATION ---
def aggregate_results(results: List[dict]):
    final = {}
    keys = results[0].keys()

    for key in keys:
        values = [r.get(key) for r in results if key in r]
        if not values:
            continue

        # is_lawn: True только если ВСЕ фото — газон (защита от any()).
        # confidence остаётся прежним поведением проекта (первый числовой
        # результат в ветке else ниже) — max() вводил бы в заблуждение.
        if key == "is_lawn":
            final[key] = all(bool(v) for v in values)
            continue

        # булевые → ANY
        if isinstance(values[0], bool):
            final[key] = any(values)

        # weed_density → максимум
        elif key == "weed_density":
            order = {"low": 1, "medium": 2, "high": 3}
            best = None
            best_score = 0

            for v in values:
                if v in order and order[v] > best_score:
                    best = v
                    best_score = order[v]

            final[key] = best

        # строки → чаще всего
        elif isinstance(values[0], str):
            final[key] = max(set(values), key=values.count)

        else:
            final[key] = values[0]

    return final


# --- USER-FACING MESSAGE ---
USER_ERROR_MESSAGE = "Сервис анализа временно недоступен. Попробуйте позже."
JSON_ERROR_MESSAGE = "AI вернул некорректный результат. Попробуйте другие снимки."
NOT_LAWN_MESSAGE = (
    "Одно или несколько загруженных изображений не содержат газон. "
    "Замените неподходящие фотографии и попробуйте снова."
)
LOW_CONFIDENCE_MESSAGE = (
    "Не удалось выполнить достоверный анализ газона. "
    "Загрузите более чёткие фотографии газона и попробуйте снова."
)
UNRECOGNIZED_IMAGE_MESSAGE = (
    "Не удалось достоверно распознать изображение. "
    "Попробуйте загрузить другие фотографии газона."
)
_MISSING = object()


def validate_vision_results(results: List[dict]) -> None:
    """
    Проверяет результаты Vision до агрегации и RuleEngine.

    - is_lawn обязателен; отсутствие / не-bool → HTTP 422.
    - Если хотя бы одно фото не газон (is_lawn=false) → HTTP 400.
    - Если уверенность в диагностике нулевая / отсутствует → HTTP 422.
    """
    for result in results:
        is_lawn = result.get("is_lawn", _MISSING)
        if is_lawn is _MISSING or not isinstance(is_lawn, bool):
            raise HTTPException(
                status_code=422,
                detail=UNRECOGNIZED_IMAGE_MESSAGE,
            )
        if is_lawn is False:
            raise HTTPException(status_code=400, detail=NOT_LAWN_MESSAGE)

    confidences: List[float] = []
    for result in results:
        c = result.get("confidence")
        if isinstance(c, (int, float)):
            confidences.append(float(c))
        else:
            confidences.append(0.0)

    if not confidences or max(confidences) <= 0:
        raise HTTPException(status_code=422, detail=LOW_CONFIDENCE_MESSAGE)


def _analyze_one_image(base64_image: str, mime: str = "jpeg") -> Optional[dict]:
    """
    Анализ одного изображения выбранным Vision-провайдером.
    Вынесено отдельно, чтобы тесты могли подменять вызов без реальных API.
    """
    if provider_name == "gemini":
        try:
            return gemini_analyze_image(base64_image)
        except Exception as e:
            _log_provider_error(e)
            raise HTTPException(status_code=503, detail=USER_ERROR_MESSAGE)

    if provider_name == "qwen":
        try:
            return qwen_analyze_image(base64_image, mime_type=mime)
        except QwenProviderError as e:
            _log_provider_error(e)
            raise HTTPException(status_code=503, detail=USER_ERROR_MESSAGE)

    try:
        response = client.chat.completions.create(
            model=openai_vision_model,
            temperature=0,
            timeout=60,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Проанализируй газон"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{mime};base64,{base64_image}"
                            },
                        },
                    ],
                },
            ],
        )
    except Exception as e:
        _log_provider_error(e)
        raise HTTPException(status_code=503, detail=USER_ERROR_MESSAGE)

    content = response.choices[0].message.content.strip()

    if "```" in content:
        content = content.replace("```json", "").replace("```", "").strip()

    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1:
        content = content[start : end + 1]

    try:
        return json.loads(content)
    except Exception as e:
        logger.warning(
            "Некорректный JSON в ответе модели: %s",
            e,
            extra={
                "endpoint": "/analyze-photo",
                "provider": provider_name,
                "model": openai_vision_model,
            },
        )
        return None


# --- ANALYZE ---
@app.post("/analyze-photo")
async def analyze_photo(files: List[UploadFile] = File(...)):
    if provider_name not in ALLOWED_PROVIDERS:
        logger.error(
            "Неизвестный VISION_PROVIDER='%s'. Допустимые значения: %s",
            provider_name,
            ", ".join(ALLOWED_PROVIDERS),
            extra={"endpoint": "/analyze-photo", "provider": provider_name, "model": "unknown"},
        )
        raise HTTPException(
            status_code=500,
            detail="Сервис анализа временно недоступен. Попробуйте позже.",
        )

    if len(files) < 2 or len(files) > 5:
        raise HTTPException(
            status_code=400,
            detail="Загрузите от 2 до 5 изображений газона.",
        )

    results = []

    for file in files:
        contents = await file.read()
        base64_image = encode_image(contents)
        mime = _detect_mime(file)
        parsed = _analyze_one_image(base64_image, mime)
        if parsed is not None:
            results.append(parsed)

    if not results:
        logger.warning(
            "Не удалось распарсить ни один результат от модели",
            extra={
                "endpoint": "/analyze-photo",
                "provider": provider_name,
                "model": openai_vision_model,
            },
        )
        raise HTTPException(status_code=422, detail=JSON_ERROR_MESSAGE)

    # Валидация ДО агрегации и ДО RuleEngine: одна плохая фото → отказ всего набора.
    validate_vision_results(results)

    final_state = aggregate_results(results)
    for key in _VALIDATION_ONLY_KEYS:
        final_state.pop(key, None)

    actions = engine.evaluate(final_state)
    recommendations = engine.enrich(actions, final_state)

    return {
        "individual_results": results,
        "final_state": final_state,
        "actions": actions,
        "recommendations": recommendations,
    }