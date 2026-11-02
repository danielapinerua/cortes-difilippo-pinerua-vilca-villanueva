"""Tests de US06 (Gestionar clientes) — CU5.

  GET    /api/v1/clients?search=&plan_id=   (admin)
  GET    /api/v1/clients/{id}               (admin)
  POST   /api/v1/clients                    (admin)
  PUT    /api/v1/clients/{id}               (admin)

No usan MySQL: se reutiliza el store en memoria de `fake_clients` (conftest) y
se parchean los métodos nuevos del repositorio con una fixture LOCAL. Así este
archivo no obliga a tocar `conftest.py` (mismo criterio que US14).
"""
from datetime import datetime
from decimal import Decimal

import pymysql
import pytest

from app.repositories import clients_repository

CLIENTS = "/api/v1/clients"
NOW = datetime(2026, 10, 31, 10, 0, 0)


@pytest.fixture
def clients_store(monkeypatch, fake_clients, fake_plans):
    """Completa `fake_clients` con los métodos de US06 y carga dos planes."""
    fake_plans[1] = {"id": 1, "name": "Básico", "description": None, "price": Decimal("3500.00")}
    fake_plans[2] = {"id": 2, "name": "Profesional", "description": None, "price": Decimal("5900.00")}

    def get_by_id(client_id):
        row = fake_clients.get(client_id)
        return dict(row) if row else None

    def get_detail(client_id):
        row = fake_clients.get(client_id)
        if row is None:
            return None
        plan = fake_plans.get(row["plan_id"], {})
        return {
            **row,
            "created_at": NOW,
            "updated_at": NOW,
            "plan_name": plan.get("name"),
            "plan_price": plan.get("price"),
        }

    def search(search=None, plan_id=None):
        rows = []
        for row in fake_clients.values():
            if plan_id is not None and row["plan_id"] != plan_id:
                continue
            if search:
                haystack = " ".join(
                    str(row.get(field) or "") for field in ("name", "email", "dni")
                ).lower()
                if search.lower() not in haystack:
                    continue
            rows.append(get_detail(row["id"]))
        return sorted(rows, key=lambda r: (r["name"], r["id"]))

    def update(client_id, data):
        fake_clients[client_id].update(data)

    def email_exists(email, exclude_id=None):
        return any(
            c["email"] == email and c["id"] != exclude_id for c in fake_clients.values()
        )

    def dni_exists(dni, exclude_id=None):
        return any(
            c["dni"] == dni and c["id"] != exclude_id for c in fake_clients.values()
        )

    def user_id_exists(user_id, exclude_id=None):
        return any(
            c["user_id"] == user_id and c["id"] != exclude_id
            for c in fake_clients.values()
        )

    for name, fn in {
        "get_by_id": get_by_id,
        "get_detail": get_detail,
        "search": search,
        "update": update,
        "email_exists": email_exists,
        "dni_exists": dni_exists,
        "user_id_exists": user_id_exists,
    }.items():
        monkeypatch.setattr(clients_repository, name, fn)

    return fake_clients


def _seed(**overrides):
    data = {
        "user_id": None,
        "plan_id": 1,
        "name": "Cliente de Prueba",
        "email": "cliente@ejemplo.com",
        "phone": None,
        "dni": None,
    }
    data.update(overrides)
    return clients_repository.create(**data)


def _payload(**overrides):
    data = {
        "name": "Mariana Díaz",
        "email": "mariana@ejemplo.com",
        "phone": "+54 911 2222-3333",
        "dni": "28.456.321",
        "plan_id": 2,
    }
    data.update(overrides)
    return data


# ---- Permisos ----------------------------------------------------------------

def test_listar_sin_token_devuelve_401(client):
    r = client.get(CLIENTS)
    assert r.status_code == 401
    assert r.get_json()["error"]["code"] == "unauthorized"


def test_cliente_no_puede_listar_403(client, customer, clients_store):
    r = client.get(CLIENTS, headers=customer)
    assert r.status_code == 403
    assert r.get_json()["error"]["code"] == "forbidden"


def test_cliente_no_puede_crear_403(client, customer, clients_store):
    assert client.post(CLIENTS, json=_payload(), headers=customer).status_code == 403


