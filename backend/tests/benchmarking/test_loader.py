import pytest

from app.benchmarking.nutrition5k_loader import Nutrition5kLoader


@pytest.fixture
def loader():
    return Nutrition5kLoader()


def test_loader_parsing(loader):
    # This relies on metadata files being present (which they are)
    dishes = loader.load_dishes(limit=5)
    if not dishes:
        pytest.skip("No data found")

    assert len(dishes) == 5
    dish = dishes[0]
    assert dish.dish_id
    assert dish.total_calories > 0
    assert len(dish.ingredients) >= 0


def test_loader_determinism(loader):
    run1 = loader.load_dishes(seed=99, limit=50)
    run2 = loader.load_dishes(seed=99, limit=50)

    if not run1:
        pytest.skip("No data found")

    ids1 = [d.dish_id for d in run1]
    ids2 = [d.dish_id for d in run2]

    assert ids1 == ids2


def test_loader_filtering(loader):
    simple = loader.load_dishes(complexity="simple", limit=10)
    if not simple:
        pytest.skip("No simple dishes found")

    for d in simple:
        assert d.complexity == "simple"
        assert len(d.ingredients) <= 3

    complex_ = loader.load_dishes(complexity="complex", limit=10)
    if not complex_:
        pytest.skip("No complex dishes found")

    for d in complex_:
        assert d.complexity == "complex"
        assert len(d.ingredients) > 3
