"""
4 Automatic Tests for demo_repo/app.py.
"""
import pytest
from demo_repo.app import app, apply_discount, calculate_subtotal


@pytest.fixture
def client():
    """Creates a Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_health_check_endpoint(client):
    """Test 1: Verify /health returns 200 and status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"


def test_calculate_subtotal_basic():
    """Test 2: Verify subtotal math for multiple items."""
    items = [
        {"price": 15.50, "qty": 2},
        {"price": 9.00, "qty": 1},
    ]
    assert calculate_subtotal(items) == 40.00


def test_apply_discount_codes():
    """Test 3: Verify SAVE10 and SAVE20 discount codes work properly."""
    assert apply_discount(100.0, "SAVE10") == 90.00
    assert apply_discount(100.0, "save20") == 80.00
    assert apply_discount(100.0, "UNKNOWN") == 100.00


def test_checkout_endpoint_negative_rejected(client):
    """Test 4: Verify negative item prices return HTTP 400."""
    response = client.post(
        "/checkout",
        json={"items": [{"price": -5.0, "qty": 1}]},
    )
    assert response.status_code == 400
    assert "non-negative" in response.get_json()["error"]


def test_sponsor_match_endpoint(client):
    """Test 5: Verify sponsor matching endpoint returns correct filtered sponsors."""
    payload = {
        "student": {"name": "Alice", "gpa": 3.5, "major": "Computer Science"},
        "sponsors": [
            {
                "company_name": "TechCorp",
                "min_gpa": 3.0,
                "target_majors": ["Computer Science", "Math"]
            },
            {
                "company_name": "BizInc",
                "min_gpa": 3.7,
                "target_majors": ["Business"]
            },
            {
                "company_name": "MathCo",
                "min_gpa": 3.0,
                "target_majors": ["Math"]
            }
        ]
    }
    response = client.post("/api/sponsor-match", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert data == [
        {
            "company_name": "TechCorp",
            "min_gpa": 3.0,
            "target_majors": ["Computer Science", "Math"]
        }
    ]