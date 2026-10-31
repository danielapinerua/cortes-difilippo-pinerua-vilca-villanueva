from app.constants import STATUS_COMPLETED, STATUS_PENDING, STATUS_REJECTED
from app.repositories import administrators_repository, service_requests_repository

BASE = "/api/v1/service-requests"


def _solicitud(status_id=STATUS_PENDING, rejection_reason=None, resolved_at=None):
    """Fila de service_requests en memoria (molde de la fila real)."""
    return {
        "id": 1,
        "client_id": 1,
        "service_id": 3,
        "status_id": status_id,
        "priority_id": None,
        "administrator_id": None,
        "modification_type": "Cambio de horario",
        "description": "Mover la reunion al viernes",
        "rejection_reason": rejection_reason,
        "created_at": "2026-10-31 10:00:00",
        "resolved_at": resolved_at,
    }


# ---- Permisos ----------------------------------------------------------------

def test_solicitud_sin_token_devuelve_401(client):
    r = client.put(f"{BASE}/1/resolution")
    assert r.status_code == 401
    assert r.get_json()["error"]["code"] == "unauthorized"


def test_cliente_no_puede_atender_solicitud_devuelve_403(client, customer):
    r = client.put(f"{BASE}/1/resolution", json={"decision": "approve"}, headers=customer)
    assert r.status_code == 403
    assert r.get_json()["error"]["code"] == "forbidden"


# ---- Validaciones del body (422) ---------------------------------------------

def test_body_no_json_devuelve_422(client, admin):
    r = client.put(f"{BASE}/1/resolution", data="no soy json", content_type="text/plain", headers=admin)
    assert r.status_code == 422
    assert r.get_json()["error"]["code"] == "validation_error"


def test_decision_faltante_devuelve_422(client, admin):
    r = client.put(f"{BASE}/1/resolution", json={}, headers=admin)
    assert r.status_code == 422
    assert r.get_json()["error"]["code"] == "validation_error"
    assert "decision" in r.get_json()["error"]["details"]


def test_decision_invalida_devuelve_422(client, admin):
    r = client.put(f"{BASE}/1/resolution", json={"decision": "maybe"}, headers=admin)
    assert r.status_code == 422
    assert "decision" in r.get_json()["error"]["details"]


def test_rechazo_sin_motivo_devuelve_422(client, admin, monkeypatch):
    monkeypatch.setattr(service_requests_repository, "get_by_id", lambda rid: _solicitud())
    r = client.put(f"{BASE}/1/resolution", json={"decision": "reject"}, headers=admin)
    assert r.status_code == 422
    assert r.get_json()["error"]["code"] == "validation_error"
    assert "rejection_reason" in r.get_json()["error"]["details"]


def test_rechazo_con_motivo_vacio_devuelve_422(client, admin, monkeypatch):
    monkeypatch.setattr(service_requests_repository, "get_by_id", lambda rid: _solicitud())
    r = client.put(f"{BASE}/1/resolution", json={"decision": "reject", "rejection_reason": "   "}, headers=admin)
    assert r.status_code == 422
    assert "rejection_reason" in r.get_json()["error"]["details"]


def test_rechazo_con_motivo_mayor_a_500_devuelve_422(client, admin, monkeypatch):
    monkeypatch.setattr(service_requests_repository, "get_by_id", lambda rid: _solicitud())
    r = client.put(
        f"{BASE}/1/resolution",
        json={"decision": "reject", "rejection_reason": "x" * 501},
        headers=admin,
    )
    assert r.status_code == 422
    assert "rejection_reason" in r.get_json()["error"]["details"]


# ---- Errores de negocio (404 / 409) -------------------------------------------

def test_solicitud_inexistente_devuelve_404(client, admin, monkeypatch):
    monkeypatch.setattr(service_requests_repository, "get_by_id", lambda rid: None)
    r = client.put(f"{BASE}/999/resolution", json={"decision": "approve"}, headers=admin)
    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"


