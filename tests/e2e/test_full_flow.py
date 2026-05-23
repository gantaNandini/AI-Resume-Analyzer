"""
End-to-end smoke tests for the full platform pipeline.
Requirements: 1.1, 2.1, 4.6, 10.1, 11.1, 12.1
"""
from __future__ import annotations
import os
import pytest
import httpx

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost")
AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8001")
FILE_URL = os.getenv("FILE_URL", "http://localhost:8002")


@pytest.fixture(scope="module")
def auth_token():
    """Register a test user and return JWT."""
    import uuid
    email = f"e2e-{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123!"

    resp = httpx.post(f"{AUTH_URL}/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201, f"Registration failed: {resp.text}"
    return resp.json()["access_token"]


def test_health_auth_service():
    resp = httpx.get(f"{AUTH_URL}/health")
    assert resp.status_code == 200
    assert resp.json()["status"] in ("ok", "degraded")


def test_health_file_processor():
    resp = httpx.get(f"{FILE_URL}/health")
    assert resp.status_code == 200


def test_register_and_login():
    import uuid
    email = f"login-test-{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123!"

    # Register
    resp = httpx.post(f"{AUTH_URL}/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201
    assert "access_token" in resp.json()

    # Login
    resp = httpx.post(f"{AUTH_URL}/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_duplicate_email_returns_409():
    import uuid
    email = f"dup-{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123!"
    httpx.post(f"{AUTH_URL}/auth/register", json={"email": email, "password": password})
    resp = httpx.post(f"{AUTH_URL}/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 409


def test_short_password_returns_422():
    resp = httpx.post(f"{AUTH_URL}/auth/register", json={"email": "x@x.com", "password": "short"})
    assert resp.status_code == 422


def test_upload_requires_auth():
    resp = httpx.post(f"{FILE_URL}/files/upload")
    assert resp.status_code == 401


def test_job_history_requires_auth():
    resp = httpx.get(f"{FILE_URL}/files/jobs")
    assert resp.status_code == 401


@pytest.mark.skipif(
    not os.path.exists("tests/fixtures/sample_resume.pdf"),
    reason="Fixture files not present"
)
def test_full_upload_and_poll(auth_token):
    """Full pipeline: upload → poll → result. Requires fixture files."""
    headers = {"Authorization": f"Bearer {auth_token}"}

    with open("tests/fixtures/sample_resume.pdf", "rb") as rf, \
         open("tests/fixtures/sample_jd.txt", "rb") as jf:
        resp = httpx.post(
            f"{FILE_URL}/files/upload",
            headers=headers,
            files={"resume": ("resume.pdf", rf, "application/pdf"),
                   "jd": ("jd.txt", jf, "text/plain")},
            timeout=30.0,
        )

    assert resp.status_code == 202
    job_id = resp.json()["job_id"]
    assert job_id

    # Poll until completed or failed (max 90s)
    import time
    for _ in range(30):
        time.sleep(3)
        status_resp = httpx.get(f"{FILE_URL}/files/jobs/{job_id}/status", headers=headers)
        assert status_resp.status_code == 200
        status = status_resp.json()["status"]
        if status == "completed":
            result = status_resp.json()["result"]
            assert result is not None
            assert isinstance(result["ats_score"], int)
            assert 0 <= result["ats_score"] <= 100
            assert result["band"] in ("Poor", "Fair", "Strong")
            assert "skill_gap" in result
            assert "suggestions" in result
            return
        elif status == "failed":
            pytest.fail(f"Job failed: {status_resp.json()}")

    pytest.fail("Job did not complete within 90 seconds")
