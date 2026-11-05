"""Tests unitarios del módulo de notificaciones internas.

No tocan MySQL: reemplazan `notifications_repository.create` por una
función en memoria. El INSERT real se prueba en los e2e.
"""
import pytest

from app.repositories import notifications_repository
from app.services import notifications_service


def test_crear_notificacion_devuelve_id_y_guarda_datos(monkeypatch):
    capturado = {}

    def create(user_id, message):
        capturado["user_id"] = user_id
        capturado["message"] = message
        return 7

    monkeypatch.setattr(notifications_repository, "create", create)

    notification_id = notifications_service.create_notification(2, "Tu solicitud #1 fue aprobada.")

    assert notification_id == 7
    assert capturado == {
        "user_id": 2,
        "message": "Tu solicitud #1 fue aprobada.",
    }


def test_mensaje_mas_largo_que_500_se_trunca(monkeypatch):
    capturado = {}

    def create(user_id, message):
        capturado["message"] = message
        return 1

    monkeypatch.setattr(notifications_repository, "create", create)

    notifications_service.create_notification(2, "x" * 600)

    assert len(capturado["message"]) == notifications_service.MESSAGE_MAX
    assert capturado["message"].endswith("...")


def test_mensaje_se_limpia_con_strip(monkeypatch):
    capturado = {}

    def create(user_id, message):
        capturado["message"] = message
        return 1

    monkeypatch.setattr(notifications_repository, "create", create)

    notifications_service.create_notification(2, "  hola  ")

    assert capturado["message"] == "hola"


@pytest.mark.parametrize("user_id", [None, 0, -1, True, "2", 2.5])
def test_user_id_invalido_lanza_value_error(user_id):
    with pytest.raises(ValueError):
        notifications_service.create_notification(user_id, "mensaje")


@pytest.mark.parametrize("message", [None, "", "   ", 123])
def test_mensaje_invalido_lanza_value_error(message):
    with pytest.raises(ValueError):
        notifications_service.create_notification(2, message)
