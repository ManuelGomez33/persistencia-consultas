import pytest

from app.core.exceptions import ParametrosInvalidos, RecursoNoEncontrado
from app.core.in_memory_repository import InMemoryPdfRepository
from app.services.consulta_service import ConsultaPdfService


@pytest.fixture
def servicio(documento):
    repositorio = InMemoryPdfRepository([documento()])
    return ConsultaPdfService(repositorio)


async def test_obtener_por_id_devuelve_el_documento(servicio, documento):
    esperado = documento()

    assert await servicio.obtener_por_id(esperado.id) == esperado


async def test_obtener_por_id_lanza_recurso_no_encontrado(servicio):
    with pytest.raises(RecursoNoEncontrado):
        await servicio.obtener_por_id("id-inexistente")


async def test_obtener_por_checksum_devuelve_el_documento(servicio, documento):
    esperado = documento()

    assert await servicio.obtener_por_checksum(esperado.checksum) == esperado


async def test_obtener_por_checksum_lanza_recurso_no_encontrado(servicio):
    with pytest.raises(RecursoNoEncontrado):
        await servicio.obtener_por_checksum("checksum-inexistente")


async def test_listar_devuelve_los_documentos_y_el_total(servicio, documento):
    documentos, total = await servicio.listar(limit=20, offset=0)

    assert documentos == [documento()]
    assert total == 1


async def test_listar_devuelve_el_total_completo_aunque_la_pagina_este_vacia(servicio):
    documentos, total = await servicio.listar(limit=20, offset=50)

    assert documentos == []
    assert total == 1


async def test_listar_rechaza_un_limit_menor_a_uno(servicio):
    with pytest.raises(ParametrosInvalidos):
        await servicio.listar(limit=0, offset=0)


async def test_listar_rechaza_un_limit_mayor_al_maximo(servicio):
    with pytest.raises(ParametrosInvalidos):
        await servicio.listar(limit=101, offset=0)


async def test_listar_rechaza_un_offset_negativo(servicio):
    with pytest.raises(ParametrosInvalidos):
        await servicio.listar(limit=20, offset=-1)


async def test_el_error_de_no_encontrado_expone_el_codigo_del_contrato(servicio):
    with pytest.raises(RecursoNoEncontrado) as error:
        await servicio.obtener_por_id("id-inexistente")

    assert error.value.code == "RESOURCE_NOT_FOUND"
    assert error.value.status_code == 404


async def test_el_error_de_validacion_expone_el_codigo_del_contrato(servicio):
    with pytest.raises(ParametrosInvalidos) as error:
        await servicio.listar(limit=0, offset=0)

    assert error.value.code == "VALIDATION_ERROR"
    assert error.value.status_code == 400
