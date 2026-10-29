from .conftest import PASSWORD

LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"


def test_login_correcto_devuelve_token_y_usuario(client, fake_users):
    r = client.post(LOGIN, json={"email": "admin@test.com", "password": PASSWORD})
    assert r.status_code == 200
    body = r.get_json()
    assert body["token_type"] == "Bearer"
    assert body["token"]
    assert body["user"] == {"id": 1, "email": "admin@test.com", "role": "admin"}
    assert "password_hash" not in str(body)
    assert fake_users.logins == [1]  # se registró el último ingreso


def test_login_fallido_usa_el_mismo_mensaje_para_email_y_password(client):
    """US16: no se debe revelar cuál de los dos campos falló."""
    mala_password = client.post(LOGIN, json={"email": "admin@test.com", "password": "otra"})
    email_inexistente = client.post(LOGIN, json={"email": "nadie@test.com", "password": PASSWORD})
    assert mala_password.status_code == email_inexistente.status_code == 401
    assert mala_password.get_json() == email_inexistente.get_json()


def test_login_cuenta_desactivada_devuelve_401(client):
    r = client.post(LOGIN, json={"email": "baja@test.com", "password": PASSWORD})
    assert r.status_code == 401


def test_login_sin_datos_devuelve_422(client):
    r = client.post(LOGIN, json={})
    assert r.status_code == 422
    assert set(r.get_json()["error"]["details"]) == {"email", "password"}


def test_me_con_token_devuelve_el_usuario(client, customer):
    r = client.get(ME, headers=customer)
    assert r.status_code == 200
    assert r.get_json() == {"id": 2, "email": "cliente@test.com", "role": "client"}


def test_me_sin_token_401(client):
    assert client.get(ME).status_code == 401


def test_token_adulterado_401(client, admin):
    token = admin["Authorization"]
    r = client.get(ME, headers={"Authorization": token[:-3] + "xyz"})
    assert r.status_code == 401
    assert r.get_json()["error"]["message"] == "Token inválido."


def test_header_sin_bearer_401(client):
    r = client.get(ME, headers={"Authorization": "Basic abc"})
    assert r.status_code == 401


def test_token_vencido_401(client, admin, monkeypatch):
    # Con vencimiento de -1 segundo, cualquier token ya está "viejo".
    client.application.config["TOKEN_MAX_AGE_SECONDS"] = -1
    r = client.get(ME, headers=admin)
    assert r.status_code == 401
    assert "expiró" in r.get_json()["error"]["message"]
