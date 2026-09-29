from datetime import datetime, timezone

import pytest

from app.models.pdf_document import PdfDocument


@pytest.fixture(autouse=True)
def entorno_de_test(monkeypatch):
    """Provee la configuración para que la suite no dependa de un .env presente."""
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
            "created_at": datetime(2026, 9, 14, 18, 0, 0, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 9, 14, 18, 0, 0, tzinfo=timezone.utc),
        }
        return PdfDocument(**{**valores, **campos})

    return construir
