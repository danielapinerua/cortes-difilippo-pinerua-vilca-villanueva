"""Fixtures. El front corre de verdad (create_app), pero su `requests.Session` se
reemplaza por un adaptador que, en vez de ir a la red, llama al API FALSO en memoria."""
import json as jsonlib

import pytest

from app import api_client, create_app
from app.config import TestConfig
from .fake_api import PASSWORD, add_request, create_fake_api  # noqa: F401


class _Resp:
    """Imita lo mínimo de requests.Response que usa api_client."""
    def __init__(self, flask_resp):
        self.status_code = flask_resp.status_code
        self.content = flask_resp.data
        self.text = flask_resp.get_data(as_text=True)

    def json(self):
        return jsonlib.loads(self.text)


class _FakeHttp:
    def __init__(self, fake_app):
        self.client = fake_app.test_client()
        self.raise_error = None  # poner una excepción para simular API caído

    def request(self, method, url, headers=None, json=None, params=None, timeout=None):
        if self.raise_error:
            raise self.raise_error
        path = url.split("api.test", 1)[1]
        r = self.client.open(path, method=method, headers=headers, json=json, query_string=params)
        return _Resp(r)


@pytest.fixture
def fake_api():
    return create_fake_api()


@pytest.fixture
def http(fake_api, monkeypatch):
    fake_http = _FakeHttp(fake_api)
    monkeypatch.setattr(api_client, "_http", fake_http)
    return fake_http


@pytest.fixture
def app(http):
    return create_app(TestConfig)


@pytest.fixture
def browser(app):
    """Un 'navegador' con cookies. csrf() obtiene el token real que la app puso en la sesión."""
    c = app.test_client()

    def csrf():
        with c.session_transaction() as s:
            if "csrf" not in s:
                s["csrf"] = "tok"
            return s["csrf"]
    c.csrf = csrf
    return c


def login_as(browser, email):
    r = browser.post("/login", data={"email": email, "password": PASSWORD, "csrf_token": browser.csrf()})
    assert r.status_code == 302, r.get_data(as_text=True)
    return r


@pytest.fixture
def client_browser(browser):
    login_as(browser, "cliente@test.com")
    return browser


@pytest.fixture
def admin_browser(browser):
    login_as(browser, "admin@test.com")
    return browser
