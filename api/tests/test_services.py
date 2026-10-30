from app.repositories import clients_repository, services_repository

BASE = "/api/v1/me/services"


def test_me_services_sin_token_devuelve_401(client):
    r = client.get(BASE)
    assert r.status_code == 401
    assert r.get_json()["error"]["code"] == "unauthorized"


def test_cliente_con_servicios_obtiene_200_con_lista(client, customer, monkeypatch):
    monkeypatch.setattr(clients_repository, "get_client_id_by_user_id", lambda user_id: 1)
    monkeypatch.setattr(
        services_repository,
        "list_contracted_by_client",
        lambda client_id: [
            {
                "id": 1,
                "name": "Consultoría en Finanzas y Contabilidad",
                "description": "Asesoría en gestión financiera y tributaria",
                "contracted_at": "2026-01-15 10:00:00",
            },
        ],
    )

    r = client.get(BASE, headers=customer)
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Consultoría en Finanzas y Contabilidad"


def test_cliente_sin_servicios_devuelve_200_con_lista_vacia(client, customer, monkeypatch):
    monkeypatch.setattr(clients_repository, "get_client_id_by_user_id", lambda user_id: 1)
    monkeypatch.setattr(services_repository, "list_contracted_by_client", lambda client_id: [])

    r = client.get(BASE, headers=customer)
    assert r.status_code == 200
    assert r.get_json() == []


def test_admin_no_puede_ver_sus_servicios_devuelve_403(client, admin):
    r = client.get(BASE, headers=admin)
    assert r.status_code == 403
    assert r.get_json()["error"]["code"] == "forbidden"


def test_cliente_sin_perfil_en_clients_devuelve_404(client, customer, monkeypatch):
    monkeypatch.setattr(clients_repository, "get_client_id_by_user_id", lambda user_id: None)

    r = client.get(BASE, headers=customer)
    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"