def test_cliente_no_puede_ver_detalle_403(client, customer, clients_store):
    assert client.get(f"{CLIENTS}/1", headers=customer).status_code == 403


def test_cliente_no_puede_modificar_403(client, customer, clients_store):
    r = client.put(f"{CLIENTS}/1", json={"phone": "1234567"}, headers=customer)
    assert r.status_code == 403


# ---- Listado y búsqueda ------------------------------------------------------

def test_lista_vacia_devuelve_200_y_lista_vacia(client, admin, clients_store):
    r = client.get(CLIENTS, headers=admin)
    assert r.status_code == 200
    assert r.get_json() == []


def test_lista_trae_plan_y_has_login(client, admin, clients_store):
    _seed(user_id=2, plan_id=2, name="Con Login", email="con@ejemplo.com")
    _seed(plan_id=1, name="Sin Login", email="sin@ejemplo.com")

    body = client.get(CLIENTS, headers=admin).get_json()

    assert [c["name"] for c in body] == ["Con Login", "Sin Login"]
    assert body[0]["plan_name"] == "Profesional"
    assert body[0]["plan_price"] == 5900.0
    assert body[0]["has_login"] is True
    assert body[1]["has_login"] is False
    assert "user_id" not in body[0]


def test_search_por_nombre(client, admin, clients_store):
    _seed(name="Mariana Díaz", email="mariana@ejemplo.com")
    _seed(name="Carlos Ruiz", email="carlos@ejemplo.com")

    body = client.get(CLIENTS, query_string={"search": "mariana"}, headers=admin).get_json()

    assert [c["name"] for c in body] == ["Mariana Díaz"]


def test_search_por_email_y_dni(client, admin, clients_store):
    _seed(name="Mariana Díaz", email="mariana@ejemplo.com", dni="28456321")
    _seed(name="Carlos Ruiz", email="carlos@ejemplo.com", dni="30111222")

    por_email = client.get(CLIENTS, query_string={"search": "carlos@"}, headers=admin).get_json()
    por_dni = client.get(CLIENTS, query_string={"search": "30111222"}, headers=admin).get_json()

    assert [c["name"] for c in por_email] == ["Carlos Ruiz"]
    assert [c["name"] for c in por_dni] == ["Carlos Ruiz"]


def test_filtro_plan_id(client, admin, clients_store):
    _seed(plan_id=1, name="Básico", email="b@ejemplo.com")
    _seed(plan_id=2, name="Pro", email="p@ejemplo.com")

    body = client.get(CLIENTS, query_string={"plan_id": 2}, headers=admin).get_json()

    assert [c["name"] for c in body] == ["Pro"]


@pytest.mark.parametrize("valor", ["abc", "-1", "1.5"])
def test_filtro_plan_id_invalido_422(client, admin, clients_store, valor):
    r = client.get(CLIENTS, query_string={"plan_id": valor}, headers=admin)
    assert r.status_code == 422
    assert "plan_id" in r.get_json()["error"]["details"]


# ---- Detalle -----------------------------------------------------------------

def test_detalle_existente(client, admin, clients_store):
    client_id = _seed(name="Mariana Díaz", email="mariana@ejemplo.com", plan_id=2)

    r = client.get(f"{CLIENTS}/{client_id}", headers=admin)

    assert r.status_code == 200
    assert r.get_json()["plan_name"] == "Profesional"


def test_detalle_inexistente_404(client, admin, clients_store):
    r = client.get(f"{CLIENTS}/999", headers=admin)
    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"


# ---- Alta --------------------------------------------------------------------

def test_alta_minima_201(client, admin, clients_store):
    r = client.post(CLIENTS, json=_payload(), headers=admin)

    assert r.status_code == 201
    body = r.get_json()
    assert body["id"] == 1
    assert body["name"] == "Mariana Díaz"
    assert body["plan_name"] == "Profesional"
    assert body["has_login"] is False


def test_alta_normaliza_email_telefono_y_dni(client, admin, clients_store):
    r = client.post(
        CLIENTS,
        json=_payload(
            email="  MARIANA@Ejemplo.COM ",
            phone="+54 (911) 2222-3333",
            dni="28.456.321",
        ),
        headers=admin,
    )

    body = r.get_json()
    assert body["email"] == "mariana@ejemplo.com"
    assert body["phone"] == "+5491122223333"
    assert body["dni"] == "28456321"


