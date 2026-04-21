"""
Playwright E2E tests for register and login pages.
Positive and negative flows covering client-side validation and server responses.
"""
import httpx
import pytest

SERVER_URL = "http://127.0.0.1:8001"


# ── Positive Tests ─────────────────────────────────────────────────────────────

def test_register_valid_data(page, live_server):
    page.goto(f"{SERVER_URL}/static/register.html")
    page.fill("#email", "newuser@example.com")
    page.fill("#password", "securepass123")
    page.fill("#confirm_password", "securepass123")
    page.click("button[type=submit]")
    page.wait_for_selector("#success-msg", state="visible", timeout=8000)
    text = page.inner_text("#success-msg").lower()
    assert "success" in text


def test_login_valid_credentials(page, live_server):
    httpx.post(f"{SERVER_URL}/users/register", json={
        "email": "loginuser@example.com",
        "password": "securepass123",
    })

    page.goto(f"{SERVER_URL}/static/login.html")
    page.fill("#email", "loginuser@example.com")
    page.fill("#password", "securepass123")
    page.click("button[type=submit]")
    page.wait_for_selector("#success-msg", state="visible", timeout=8000)
    text = page.inner_text("#success-msg").lower()
    assert "success" in text


# ── Negative Tests ─────────────────────────────────────────────────────────────

def test_register_short_password_shows_frontend_error(page, live_server):
    page.goto(f"{SERVER_URL}/static/register.html")
    page.fill("#email", "shortpass@example.com")
    page.fill("#password", "abc")
    page.fill("#confirm_password", "abc")
    page.click("button[type=submit]")
    page.wait_for_selector("#error-msg", state="visible", timeout=5000)
    text = page.inner_text("#error-msg").lower()
    assert "password" in text


def test_login_wrong_password_shows_error(page, live_server):
    httpx.post(f"{SERVER_URL}/users/register", json={
        "email": "wrongpass@example.com",
        "password": "correctpass123",
    })

    page.goto(f"{SERVER_URL}/static/login.html")
    page.fill("#email", "wrongpass@example.com")
    page.fill("#password", "totallyWrongPass999")
    page.click("button[type=submit]")
    page.wait_for_selector("#error-msg", state="visible", timeout=8000)
    text = page.inner_text("#error-msg").lower()
    assert "invalid" in text
