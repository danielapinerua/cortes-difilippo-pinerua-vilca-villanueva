VALID = {"name": "Ana Pérez", "email": "ana@test.com", "phone": "", "dni": "",
         "password": "Clave-nueva-1", "password_confirm": "Clave-nueva-1"}


def post(browser, **over):
    data = {**VALID, **over, "csrf_token": browser.csrf()}
    return browser.post("/register", data=data)


def test_registro_exitoso_redirige_al_login(browser, fake_api):
    r = post(browser)
    assert r.status_code == 302 and r.headers["Location"].endswith("/login")
    assert any(u["email"] == "ana@test.com" and u["role"] == "client" for u in fake_api.state["users"].values())
    assert "Cuenta creada" in browser.get("/login").get_data(as_text=True)


def test_telefono_y_dni_vacios_viajan_como_null(browser, monkeypatch):
    from app import api_client
    sent = {}
    monkeypatch.setattr(api_client, "register", lambda payload: sent.update(payload) or {})
    post(browser)
    assert sent["phone"] is None and sent["dni"] is None


def test_errores_del_api_se_muestran_junto_a_cada_campo(browser):
    r = post(browser, name="  ", password="123", password_confirm="456")
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert html.count("invalid-feedback") >= 3
    assert "Es obligatorio." in html
    assert "al menos 8 caracteres" in html
    assert "no coinciden" in html


def test_registro_con_error_conserva_lo_escrito_pero_no_las_contrasenas(browser):
    r = post(browser, name="Ana Pérez", password="123", password_confirm="456")
    html = r.get_data(as_text=True)
    assert 'value="Ana Pérez"' in html
    assert 'value="ana@test.com"' in html
    assert 'value="123"' not in html and 'value="456"' not in html


def test_email_duplicado_se_informa_en_el_campo(browser):
    r = post(browser, email="cliente@test.com")
    assert r.status_code == 200
    assert "Ya existe una cuenta con ese email." in r.get_data(as_text=True)


def test_el_rol_no_se_puede_elegir_desde_el_formulario(browser, fake_api):
    post(browser, role="admin")
    assert fake_api.state["users"][max(fake_api.state["users"])]["role"] == "client"


def test_html_en_los_campos_se_escapa(browser):
    r = post(browser, name='<script>alert(1)</script>', password="1", password_confirm="2")
    html = r.get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
