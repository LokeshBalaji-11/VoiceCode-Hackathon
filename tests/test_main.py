import pytest
from demo_repo.app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client

def test_sponsor_match_endpoint(client):
    """Verify sponsor matching works correctly via the Flask endpoint."""
    payload = {
        "student": {"name": "Alice", "gpa": 3.5, "major": "Computer Science"},
        "sponsors": [
            {"company_name": "TechCorp", "min_gpa": 3.0, "target_majors": ["Computer Science", "Engineering"]},
            {"company_name": "ArtsFund", "min_gpa": 3.2, "target_majors": ["Art"]},
            {"company_name": "LowGPA", "min_gpa": 3.8, "target_majors": ["Computer Science"]},
        ],
    }
    response = client.post("/api/sponsor-match", json=payload)
    assert response.status_code == 200

# --- Agent Auto-Patch ---
import pytest
from demo_repo.app import app

@pytest.fixture
def client():
    """Creates a Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_sponsor_match_no_eligible_sponsors(client):
    """Test that sponsor matching returns an empty list when the student's GPA is too low for any sponsor."""
    payload = {
        "student": {"name": "Bob", "gpa": 2.0, "major": "Computer Science"},
        "sponsors": [
            {
                "company_name": "TechCorp",
                "min_gpa": 3.0,
                "target_majors": ["Computer Science", "Math"]
            },
            {
                "company_name": "BizInc",
                "min_gpa": 2.5,
                "target_majors": ["Business"]
            }
        ]
    }
    response = client.post("/api/sponsor-match", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert data == []


# --- Agent Auto-Patch ---
import pytest
from demo_repo.app import app


@pytest.fixture
def client():
    """Creates a Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_sponsor_match_no_eligible(client):
    """Test that sponsor-match returns an empty list when student GPA is below all sponsors' minimum GPA."""
    payload = {
        "student": {"name": "Bob", "gpa": 2.0, "major": "History"},
        "sponsors": [
            {
                "company_name": "TechCorp",
                "min_gpa": 3.0,
                "target_majors": ["Computer Science", "Math"]
            },
            {
                "company_name": "BizInc",
                "min_gpa": 3.5,
                "target_majors": ["Business", "History"]
            }
        ]
    }
    response = client.post("/api/sponsor-match", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert data == []
