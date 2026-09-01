"""Regression-тесты валидации газона /analyze-photo без реальных Vision API."""

from io import BytesIO

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import main
from main import (
    LOW_CONFIDENCE_MESSAGE,
    NOT_LAWN_MESSAGE,
    UNRECOGNIZED_IMAGE_MESSAGE,
    aggregate_results,
    validate_vision_results,
)


def _lawn_result(**overrides):
    base = {
        "is_lawn": True,
        "lawn_confidence": 0.95,
        "dryness": False,
        "pale_grass": False,
        "weed_presence": False,
        "weed_type": None,
        "weed_density": None,
        "fungal_signs": False,
        "thin_lawn": False,
        "bare_spots": False,
        "needs_mowing": False,
        "moss_presence": False,
        "soil_issue": None,
        "confidence": 0.85,
    }
    base.update(overrides)
    return base


def _non_lawn_result(**overrides):
    return _lawn_result(
        is_lawn=False,
        lawn_confidence=0.05,
        confidence=0.0,
        **overrides,
    )


# --- validate_vision_results ---


def test_validate_accepts_all_lawns():
    validate_vision_results([_lawn_result(), _lawn_result(confidence=0.7)])


def test_validate_rejects_any_non_lawn():
    with pytest.raises(HTTPException) as exc:
        validate_vision_results([_lawn_result(), _non_lawn_result()])
    assert exc.value.status_code == 400
    assert NOT_LAWN_MESSAGE in exc.value.detail


def test_validate_rejects_all_non_lawn():
    with pytest.raises(HTTPException) as exc:
        validate_vision_results([_non_lawn_result(), _non_lawn_result()])
    assert exc.value.status_code == 400


def test_validate_rejects_zero_confidence():
    with pytest.raises(HTTPException) as exc:
        validate_vision_results(
            [
                _lawn_result(confidence=0.0),
                _lawn_result(confidence=0.0),
            ]
        )
    assert exc.value.status_code == 422
    assert LOW_CONFIDENCE_MESSAGE in exc.value.detail


def test_validate_accepts_if_any_photo_has_positive_confidence():
    validate_vision_results(
        [
            _lawn_result(confidence=0.0),
            _lawn_result(confidence=0.6),
        ]
    )


def test_validate_not_lawn_takes_priority_over_confidence():
    """Смешанный набор: сначала отказ по is_lawn, не сообщение о confidence."""
    with pytest.raises(HTTPException) as exc:
        validate_vision_results(
            [
                _lawn_result(confidence=0.9),
                _non_lawn_result(),
            ]
        )
    assert exc.value.status_code == 400
    assert NOT_LAWN_MESSAGE in exc.value.detail


def test_validate_rejects_missing_is_lawn():
    """Отсутствие is_lawn нельзя трактовать как True."""
    bad = _lawn_result()
    del bad["is_lawn"]
    with pytest.raises(HTTPException) as exc:
        validate_vision_results([_lawn_result(), bad])
    assert exc.value.status_code == 422
    assert UNRECOGNIZED_IMAGE_MESSAGE in exc.value.detail


def test_validate_rejects_non_bool_is_lawn():
    with pytest.raises(HTTPException) as exc:
        validate_vision_results([_lawn_result(is_lawn=None), _lawn_result()])
    assert exc.value.status_code == 422
    assert UNRECOGNIZED_IMAGE_MESSAGE in exc.value.detail


# --- aggregate_results ---


def test_aggregate_is_lawn_uses_all_not_any():
    """Защита: any([True, False]) == True — нельзя терять плохую фото."""
    final = aggregate_results([_lawn_result(), _non_lawn_result()])
    assert final["is_lawn"] is False


def test_aggregate_confidence_keeps_first_value():
    """Прежнее поведение проекта: числовые поля → values[0], не max()."""
    final = aggregate_results(
        [
            _lawn_result(confidence=0.15),
            _lawn_result(confidence=0.95),
        ]
    )
    assert final["confidence"] == 0.15


# --- /analyze-photo с mock Vision ---


@pytest.fixture
def client():
    return TestClient(main.app)


def _fake_files(n: int = 2):
    """Минимальные «файлы» для multipart; Vision подменяется mock'ом."""
    return [
        ("files", (f"photo{i}.jpg", BytesIO(b"fake-image-bytes"), "image/jpeg"))
        for i in range(n)
    ]


def test_analyze_photo_ok_with_lawns(client, monkeypatch):
    queue = [
        _lawn_result(weed_presence=True, weed_type="broadleaf", weed_density="low"),
        _lawn_result(),
    ]

    def fake_analyze(_b64, mime="jpeg"):
        return queue.pop(0)

    monkeypatch.setattr(main, "_analyze_one_image", fake_analyze)

    response = client.post("/analyze-photo", files=_fake_files(2))
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert "final_state" in data
    assert "is_lawn" not in data["final_state"]
    assert data["final_state"]["weed_presence"] is True


def test_analyze_photo_rejects_all_furniture(client, monkeypatch):
    queue = [_non_lawn_result(), _non_lawn_result()]

    monkeypatch.setattr(
        main,
        "_analyze_one_image",
        lambda *_a, **_k: queue.pop(0),
    )

    response = client.post("/analyze-photo", files=_fake_files(2))
    assert response.status_code == 400
    assert NOT_LAWN_MESSAGE in response.json()["detail"]


def test_analyze_photo_rejects_mixed_set(client, monkeypatch):
    queue = [_lawn_result(), _lawn_result(), _non_lawn_result()]

    monkeypatch.setattr(
        main,
        "_analyze_one_image",
        lambda *_a, **_k: queue.pop(0),
    )

    response = client.post("/analyze-photo", files=_fake_files(3))
    assert response.status_code == 400
    assert NOT_LAWN_MESSAGE in response.json()["detail"]


def test_analyze_photo_rejects_zero_confidence(client, monkeypatch):
    queue = [
        _lawn_result(confidence=0.0),
        _lawn_result(confidence=0.0),
    ]

    monkeypatch.setattr(
        main,
        "_analyze_one_image",
        lambda *_a, **_k: queue.pop(0),
    )

    response = client.post("/analyze-photo", files=_fake_files(2))
    assert response.status_code == 422
    assert LOW_CONFIDENCE_MESSAGE in response.json()["detail"]


def test_analyze_photo_rejects_missing_is_lawn(client, monkeypatch):
    missing = _lawn_result()
    del missing["is_lawn"]
    queue = [_lawn_result(), missing]

    monkeypatch.setattr(
        main,
        "_analyze_one_image",
        lambda *_a, **_k: queue.pop(0),
    )

    response = client.post("/analyze-photo", files=_fake_files(2))
    assert response.status_code == 422
    assert UNRECOGNIZED_IMAGE_MESSAGE in response.json()["detail"]


def test_shared_prompt_contains_is_lawn():
    from vision.prompts import SYSTEM_PROMPT
    from vision import gemini_provider, qwen_provider

    assert "is_lawn" in SYSTEM_PROMPT
    assert "lawn_confidence" in SYSTEM_PROMPT
    assert gemini_provider.SYSTEM_PROMPT is SYSTEM_PROMPT
    assert qwen_provider.SYSTEM_PROMPT is SYSTEM_PROMPT
    assert main.SYSTEM_PROMPT is SYSTEM_PROMPT
