from unittest.mock import MagicMock, patch

import pytest

from app.schemas.analysis import FoodItem
from app.services.semantic_gatekeeper import SemanticGatekeeper


@pytest.fixture
def mock_registry():
    with patch("app.services.semantic_gatekeeper.registry") as mock:
        yield mock


def test_assess_lexical_boundedness_no_umbrella(mock_registry):
    # Setup
    mock_registry.get_risk_profile.return_value.is_umbrella_term = False

    items = [FoodItem(name="Turkey Sandwich", confidence=0.9, quantity="1")]

    # Execute
    unbounded = SemanticGatekeeper.assess_lexical_boundedness(items)

    # Verify
    assert len(unbounded) == 0


def test_assess_lexical_boundedness_with_umbrella(mock_registry):
    # Setup
    def get_risk_profile_side_effect(name):
        mock = MagicMock()
        if name == "Sandwich":
            mock.is_umbrella_term = True
        else:
            mock.is_umbrella_term = False
        return mock

    mock_registry.get_risk_profile.side_effect = get_risk_profile_side_effect

    items = [
        FoodItem(name="Sandwich", confidence=0.9, quantity="1"),
        FoodItem(name="Apple", confidence=0.95, quantity="1"),
    ]

    # Execute
    unbounded = SemanticGatekeeper.assess_lexical_boundedness(items)

    # Verify
    assert len(unbounded) == 1
    assert "Sandwich" in unbounded
