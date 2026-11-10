from datetime import datetime

from .conftest import add_request


def text(r):
    return r.get_data(as_text=True)


def pos(html, needle):
    return html.index(needle)


def test_bandeja_ordena_por_prioridad_y_deja_sin_prioridad_al_final(admin_browser, fake_api):
    add_request(fake_api.state, priority_id=None, modification_type="SIN-PRIO")
    add_request(fake_api.state, priority_id=3, modification_type="BAJA")
    add_request(fake_api.state, priority_id=1, modification_type="ALTA")
    html = text(admin_browser.get("/admin/requests"))
    assert pos(html, "ALTA") < pos(html, "BAJA") < pos(html, "SIN-PRIO")
    assert "Sin asignar" in html


def test_bandeja_muestra_cliente_servicio_y_botones_segun_estado(admin_browser, fake_api):
    add_request(fake_api.state, status_id=1)
    add_request(fake_api.state, status_id=5, resolved_at=datetime(2026, 11, 1, 9, 0))
    html = text(admin_browser.get("/admin/requests"))
    assert "Mariana Gómez" in html and "Consultoría en Marketing Digital" in html
    import re
    labels = re.findall(r'class="btn btn-sm btn-outline-primary"[^>]*>\s*(\w+)\s*</a>', html)
    assert labels == ["Atender", "Ver"]   # pendiente → Atender ; resuelta → Ver


def test_bandeja_vacia(admin_browser):
    assert "No hay solicitudes" in text(admin_browser.get("/admin/requests"))


def test_filtros_de_estado_y_prioridad_se_combinan(admin_browser, fake_api):
    add_request(fake_api.state, status_id=1, priority_id=1, modification_type="A-OK")
    add_request(fake_api.state, status_id=1, priority_id=2, modification_type="B-NO")
    add_request(fake_api.state, status_id=5, priority_id=1, modification_type="C-NO")
    html = text(admin_browser.get("/admin/requests?status_id=1&priority_id=1"))
    assert "A-OK" in html and "B-NO" not in html and "C-NO" not in html
    assert "1 solicitud." in html


def test_filtros_sin_coincidencias(admin_browser, fake_api):
    add_request(fake_api.state, status_id=1)
    assert "Ninguna solicitud coincide" in text(admin_browser.get("/admin/requests?status_id=5"))


def test_detalle_pendiente_muestra_el_formulario_de_resolucion(admin_browser, fake_api):
    add_request(fake_api.state, description="Línea 1\nLínea 2")
    html = text(admin_browser.get("/admin/requests/1"))
    assert "Atender solicitud" in html and 'name="decision"' in html
    assert "csrf_token" in html


def test_detalle_resuelta_no_muestra_formulario(admin_browser, fake_api):
    add_request(fake_api.state, status_id=4, rejection_reason="No corresponde", resolved_at=datetime(2026, 11, 1, 9, 0))
    html = text(admin_browser.get("/admin/requests/1"))
    assert 'name="decision"' not in html
    assert "ya fue resuelta" in html and "No corresponde" in html


def test_detalle_inexistente_404(admin_browser):
    r = admin_browser.get("/admin/requests/99")
    assert r.status_code == 404 and "La solicitud no existe." in text(r)


def test_aprobar_marca_realizada_y_vuelve_a_la_bandeja(admin_browser, fake_api):
    add_request(fake_api.state)
    r = admin_browser.post("/admin/requests/1/resolution",
                           data={"decision": "approve", "csrf_token": admin_browser.csrf()})
    assert r.status_code == 302 and r.headers["Location"].endswith("/admin/requests")
    assert fake_api.state["requests"][0]["status_id"] == 5
    assert "Solicitud aprobada." in text(admin_browser.get("/admin/requests"))


def test_rechazar_con_motivo(admin_browser, fake_api):
    add_request(fake_api.state)
    admin_browser.post("/admin/requests/1/resolution", data={
        "decision": "reject", "rejection_reason": "  Fuera del plan  ", "csrf_token": admin_browser.csrf()})
    req = fake_api.state["requests"][0]
    assert req["status_id"] == 4 and req["rejection_reason"] == "Fuera del plan"


def test_rechazar_sin_motivo_muestra_el_error_conserva_el_formulario_y_no_cambia_nada(admin_browser, fake_api):
    add_request(fake_api.state)
    r = admin_browser.post("/admin/requests/1/resolution", data={
        "decision": "reject", "rejection_reason": "   ", "csrf_token": admin_browser.csrf()})
    html = text(r)
    assert r.status_code == 422
    assert "El motivo del rechazo es obligatorio." in html
    assert 'id="d-reject"' in html and "checked" in html      # sigue en "Rechazar"
    reason_box_tag = html.split('id="reason-box"')[1].split(">")[0]
    assert "hidden" not in reason_box_tag                      # el motivo queda visible
    assert fake_api.state["requests"][0]["status_id"] == 1


def test_el_motivo_no_se_manda_al_aprobar(admin_browser, fake_api, monkeypatch):
    from app import api_client
    sent = {}
    monkeypatch.setattr(api_client, "resolve_request",
                        lambda token, rid, decision, reason=None: sent.update(decision=decision, reason=reason) or {})
    add_request(fake_api.state)
    admin_browser.post("/admin/requests/1/resolution", data={
        "decision": "approve", "rejection_reason": "texto que quedó escrito", "csrf_token": admin_browser.csrf()})
    assert sent == {"decision": "approve", "reason": None}


def test_decision_invalida_forzada_se_informa(admin_browser, fake_api):
    add_request(fake_api.state)
    r = admin_browser.post("/admin/requests/1/resolution", data={"decision": "borrar", "csrf_token": admin_browser.csrf()})
    assert r.status_code == 422 and "approve" in text(r)


def test_resolver_una_ya_resuelta_avisa_conflicto(admin_browser, fake_api):
    add_request(fake_api.state, status_id=5, resolved_at=datetime(2026, 11, 1, 9, 0))
    r = admin_browser.post("/admin/requests/1/resolution",
                           data={"decision": "approve", "csrf_token": admin_browser.csrf()}, follow_redirects=True)
    assert "ya no está pendiente" in text(r)


def test_cliente_no_puede_resolver_solicitudes(client_browser, fake_api):
    add_request(fake_api.state)
    r = client_browser.post("/admin/requests/1/resolution",
                            data={"decision": "approve", "csrf_token": client_browser.csrf()})
    assert r.status_code == 302
    assert fake_api.state["requests"][0]["status_id"] == 1
