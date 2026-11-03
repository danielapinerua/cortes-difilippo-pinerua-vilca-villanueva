"""Tests E2E de US02 contra MySQL real.

Complementan a `tests/test_service_requests_create.py`: acá se prueba el INSERT
real, las FK de `client_services` y el estado inicial guardado en la base.

Requieren la base `tech_solutions_test`:

    cd api && pytest tests/e2e -m e2e
"""
import pytest

from app.constants import STATUS_PENDING

from .conftest import CONTRACTED_SERVICE_ID, NOT_CONTRACTED_SERVICE_ID

pytestmark = pytest.mark.e2e

BASE = "/api/v1/me/service-requests"
ADMIN_LIST = "/api/v1/service-requests"


def test_crear_solicitud_devuelve_201_con_estado_pendiente(http, customer):
    r = http.post(
        BASE,
        json={
            "service_id": CONTRACTED_SERVICE_ID,
            "modification_type": "  Cambio de horario  ",
            "description": "  Mover la reunion al viernes  ",
        },
        headers=customer.headers,
    )

    assert r.status_code == 201
    body = r.get_json()
    assert body["client_id"] == customer.client_id
    assert body["service_id"] == CONTRACTED_SERVICE_ID
    assert body["status_id"] == STATUS_PENDING
    assert body["status_name"] == "pendiente"
    assert body["priority_id"] is None
    assert body["administrator_id"] is None
    assert body["modification_type"] == "Cambio de horario"
    assert body["description"] == "Mover la reunion al viernes"


def test_solicitud_queda_persistida_en_mis_solicitudes(http, customer):
    created = http.post(
        BASE,
        json={
            "service_id": CONTRACTED_SERVICE_ID,
            "modification_type": "Cambio de horario",
        },
        headers=customer.headers,
    ).get_json()

    r = http.get(BASE, headers=customer.headers)
    assert r.status_code == 200
    rows = r.get_json()
    row = next((x for x in rows if x["id"] == created["id"]), None)
    assert row is not None
    assert row["status_name"] == "pendiente"
    assert row["service_id"] == CONTRACTED_SERVICE_ID


def test_servicio_no_contratado_devuelve_404(http, customer):
    r = http.post(
        BASE,
        json={
            "service_id": NOT_CONTRACTED_SERVICE_ID,
            "modification_type": "Cambio de horario",
        },
        headers=customer.headers,
    )

    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"


def test_service_id_faltante_devuelve_422(http, customer):
    r = http.post(
        BASE,
        json={"modification_type": "Cambio de horario"},
        headers=customer.headers,
    )

    assert r.status_code == 422
    assert "service_id" in r.get_json()["error"]["details"]


def test_admin_no_puede_crear_solicitud_403(http, admin):
    r = http.post(
        BASE,
        json={
            "service_id": CONTRACTED_SERVICE_ID,
            "modification_type": "Cambio de horario",
        },
        headers=admin,
    )

    assert r.status_code == 403
    assert r.get_json()["error"]["code"] == "forbidden"


def test_admin_ve_la_solicitud_como_pendiente(http, customer, admin):
    created = http.post(
        BASE,
        json={
            "service_id": CONTRACTED_SERVICE_ID,
            "modification_type": "Cambio de horario",
        },
        headers=customer.headers,
    ).get_json()

    r = http.get(ADMIN_LIST, headers=admin)
    assert r.status_code == 200
    row = next((x for x in r.get_json() if x["id"] == created["id"]), None)
    assert row is not None
    assert row["status_id"] == STATUS_PENDING
    assert row["status_name"] == "pendiente"
