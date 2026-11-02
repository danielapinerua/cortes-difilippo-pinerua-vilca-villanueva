"""Tests de US14 (Consultar solicitudes y estados) y US05 (Consultar estado de una solicitud).

  GET /api/v1/service-requests?status_id=&priority_id=&client_id=   (admin)
  GET /api/v1/service-requests/{id}                                 (admin)
  GET /api/v1/me/service-requests?status_id=                        (client)

Como el resto de los tests, no usan MySQL: se reemplaza el repositorio por una
función en memoria que además ANOTA con qué filtros la llamaron. Así se
comprueba lo importante de esta capa: qué filtros llegan al repositorio, quién
puede entrar y qué se devuelve.
"""
from datetime import datetime

import pytest

from app.repositories import clients_repository, service_requests_repository

ADMIN_LIST = "/api/v1/service-requests"
MY_LIST = "/api/v1/me/service-requests"
CUSTOMER_CLIENT_ID = 7  # id de cliente que le asignamos al usuario `customer`


def _row(request_id=1, status_id=1, status_name="pendiente", priority_id=None, **extra):
    """Fila como la devuelve el JOIN del repositorio (con los nombres legibles)."""
    row = {
        "id": request_id,
        "client_id": CUSTOMER_CLIENT_ID,
        "client_name": "Mariana Gómez",
        "service_id": 3,
        "service_name": "Consultoría en Marketing Digital",
        "status_id": status_id,
        "status_name": status_name,
        "priority_id": priority_id,
        "priority_name": None if priority_id is None else "alta",
        "priority_level": None if priority_id is None else 1,
        "modification_type": "Cambio de horario",
        "description": "Mover la reunión al viernes",
        "rejection_reason": None,
        "created_at": datetime(2026, 10, 31, 10, 0, 0),
        "resolved_at": None,
    }
    row.update(extra)
    return row


@pytest.fixture
def search_calls(monkeypatch):
    """Reemplaza search() y anota con qué filtros se la llamó. Devuelve (llamadas, filas)."""
    calls, rows = [], []

    def fake_search(client_id=None, status_id=None, priority_id=None):
        calls.append({"client_id": client_id, "status_id": status_id, "priority_id": priority_id})
        return list(rows)

    monkeypatch.setattr(service_requests_repository, "search", fake_search)
    return calls, rows


@pytest.fixture
def customer_profile(monkeypatch):
    """El usuario `customer` (id 2) tiene perfil de cliente con id CUSTOMER_CLIENT_ID."""
    monkeypatch.setattr(
        clients_repository, "get_client_id_by_user_id",
        lambda user_id: CUSTOMER_CLIENT_ID if user_id == 2 else None,
    )


# ---- Bandeja del administrador: permisos -------------------------------------

def test_listar_sin_token_devuelve_401(client):
    r = client.get(ADMIN_LIST)
    assert r.status_code == 401
    assert r.get_json()["error"]["code"] == "unauthorized"


def test_cliente_no_puede_ver_la_bandeja_del_admin_403(client, customer):
    r = client.get(ADMIN_LIST, headers=customer)
    assert r.status_code == 403
    assert r.get_json()["error"]["code"] == "forbidden"


def test_cliente_no_puede_ver_detalle_de_solicitud_403(client, customer):
    assert client.get(f"{ADMIN_LIST}/1", headers=customer).status_code == 403


# ---- Bandeja del administrador: comportamiento -------------------------------

def test_admin_lista_solicitudes_con_datos_legibles(client, admin, search_calls):
    calls, rows = search_calls
    rows.append(_row(1, priority_id=1))
    rows.append(_row(2))

    r = client.get(ADMIN_LIST, headers=admin)

    assert r.status_code == 200
    body = r.get_json()
    assert [s["id"] for s in body] == [1, 2]
    assert body[0]["client_name"] == "Mariana Gómez"
    assert body[0]["service_name"] == "Consultoría en Marketing Digital"
    assert body[0]["status_name"] == "pendiente"
    assert body[0]["priority_name"] == "alta"
    assert body[1]["priority_id"] is None  # sin prioridad asignada todavía
    assert calls == [{"client_id": None, "status_id": None, "priority_id": None}]


def test_admin_lista_vacia_devuelve_200_y_lista_vacia(client, admin, search_calls):
    r = client.get(ADMIN_LIST, headers=admin)
    assert r.status_code == 200
    assert r.get_json() == []


def test_admin_filtros_llegan_al_repositorio_como_enteros(client, admin, search_calls):
    calls, _ = search_calls
    r = client.get(f"{ADMIN_LIST}?status_id=1&priority_id=2&client_id=7", headers=admin)
    assert r.status_code == 200
    assert calls == [{"client_id": 7, "status_id": 1, "priority_id": 2}]


def test_admin_filtros_vacios_se_ignoran(client, admin, search_calls):
    """La URL de ejemplo del plan es ?status_id=&priority_id=&client_id= (todo vacío)."""
    calls, _ = search_calls
    r = client.get(f"{ADMIN_LIST}?status_id=&priority_id=&client_id=", headers=admin)
    assert r.status_code == 200
    assert calls == [{"client_id": None, "status_id": None, "priority_id": None}]


def test_admin_filtro_parcial(client, admin, search_calls):
    calls, _ = search_calls
    client.get(f"{ADMIN_LIST}?status_id=1", headers=admin)
    assert calls == [{"client_id": None, "status_id": 1, "priority_id": None}]