def test_solicitud_ya_no_esta_pendiente_devuelve_409(client, admin, monkeypatch):
    monkeypatch.setattr(service_requests_repository, "get_by_id", lambda rid: _solicitud(status_id=STATUS_COMPLETED))
    r = client.put(f"{BASE}/1/resolution", json={"decision": "approve"}, headers=admin)
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "conflict"


def test_admin_sin_perfil_en_administrators_devuelve_404(client, admin, monkeypatch):
    monkeypatch.setattr(service_requests_repository, "get_by_id", lambda rid: _solicitud())
    monkeypatch.setattr(administrators_repository, "get_by_user_id", lambda user_id: None)
    r = client.put(f"{BASE}/1/resolution", json={"decision": "approve"}, headers=admin)
    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"


# ---- Happy paths --------------------------------------------------------------

def test_admin_puede_atender_y_aprobar(client, admin, monkeypatch):
    solicitud = _solicitud()

    def get_by_id(rid):
        return dict(solicitud)

    def update_resolution(rid, status_id, administrator_id, rejection_reason):
        solicitud["status_id"] = status_id
        solicitud["administrator_id"] = administrator_id
        solicitud["rejection_reason"] = rejection_reason
        solicitud["resolved_at"] = "2026-10-31 12:00:00"
        return 1

    monkeypatch.setattr(service_requests_repository, "get_by_id", get_by_id)
    monkeypatch.setattr(service_requests_repository, "update_resolution", update_resolution)
    monkeypatch.setattr(
        administrators_repository,
        "get_by_user_id",
        lambda user_id: {"id": 1, "user_id": user_id, "name": "Samantha"},
    )

    r = client.put(f"{BASE}/1/resolution", json={"decision": "approve"}, headers=admin)
    assert r.status_code == 200
    body = r.get_json()
    assert body["status_id"] == STATUS_COMPLETED
    assert body["administrator_id"] == 1
    assert body["rejection_reason"] is None
    assert body["resolved_at"] is not None


def test_admin_puede_atender_y_rechazar(client, admin, monkeypatch):
    solicitud = _solicitud()
    motivo = "El alcance pedido excede lo contratado"

    def get_by_id(rid):
        return dict(solicitud)

    def update_resolution(rid, status_id, administrator_id, rejection_reason):
        solicitud["status_id"] = status_id
        solicitud["administrator_id"] = administrator_id
        solicitud["rejection_reason"] = rejection_reason
        solicitud["resolved_at"] = "2026-10-31 12:00:00"
        return 1

    monkeypatch.setattr(service_requests_repository, "get_by_id", get_by_id)
    monkeypatch.setattr(service_requests_repository, "update_resolution", update_resolution)
    monkeypatch.setattr(
        administrators_repository,
        "get_by_user_id",
        lambda user_id: {"id": 1, "user_id": user_id, "name": "Samantha"},
    )

    r = client.put(
        f"{BASE}/1/resolution",
        json={"decision": "reject", "rejection_reason": motivo},
        headers=admin,
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["status_id"] == STATUS_REJECTED
    assert body["administrator_id"] == 1
    assert body["rejection_reason"] == motivo
    assert body["resolved_at"] is not None


# ---- Condición de carrera ----------------------------------------------------

def test_update_resolution_que_no_encuentra_fila_devuelve_409(client, admin, monkeypatch):
    monkeypatch.setattr(service_requests_repository, "get_by_id", lambda rid: _solicitud())
    monkeypatch.setattr(service_requests_repository, "update_resolution", lambda *args, **kwargs: 0)
    monkeypatch.setattr(
        administrators_repository,
        "get_by_user_id",
        lambda user_id: {"id": 1, "user_id": user_id, "name": "Samantha"},
    )

    r = client.put(f"{BASE}/1/resolution", json={"decision": "approve"}, headers=admin)
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "conflict"
