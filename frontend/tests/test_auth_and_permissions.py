import requests

from .conftest import PASSWORD, add_request, login_as


def text(resp):
    return resp.get_data(as_text=True)


# ---- Entrada según rol -----------------------------------------------------------

def test_raiz_sin_sesion_manda_al_login(browser):
    r = browser.get("/")
    assert r.status_code == 302 and r.headers["Location"].endswith("/login")


def test_login_cliente_va_a_sus_servicios(browser):
    r = login_as(browser, "cliente@test.com")
    assert r.headers["Location"].endswith("/services")


def test_login_admin_va_a_la_bandeja(browser):
    r = login_as(browser, "admin@test.com")
    assert r.headers["Location"].endswith("/admin/requests")


def test_la_sesion_guarda_token_y_usuario_pero_nunca_la_password(browser):
    login_as(browser, "cliente@test.com")
    with browser.session_transaction() as s:
        assert s["token"] == "token-2"
        assert s["user"] == {"id": 2, "email": "cliente@test.com", "role": "client"}
        assert PASSWORD not in str(dict(s))


def test_cookie_de_sesion_es_httponly_y_samesite(browser):
    r = login_as(browser, "cliente@test.com")
    cookie = r.headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie


# ---- Login fallido (US16) ----------------------------------------------------------

def test_login_incorrecto_muestra_el_mensaje_del_api_y_no_inicia_sesion(browser):
    r = browser.post("/login", data={"email": "cliente@test.com", "password": "mala", "csrf_token": browser.csrf()})
    assert r.status_code == 200
    assert "Email o contraseña incorrectos." in text(r)
    with browser.session_transaction() as s:
        assert "token" not in s


def test_login_vacio_pide_completar_los_campos(browser):
    r = browser.post("/login", data={"email": "", "password": "", "csrf_token": browser.csrf()})
    assert r.status_code == 200
    assert "Completá el email y la contraseña." in text(r)


def test_login_conserva_el_email_pero_nunca_la_password(browser):
    r = browser.post("/login", data={"email": "cliente@test.com", "password": "mala", "csrf_token": browser.csrf()})
    html = text(r)
    assert 'value="cliente@test.com"' in html
    assert "mala" not in html


# ---- CSRF ---------------------------------------------------------------------------

def test_post_sin_csrf_es_rechazado_400(browser):
    r = browser.post("/login", data={"email": "cliente@test.com", "password": PASSWORD})
    assert r.status_code == 400


def test_post_con_csrf_falso_es_rechazado_400(browser):
    browser.csrf()
    r = browser.post("/login", data={"email": "cliente@test.com", "password": PASSWORD, "csrf_token": "falso"})
    assert r.status_code == 400


def test_resolver_sin_csrf_no_llega_al_api(admin_browser, fake_api):
    add_request(fake_api.state)
    admin_browser.post("/admin/requests/1/resolution", data={"decision": "approve"})
    assert fake_api.state["requests"][0]["status_id"] == 1
    assert ("PUT", "/api/v1/service-requests/1/resolution") not in fake_api.state["calls"]


# ---- Logout -------------------------------------------------------------------------

def test_logout_solo_por_post(client_browser):
    assert client_browser.get("/logout").status_code == 405


def test_logout_limpia_la_sesion(client_browser):
    r = client_browser.post("/logout", data={"csrf_token": client_browser.csrf()})
    assert r.status_code == 302
    with client_browser.session_transaction() as s:
        assert "token" not in s
    assert client_browser.get("/services").status_code == 302  # ya no entra


# ---- Permisos de página -------------------------------------------------------------

def test_anonimo_no_entra_a_paginas_privadas(browser):
    for path in ("/services", "/requests", "/requests/new", "/admin/requests", "/admin/requests/1"):
        r = browser.get(path)
        assert r.status_code == 302 and r.headers["Location"].endswith("/login"), path


def test_cliente_no_entra_a_paginas_de_admin(client_browser, fake_api):
    r = client_browser.get("/admin/requests")
    assert r.status_code == 302 and r.headers["Location"].endswith("/services")
    # ni siquiera le preguntamos nada al API
    assert not any(p.endswith("/service-requests") for _, p in fake_api.state["calls"])


def test_admin_no_entra_a_paginas_de_cliente(admin_browser):
    r = admin_browser.get("/services")
    assert r.status_code == 302 and r.headers["Location"].endswith("/admin/requests")


def test_usuario_logueado_que_visita_login_vuelve_a_su_inicio(client_browser):
    assert client_browser.get("/login").headers["Location"].endswith("/services")


# ---- Defensa en profundidad: el API es quien manda ----------------------------------

def test_si_alguien_falsea_el_rol_en_el_front_el_api_responde_403_y_se_muestra_sin_bucle(client_browser):
    """Sesión manipulada: rol 'admin' pero con el token de un cliente.
    El front lo deja pasar a la página, pero el API manda: 403 → página de error (sin redirigir en bucle)."""
    with client_browser.session_transaction() as s:
        s["user"] = {"id": 2, "email": "cliente@test.com", "role": "admin"}
    r = client_browser.get("/admin/requests")
    assert r.status_code == 403
    assert "No tenés permiso" in text(r)


def test_token_vencido_en_el_api_limpia_la_sesion_y_manda_al_login(client_browser):
    with client_browser.session_transaction() as s:
        s["token"] = "token-999"  # el API no lo reconoce → 401
    r = client_browser.get("/services")
    assert r.status_code == 302 and r.headers["Location"].endswith("/login")
    with client_browser.session_transaction() as s:
        assert "token" not in s
    assert "Tu sesión venció" in text(client_browser.get("/login"))


# ---- API caído ----------------------------------------------------------------------

def test_api_caido_muestra_503_amigable_sin_detalles_tecnicos(client_browser, http):
    http.raise_error = requests.ConnectionError("Connection refused: 10.0.0.5:5000")
    r = client_browser.get("/services")
    assert r.status_code == 503
    html = text(r)
    assert "Servicio no disponible" in html
    assert "10.0.0.5" not in html and "Connection refused" not in html


def test_api_caido_en_el_login_tambien_muestra_503(browser, http):
    http.raise_error = requests.Timeout("timeout")
    r = browser.post("/login", data={"email": "a@a.com", "password": "x", "csrf_token": browser.csrf()})
    assert r.status_code == 503


def test_pagina_inexistente_404(browser):
    assert browser.get("/no-existe").status_code == 404
