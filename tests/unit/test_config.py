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
