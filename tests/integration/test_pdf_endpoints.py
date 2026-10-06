import pytest
from fastapi.testclient import TestClient

from app.core.composition import obtener_servicio
from app.core.in_memory_repository import InMemoryPdfRepository
from app.core.repository import PdfRepository
from app.main import app
from app.models.pdf_document import PdfDocument
from app.services.consulta_service import ConsultaPdfService

ID_EXISTENTE = "8f6f7c3e-12d5-4f57-9c6c-123456789abc"
CHECKSUM_EXISTENTE = "a7f5f35426b927411fc9231b56382173"


@pytest.fixture
def cliente(documento):
    servicio = ConsultaPdfService(InMemoryPdfRepository([documento()]))
    app.dependency_overrides[obtener_servicio] = lambda: servicio
    with TestClient(app) as cliente_de_prueba:
        yield cliente_de_prueba
    app.dependency_overrides.clear()


def test_health_responde_ok(cliente):
    respuesta = cliente.get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_listar_devuelve_la_forma_del_contrato(cliente):
    respuesta = cliente.get("/pdf")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 1
    assert cuerpo["limit"] == 20
    assert cuerpo["offset"] == 0
    assert cuerpo["items"][0]["id"] == ID_EXISTENTE


def test_listar_acepta_limit_y_offset(cliente):
    respuesta = cliente.get("/pdf", params={"limit": 5, "offset": 0})

    assert respuesta.status_code == 200
    assert respuesta.json()["limit"] == 5


def test_listar_rechaza_parametros_invalidos(cliente):
    respuesta = cliente.get("/pdf", params={"limit": 0})

    assert respuesta.status_code == 400
    assert respuesta.json()["error"]["code"] == "VALIDATION_ERROR"


def test_listar_rechaza_parametros_que_no_son_numeros(cliente):
    respuesta = cliente.get(
        "/pdf", params={"limit": "abc"}, headers={"X-Correlation-ID": "parametros-invalidos"}
    )

    assert respuesta.status_code == 400
    error = respuesta.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["correlation_id"] == "parametros-invalidos"


def test_buscar_por_id_devuelve_el_documento(cliente):
    respuesta = cliente.get(f"/pdf/{ID_EXISTENTE}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["id"] == ID_EXISTENTE
    assert cuerpo["nombre"] == "contrato.pdf"
    assert cuerpo["created_at"] == "2026-09-14T18:00:00Z"


def test_buscar_por_id_inexistente_devuelve_404(cliente):
    respuesta = cliente.get("/pdf/id-inexistente")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_buscar_por_checksum_devuelve_el_documento(cliente):
    respuesta = cliente.get(f"/pdf/checksum/{CHECKSUM_EXISTENTE}")

    assert respuesta.status_code == 200
    assert respuesta.json()["checksum"] == CHECKSUM_EXISTENTE


def test_buscar_por_checksum_inexistente_devuelve_404(cliente):
    respuesta = cliente.get("/pdf/checksum/checksum-inexistente")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_el_error_respeta_el_contrato_comun(cliente):
    cuerpo = cliente.get("/pdf/id-inexistente").json()

    assert set(cuerpo["error"]) == {"code", "message", "details", "correlation_id"}


def test_se_propaga_el_correlation_id_recibido(cliente):
    enviado = "11111111-2222-3333-4444-555555555555"

    respuesta = cliente.get("/health", headers={"X-Correlation-ID": enviado})

    assert respuesta.headers["X-Correlation-ID"] == enviado


def test_se_genera_un_correlation_id_cuando_no_viene(cliente):
    respuesta = cliente.get("/health")

    assert respuesta.headers["X-Correlation-ID"]


def test_el_correlation_id_recibido_aparece_en_el_cuerpo_del_error(cliente):
    enviado = "11111111-2222-3333-4444-555555555555"

    respuesta = cliente.get("/pdf/id-inexistente", headers={"X-Correlation-ID": enviado})

    assert respuesta.json()["error"]["correlation_id"] == enviado


class RepositorioCaido(PdfRepository):
    """Simula una dependencia de infraestructura que deja de responder."""

    async def get_by_id(self, documento_id: str) -> PdfDocument | None:
        raise RuntimeError("la base de datos no responde")

    async def get_by_checksum(self, checksum: str) -> PdfDocument | None:
        raise RuntimeError("la base de datos no responde")

    async def listar(self, limit: int, offset: int) -> list[PdfDocument]:
        raise RuntimeError("la base de datos no responde")

    async def contar(self) -> int:
        raise RuntimeError("la base de datos no responde")


def test_un_fallo_de_infraestructura_devuelve_el_error_comun():
    app.dependency_overrides[obtener_servicio] = lambda: ConsultaPdfService(RepositorioCaido())
    with TestClient(app, raise_server_exceptions=False) as cliente_de_prueba:
        respuesta = cliente_de_prueba.get(f"/pdf/{ID_EXISTENTE}")
    app.dependency_overrides.clear()

    assert respuesta.status_code == 500
    cuerpo = respuesta.json()
    assert cuerpo["error"]["code"] == "INTERNAL_ERROR"
    assert cuerpo["error"]["correlation_id"]
