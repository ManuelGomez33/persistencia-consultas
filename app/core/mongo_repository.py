from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import PyMongoError

from app.core.exceptions import BaseDeDatosNoDisponible
from app.core.repository import PdfRepository
from app.models.pdf_document import PdfDocument


class MongoPdfRepository(PdfRepository):
    """Lee la colección que escribe persistencia-actualizaciones: el UUID del documento
    va en `_id` (su contrato, A10), que además ya está indexado."""

    def __init__(self, coleccion: AsyncIOMotorCollection) -> None:
        self._coleccion = coleccion

    async def get_by_id(self, documento_id: str) -> PdfDocument | None:
        return await self._buscar_uno({"_id": documento_id})

    async def get_by_checksum(self, checksum: str) -> PdfDocument | None:
        return await self._buscar_uno({"checksum": checksum})

    async def listar(self, limit: int, offset: int) -> list[PdfDocument]:
        with _base_no_disponible_si_falla():
            cursor = self._coleccion.find().sort("created_at", -1).skip(offset).limit(limit)
            return [documento_desde_mongo(datos) async for datos in cursor]

    async def contar(self) -> int:
        with _base_no_disponible_si_falla():
            return await self._coleccion.count_documents({})

    async def _buscar_uno(self, filtro: dict) -> PdfDocument | None:
        with _base_no_disponible_si_falla():
            datos = await self._coleccion.find_one(filtro)
        return documento_desde_mongo(datos) if datos else None


@contextmanager
def _base_no_disponible_si_falla() -> Iterator[None]:
    """Traduce cualquier error del driver al error del contrato (DATABASE_ERROR 503)."""
    try:
        yield
    except PyMongoError as error:
        raise BaseDeDatosNoDisponible("MongoDB no está disponible") from error


def documento_desde_mongo(datos: dict) -> PdfDocument:
    return PdfDocument(
        id=datos["_id"],
        nombre=datos["nombre"],
        checksum=datos["checksum"],
        texto=datos["texto"],
        tamano_bytes=datos["tamano_bytes"],
        paginas=datos.get("paginas"),
        created_at=_en_utc(datos["created_at"]),
        updated_at=_en_utc(datos["updated_at"]),
    )


def _en_utc(momento: datetime) -> datetime:
    return momento.replace(tzinfo=UTC) if momento.tzinfo is None else momento
