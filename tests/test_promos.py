import pytest
from demo_repo.app import apply_discount


def test_vip50_discount_above_threshold():
    assert apply_discount(250.0, "VIP50") == 125.0


def test_vip50_error_below_threshold():
    with pytest.raises(ValueError) as exc:
        apply_discount(150.0, "VIP50")
    assert "VIP50" in str(exc.value)


def test_other_discounts():
    assert apply_discount(100.0, "SAVE10") == 90.0
    assert apply_discount(100.0, "save20") == 80.0
    assert apply_discount(100.0, "SAVE50") == 50.0
    assert apply_discount(100.0, None) == 100.0
    assert apply_discount(100.0, "UNKNOWN") == 100.0
