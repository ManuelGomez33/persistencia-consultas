import json
from datetime import UTC, datetime

from app.schemas.pdf import PdfDocumentResponse, PdfListResponse


def test_response_se_construye_desde_el_modelo_de_dominio(documento):
    respuesta = PdfDocumentResponse.from_domain(documento())

    assert respuesta.id == "8f6f7c3e-12d5-4f57-9c6c-123456789abc"
    assert respuesta.nombre == "contrato.pdf"
    assert respuesta.checksum == "a7f5f35426b927411fc9231b56382173"
    assert respuesta.texto == "Contenido extraído del PDF"
    assert respuesta.tamano_bytes == 245760
    assert respuesta.paginas == 3


def test_response_serializa_las_fechas_en_iso_8601_utc(documento):
    respuesta = PdfDocumentResponse.from_domain(documento())

    serializado = json.loads(respuesta.model_dump_json())

    assert serializado["created_at"] == "2026-09-14T18:00:00.000Z"
    assert serializado["updated_at"] == "2026-09-14T18:00:00.000Z"


def test_response_serializa_las_fechas_con_milisegundos(documento):
    # Mismo formato que devuelve persistencia-actualizaciones (su contrato, A15):
    # MongoDB guarda milisegundos, así el POST y el GET del mismo documento coinciden.
    creado = datetime(2026, 9, 14, 18, 0, 0, 123000, tzinfo=UTC)
    respuesta = PdfDocumentResponse.from_domain(documento(created_at=creado))

    serializado = json.loads(respuesta.model_dump_json())

    assert serializado["created_at"] == "2026-09-14T18:00:00.123Z"


def test_listado_respeta_la_forma_del_contrato(documento):
    listado = PdfListResponse(
        items=[PdfDocumentResponse.from_domain(documento())],
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
