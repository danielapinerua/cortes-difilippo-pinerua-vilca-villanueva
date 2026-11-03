"""Tests de US04 (Realizar un reclamo)."""

import pytest

from app.repositories import (
    clients_repository,
    claims_repository,
    service_requests_repository,
)

BASE = "/api/v1/me/claims"
CUSTOMER_CLIENT_ID = 7
SERVICE_ID = 3


def _claim(claim_id=1, **extra):
    """Fila como la devuelve el repositorio de reclamos."""

    row = {
        "id": claim_id,
        "client_id": CUSTOMER_CLIENT_ID,
        "service_id": SERVICE_ID,
        "priority_id": 2,
        "administrator_id": None,
        "category": "technical",
        "description": "El servicio presenta interrupciones.",
        "status": "pending",
        "created_at": "2026-11-01 10:00:00",
        "resolved_at": None,
    }
    row.update(extra)
    return row


@pytest.fixture
def claim_repositories(monkeypatch):
    """Simula los repositorios utilizados por US04."""

    calls = {
        "created": [],
        "contracted": [],
    }


    def fake_get_client_id_by_user_id(user_id):
        return CUSTOMER_CLIENT_ID if user_id == 2 else None


    def fake_is_contracted_by_client(client_id, service_id):
        calls["contracted"].append((client_id, service_id))
        return client_id == CUSTOMER_CLIENT_ID and service_id == SERVICE_ID


    def fake_create(client_id, service_id, category, description, priority_id):
        calls["created"].append({
            "client_id": client_id,
            "service_id": service_id,
            "category": category,
            "description": description,
            "priority_id": priority_id,
        })
        return 1


    def fake_get_by_id(claim_id):
        return _claim(claim_id)

    monkeypatch.setattr(
        clients_repository,
        "get_client_id_by_user_id",
        fake_get_client_id_by_user_id,
    )
    monkeypatch.setattr(
        service_requests_repository,
        "is_contracted_by_client",
        fake_is_contracted_by_client,
    )
    monkeypatch.setattr(claims_repository, "create", fake_create)
    monkeypatch.setattr(claims_repository, "get_by_id", fake_get_by_id)

    return calls


def test_realizar_reclamo_sin_token_devuelve_401(client):
    r = client.post(BASE, json={
        "service_id": SERVICE_ID,
        "category": "technical",
        "description": "El servicio presenta interrupciones.",
    })

    assert r.status_code == 401
    assert r.get_json()["error"]["code"] == "unauthorized"


def test_admin_no_puede_realizar_reclamos_403(client, admin):
    r = client.post(BASE, headers=admin, json={
        "service_id": SERVICE_ID,
        "category": "technical",
        "description": "El servicio presenta interrupciones.",
    })

    assert r.status_code == 403
    assert r.get_json()["error"]["code"] == "forbidden"


def test_cliente_sin_perfil_devuelve_404(client, customer, claim_repositories, monkeypatch):
    monkeypatch.setattr(
        clients_repository,
        "get_client_id_by_user_id",
        lambda user_id: None,
    )

    r = client.post(BASE, headers=customer, json={
        "service_id": SERVICE_ID,
        "category": "technical",
        "description": "El servicio presenta interrupciones.",
    })

    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"


def test_cliente_no_puede_reclamar_servicio_no_contratado(
    client, customer, claim_repositories
):
    r = client.post(BASE, headers=customer, json={
        "service_id": 99,
        "category": "technical",
        "description": "El servicio presenta interrupciones.",
    })

    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"


def test_cliente_registra_reclamo_correctamente(
    client, customer, claim_repositories
):
    calls = claim_repositories

    r = client.post(BASE, headers=customer, json={
        "service_id": SERVICE_ID,
        "category": "technical",
        "description": "El servicio presenta interrupciones.",
    })

    assert r.status_code == 201

    data = r.get_json()
    assert data["id"] == 1
    assert data["client_id"] == CUSTOMER_CLIENT_ID
    assert data["service_id"] == SERVICE_ID
    assert data["category"] == "technical"
    assert data["description"] == "El servicio presenta interrupciones."
    assert data["status"] == "pending"

    assert calls["contracted"] == [(CUSTOMER_CLIENT_ID, SERVICE_ID)]

    assert calls["created"] == [{
        "client_id": CUSTOMER_CLIENT_ID,
        "service_id": SERVICE_ID,
        "category": "technical",
        "description": "El servicio presenta interrupciones.",
        "priority_id": 2,
    }]


def test_realizar_reclamo_sin_json_devuelve_400(client, customer):
    r = client.post(BASE, headers=customer)

    assert r.status_code == 400
    assert r.get_json()["error"] == "Se esperaba un objeto JSON."


def test_realizar_reclamo_sin_service_id_devuelve_422(
    client, customer, claim_repositories
):
    r = client.post(BASE, headers=customer, json={
        "category": "technical",
        "description": "El servicio presenta interrupciones.",
    })

    assert r.status_code == 422
    assert r.get_json()["error"]["code"] == "validation_error"


def test_realizar_reclamo_sin_descripcion_devuelve_422(
    client, customer, claim_repositories
):
    r = client.post(BASE, headers=customer, json={
        "service_id": SERVICE_ID,
        "category": "technical",
        "description": "",
    })

    assert r.status_code == 422
    assert r.get_json()["error"]["code"] == "validation_error"


def test_realizar_reclamo_con_categoria_invalida_devuelve_422(
    client, customer, claim_repositories
):
    r = client.post(BASE, headers=customer, json={
        "service_id": SERVICE_ID,
        "category": "billing",
        "description": "El servicio presenta interrupciones.",
    })

    assert r.status_code == 422
    assert r.get_json()["error"]["code"] == "validation_error"