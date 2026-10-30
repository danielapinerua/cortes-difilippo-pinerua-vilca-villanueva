"""Tests de US17 - Registro de visitante.

Igual que el resto: repositorios en memoria, sin MySQL.
"""
import pymysql
import pytest
from flask import g

from app import db
from app.repositories import users_repository

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"

VALID = {
    "name": "Mariana Díaz",
    "email": "mariana@ejemplo.com",
    "password": "ClaveSegura123",
    "password_confirm": "ClaveSegura123",
    "phone": "+54 911 2222 3333",
    "dni": "28456321",
}


def _body(**overrides):
    data = dict(VALID)
    data.update(overrides)
    return data


# ---- Camino feliz ----------------------------------------------------------

def test_registro_crea_usuario_y_cliente(client, default_plan, fake_users, fake_clients):
    r = client.post(REGISTER, json=VALID)
    assert r.status_code == 201

    body = r.get_json()
    assert body["user"]["email"] == "mariana@ejemplo.com"
    assert body["user"]["role"] == "client"
    assert body["client"]["plan"] == {"id": 4, "name": "Gratuito"}

    # Sin auto-login: no hay token y no se registró el ingreso.
    assert "token" not in body
    assert fake_users.logins == []

    # Se crearon las dos filas y quedaron enlazadas.
    user_id = body["user"]["id"]
    client_id = body["client"]["id"]
    assert fake_users.users[user_id]["role"] == "client"
    assert fake_clients[client_id]["user_id"] == user_id
    assert fake_clients[client_id]["plan_id"] == 4


def test_puede_iniciar_sesion_despues_de_registrarse(client, default_plan):
    client.post(REGISTER, json=VALID)
    r = client.post(LOGIN, json={"email": VALID["email"], "password": VALID["password"]})
    assert r.status_code == 200
    assert r.get_json()["user"]["role"] == "client"


def test_email_se_normaliza_a_minusculas(client, default_plan):
    r = client.post(REGISTER, json=_body(email="  MARIANA@Ejemplo.COM "))
    assert r.status_code == 201
    assert r.get_json()["user"]["email"] == "mariana@ejemplo.com"


def test_telefono_y_dni_son_opcionales(client, default_plan, fake_clients):
    r = client.post(REGISTER, json=_body(phone=None, dni=None))
    assert r.status_code == 201
    assert fake_clients[r.get_json()["client"]["id"]]["phone"] is None
    assert fake_clients[r.get_json()["client"]["id"]]["dni"] is None


def test_telefono_y_dni_se_normalizan(client, default_plan, fake_clients):
    r = client.post(REGISTER, json=_body(phone="+54 (911) 2222-3333", dni="28.456.321"))
    assert r.status_code == 201
    stored = fake_clients[r.get_json()["client"]["id"]]
    assert stored["phone"] == "+5491122223333"
    assert stored["dni"] == "28456321"


# ---- Validaciones (422) ----------------------------------------------------

def test_faltan_campos_obligatorios(client, default_plan):
    r = client.post(REGISTER, json={})
    assert r.status_code == 422
    assert set(r.get_json()["error"]["details"]) == {"name", "email", "password"}


@pytest.mark.parametrize("email", [
    "sin-arroba", "a@b", "a b@c.com", "@x.com", "x@.com", "x@y.", "",
])
def test_email_invalido(client, default_plan, email):
    r = client.post(REGISTER, json=_body(email=email))
    assert r.status_code == 422
    assert "email" in r.get_json()["error"]["details"]


@pytest.mark.parametrize("password,error", [
    ("corta1", "8 caracteres"),
    ("solamenteletras", "letras y números"),
    ("123456789", "letras y números"),
    ("admin123", "común"),
])
def test_password_insegura(client, default_plan, password, error):
    r = client.post(REGISTER, json=_body(password=password, password_confirm=password))
    assert r.status_code == 422
    assert error in r.get_json()["error"]["details"]["password"]


def test_password_no_puede_ser_igual_al_email(client, default_plan):
    email = "mariana123@ejemplo.com"
    r = client.post(REGISTER, json=_body(email=email, password=email, password_confirm=email))
    assert r.status_code == 422
    assert "email" in r.get_json()["error"]["details"]["password"]


def test_password_confirmacion_distinta(client, default_plan):
    r = client.post(REGISTER, json=_body(password_confirm="OtraClave123"))
    assert r.status_code == 422
    assert "password_confirm" in r.get_json()["error"]["details"]


@pytest.mark.parametrize("name", ["Mariana123", "M", "a" * 151, "   "])
def test_nombre_invalido(client, default_plan, name):
    r = client.post(REGISTER, json=_body(name=name))
    assert r.status_code == 422
    assert "name" in r.get_json()["error"]["details"]


