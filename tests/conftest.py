import pytest


@pytest.fixture(autouse=True)
def entorno_de_test(monkeypatch):
    """Provee la configuración para que la suite no dependa de un .env presente."""
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGO_DATABASE", "pdfs_test")
    monkeypatch.setenv("MONGO_COLLECTION", "pdfs")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("REDIS_TTL_SECONDS", "300")