def test_alta_vincula_cuenta_de_cliente_sin_perfil(client, admin, clients_store):
    # `cliente@test.com` es el usuario 2 (rol client) y todavía no tiene perfil.
    r = client.post(CLIENTS, json=_payload(email="cliente@test.com"), headers=admin)

    assert r.status_code == 201
    assert r.get_json()["has_login"] is True
    assert clients_store[1]["user_id"] == 2


def test_alta_con_email_de_admin_409(client, admin, clients_store):
    r = client.post(CLIENTS, json=_payload(email="admin@test.com"), headers=admin)
    assert r.status_code == 409
    assert "email" in r.get_json()["error"]["details"]


def test_alta_con_cuenta_que_ya_tiene_perfil_409(client, admin, clients_store):
    _seed(user_id=2, name="Ya tiene perfil", email="contacto@ejemplo.com")

    r = client.post(CLIENTS, json=_payload(email="cliente@test.com"), headers=admin)

    assert r.status_code == 409
    assert "email" in r.get_json()["error"]["details"]


def test_faltan_campos_obligatorios_422(client, admin, clients_store):
    r = client.post(CLIENTS, json={}, headers=admin)

    assert r.status_code == 422
    assert set(r.get_json()["error"]["details"]) == {"name", "email", "plan_id"}


def test_email_invalido_422(client, admin, clients_store):
    r = client.post(CLIENTS, json=_payload(email="no-es-email"), headers=admin)
    assert r.status_code == 422
    assert "email" in r.get_json()["error"]["details"]


def test_plan_inexistente_422(client, admin, clients_store):
    r = client.post(CLIENTS, json=_payload(plan_id=99), headers=admin)
    assert r.status_code == 422
    assert r.get_json()["error"]["details"]["plan_id"] == "El plan no existe."


def test_plan_id_como_texto_422(client, admin, clients_store):
    r = client.post(CLIENTS, json=_payload(plan_id="2"), headers=admin)
    assert r.status_code == 422
    assert "plan_id" in r.get_json()["error"]["details"]


def test_email_duplicado_409(client, admin, clients_store):
    _seed(email="mariana@ejemplo.com", name="Otra")

    r = client.post(CLIENTS, json=_payload(), headers=admin)

    assert r.status_code == 409
    assert "email" in r.get_json()["error"]["details"]


def test_dni_duplicado_409(client, admin, clients_store):
    _seed(email="otro@ejemplo.com", dni="28456321")

    r = client.post(CLIENTS, json=_payload(), headers=admin)

    assert r.status_code == 409
    assert "dni" in r.get_json()["error"]["details"]


def test_nombre_con_digitos_422(client, admin, clients_store):
    r = client.post(CLIENTS, json=_payload(name="Tech 24"), headers=admin)
    assert r.status_code == 422
    assert "name" in r.get_json()["error"]["details"]


def test_telefono_invalido_422(client, admin, clients_store):
    r = client.post(CLIENTS, json=_payload(phone="123"), headers=admin)
    assert r.status_code == 422
    assert "phone" in r.get_json()["error"]["details"]


def test_cuerpo_no_objeto_422(client, admin, clients_store):
    r = client.post(CLIENTS, json=[], headers=admin)
    assert r.status_code == 422
    assert r.get_json()["error"]["code"] == "validation_error"


# ---- Modificación ------------------------------------------------------------

def test_update_parcial_solo_telefono(client, admin, clients_store):
    client_id = _seed(name="Mariana Díaz", email="mariana@ejemplo.com", phone="+5491100000000")

    r = client.put(f"{CLIENTS}/{client_id}", json={"phone": "+54 911 5555-0000"}, headers=admin)

    assert r.status_code == 200
    body = r.get_json()
    assert body["phone"] == "+5491155550000"
    assert body["name"] == "Mariana Díaz"  # no se tocó


def test_update_inexistente_404(client, admin, clients_store):
    r = client.put(f"{CLIENTS}/999", json={"phone": "1234567"}, headers=admin)
    assert r.status_code == 404


