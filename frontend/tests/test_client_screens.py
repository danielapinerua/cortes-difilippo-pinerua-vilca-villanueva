from datetime import datetime

from .conftest import add_request


def text(r):
    return r.get_data(as_text=True)


def test_servicios_se_listan_con_su_fecha_de_contratacion(client_browser):
    html = text(client_browser.get("/services"))
    assert "Consultoría en Marketing Digital" in html
    assert "Soporte Técnico Mensual" in html
    assert "Sin descripción." in html            # el servicio 4 no tiene descripción
    assert "01/09/2026" in html                  # RFC-822 → dd/mm/aaaa


def test_cada_servicio_enlaza_a_la_nueva_solicitud_con_el_servicio_elegido(client_browser):
    html = text(client_browser.get("/services"))
    assert "/requests/new?service_id=3" in html


def test_cliente_sin_servicios_ve_estado_vacio(client_browser, fake_api):
    fake_api.state["contracted"][7] = []
    assert "Todavía no tenés servicios contratados" in text(client_browser.get("/services"))


def test_formulario_nueva_solicitud_preselecciona_el_servicio(client_browser):
    html = text(client_browser.get("/requests/new?service_id=4"))
    assert 'value="4" selected' in html


def test_crear_solicitud_ok_redirige_a_mis_solicitudes(client_browser, fake_api):
    r = client_browser.post("/requests/new", data={
        "service_id": "3", "modification_type": "Cambio de horario",
        "description": "Mover al viernes", "csrf_token": client_browser.csrf()})
    assert r.status_code == 302 and r.headers["Location"].endswith("/requests")
    assert len(fake_api.state["requests"]) == 1
    assert "Solicitud #1 enviada" in text(client_browser.get("/requests"))


def test_descripcion_vacia_se_envia_como_null(client_browser, fake_api):
    client_browser.post("/requests/new", data={"service_id": "3", "modification_type": "X",
                                               "description": "  ", "csrf_token": client_browser.csrf()})
    assert fake_api.state["requests"][0]["description"] is None


def test_tipo_de_modificacion_vacio_muestra_el_error_del_api_y_conserva_lo_escrito(client_browser, fake_api):
    r = client_browser.post("/requests/new", data={
        "service_id": "3", "modification_type": "", "description": "Texto largo",
        "csrf_token": client_browser.csrf()})
    html = text(r)
    assert r.status_code == 200
    assert "Es obligatorio y debe ser texto." in html
    assert "Texto largo" in html
    assert 'value="3" selected' in html
    assert fake_api.state["requests"] == []


def test_sin_elegir_servicio_se_avisa_sin_llamar_al_api(client_browser, fake_api):
    r = client_browser.post("/requests/new", data={"service_id": "", "modification_type": "X",
                                                   "csrf_token": client_browser.csrf()})
    assert "Elegí un servicio." in text(r)
    assert ("POST", "/api/v1/me/service-requests") not in fake_api.state["calls"]


def test_servicio_ajeno_forzado_en_el_formulario_muestra_error(client_browser, fake_api):
    """Servicio 4 no lo tiene contratado el cliente 8; el API responde 404 y el front lo muestra."""
    # cliente2 (user 3 / cliente 8) solo tiene el servicio 3
    from .conftest import login_as
    client_browser.post("/logout", data={"csrf_token": client_browser.csrf()})
    login_as(client_browser, "otro@test.com")
    r = client_browser.post("/requests/new", data={"service_id": "4", "modification_type": "X",
                                                   "csrf_token": client_browser.csrf()})
    assert "no tiene contratado ese servicio" in text(r)


def test_mis_solicitudes_muestra_estado_y_motivo_de_rechazo(client_browser, fake_api):
    add_request(fake_api.state, status_id=4, rejection_reason="Servicio fuera del plan")
    add_request(fake_api.state, status_id=1)
    html = text(client_browser.get("/requests"))
    assert "Rechazada" in html and "Pendiente" in html
    assert "Motivo del rechazo:" in html and "Servicio fuera del plan" in html


def test_solo_ve_sus_solicitudes(client_browser, fake_api):
    add_request(fake_api.state, client_id=7, modification_type="Mía")
    add_request(fake_api.state, client_id=8, modification_type="AJENA-NO-MOSTRAR")
    html = text(client_browser.get("/requests"))
    assert "Mía" in html and "AJENA-NO-MOSTRAR" not in html


def test_filtro_por_estado(client_browser, fake_api):
    add_request(fake_api.state, status_id=1, modification_type="PENDIENTE-X")
    add_request(fake_api.state, status_id=5, modification_type="REALIZADA-X")
    html = text(client_browser.get("/requests?status_id=5"))
    assert "REALIZADA-X" in html and "PENDIENTE-X" not in html


def test_filtro_basura_se_ignora_y_no_rompe(client_browser, fake_api):
    add_request(fake_api.state, modification_type="VISIBLE-X")
    r = client_browser.get("/requests?status_id=hola;DROP")
    assert r.status_code == 200 and "VISIBLE-X" in text(r)


def test_filtro_sin_resultados_y_sin_solicitudes_tienen_mensajes_distintos(client_browser, fake_api):
    assert "Todavía no pediste ninguna modificación" in text(client_browser.get("/requests"))
    add_request(fake_api.state, status_id=1)
    assert "No hay solicitudes con ese estado" in text(client_browser.get("/requests?status_id=5"))


def test_fechas_se_muestran_sin_conversion_de_zona(client_browser, fake_api):
    add_request(fake_api.state, status_id=5, resolved_at=datetime(2026, 11, 1, 9, 30))
    html = text(client_browser.get("/requests"))
    assert "31/10/2026 10:00" in html and "01/11/2026 09:30" in html


def test_texto_con_html_se_escapa_xss(client_browser, fake_api):
    add_request(fake_api.state, modification_type="<img src=x onerror=alert(1)>",
                description="<script>alert('xss')</script>")
    html = text(client_browser.get("/requests"))
    assert "<script>alert" not in html and "<img src=x" not in html
    assert "&lt;script&gt;" in html
