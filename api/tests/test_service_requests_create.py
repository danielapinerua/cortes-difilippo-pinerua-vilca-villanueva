"""Tests de US02 - Solicitar modificación de servicio.

  POST /api/v1/me/service-requests

Como el resto de los tests, no usan MySQL: los repositorios se reemplazan por
funciones en memoria. El `client_id` siempre sale del token del cliente.
"""
from types import SimpleNamespace

import pytest

from app.constants import STATUS_PENDING
from app.repositories import clients_repository, service_requests_repository

BASE = "/api/v1/me/service-requests"
CUSTOMER_CLIENT_ID = 7
CONTRACTED_SERVICE_ID = 3


def _detail(**overrides):
    """Fila como la devuelve el JOIN de US14/US05."""
    row = {
        "id": 1,
        "client_id": CUSTOMER_CLIENT_ID,
        "client_name": "Mariana Gómez",
        "service_id": CONTRACTED_SERVICE_ID,
        "service_name": "Consultoría en Marketing Digital",
        "status_id": STATUS_PENDING,
        "status_name": "pendiente",
        "priority_id": None,
        "priority_name": None,
        "priority_level": None,
        "administrator_id": None,
        "modification_type": "Cambio de horario",
        "description": "Mover la reunión al viernes",
        "rejection_reason": None,
        "created_at": "2026-11-03 10:00:00",
        "resolved_at": None,
    }
    row.update(overrides)
    return row


@pytest.fixture
def customer_profile(monkeypatch):
    """El usuario `customer` (id 2) tiene perfil de cliente con id 7."""
    monkeypatch.setattr(
        clients_repository,
        "get_client_id_by_user_id",
        lambda user_id: CUSTOMER_CLIENT_ID if user_id == 2 else None,
    )


@pytest.fixture
def fake_service_requests(monkeypatch):
    """Reemplaza las operaciones del repositorio y guarda lo que recibe."""
    state = SimpleNamespace(
        contracted=True,
        created=None,
        row=_detail(),
        is_contracted_calls=[],
    )

    def is_contracted_by_client(client_id, service_id):
        state.is_contracted_calls.append((client_id, service_id))
        return state.contracted

    def create(client_id, service_id, modification_type, description=None):
        state.created = {
            "client_id": client_id,
            "service_id": service_id,
            "modification_type": modification_type,
            "description": description,
        }
        return 1

    def get_detail(request_id):
        return {**state.row, "id": request_id}

    monkeypatch.setattr(
        service_requests_repository, "is_contracted_by_client", is_contracted_by_client
    )
    monkeypatch.setattr(service_requests_repository, "create", create)
    monkeypatch.setattr(service_requests_repository, "get_detail", get_detail)
    return state


# ---- Permisos ---------------------------------------------------------------

def test_sin_token_devuelve_401(client):
    r = client.post(BASE, json={"service_id": 1, "modification_type": "Cambio"})

    assert r.status_code == 401
    assert r.get_json()["error"]["code"] == "unauthorized"


def test_admin_no_puede_crear_solicitud_403(client, admin):
    r = client.post(
        BASE,
        json={"service_id": 1, "modification_type": "Cambio"},
        headers=admin,
    )

    assert r.status_code == 403
    assert r.get_json()["error"]["code"] == "forbidden"


# ---- Validaciones del body (422) --------------------------------------------

def test_body_no_json_devuelve_422(client, customer):
    r = client.post(
        BASE,
        data="no soy json",
        content_type="text/plain",
        headers=customer,
    )

    assert r.status_code == 422
    assert r.get_json()["error"]["code"] == "validation_error"


def test_service_id_faltante_devuelve_422(
    client, customer, customer_profile, fake_service_requests
):
    r = client.post(
        BASE,
        json={"modification_type": "Cambio de horario"},
        headers=customer,
    )

    assert r.status_code == 422
    assert "service_id" in r.get_json()["error"]["details"]


def test_service_id_invalido_devuelve_422(
    client, customer, customer_profile, fake_service_requests
):
    for value in ("3", 0, -1, True):
        r = client.post(
            BASE,
            json={"service_id": value, "modification_type": "Cambio de horario"},
            headers=customer,
        )

        assert r.status_code == 422
        assert "service_id" in r.get_json()["error"]["details"]


def test_modification_type_faltante_devuelve_422(
    client, customer, customer_profile, fake_service_requests
):
    r = client.post(
        BASE,
        json={"service_id": CONTRACTED_SERVICE_ID},
        headers=customer,
    )

    assert r.status_code == 422
    assert "modification_type" in r.get_json()["error"]["details"]


