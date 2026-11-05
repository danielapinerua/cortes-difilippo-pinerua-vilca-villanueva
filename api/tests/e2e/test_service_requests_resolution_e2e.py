"""Tests E2E de US09 contra MySQL real.

Complementan a `tests/test_service_requests_admin.py`: acá se prueba el
UPDATE real, la FK de `administrator_id`, el INSERT en `notifications`,
el rollback y la visibilidad del cambio para el cliente.

Requieren la base `tech_solutions_test`:

    cd api && pytest tests/e2e -m e2e
"""
import pytest

from app.constants import (
    DEFAULT_PLAN_ID,
    STATUS_COMPLETED,
    STATUS_PENDING,
    STATUS_REJECTED,
)
from app.db import get_db
from app.services import notifications_service

from .conftest import CONTRACTED_SERVICE_ID

pytestmark = pytest.mark.e2e

BASE = "/api/v1/me/service-requests"
RESOLUTION = "/api/v1/service-requests"


def _crear_solicitud(http, customer, modification_type="Cambio de horario"):
    r = http.post(
        BASE,
        json={
            "service_id": CONTRACTED_SERVICE_ID,
            "modification_type": modification_type,
        },
        headers=customer.headers,
    )
    assert r.status_code == 201, r.get_json()
    return r.get_json()


def _notificaciones_de(app, user_id):
    with app.app_context():
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                "SELECT id, user_id, message, is_read, created_at "
                "FROM notifications WHERE user_id = %s ORDER BY id",
                (user_id,),
            )
            return list(cur.fetchall())


def _solicitud_en_bd(app, request_id):
    with app.app_context():
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                "SELECT status_id, administrator_id, rejection_reason, resolved_at "
                "FROM service_requests WHERE id = %s",
                (request_id,),
            )
            return cur.fetchone()


def _crear_solicitud_de_cliente_sin_login(app):
    """Cliente creado por el admin (sin cuenta): clients.user_id = NULL."""
    with app.app_context():
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO clients (user_id, plan_id, name, email) "
                "VALUES (NULL, %s, %s, %s)",
                (DEFAULT_PLAN_ID, "E2E Sin Login", "e2e.sinlogin@ejemplo.com"),
            )
            client_id = cur.lastrowid
            cur.execute(
                "INSERT INTO client_services (client_id, service_id) "
                "VALUES (%s, %s)",
                (client_id, CONTRACTED_SERVICE_ID),
            )
            cur.execute(
                "INSERT INTO service_requests "
                "(client_id, service_id, status_id, modification_type) "
                "VALUES (%s, %s, %s, %s)",
                (client_id, CONTRACTED_SERVICE_ID, STATUS_PENDING, "Cambio de horario"),
            )
            request_id = cur.lastrowid
        db.commit()
    return request_id


def test_aprobar_solicitud_actualiza_estado_y_crea_notificacion(
    http, customer, admin, app
):
    created = _crear_solicitud(http, customer)

    r = http.put(
        f"{RESOLUTION}/{created['id']}/resolution",
        json={"decision": "approve"},
        headers=admin,
    )

    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["status_id"] == STATUS_COMPLETED
    assert body["status_name"] == "realizado"
    assert body["client_id"] == customer.client_id
    assert body["client_name"] == "E2E Cliente"
    assert body["service_id"] == CONTRACTED_SERVICE_ID
    assert body["service_name"]
    assert body["administrator_id"] is not None
    assert body["rejection_reason"] is None
    assert body["resolved_at"] is not None

    rows = _notificaciones_de(app, customer.user_id)
    assert len(rows) == 1
    assert rows[0]["is_read"] == 0
    assert rows[0]["created_at"] is not None
    assert rows[0]["message"] == (
        f"Tu solicitud #{created['id']} ({body['service_name']}) "
        "fue aprobada. Estado: realizado."
    )


