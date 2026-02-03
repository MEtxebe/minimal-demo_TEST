import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    # Snapshot and restore global in-memory activities for test isolation
    original = copy.deepcopy(activities)
    try:
        yield
    finally:
        activities.clear()
        activities.update(original)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # basic sanity
    assert "Chess Club" in data


def test_signup_and_prevent_duplicate():
    activity = "Chess Club"
    email = "tester@example.com"
    path = f"/activities/{quote(activity)}/signup"

    # First signup should succeed
    resp1 = client.post(path, params={"email": email})
    assert resp1.status_code == 200
    assert "Signed up" in resp1.json().get("message", "")

    # Second signup should be rejected as duplicate
    resp2 = client.post(path, params={"email": email})
    assert resp2.status_code == 400
    assert "already registered" in resp2.json().get("detail", "")


def test_remove_participant():
    activity = "Programming Class"
    email = "remove_me@example.com"
    signup_path = f"/activities/{quote(activity)}/signup"
    delete_path = f"/activities/{quote(activity)}/participants"

    # Signup first
    r = client.post(signup_path, params={"email": email})
    assert r.status_code == 200

    # Now delete
    r2 = client.delete(delete_path, params={"email": email})
    assert r2.status_code == 200
    assert "Removed" in r2.json().get("message", "")

    # Deleting again should return 404
    r3 = client.delete(delete_path, params={"email": email})
    assert r3.status_code == 404