def test_update_puede_repetir_su_propio_email(client, admin, clients_store):
    client_id = _seed(email="mariana@ejemplo.com")

    r = client.put(f"{CLIENTS}/{client_id}", json={"email": "mariana@ejemplo.com"}, headers=admin)

    assert r.status_code == 200
    assert r.get_json()["email"] == "mariana@ejemplo.com"


def test_update_email_de_otro_cliente_409(client, admin, clients_store):
    _seed(email="mariana@ejemplo.com")
    otro = _seed(email="otro@ejemplo.com")

    r = client.put(f"{CLIENTS}/{otro}", json={"email": "mariana@ejemplo.com"}, headers=admin)

    assert r.status_code == 409
    assert "email" in r.get_json()["error"]["details"]


def test_update_telefono_null_limpia(client, admin, clients_store):
    client_id = _seed(phone="+5491100000000")

    r = client.put(f"{CLIENTS}/{client_id}", json={"phone": None}, headers=admin)

    assert r.status_code == 200
    assert r.get_json()["phone"] is None


def test_update_cambia_plan(client, admin, clients_store):
    client_id = _seed(plan_id=1)

    r = client.put(f"{CLIENTS}/{client_id}", json={"plan_id": 2}, headers=admin)

    assert r.status_code == 200
    assert r.get_json()["plan_name"] == "Profesional"
    assert r.get_json()["plan_price"] == 5900.0


def test_update_plan_inexistente_422(client, admin, clients_store):
    client_id = _seed(plan_id=1)

    r = client.put(f"{CLIENTS}/{client_id}", json={"plan_id": 99}, headers=admin)

    assert r.status_code == 422
    assert "plan_id" in r.get_json()["error"]["details"]


def test_update_cuerpo_vacio_200_sin_cambios(client, admin, clients_store):
    client_id = _seed(name="Mariana Díaz")

    r = client.put(f"{CLIENTS}/{client_id}", json={}, headers=admin)

    assert r.status_code == 200
    assert r.get_json()["name"] == "Mariana Díaz"


def test_update_email_de_otra_cuenta_409(client, admin, clients_store):
    otro = _seed(email="otro@ejemplo.com")  # sin login

    # `cliente@test.com` es el login del usuario 2, que no es el vinculado a `otro`.
    r = client.put(f"{CLIENTS}/{otro}", json={"email": "cliente@test.com"}, headers=admin)

    assert r.status_code == 409
    assert "email" in r.get_json()["error"]["details"]


def test_update_puede_repetir_el_email_de_su_cuenta(client, admin, clients_store):
    client_id = _seed(user_id=2, email="cliente@test.com")

    r = client.put(
        f"{CLIENTS}/{client_id}",
        json={"email": "cliente@test.com", "phone": "+5491100000000"},
        headers=admin,
    )

    assert r.status_code == 200
    assert r.get_json()["has_login"] is True


def test_update_dni_duplicado_409(client, admin, clients_store):
    _seed(email="a@ejemplo.com", dni="28456321")
    otro = _seed(email="b@ejemplo.com", dni="30111222")

    r = client.put(f"{CLIENTS}/{otro}", json={"dni": "28456321"}, headers=admin)

    assert r.status_code == 409
    assert "dni" in r.get_json()["error"]["details"]


# ---- Seguridad y red de seguridad -------------------------------------------

def test_la_respuesta_no_expone_password_hash(client, admin, clients_store):
    client_id = _seed(user_id=2, email="cliente@test.com")

    body = client.get(f"{CLIENTS}/{client_id}", headers=admin).get_json()

    assert "password_hash" not in body


def test_duplicado_de_mysql_se_traduce_a_409(client, admin, clients_store, monkeypatch):
    def boom(**kwargs):
        raise pymysql.err.IntegrityError(
            1062, "Duplicate entry '2' for key 'clients.uq_clients_user_id'"
        )

    monkeypatch.setattr(clients_repository, "create", boom)

    r = client.post(CLIENTS, json=_payload(email="nuevo@ejemplo.com"), headers=admin)

    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "duplicate_entry"
    assert "user_id" in r.get_json()["error"]["details"]
