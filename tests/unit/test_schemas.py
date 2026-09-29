import json
from datetime import datetime, timezone

from app.models.pdf_document import PdfDocument
from app.schemas.pdf import PdfDocumentResponse, PdfListResponse


def un_documento() -> PdfDocument:
    return PdfDocument(
        id="8f6f7c3e-12d5-4f57-9c6c-123456789abc",
        nombre="contrato.pdf",
        checksum="a7f5f35426b927411fc9231b56382173",
        texto="Contenido extraído del PDF",
        tamano_bytes=245760,
        paginas=3,
        created_at=datetime(2026, 9, 14, 18, 0, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 9, 14, 18, 0, 0, tzinfo=timezone.utc),
    )


def test_response_se_construye_desde_el_modelo_de_dominio():
    respuesta = PdfDocumentResponse.from_domain(un_documento())

    assert respuesta.id == "8f6f7c3e-12d5-4f57-9c6c-123456789abc"
    assert respuesta.nombre == "contrato.pdf"
    assert respuesta.checksum == "a7f5f35426b927411fc9231b56382173"
    assert respuesta.texto == "Contenido extraído del PDF"
    assert respuesta.tamano_bytes == 245760
    assert respuesta.paginas == 3


def test_response_serializa_las_fechas_en_iso_8601_utc():
    respuesta = PdfDocumentResponse.from_domain(un_documento())

    serializado = json.loads(respuesta.model_dump_json())

    assert serializado["created_at"] == "2026-09-14T18:00:00Z"
    assert serializado["updated_at"] == "2026-09-14T18:00:00Z"


def test_listado_respeta_la_forma_del_contrato():
    listado = PdfListResponse(
        items=[PdfDocumentResponse.from_domain(un_documento())],
        total=1,
        limit=20,
        offset=0,
    )

    serializado = json.loads(listado.model_dump_json())

    assert list(serializado.keys()) == ["items", "total", "limit", "offset"]
    assert serializado["total"] == 1
    assert serializado["limit"] == 20
    assert serializado["offset"] == 0
    assert serializado["items"][0]["nombre"] == "contrato.pdf"


def test_listado_vacio_devuelve_items_vacio_y_total_cero():
    listado = PdfListResponse(items=[], total=0, limit=20, offset=0)

    serializado = json.loads(listado.model_dump_json())

    assert serializado["items"] == []
    assert serializado["total"] == 0
