import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_lee_las_variables_de_entorno(monkeypatch):
    monkeypatch.setenv("MONGO_URI", "mongodb://mongo-de-prueba:27017")
    monkeypatch.setenv("MONGO_DATABASE", "base_de_prueba")
    monkeypatch.setenv("MONGO_COLLECTION", "coleccion_de_prueba")
    monkeypatch.setenv("REDIS_URL", "redis://redis-de-prueba:6379/1")
    monkeypatch.setenv("REDIS_TTL_SECONDS", "60")

    settings = Settings()

    assert settings.mongo_uri == "mongodb://mongo-de-prueba:27017"
    assert settings.mongo_database == "base_de_prueba"
    assert settings.mongo_collection == "coleccion_de_prueba"
    assert settings.redis_url == "redis://redis-de-prueba:6379/1"
    assert settings.redis_ttl_seconds == 60


def test_settings_falla_si_falta_una_variable_obligatoria(monkeypatch):
    monkeypatch.delenv("MONGO_URI")

    with pytest.raises(ValidationError):
        Settings()


def test_log_level_es_opcional_e_info_por_defecto():
    assert Settings().log_level == "INFO"


def test_log_level_invalido_impide_arrancar(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "VERBOSE")

    with pytest.raises(ValidationError):
        Settings()


def test_settings_lee_la_integracion_con_consul(monkeypatch, tmp_path):
    token_file = tmp_path / "microservices.token"
    token_file.write_text("secret-token", encoding="utf-8")
    monkeypatch.setenv("CONSUL_ENABLED", "true")
    monkeypatch.setenv("CONSUL_HTTP_ADDR", "http://consul:8500")
    monkeypatch.setenv("CONSUL_HTTP_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("CONSUL_SERVICE_ADDRESS", "persistencia-consultas")
    monkeypatch.setenv("CONSUL_SERVICE_PORT", "8000")

    settings = Settings()

    assert settings.consul_enabled is True
    assert settings.consul_http_addr == "http://consul:8500"
    assert settings.consul_http_token_file == str(token_file)
    assert settings.consul_service_address == "persistencia-consultas"
    assert settings.consul_service_port == 8000
