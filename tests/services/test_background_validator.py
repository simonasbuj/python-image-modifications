from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.services.background_validator import BackgroundValidator


@pytest.fixture
def validator_service() -> BackgroundValidator:
    return BackgroundValidator(api_endpoint="http://fake:8000")


def make_mock_response(data: Any, status_code: int = 200) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = data
    mock_resp.raise_for_status.return_value = None
    return mock_resp


def test_get_pending_modifications_success(
    validator_service: BackgroundValidator,
) -> None:
    mock_response: list[dict[str, str | int]] = [
        {
            "id": 0,
            "image_id": 0,
            "modified_image_path": "string",
            "modification_algorithm": "string",
            "num_modifications": 0,
            "verification_status": "string",
            "created_at": "2026-02-27T12:35:59.967Z",
            "verified_at": "2026-02-27T12:35:59.967Z",
        }
    ]

    with patch(
        "requests.get", return_value=make_mock_response(mock_response)
    ) as mock_get:
        result = validator_service.get_pending_modifications()

    mock_get.assert_called_once_with(
        f"{validator_service.api_endpoint}/api/modifications",
        params={"skip": 0, "limit": 100, "status": "pending"},
        timeout=60,
    )
    assert result == mock_response


def test_validate_modification_success(validator_service: BackgroundValidator) -> None:
    mod_id = 1
    mock_response: dict[str, str | int] = {
        "modification_id": mod_id,
        "message": "string",
        "reversed_path": "string",
        "original_path": "string",
        "modified_path": "string",
        "is_reversible": True,
    }

    with patch(
        "requests.post", return_value=make_mock_response(mock_response)
    ) as mock_post:
        result = validator_service.validate_modification(mod_id)

    mock_post.assert_called_once_with(
        f"{validator_service.api_endpoint}/api/modifications/{mod_id}/reverse/",
        json={"should_save_reversed_img": False},
        timeout=60,
    )
    assert result == mock_response
