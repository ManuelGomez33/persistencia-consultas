import hashlib
import logging

import pytest

from app.core.cache import Cache
from app.core.cached_repository import CachedPdfRepository
from app.core.exceptions import CacheNoDisponible
from app.core.in_memory_cache import InMemoryCache
from app.core.in_memory_repository import InMemoryPdfRepository

TTL = 300


@pytest.fixture
def cache():
    return InMemoryCache()


def con_documentos(documentos, cache):
    return CachedPdfRepository(InMemoryPdfRepository(documentos), cache, TTL)


async def test_miss_consulta_el_repositorio_y_guarda_el_resultado(documento, cache):
    esperado = documento()
    repositorio = con_documentos([esperado], cache)

    assert await repositorio.get_by_id(esperado.id) == esperado
    assert await cache.get(f"pdf:id:{esperado.id}") is not None


async def test_hit_responde_sin_consultar_el_repositorio(documento, cache):
    esperado = documento()
    await con_documentos([esperado], cache).get_by_id(esperado.id)

    sin_documentos = con_documentos([], cache)

    assert await sin_documentos.get_by_id(esperado.id) == esperado


async def test_el_documento_cacheado_conserva_fechas_y_campos_opcionales(documento, cache):
    esperado = documento(paginas=None)
    await con_documentos([esperado], cache).get_by_id(esperado.id)

    recuperado = await con_documentos([], cache).get_by_id(esperado.id)

    assert recuperado.created_at == esperado.created_at
    assert recuperado.updated_at == esperado.updated_at
    assert recuperado.paginas is None


async def test_busqueda_por_checksum_usa_su_propia_clave(documento, cache):
    esperado = documento()
    await con_documentos([esperado], cache).get_by_checksum(esperado.checksum)

    assert await cache.get(f"pdf:checksum:{esperado.checksum}") is not None
    assert await con_documentos([], cache).get_by_checksum(esperado.checksum) == esperado


async def test_un_documento_inexistente_no_se_cachea(cache):
    repositorio = con_documentos([], cache)

    assert await repositorio.get_by_id("id-inexistente") is None
    assert await cache.get("pdf:id:id-inexistente") is None


async def test_el_listado_se_sirve_desde_cache(documento, cache):
    esperado = documento()
    await con_documentos([esperado], cache).listar(limit=20, offset=0)

    assert await con_documentos([], cache).listar(limit=20, offset=0) == [esperado]


async def test_listados_con_distinta_paginacion_no_comparten_cache(documento, cache):
    esperado = documento()
    await con_documentos([esperado], cache).listar(limit=20, offset=0)

    assert await con_documentos([], cache).listar(limit=20, offset=1) == []


def clave_de_listado(limit: int, offset: int) -> str:
    """Clave del contrato: pdf:list:{hash-de-parametros}."""
    parametros = f"limit={limit}&offset={offset}"
    return f"pdf:list:{hashlib.sha256(parametros.encode()).hexdigest()}"


async def test_el_listado_usa_la_clave_del_contrato(documento, cache):
    await con_documentos([documento()], cache).listar(limit=20, offset=0)

    assert await cache.get(clave_de_listado(20, 0)) is not None
    assert await cache.get("pdf:list:20:0") is None


async def test_el_total_no_se_cachea(documento, cache):
    # pdf:total no es una clave del contrato: persistencia-actualizaciones no la
    # invalidaría al escribir y el total quedaría viejo hasta que venza el TTL.
    await con_documentos([documento()], cache).contar()

    assert await con_documentos([], cache).contar() == 0
    assert await cache.get("pdf:total") is None


class CacheCaida(Cache):
    """Simula el adaptador de Redis cuando Redis no responde; cuenta las escrituras."""

    def __init__(self) -> None:
        self.escrituras = 0

    async def get(self, clave: str) -> str | None:
        raise CacheNoDisponible("Redis no está disponible")

    async def set(self, clave: str, valor: str, ttl_seconds: int) -> None:
        self.escrituras += 1
        raise CacheNoDisponible("Redis no está disponible")


async def test_sin_redis_el_documento_se_busca_en_el_repositorio(documento):
    esperado = documento()

    assert await con_documentos([esperado], CacheCaida()).get_by_id(esperado.id) == esperado


async def test_sin_redis_el_listado_se_busca_en_el_repositorio(documento):
    esperado = documento()

    assert await con_documentos([esperado], CacheCaida()).listar(limit=20, offset=0) == [esperado]


async def test_sin_redis_se_registra_una_advertencia(documento, caplog):
    await con_documentos([documento()], CacheCaida()).get_by_id(documento().id)

    assert any(r.levelno == logging.WARNING for r in caplog.records)


@pytest.mark.parametrize(
    "consultar",
    [
        pytest.param(lambda repo, doc: repo.get_by_id(doc.id), id="por-id"),
        pytest.param(lambda repo, doc: repo.get_by_checksum(doc.checksum), id="por-checksum"),
        pytest.param(lambda repo, doc: repo.listar(limit=20, offset=0), id="listado"),
    ],
)
async def test_si_la_lectura_de_cache_fallo_no_se_intenta_guardar(documento, consultar):
    # Cada intento contra Redis caído espera el timeout del cliente: si la lectura ya
    # falló, guardar el resultado solo sumaría otra espera.
    cache = CacheCaida()
    esperado = documento()

    await consultar(con_documentos([esperado], cache), esperado)

    assert cache.escrituras == 0
