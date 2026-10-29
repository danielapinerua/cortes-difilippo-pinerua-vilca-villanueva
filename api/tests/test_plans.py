import pymysql

from app.repositories import plans_repository

BASE = "/api/v1/plans"


def test_health_es_publico(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


# ---- Permisos --------------------------------------------------------------

def test_sin_token_devuelve_401(client):
    r = client.get(BASE)
    assert r.status_code == 401
    assert r.get_json()["error"]["code"] == "unauthorized"


def test_cliente_puede_ver_planes(client, customer):
    assert client.get(BASE, headers=customer).status_code == 200


def test_cliente_no_puede_crear_plan_403(client, customer):
    r = client.post(BASE, json={"name": "X", "price": 1}, headers=customer)
    assert r.status_code == 403
    assert r.get_json()["error"]["code"] == "forbidden"


def test_cliente_no_puede_borrar_ni_modificar(client, customer, admin):
    client.post(BASE, json={"name": "Básico", "price": 100}, headers=admin)
    assert client.put(f"{BASE}/1", json={"price": 1}, headers=customer).status_code == 403
    assert client.delete(f"{BASE}/1", headers=customer).status_code == 403
    assert client.get(f"{BASE}/1", headers=customer).get_json()["price"] == 100  # intacto


# ---- CRUD (como administrador) ---------------------------------------------

def test_listar_vacio(client, admin):
    r = client.get(BASE, headers=admin)
    assert r.status_code == 200
    assert r.get_json() == []


def test_crear_y_obtener(client, admin):
    r = client.post(BASE, json={"name": "Básico", "description": "Plan inicial", "price": 3500.5}, headers=admin)
    assert r.status_code == 201
    created = r.get_json()
    assert created["id"] == 1
    assert created["name"] == "Básico"

    r = client.get(f"{BASE}/1", headers=admin)
    assert r.status_code == 200
    assert r.get_json()["price"] == 3500.5


def test_crear_invalido_devuelve_422_con_detalle(client, admin):
    r = client.post(BASE, json={"name": "  ", "price": -5}, headers=admin)
    assert r.status_code == 422
    err = r.get_json()["error"]
    assert err["code"] == "validation_error"
    assert set(err["details"]) == {"name", "price"}


def test_nombre_demasiado_largo_422(client, admin):
    r = client.post(BASE, json={"name": "x" * 101, "price": 1}, headers=admin)
    assert r.status_code == 422
    assert "name" in r.get_json()["error"]["details"]


def test_crear_sin_json_devuelve_422(client, admin):
    r = client.post(BASE, data="no soy json", content_type="text/plain", headers=admin)
    assert r.status_code == 422


def test_obtener_inexistente_devuelve_404(client, admin):
    r = client.get(f"{BASE}/99", headers=admin)
    assert r.status_code == 404
    assert r.get_json()["error"]["code"] == "not_found"


def test_actualizar_parcial(client, admin):
    client.post(BASE, json={"name": "Básico", "price": 100}, headers=admin)
    r = client.put(f"{BASE}/1", json={"price": 250}, headers=admin)
    assert r.status_code == 200
    body = r.get_json()
    assert body["price"] == 250
    assert body["name"] == "Básico"  # no se tocó


def test_eliminar(client, admin):
    client.post(BASE, json={"name": "Básico", "price": 100}, headers=admin)
    assert client.delete(f"{BASE}/1", headers=admin).status_code == 204
    assert client.get(f"{BASE}/1", headers=admin).status_code == 404


# ---- Errores de la base ----------------------------------------------------

def test_eliminar_plan_en_uso_devuelve_409_in_use(client, admin, monkeypatch):
    client.post(BASE, json={"name": "Básico", "price": 100}, headers=admin)

    def boom(plan_id):
        raise pymysql.err.IntegrityError(1451, "Cannot delete or update a parent row")

    monkeypatch.setattr(plans_repository, "delete", boom)
    r = client.delete(f"{BASE}/1", headers=admin)
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "in_use"


def test_nombre_repetido_devuelve_409_duplicate(client, admin, monkeypatch):
    def boom(data):
        raise pymysql.err.IntegrityError(1062, "Duplicate entry 'Básico' for key 'uq_plans_name'")

    monkeypatch.setattr(plans_repository, "create", boom)
    r = client.post(BASE, json={"name": "Básico", "price": 100}, headers=admin)
    assert r.status_code == 409
    assert r.get_json()["error"]["code"] == "duplicate_entry"


# ---- Rutas inexistentes ----------------------------------------------------

def test_ruta_inexistente_usa_formato_de_error(client):
    r = client.get("/api/v1/no-existe")
    assert r.status_code == 404
    assert "error" in r.get_json()


def test_metodo_no_permitido(client):
    r = client.patch(BASE)
    assert r.status_code == 405
    assert r.get_json()["error"]["code"] == "method_not_allowed"
