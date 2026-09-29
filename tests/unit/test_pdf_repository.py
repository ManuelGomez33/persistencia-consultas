from datetime import UTC, datetime

import pytest

from app.core.cached_repository import CachedPdfRepository
from app.core.in_memory_cache import InMemoryCache
from app.core.in_memory_repository import InMemoryPdfRepository

TTL = 300


@pytest.fixture(params=["en-memoria", "con-cache"])
def repositorio_con(request):
    """Construye cada implementación de PdfRepository. La misma suite corre contra las
    dos: si un adaptador endureciera el contrato del puerto, estos tests lo detectan."""

    def construir(documentos):
        en_memoria = InMemoryPdfRepository(documentos)
        if request.param == "con-cache":
            return CachedPdfRepository(en_memoria, InMemoryCache(), TTL)
        return en_memoria

    return construir


@pytest.fixture
def tres_documentos(documento):
    primero = documento(
        id="11111111-1111-1111-1111-111111111111",
        checksum="checksum-1",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    segundo = documento(
        id="22222222-2222-2222-2222-222222222222",
        checksum="checksum-2",
        created_at=datetime(2026, 2, 1, tzinfo=UTC),
    )
    tercero = documento(
        id="33333333-3333-3333-3333-333333333333",
        checksum="checksum-3",
        created_at=datetime(2026, 3, 1, tzinfo=UTC),
    )
    return primero, segundo, tercero


async def test_get_by_id_devuelve_el_documento(repositorio_con, documento):
    esperado = documento()
    repositorio = repositorio_con([esperado])

    assert await repositorio.get_by_id(esperado.id) == esperado


async def test_get_by_id_devuelve_none_cuando_no_existe(repositorio_con, documento):
    repositorio = repositorio_con([documento()])

    assert await repositorio.get_by_id("id-inexistente") is None


async def test_get_by_checksum_devuelve_el_documento(repositorio_con, documento):
    esperado = documento()
    repositorio = repositorio_con([esperado])

    assert await repositorio.get_by_checksum(esperado.checksum) == esperado


async def test_get_by_checksum_devuelve_none_cuando_no_existe(repositorio_con, documento):
    repositorio = repositorio_con([documento()])

    assert await repositorio.get_by_checksum("checksum-inexistente") is None


async def test_listar_devuelve_los_mas_recientes_primero(repositorio_con, tres_documentos):
    primero, segundo, tercero = tres_documentos
    repositorio = repositorio_con([primero, segundo, tercero])

    assert await repositorio.listar(limit=20, offset=0) == [tercero, segundo, primero]


async def test_listar_respeta_limit_y_offset(repositorio_con, tres_documentos):
    primero, segundo, tercero = tres_documentos
    repositorio = repositorio_con([primero, segundo, tercero])

    assert await repositorio.listar(limit=1, offset=1) == [segundo]


async def test_listar_devuelve_vacio_cuando_el_offset_supera_el_total(
    repositorio_con, tres_documentos
):
    repositorio = repositorio_con(list(tres_documentos))

    assert await repositorio.listar(limit=20, offset=99) == []


async def test_contar_devuelve_la_cantidad_total(repositorio_con, tres_documentos):
    repositorio = repositorio_con(list(tres_documentos))

    assert await repositorio.contar() == 3


async def test_contar_devuelve_cero_en_un_repositorio_vacio(repositorio_con):
    repositorio = repositorio_con([])

    assert await repositorio.contar() == 0
