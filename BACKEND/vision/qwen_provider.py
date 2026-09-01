"""
Qwen Vision-провайдер для GreenScan.

Использует OpenRouter-совместимый OpenAI-клиент для обращения к модели
Qwen2.5-VL (по умолчанию `qwen/qwen-2.5-vl-7b-instruct:free`) с целью
визуальной диагностики газона.

Провайдер возвращает данные в той же внутренней структуре, что и
остальные Vision-провайдеры проекта (OpenAI / Gemini). RuleEngine
и KnowledgeBase обрабатывают результат без изменений.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from openai import OpenAI

from vision.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "qwen/qwen-2.5-vl-7b-instruct:free"

# Допустимые MIME-типы изображений, которые поддерживает Qwen через OpenRouter.
_ALLOWED_MIME = {"jpeg", "jpg", "png", "webp"}


class QwenProviderError(RuntimeError):
    """Базовое исключение провайдера Qwen (OpenRouter)."""


def _normalize_mime(mime_type: Optional[str]) -> str:
    """
    Приводит произвольный MIME (или None) к виду 'jpeg' | 'png' | 'webp'.
    По умолчанию используется 'jpeg', как и в существующих провайдерах.
    """
    if not mime_type:
        return "jpeg"
    mt = mime_type.lower().strip()
    # 'image/jpeg' → 'jpeg'
    if "/" in mt:
        mt = mt.split("/", 1)[1]
    if mt == "jpg":
        mt = "jpeg"
    if mt not in _ALLOWED_MIME:
        logger.warning("Qwen: неизвестный MIME '%s', использую jpeg", mime_type)
        return "jpeg"
    return mt


def _build_client() -> OpenAI:
    """Создаёт OpenAI-совместимый клиент для OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise QwenProviderError(
            "Не задан OPENROUTER_API_KEY. Укажите ключ в .env (см. .env.example)."
        )
    return OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)


def _strip_markdown_fence(content: str) -> str:
    """
    Удаляет Markdown-обёртку ```json ... ```, если она есть,
    и вырезает первый валидный JSON-объект из строки.
    """
    if "```" in content:
        content = content.replace("```json", "").replace("```", "").strip()

    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        content = content[start : end + 1]
    return content.strip()


def _validate(parsed: Any) -> dict:
    """
    Минимальная проверка структуры ответа. Должны присутствовать
    все ключи, ожидаемые RuleEngine (bool/None/str), иначе — ошибка.
    """
    if not isinstance(parsed, dict):
        raise QwenProviderError("Ответ модели не является JSON-объектом")

    required_bools = {
        "dryness",
        "pale_grass",
        "weed_presence",
        "fungal_signs",
        "thin_lawn",
        "bare_spots",
        "needs_mowing",
        "moss_presence",
    }
    missing = [k for k in required_bools if k not in parsed]
    if missing:
        raise QwenProviderError(
            "В ответе модели отсутствуют обязательные поля: " + ", ".join(missing)
        )

    return parsed


def analyze_image(
    base64_image: str,
    mime_type: Optional[str] = "jpeg",
) -> Optional[dict]:
    """
    Анализирует одно изображение газона и возвращает словарь LawnState
    (или None, если ответ не удалось распарсить).

    Параметры:
        base64_image: строка base64 (без префикса data:...).
        mime_type: MIME-тип изображения, например 'image/jpeg' / 'png' / 'webp'.
                   Если None или неизвестен — используется 'jpeg'.
    """
    if not base64_image:
        logger.warning("Qwen: пустое изображение, пропускаю")
        return None

    try:
        client = _build_client()
    except QwenProviderError as e:
        # Ошибка конфигурации — пробрасываем наверх, чтобы endpoint вернул 500
        # с человеческим сообщением (без раскрытия ключа).
        raise

    mime = _normalize_mime(mime_type)
    model = os.getenv("QWEN_VISION_MODEL", DEFAULT_MODEL)

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0,
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
    except Exception as e:  # openai.OpenAIError и прочие сетевые ошибки
        type_name = type(e).__name__
        msg = str(e)
        # Не раскрываем ключ — он может встретиться в дампах исключений.
        msg = msg.replace(os.getenv("OPENROUTER_API_KEY", ""), "***")
        raise QwenProviderError(f"OpenRouter вернул ошибку ({type_name}): {msg}") from e

    if not response or not getattr(response, "choices", None):
        raise QwenProviderError("Qwen: пустой ответ от OpenRouter (нет choices)")

    choice = response.choices[0]
    raw_content = getattr(getattr(choice, "message", None), "content", None)
    if not raw_content or not raw_content.strip():
        raise QwenProviderError("Qwen: модель вернула пустой content")

    content = _strip_markdown_fence(raw_content)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error("Qwen: невалидный JSON: %s | RAW=%r", e, content)
        raise QwenProviderError(f"Qwen: невалидный JSON в ответе модели: {e}") from e

    return _validate(parsed)


def get_default_model() -> str:
    """Возвращает имя модели, которое фактически будет использоваться."""
    return os.getenv("QWEN_VISION_MODEL", DEFAULT_MODEL)