@pytest.mark.parametrize("valor", ["abc", "-1", "1.5", "1;DROP TABLE users", "²"])
def test_admin_filtro_no_numerico_devuelve_422_y_no_consulta(client, admin, search_calls, valor):
    calls, _ = search_calls
    r = client.get(ADMIN_LIST, query_string={"status_id": valor}, headers=admin)
    assert r.status_code == 422
    err = r.get_json()["error"]
    assert err["code"] == "validation_error"
    assert "status_id" in err["details"]
    assert calls == []  # ni siquiera llegó al repositorio


def test_admin_filtros_invalidos_informa_todos_juntos(client, admin, search_calls):
    r = client.get(f"{ADMIN_LIST}?status_id=x&client_id=y", headers=admin)
    assert r.status_code == 422
    assert set(r.get_json()["error"]["details"]) == {"status_id", "client_id"}


def test_las_fechas_se_serializan_a_json(client, admin, search_calls):
    """Las filas traen datetime reales (como PyMySQL); jsonify tiene que poder con ellos."""
    _, rows = search_calls
    rows.append(_row(1, status_id=5, status_name="realizado", resolved_at=datetime(2026, 11, 1, 9, 30)))
    body = client.get(ADMIN_LIST, headers=admin).get_json()
    assert body[0]["created_at"] and body[0]["resolved_at"]


# ---- Detalle (administrador) -------------------------------------------------

def test_admin_ve_detalle(client, admin, monkeypatch):
    monkeypatch.setattr(service_requests_repository, "get_detail", lambda rid: _row(rid))
    r = client.get(f"{ADMIN_LIST}/5", headers=admin)
    assert r.status_code == 200
    assert r.get_json()["id"] == 5
    assert r.get_json()["client_name"] == "Mariana Gómez"


def test_detalle_inexistente_devuelve_404(client, admin, monkeypatch):
    monkeypatch.setattr(service_requests_repository, "get_detail", lambda rid: None)
    r = client.get(f"{ADMIN_LIST}/99", headers=admin)
    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"


def test_detalle_con_id_no_numerico_es_404_de_ruta(client, admin):
    assert client.get(f"{ADMIN_LIST}/abc", headers=admin).status_code == 404


# ---- Solicitudes del cliente (US14 + US05) -----------------------------------

def test_mis_solicitudes_sin_token_devuelve_401(client):
    assert client.get(MY_LIST).status_code == 401


def test_admin_no_puede_usar_el_endpoint_de_cliente_403(client, admin):
    r = client.get(MY_LIST, headers=admin)
    assert r.status_code == 403
    assert r.get_json()["error"]["code"] == "forbidden"


def test_cliente_ve_solo_sus_solicitudes_usando_el_id_del_token(client, customer, customer_profile, search_calls):
    calls, rows = search_calls
    rows.append(_row(1))

    r = client.get(MY_LIST, headers=customer)

    assert r.status_code == 200
    assert len(r.get_json()) == 1
    # El client_id salió del usuario del token (user 2 -> cliente 7), no de la URL.
    assert calls == [{"client_id": CUSTOMER_CLIENT_ID, "status_id": None, "priority_id": None}]


def test_cliente_no_puede_ver_solicitudes_ajenas_cambiando_client_id_en_la_url(
    client, customer, customer_profile, search_calls
):
    calls, _ = search_calls
    r = client.get(f"{MY_LIST}?client_id=99&priority_id=1", headers=customer)
    assert r.status_code == 200
    # Se ignoran client_id y priority_id: sigue siendo SU cliente y sin ese filtro.
    assert calls == [{"client_id": CUSTOMER_CLIENT_ID, "status_id": None, "priority_id": None}]


def test_cliente_puede_filtrar_por_estado(client, customer, customer_profile, search_calls):
    calls, _ = search_calls
    client.get(f"{MY_LIST}?status_id=4", headers=customer)
    assert calls == [{"client_id": CUSTOMER_CLIENT_ID, "status_id": 4, "priority_id": None}]


def test_cliente_status_id_invalido_devuelve_422(client, customer, customer_profile, search_calls):
    calls, _ = search_calls
    r = client.get(f"{MY_LIST}?status_id=abc", headers=customer)
    assert r.status_code == 422
    assert "status_id" in r.get_json()["error"]["details"]
    assert calls == []


def test_cliente_sin_solicitudes_recibe_lista_vacia(client, customer, customer_profile, search_calls):
    """Una lista vacía es válida: el cliente todavía no pidió nada."""
    r = client.get(MY_LIST, headers=customer)
    assert r.status_code == 200
    assert r.get_json() == []


def test_cliente_sin_perfil_devuelve_404(client, customer, search_calls, monkeypatch):
    monkeypatch.setattr(clients_repository, "get_client_id_by_user_id", lambda user_id: None)
    calls, _ = search_calls
    r = client.get(MY_LIST, headers=customer)
    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"
    assert calls == []


def test_us05_el_cliente_ve_estado_y_motivo_de_rechazo(client, customer, customer_profile, search_calls):
    """US05: por cada solicitud el cliente ve el estado y, si fue rechazada, el motivo."""
    _, rows = search_calls
    rows.append(_row(1, status_id=4, status_name="rechazado",
                     rejection_reason="Servicio fuera del plan", resolved_at=datetime(2026, 11, 1, 9, 30)))
    item = client.get(MY_LIST, headers=customer).get_json()[0]
    assert item["status_id"] == 4
    assert item["status_name"] == "rechazado"
    assert item["rejection_reason"] == "Servicio fuera del plan"
    assert item["resolved_at"]
