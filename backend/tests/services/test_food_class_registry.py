from unittest.mock import mock_open, patch

import pytest

from app.services.food_class_registry import FoodClassRegistry, RiskProfile

# Mock YAML data
MOCK_YAML_DATA = """
default:
  weights: { ingredients: 0.5, prep: 0.5, volume: 0.5 }
  semantic_penalty: 0.0
  mandatory_clarification: false
  is_umbrella_term: false

classes:
  burger:
    weights: { ingredients: 0.9, prep: 0.7, volume: 0.3 }
    semantic_penalty: 4.0
    mandatory_clarification: true
    is_umbrella_term: true
    aliases: ["hamburger", "patty"]
  
  milk:
    weights: { ingredients: 0.8, prep: 0.2, volume: 0.2 }
    semantic_penalty: 3.5
    mandatory_clarification: true
    is_umbrella_term: true
    aliases: ["latte"]
"""


@pytest.fixture
def mock_registry():
    # Reset singleton
    FoodClassRegistry._instance = None

    with patch("builtins.open", mock_open(read_data=MOCK_YAML_DATA)):
        with patch("pathlib.Path.exists", return_value=True):
            registry = FoodClassRegistry()
            yield registry


def test_singleton_behavior(mock_registry):
    r1 = FoodClassRegistry()
    r2 = FoodClassRegistry()
    assert r1 is r2
    assert r1 is mock_registry


def test_load_registry(mock_registry):
    assert mock_registry._default_profile is not None
    assert mock_registry._default_profile.semantic_penalty == 0.0
    assert "burger" in mock_registry._registry
    assert "milk" in mock_registry._registry


def test_lookup_exact_match(mock_registry):
    assert mock_registry.lookup("burger") == "burger"
    assert mock_registry.lookup("milk") == "milk"


def test_lookup_alias_match(mock_registry):
    assert mock_registry.lookup("hamburger") == "burger"
    assert mock_registry.lookup("latte") == "milk"


def test_lookup_case_insensitive(mock_registry):
    assert mock_registry.lookup("Hamburger") == "burger"
    assert mock_registry.lookup("LATTE") == "milk"


def test_lookup_fuzzy_containment(mock_registry):
    # "vegan burger" contains "burger"
    assert mock_registry.lookup("vegan burger") == "burger"
    # "soy latte" contains "latte" -> "milk"
    assert mock_registry.lookup("soy latte") == "milk"
    # "burger king" contains "burger"
    assert mock_registry.lookup("burger king meal") == "burger"


def test_lookup_no_match(mock_registry):
    assert mock_registry.lookup("apple") is None
    assert mock_registry.lookup("water") is None


def test_get_risk_profile_match(mock_registry):
    profile = mock_registry.get_risk_profile("hamburger")
    assert isinstance(profile, RiskProfile)
    assert profile.semantic_penalty == 4.0
    assert profile.mandatory_clarification is True
    assert profile.weights["ingredients"] == 0.9


def test_get_risk_profile_default(mock_registry):
    profile = mock_registry.get_risk_profile("apple")
    assert isinstance(profile, RiskProfile)
    assert profile.semantic_penalty == 0.0
    assert profile.mandatory_clarification is False


def test_load_invalid_yaml_fresh_start():
    # Reset singleton to ensure a fresh start
    FoodClassRegistry._instance = None

    # Mock open to return invalid YAML
    with patch("builtins.open", mock_open(read_data="invalid: yaml: content: :")):
        with patch("pathlib.Path.exists", return_value=True):
            registry = FoodClassRegistry()

            # Since load failed, registry should be empty
            assert registry.lookup("burger") is None

            # Implementation detail: _registry is init to {} in class
            # So it stays empty.
            assert not registry._registry
