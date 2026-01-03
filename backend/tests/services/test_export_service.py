
import json
from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.log import DietaryLog
from app.services import export_service


@pytest.mark.asyncio
async def test_export_logs_as_csv():
    # Arrange
    user_id = uuid4()
    log = DietaryLog(
        id=uuid4(),
        user_id=user_id,
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        calories=500,
        transcript="A tasty burger",
        description="Burger with cheese",
        image_path="path/to/image.jpg",
        status="logged"
    )
    # Mock user relationship
    user_mock = MagicMock()
    user_mock.email = "test@example.com"
    log.user = user_mock

    # Act
    csv_gen = export_service.export_logs_as_csv([log])
    content = "".join([str(chunk) for chunk in csv_gen])

    # Assert
    expected_header = "Log ID,User Email,Meal Type,Food Items,Calories,Created At,Transcription"
    assert expected_header in content
    assert str(log.id) in content
    assert "test@example.com" in content
    assert "A tasty burger" in content
    assert "Burger with cheese" in content # Food Items
    assert "2023-01-01T12:00:00+00:00" in content

@pytest.mark.asyncio
async def test_export_logs_as_json():
    # Arrange
    user_id = uuid4()
    log = DietaryLog(
        id=uuid4(),
        user_id=user_id,
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
        calories=500,
        transcript="A tasty burger",
        description="Burger with cheese",
        image_path="path/to/image.jpg",
        status="logged"
    )
    # Mock user relationship
    user_mock = MagicMock()
    user_mock.email = "test@example.com"
    # Provide .dict() method if service uses it, or just attributes
    # The service will likely use Pydantic model serialization or dict conversion
    log.user = user_mock

    # Act
    json_gen = export_service.export_logs_as_json([log])
    content = "".join([str(chunk) for chunk in json_gen])
    
    # Assert
    data = json.loads(content)
    assert isinstance(data, list)
    assert len(data) == 1
    item = data[0]
    assert item["id"] == str(log.id)
    assert item["user_email"] == "test@example.com"
    assert item["transcript"] == "A tasty burger"
