"""
Tests for the Mergington High School Activities API.
"""

import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    """Restore the in-memory activities store to its original state after each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_dict(self):
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_contains_expected_activity(self):
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data

    def test_activity_has_required_fields(self):
        response = client.get("/activities")
        chess = response.json()["Chess Club"]
        assert "description" in chess
        assert "schedule" in chess
        assert "max_participants" in chess
        assert "participants" in chess


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_successful_signup(self):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in response.json()["message"]

    def test_signup_adds_participant(self):
        email = "newstudent@mergington.edu"
        client.post("/activities/Chess Club/signup", params={"email": email})
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]

    def test_duplicate_signup_returns_400(self):
        email = "duplicate@mergington.edu"
        client.post("/activities/Chess Club/signup", params={"email": email})
        response = client.post("/activities/Chess Club/signup", params={"email": email})
        assert response.status_code == 400

    def test_signup_unknown_activity_returns_404(self):
        response = client.post(
            "/activities/Unknown Activity/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404

    def test_signup_full_activity_returns_400(self):
        activity_name = "Math Olympiad"  # max_participants = 10
        # Fill it up
        for i in range(activities[activity_name]["max_participants"]):
            email = f"filler{i}@mergington.edu"
            if email not in activities[activity_name]["participants"]:
                activities[activity_name]["participants"].append(email)
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "overflow@mergington.edu"},
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/unregister
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_successful_unregister(self):
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 200
        assert "michael@mergington.edu" in response.json()["message"]

    def test_unregister_removes_participant(self):
        email = "michael@mergington.edu"
        client.delete("/activities/Chess Club/unregister", params={"email": email})
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]

    def test_unregister_not_enrolled_returns_400(self):
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notenrolled@mergington.edu"},
        )
        assert response.status_code == 400

    def test_unregister_unknown_activity_returns_404(self):
        response = client.delete(
            "/activities/Unknown Activity/unregister",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET / redirect
# ---------------------------------------------------------------------------

class TestRoot:
    def test_root_redirects(self):
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (301, 302, 307, 308)
        assert "/static/index.html" in response.headers["location"]
