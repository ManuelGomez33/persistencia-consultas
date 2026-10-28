import logging

import pytest
from fastapi.testclient import TestClient

from app.core.composition import obtener_settings
from app.core.consul_registry import ConsulRegistry
from app.main import app


@pytest.fixture(autouse=True)
def settings_y_nivel_restaurados():
    """obtener_settings se cachea y el lifespan cambia el nivel del root: se restauran."""
    root = logging.getLogger()
    nivel = root.level
    obtener_settings.cache_clear()
    yield
    obtener_settings.cache_clear()
    root.setLevel(nivel)


def test_registra_inicio_y_apagado_ordenados(caplog):
    caplog.set_level(logging.INFO)

    with TestClient(app):
        pass

    mensajes = [r.getMessage() for r in caplog.records]
    assert "servicio iniciado" in mensajes
    assert mensajes.index("apagado iniciado") < mensajes.index("apagado completo")


def test_el_lifespan_aplica_log_level(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    with TestClient(app):
        assert logging.getLogger().level == logging.DEBUG


def test_consul_se_registra_al_inicio_y_deregistra_al_apagar(monkeypatch, tmp_path):
    eventos = []
    token_file = tmp_path / "microservices.token"
    token_file.write_text("test-token", encoding="utf-8")
    monkeypatch.setenv("CONSUL_ENABLED", "true")
    monkeypatch.setenv("CONSUL_HTTP_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("CONSUL_SERVICE_ADDRESS", "persistencia-consultas")

    async def registrar(self):
        eventos.append("registrado")

    async def deregistrar(self):
        eventos.append("deregistrado")

    monkeypatch.setattr(ConsulRegistry, "register", registrar)
    monkeypatch.setattr(ConsulRegistry, "deregister", deregistrar)

    with TestClient(app):
        assert eventos == ["registrado"]

    assert eventos == ["registrado", "deregistrado"]