def test_rechazar_solicitud_guarda_motivo_y_crea_notificacion(
    http, customer, admin, app
):
    created = _crear_solicitud(http, customer)
    motivo = "El alcance pedido excede lo contratado"

    r = http.put(
        f"{RESOLUTION}/{created['id']}/resolution",
        json={"decision": "reject", "rejection_reason": motivo},
        headers=admin,
    )

    assert r.status_code == 200, r.get_json()
    body = r.get_json()
    assert body["status_id"] == STATUS_REJECTED
    assert body["status_name"] == "rechazado"
    assert body["rejection_reason"] == motivo
    assert body["resolved_at"] is not None

    rows = _notificaciones_de(app, customer.user_id)
    assert len(rows) == 1
    assert rows[0]["message"] == (
        f"Tu solicitud #{created['id']} ({body['service_name']}) "
        f"fue rechazada. Motivo: {motivo}"
    )


def test_aprobar_dos_veces_devuelve_409_y_no_duplica_notificacion(
    http, customer, admin, app
):
    created = _crear_solicitud(http, customer)
    url = f"{RESOLUTION}/{created['id']}/resolution"

    first = http.put(url, json={"decision": "approve"}, headers=admin)
    assert first.status_code == 200

    second = http.put(url, json={"decision": "approve"}, headers=admin)
    assert second.status_code == 409
    assert second.get_json()["error"]["code"] == "conflict"

    assert len(_notificaciones_de(app, customer.user_id)) == 1


def test_solicitud_inexistente_devuelve_404_sin_notificacion(http, customer, admin, app):
    r = http.put(
        f"{RESOLUTION}/999999/resolution",
        json={"decision": "approve"},
        headers=admin,
    )

    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"
    assert _notificaciones_de(app, customer.user_id) == []


def test_rechazo_sin_motivo_devuelve_422_sin_notificacion(http, customer, admin, app):
    created = _crear_solicitud(http, customer)

    r = http.put(
        f"{RESOLUTION}/{created['id']}/resolution",
        json={"decision": "reject"},
        headers=admin,
    )

    assert r.status_code == 422
    assert "rejection_reason" in r.get_json()["error"]["details"]
    assert _notificaciones_de(app, customer.user_id) == []


def test_cliente_sin_login_resuelve_sin_notificacion(http, admin, app):
    request_id = _crear_solicitud_de_cliente_sin_login(app)

    r = http.put(
        f"{RESOLUTION}/{request_id}/resolution",
        json={"decision": "approve"},
        headers=admin,
    )

    assert r.status_code == 200, r.get_json()
    assert r.get_json()["status_id"] == STATUS_COMPLETED

    with app.app_context():
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS total FROM notifications WHERE message LIKE %s",
                (f"%#{request_id}%",),
            )
            assert cur.fetchone()["total"] == 0


def test_fallo_de_notificacion_revierte_la_resolucion(
    http, customer, admin, app, monkeypatch
):
    created = _crear_solicitud(http, customer)

    def boom(*args, **kwargs):
        raise RuntimeError("fallo simulado de notificación")

    monkeypatch.setattr(notifications_service, "create_notification", boom)

    r = http.put(
        f"{RESOLUTION}/{created['id']}/resolution",
        json={"decision": "approve"},
        headers=admin,
    )

    assert r.status_code == 500

    row = _solicitud_en_bd(app, created["id"])
    assert row["status_id"] == STATUS_PENDING
    assert row["administrator_id"] is None
    assert row["resolved_at"] is None
    assert _notificaciones_de(app, customer.user_id) == []


def test_cliente_ve_el_nuevo_estado_en_mis_solicitudes(http, customer, admin):
    created = _crear_solicitud(http, customer)

    r = http.put(
        f"{RESOLUTION}/{created['id']}/resolution",
        json={"decision": "approve"},
        headers=admin,
    )
    assert r.status_code == 200

    mine = http.get(BASE, headers=customer.headers)
    assert mine.status_code == 200
    row = next((x for x in mine.get_json() if x["id"] == created["id"]), None)
    assert row is not None
    assert row["status_id"] == STATUS_COMPLETED
    assert row["status_name"] == "realizado"
    assert row["resolved_at"] is not None