@pytest.mark.parametrize("phone", ["abc", "123", "1234567890123456"])
def test_telefono_invalido(client, default_plan, phone):
    r = client.post(REGISTER, json=_body(phone=phone))
    assert r.status_code == 422
    assert "phone" in r.get_json()["error"]["details"]


@pytest.mark.parametrize("dni", ["123", "1234567a", "123456789"])
def test_dni_invalido(client, default_plan, dni):
    r = client.post(REGISTER, json=_body(dni=dni))
    assert r.status_code == 422
    assert "dni" in r.get_json()["error"]["details"]


def test_body_no_json(client, default_plan):
    r = client.post(REGISTER, data="no soy json", content_type="text/plain")
    assert r.status_code == 422


def test_longitudes_maximas_aceptadas(client, default_plan):
    r = client.post(REGISTER, json=_body(
        name="a" * 150,
        email="a" * 249 + "@x.com",  # 255
        phone="1" * 15,
        dni="12345678",
    ))
    assert r.status_code == 201


def test_email_demasiado_largo(client, default_plan):
    r = client.post(REGISTER, json=_body(email="a" * 250 + "@x.com"))  # 256
    assert r.status_code == 422
    assert "email" in r.get_json()["error"]["details"]


# ---- Duplicados (409) ------------------------------------------------------

def test_email_duplicado_en_users(client, default_plan):
    client.post(REGISTER, json=VALID)
    r = client.post(REGISTER, json=_body(dni="11111111"))
    assert r.status_code == 409
    error = r.get_json()["error"]
    assert error["code"] == "duplicate_entry"
    assert "email" in error["details"]


def test_email_duplicado_en_clients(client, default_plan, fake_clients):
    """Un cliente cargado por el admin, todavía sin cuenta de login."""
    fake_clients[99] = {
        "id": 99, "user_id": None, "plan_id": 1, "name": "Cliente viejo",
        "email": VALID["email"], "phone": None, "dni": None,
    }
    r = client.post(REGISTER, json=VALID)
    assert r.status_code == 409
    assert "email" in r.get_json()["error"]["details"]


def test_dni_duplicado(client, default_plan):
    client.post(REGISTER, json=VALID)
    r = client.post(REGISTER, json=_body(email="otro@ejemplo.com"))
    assert r.status_code == 409
    error = r.get_json()["error"]
    assert error["code"] == "duplicate_entry"
    assert "dni" in error["details"]


def test_carrera_de_email_mapea_el_409(client, default_plan, monkeypatch):
    """Dos registros simultáneos: el UNIQUE de MySQL frena al segundo."""
    def boom(email, password_hash, role):
        raise pymysql.err.IntegrityError(1062, "Duplicate entry 'x' for key 'uq_users_email'")

    monkeypatch.setattr(users_repository, "create", boom)
    r = client.post(REGISTER, json=VALID)
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "duplicate_entry"
    assert "email" in r.get_json()["error"]["details"]


def test_sin_plan_por_defecto_devuelve_409(client):
    """Si el script SQL no cargó el plan Gratuito, el alta no puede completarse."""
    r = client.post(REGISTER, json=VALID)
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "invalid_reference"


# ---- Seguridad -------------------------------------------------------------

def test_rol_del_body_se_ignora(client, default_plan):
    r = client.post(REGISTER, json=_body(role="admin", is_active=0, plan_id=1))
    assert r.status_code == 201
    assert r.get_json()["user"]["role"] == "client"
    assert r.get_json()["client"]["plan"]["id"] == 4


def test_no_devuelve_la_password(client, default_plan):
    r = client.post(REGISTER, json=VALID)
    raw = r.get_data(as_text=True)
    assert "password_hash" not in raw
    assert VALID["password"] not in raw


def test_get_register_no_permitido(client):
    assert client.get(REGISTER).status_code == 405


# ---- Transacción -----------------------------------------------------------

class _FakeConn:
    def __init__(self):
        self.rolled_back = False
        self.committed = False
        self.closed = False

    def rollback(self):
        self.rolled_back = True

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


def test_transaction_hace_rollback_si_falla(client):
    conn = _FakeConn()
    with client.application.test_request_context():
        g.db = conn
        with pytest.raises(ValueError):
            with db.transaction():
                raise ValueError("boom")
        assert conn.rolled_back


def test_transaction_no_hace_rollback_si_todo_ok(client):
    conn = _FakeConn()
    with client.application.test_request_context():
        g.db = conn
        with db.transaction():
            pass
        assert not conn.rolled_back