def test_modification_type_mayor_a_100_devuelve_422(
    client, customer, customer_profile, fake_service_requests
):
    r = client.post(
        BASE,
        json={"service_id": CONTRACTED_SERVICE_ID, "modification_type": "x" * 101},
        headers=customer,
    )

    assert r.status_code == 422
    assert "modification_type" in r.get_json()["error"]["details"]


def test_description_no_texto_devuelve_422(
    client, customer, customer_profile, fake_service_requests
):
    r = client.post(
        BASE,
        json={
            "service_id": CONTRACTED_SERVICE_ID,
            "modification_type": "Cambio de horario",
            "description": 123,
        },
        headers=customer,
    )

    assert r.status_code == 422
    assert "description" in r.get_json()["error"]["details"]


def test_description_mayor_a_2000_devuelve_422(
    client, customer, customer_profile, fake_service_requests
):
    r = client.post(
        BASE,
        json={
            "service_id": CONTRACTED_SERVICE_ID,
            "modification_type": "Cambio de horario",
            "description": "x" * 2001,
        },
        headers=customer,
    )

    assert r.status_code == 422
    assert "description" in r.get_json()["error"]["details"]


def test_varios_errores_se_devuelven_juntos(
    client, customer, customer_profile, fake_service_requests
):
    r = client.post(BASE, json={}, headers=customer)

    assert r.status_code == 422
    details = r.get_json()["error"]["details"]
    assert set(details) == {"service_id", "modification_type"}


# ---- Errores de negocio (404) ------------------------------------------------

def test_cliente_sin_perfil_devuelve_404(client, customer, monkeypatch):
    monkeypatch.setattr(
        clients_repository, "get_client_id_by_user_id", lambda user_id: None
    )

    r = client.post(
        BASE,
        json={"service_id": CONTRACTED_SERVICE_ID, "modification_type": "Cambio"},
        headers=customer,
    )

    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"


def test_servicio_no_contratado_devuelve_404(
    client, customer, customer_profile, fake_service_requests
):
    fake_service_requests.contracted = False

    r = client.post(
        BASE,
        json={
            "service_id": CONTRACTED_SERVICE_ID,
            "modification_type": "Cambio de horario",
        },
        headers=customer,
    )

    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"


# ---- Caso feliz --------------------------------------------------------------

def test_crear_solicitud_devuelve_201_con_estado_pendiente(
    client, customer, customer_profile, fake_service_requests
):
    r = client.post(
        BASE,
        json={
            "service_id": CONTRACTED_SERVICE_ID,
            "modification_type": "  Cambio de horario  ",
            "description": "  Mover la reunión al viernes  ",
        },
        headers=customer,
    )

    assert r.status_code == 201
    body = r.get_json()
    assert body["client_id"] == CUSTOMER_CLIENT_ID
    assert body["service_id"] == CONTRACTED_SERVICE_ID
    assert body["status_id"] == STATUS_PENDING
    assert body["status_name"] == "pendiente"
    assert body["priority_id"] is None
    assert body["administrator_id"] is None
    assert body["modification_type"] == "Cambio de horario"
    assert body["description"] == "Mover la reunión al viernes"

    assert fake_service_requests.created == {
        "client_id": CUSTOMER_CLIENT_ID,
        "service_id": CONTRACTED_SERVICE_ID,
        "modification_type": "Cambio de horario",
        "description": "Mover la reunión al viernes",
    }
    assert fake_service_requests.is_contracted_calls == [
        (CUSTOMER_CLIENT_ID, CONTRACTED_SERVICE_ID)
    ]


def test_description_vacia_se_guarda_como_null(
    client, customer, customer_profile, fake_service_requests
):
    r = client.post(
        BASE,
        json={
            "service_id": CONTRACTED_SERVICE_ID,
            "modification_type": "Cambio de horario",
            "description": "   ",
        },
        headers=customer,
    )

    assert r.status_code == 201
    assert fake_service_requests.created["description"] is None


def test_client_id_del_body_se_ignora(
    client, customer, customer_profile, fake_service_requests
):
    r = client.post(
        BASE,
        json={
            "client_id": 999,
            "service_id": CONTRACTED_SERVICE_ID,
            "modification_type": "Cambio de horario",
        },
        headers=customer,
    )

    assert r.status_code == 201
    assert fake_service_requests.created["client_id"] == CUSTOMER_CLIENT_ID
