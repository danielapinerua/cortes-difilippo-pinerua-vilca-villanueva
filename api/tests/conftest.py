"""Fixtures de pytest.

Los tests NO usan MySQL: reemplazamos los repositorios por versiones en
memoria (diccionarios). Esto es posible gracias a la separación en capas:
las rutas y los services no saben (ni les importa) de dónde salen los datos.
"""
from types import SimpleNamespace

import pytest

from app import create_app
from app.config import TestConfig
from app.repositories import clients_repository, plans_repository, users_repository
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
def default_plan(fake_plans):
    """Plan Gratuito (id 4), el que recibe un visitante al registrarse."""
    plan = {"id": 4, "name": "Gratuito", "description": "Plan de bienvenida", "price": 0.0}
    fake_plans[4] = plan
    return plan


@pytest.fixture
def fake_users(monkeypatch):
    """Dos usuarios activos (un admin y un cliente), uno desactivado y un
    `create` que respeta la numeración real de la tabla."""
    h = hash_password(PASSWORD)
    users = {
        1: {"id": 1, "email": "admin@test.com", "password_hash": h, "role": "admin", "is_active": 1},
        2: {"id": 2, "email": "cliente@test.com", "password_hash": h, "role": "client", "is_active": 1},
        3: {"id": 3, "email": "baja@test.com", "password_hash": h, "role": "client", "is_active": 0},
    }
    logins = []  # ids de usuarios a los que se les registró el último ingreso
    counter = {"next": 4}

    def get_by_email(email):
        return next((dict(u) for u in users.values() if u["email"] == email), None)

    def get_by_id(uid):
        return {k: v for k, v in users[uid].items() if k != "password_hash"} if uid in users else None

    def email_exists(email):
        return any(u["email"] == email for u in users.values())

    def create(email, password_hash, role):
        uid = counter["next"]
        counter["next"] += 1
        users[uid] = {
            "id": uid,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "is_active": 1,
        }
        return uid

    for name, fn in {"get_by_email": get_by_email, "get_by_id": get_by_id,
                     "email_exists": email_exists, "create": create,
                     "touch_last_login": lambda uid: logins.append(uid)}.items():
        monkeypatch.setattr(users_repository, name, fn)
    return SimpleNamespace(users=users, logins=logins)


@pytest.fixture
def fake_clients(monkeypatch):
    clients = {}
    counter = {"next": 1}

    def create(user_id, plan_id, name, email, phone=None, dni=None):
        client_id = counter["next"]
        counter["next"] += 1
        clients[client_id] = {
            "id": client_id,
            "user_id": user_id,
            "plan_id": plan_id,
            "name": name,
            "email": email,
            "phone": phone,
            "dni": dni,
        }
        return client_id

    def get_by_email(email):
        return next((dict(c) for c in clients.values() if c["email"] == email), None)

    def get_by_dni(dni):
        return next((dict(c) for c in clients.values() if c["dni"] == dni), None)

    def get_by_user_id(user_id):
        return next((dict(c) for c in clients.values() if c["user_id"] == user_id), None)

    for name, fn in {"create": create, "get_by_email": get_by_email,
                     "get_by_dni": get_by_dni, "get_by_user_id": get_by_user_id}.items():
        monkeypatch.setattr(clients_repository, name, fn)
    return clients


@pytest.fixture
def client(fake_plans, fake_users, fake_clients):
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
