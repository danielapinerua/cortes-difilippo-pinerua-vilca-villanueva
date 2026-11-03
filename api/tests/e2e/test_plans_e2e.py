"""Tests E2E de US07 contra MySQL real.

Complementan a `tests/test_plans.py`: acá los errores salen de MySQL de
verdad (FK `RESTRICT` = 1451, `UNIQUE` = 1062), no de un monkeypatch.

Requieren la base `tech_solutions_test`:

    sed 's/tech_solutions/tech_solutions_test/g' \\
        database/migrations/1_setup_database.sql | mysql -uroot

    cd api && pytest tests/e2e -m e2e
"""
import pytest

from app.constants import DEFAULT_PLAN_ID, DEFAULT_PLAN_PRICE

# Sin esta marca, `pytest.ini` (`-m "not e2e"`) los excluye de la corrida normal.
pytestmark = pytest.mark.e2e

BASE = "/api/v1/plans"
REGISTER = "/api/v1/auth/register"


# ---- Plan por defecto (US17) ------------------------------------------------

def test_borrar_el_plan_por_defecto_devuelve_409(http, admin):
    r = http.delete(f"{BASE}/{DEFAULT_PLAN_ID}", headers=admin)

    assert r.status_code == 409
    err = r.get_json()["error"]
    assert err["code"] == "protected_resource"
    assert "Gratuito" in err["message"]


def test_el_plan_por_defecto_sigue_existiendo(http, admin):
    http.delete(f"{BASE}/{DEFAULT_PLAN_ID}", headers=admin)

    r = http.get(f"{BASE}/{DEFAULT_PLAN_ID}", headers=admin)
    assert r.status_code == 200
    body = r.get_json()
    assert body["name"] == "Gratuito"
    assert body["price"] == DEFAULT_PLAN_PRICE


def test_el_registro_sigue_funcionando_tras_el_intento(http, admin):
    """Regresión de US17 contra MySQL: el 409 no debe romper el alta."""
    assert http.delete(f"{BASE}/{DEFAULT_PLAN_ID}", headers=admin).status_code == 409

    r = http.post(REGISTER, json={
        "name": "Registro Prueba",
        "email": "e2e.registro@ejemplo.com",
        "password": "ClaveSegura123",
        "password_confirm": "ClaveSegura123",
    })

    assert r.status_code == 201
    assert r.get_json()["client"]["plan"] == {"id": DEFAULT_PLAN_ID, "name": "Gratuito"}


# ---- Precio del plan por defecto --------------------------------------------

def test_no_se_puede_cambiar_el_precio_del_plan_por_defecto(http, admin):
    r = http.put(f"{BASE}/{DEFAULT_PLAN_ID}", json={"price": 100}, headers=admin)

    assert r.status_code == 409
    err = r.get_json()["error"]
    assert err["code"] == "protected_resource"
    assert "precio" in err["message"]


def test_el_precio_del_plan_por_defecto_sigue_en_cero(http, admin):
    http.put(f"{BASE}/{DEFAULT_PLAN_ID}", json={"price": 100}, headers=admin)

    r = http.get(f"{BASE}/{DEFAULT_PLAN_ID}", headers=admin)
    assert r.status_code == 200
    assert r.get_json()["price"] == DEFAULT_PLAN_PRICE


def test_poner_el_precio_en_cero_esta_permitido(http, admin):
    r = http.put(
        f"{BASE}/{DEFAULT_PLAN_ID}",
        json={"price": DEFAULT_PLAN_PRICE},
        headers=admin,
    )

    assert r.status_code == 200
    assert r.get_json()["price"] == DEFAULT_PLAN_PRICE


def test_se_puede_editar_el_nombre_sin_tocar_el_precio(http, admin):
    r = http.put(
        f"{BASE}/{DEFAULT_PLAN_ID}",
        json={"name": "Gratuito E2E"},
        headers=admin,
    )

    assert r.status_code == 200
    body = r.get_json()
    assert body["name"] == "Gratuito E2E"
    assert body["price"] == DEFAULT_PLAN_PRICE


# ---- CRUD contra MySQL ------------------------------------------------------

def test_plan_inexistente_devuelve_404(http, admin):
    r = http.delete(f"{BASE}/99999", headers=admin)

    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"


def test_plan_sin_clientes_se_borra(http, admin):
    r = http.post(BASE, json={"name": "E2E Temporal", "price": 100}, headers=admin)
    assert r.status_code == 201
    plan_id = r.get_json()["id"]

    assert http.delete(f"{BASE}/{plan_id}", headers=admin).status_code == 204
    assert http.get(f"{BASE}/{plan_id}", headers=admin).status_code == 404


def test_plan_en_uso_devuelve_409_in_use(http, admin):
    """El 409 lo produce la FK real (`RESTRICT`), no un monkeypatch."""
    r = http.post(BASE, json={"name": "E2E En Uso", "price": 100}, headers=admin)
    plan_id = r.get_json()["id"]

    r = http.post("/api/v1/clients", json={
        "name": "Cliente Prueba",
        "email": "e2e.cliente@ejemplo.com",
        "plan_id": plan_id,
    }, headers=admin)
    assert r.status_code == 201

    r = http.delete(f"{BASE}/{plan_id}", headers=admin)
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "in_use"


def test_nombre_repetido_devuelve_409_duplicate(http, admin):
    """El 409 lo produce el UNIQUE real (`1062`)."""
    body = {"name": "E2E Duplicado", "price": 100}
    assert http.post(BASE, json=body, headers=admin).status_code == 201

    r = http.post(BASE, json=body, headers=admin)
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "duplicate_entry"
