"""Bounded persistent browser sessions; synthetic accounts only."""
from fastapi.testclient import TestClient
from app.db import Session
from app.main import app, digest, LOGIN_LIFETIME_SECONDS
from app.models import Login
from test_flow import browser, reset


def test_login_cookie_and_server_expiry_agree_and_survive_a_day(monkeypatch):
    import app.main as main
    clock = 1_800_000_000
    monkeypatch.setattr(main, 'now', lambda: clock)
    client = browser()
    token = client.cookies.get('session')
    assert LOGIN_LIFETIME_SECONDS == 30 * 86400
    with Session() as db:
        assert db.get(Login, digest(token)).expires == clock + LOGIN_LIFETIME_SECONDS
        assert db.get(Login, token) is None
    clock += 2 * 86400
    # New browser process retains only its persistent cookie.
    reopened = TestClient(app, headers={'origin': main.origin})
    reopened.cookies.set('session', token)
    assert reopened.get('/account/me').status_code == 200
    assert reopened.post('/auth/logout').status_code == 200
    reopened.cookies.set('session', token)
    assert reopened.get('/account/me').status_code == 401


def test_fresh_login_sets_secure_persistent_cookie_and_expiry_is_enforced(monkeypatch):
    import app.main as main
    clock = 1_800_000_000
    monkeypatch.setattr(main, 'now', lambda: clock)
    browser()
    monkeypatch.setattr(main, 'secure_cookie', True)
    client = TestClient(app, base_url='https://testserver', headers={'origin': main.origin})
    response = client.post('/auth/login', json={'email': 'a@example.test', 'password': 'test-password-123'})
    cookie = response.headers['set-cookie'].lower()
    assert 'max-age=2592000' in cookie
    assert 'httponly' in cookie and 'secure' in cookie and 'samesite=strict' in cookie
    token = client.cookies.get('session')
    clock += LOGIN_LIFETIME_SECONDS - 1
    assert client.get('/account/me').status_code == 200
    clock += 1
    assert client.get('/account/me').status_code == 401
    # Reading an old token never resurrects it or extends its lifetime.
    with Session() as db:
        assert db.get(Login, digest(token)).expires == clock
