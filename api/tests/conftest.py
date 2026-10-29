"""Fixtures de pytest.

Los tests NO usan MySQL: reemplazamos los repositorios por versiones en
memoria (diccionarios). Esto es posible gracias a la separación en capas:
las rutas y los services no saben (ni les importa) de dónde salen los datos.
"""
from types import SimpleNamespace

import pytest

from app import create_app
from app.config import TestConfig
from app.repositories import plans_repository, users_repository
from app.security import hash_password

PASSWORD = "Clave-de-prueba-1"


@pytest.fixture
def fake_plans(monkeypatch):
    store = {}
    counter = {"next": 1}

    def list_all():
        return [dict(p) for p in store.values()]

    def get(plan_id):
        p = store.get(plan_id)
        return dict(p) if p else None

    def create(data):
        plan_id = counter["next"]
        counter["next"] += 1
        store[plan_id] = {"id": plan_id, "description": None, **data}
        return plan_id

    def update(plan_id, data):
        store[plan_id].update(data)

    def delete(plan_id):
        del store[plan_id]

    for name, fn in {"list_all": list_all, "get": get, "create": create,
                     "update": update, "delete": delete}.items():
        monkeypatch.setattr(plans_repository, name, fn)
    return store


@pytest.fixture
def fake_users(monkeypatch):
    """Dos usuarios activos (un admin y un cliente) y uno desactivado."""
    h = hash_password(PASSWORD)
    users = {
        1: {"id": 1, "email": "admin@test.com", "password_hash": h, "role": "admin", "is_active": 1},
        2: {"id": 2, "email": "cliente@test.com", "password_hash": h, "role": "client", "is_active": 1},
        3: {"id": 3, "email": "baja@test.com", "password_hash": h, "role": "client", "is_active": 0},
    }
    logins = []  # ids de usuarios a los que se les registró el último ingreso

    monkeypatch.setattr(users_repository, "get_by_email",
                        lambda email: next((dict(u) for u in users.values() if u["email"] == email), None))
    monkeypatch.setattr(users_repository, "get_by_id",
                        lambda uid: {k: v for k, v in users[uid].items() if k != "password_hash"} if uid in users else None)
    monkeypatch.setattr(users_repository, "touch_last_login", lambda uid: logins.append(uid))
    return SimpleNamespace(users=users, logins=logins)


@pytest.fixture
def client(fake_plans, fake_users):
    return create_app(TestConfig).test_client()


def _login(client, email):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200, r.get_json()
    return {"Authorization": f"Bearer {r.get_json()['token']}"}


@pytest.fixture
def admin(client):
    return _login(client, "admin@test.com")


@pytest.fixture
def customer(client):
    return _login(client, "cliente@test.com")
