from datetime import UTC, datetime

import pytest
from pymongo.errors import ServerSelectionTimeoutError

from app.core.exceptions import BaseDeDatosNoDisponible
from app.core.mongo_repository import MongoPdfRepository, documento_desde_mongo

CREADO = datetime(2026, 9, 14, 18, 0, tzinfo=UTC)


def datos_de_mongo(**campos) -> dict:
    """Documento tal como lo guarda persistencia-actualizaciones (su contrato, A10):
    el UUID va en `_id` y no hay un campo `id`."""
    valores = {
        "_id": "8f6f7c3e-12d5-4f57-9c6c-123456789abc",
        "nombre": "contrato.pdf",
        "checksum": "a7f5f35426b927411fc9231b56382173",
        "texto": "Contenido extraído del PDF",
        "tamano_bytes": 245760,
        "paginas": 3,
        "created_at": CREADO,
        "updated_at": CREADO,
    }
    return {**valores, **campos}


def test_mapea_los_campos_del_contrato():
    documento = documento_desde_mongo(datos_de_mongo())

    assert documento.id == "8f6f7c3e-12d5-4f57-9c6c-123456789abc"
    assert documento.nombre == "contrato.pdf"
    assert documento.checksum == "a7f5f35426b927411fc9231b56382173"
    assert documento.texto == "Contenido extraído del PDF"
    assert documento.tamano_bytes == 245760
    assert documento.paginas == 3
    assert documento.created_at == CREADO
    assert documento.updated_at == CREADO


class ColeccionQueRegistra:
    """Doble de la colección de Motor: guarda el filtro de cada find_one."""

    def __init__(self) -> None:
        self.filtros: list[dict] = []

    async def find_one(self, filtro: dict) -> dict:
        self.filtros.append(filtro)
        return datos_de_mongo()


async def test_busca_por_id_en_el_campo__id():
    coleccion = ColeccionQueRegistra()

    documento = await MongoPdfRepository(coleccion).get_by_id(
        "8f6f7c3e-12d5-4f57-9c6c-123456789abc"
    )

    assert coleccion.filtros == [{"_id": "8f6f7c3e-12d5-4f57-9c6c-123456789abc"}]
    assert documento.id == "8f6f7c3e-12d5-4f57-9c6c-123456789abc"


def test_admite_un_documento_sin_paginas():
    datos = datos_de_mongo()
    del datos["paginas"]

    assert documento_desde_mongo(datos).paginas is None


def test_normaliza_fechas_sin_zona_horaria_a_utc():
    # La fecha sin zona horaria es justamente lo que se está probando: es como las
    # devuelve un cliente de Mongo sin tz_aware.
    naive = datetime(2026, 9, 14, 18, 0)  # noqa: DTZ001

    documento = documento_desde_mongo(datos_de_mongo(created_at=naive, updated_at=naive))

    assert documento.created_at == CREADO
    assert documento.updated_at == CREADO


class ColeccionCaida:
    """Doble de la colección de Motor: cada operación falla como cuando MongoDB no
    responde."""

    def _fallar(self, *_args, **_kwargs):
        raise ServerSelectionTimeoutError("mongodb no responde")

    find_one = count_documents = _fallar

    def find(self, *_args, **_kwargs):
        return self

    def sort(self, *_args, **_kwargs):
        return self

    def skip(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        self._fallar()


@pytest.mark.parametrize(
    "consultar",
    [
        pytest.param(lambda repo: repo.get_by_id("id"), id="get_by_id"),
        pytest.param(lambda repo: repo.get_by_checksum("checksum"), id="get_by_checksum"),
        pytest.param(lambda repo: repo.listar(limit=20, offset=0), id="listar"),
        pytest.param(lambda repo: repo.contar(), id="contar"),
    ],
)
async def test_traduce_la_caida_de_mongo_a_base_de_datos_no_disponible(consultar):
    repositorio = MongoPdfRepository(ColeccionCaida())

    with pytest.raises(BaseDeDatosNoDisponible) as error:
        await consultar(repositorio)

    assert error.value.code == "DATABASE_ERROR"
    assert error.value.status_code == 503
