from datetime import UTC, datetime

import pytest

from app.core.config import Settings
from app.models.pdf_document import PdfDocument


@pytest.fixture(autouse=True)
def entorno_de_test(monkeypatch):
    """Provee la configuración de la suite desde el entorno.

    Ignorar el .env es lo que hace la suite realmente hermética: sin esto, el archivo
    de configuración local de quien desarrolla cambiaría el resultado de los tests.
    """
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("MONGO_DATABASE", "pdfs_test")
    monkeypatch.setenv("MONGO_COLLECTION", "pdfs")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("REDIS_TTL_SECONDS", "300")


@pytest.fixture
def documento():
    """Construye un PdfDocument de prueba; cada campo puede sobreescribirse."""

    def construir(**campos) -> PdfDocument:
        valores = {
            "id": "8f6f7c3e-12d5-4f57-9c6c-123456789abc",
            "nombre": "contrato.pdf",
            "checksum": "a7f5f35426b927411fc9231b56382173",
            "texto": "Contenido extraído del PDF",
            "tamano_bytes": 245760,
            "paginas": 3,
            "created_at": datetime(2026, 9, 14, 18, 0, 0, tzinfo=UTC),
            "updated_at": datetime(2026, 9, 14, 18, 0, 0, tzinfo=UTC),
        }
        return PdfDocument(**{**valores, **campos})

    return construir
