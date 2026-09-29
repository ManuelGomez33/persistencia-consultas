import json
from collections.abc import Awaitable, Callable
from dataclasses import asdict
from datetime import datetime

from app.core.cache import Cache
from app.core.repository import PdfRepository
from app.models.pdf_document import PdfDocument


class CachedPdfRepository(PdfRepository):
    """Aplica cache-aside sobre otro repositorio: consulta la caché y, ante un MISS,
    delega en el repositorio y guarda el resultado."""

    def __init__(self, repository: PdfRepository, cache: Cache, ttl_seconds: int) -> None:
        self._repository = repository
        self._cache = cache
        self._ttl_seconds = ttl_seconds

    async def get_by_id(self, documento_id: str) -> PdfDocument | None:
        return await self._documento_cacheado(
            f"pdf:id:{documento_id}",
            lambda: self._repository.get_by_id(documento_id),
        )

    async def get_by_checksum(self, checksum: str) -> PdfDocument | None:
        return await self._documento_cacheado(
            f"pdf:checksum:{checksum}",
            lambda: self._repository.get_by_checksum(checksum),
        )

    async def listar(self, limit: int, offset: int) -> list[PdfDocument]:
        clave = f"pdf:list:{limit}:{offset}"
        cacheado = await self._cache.get(clave)
        if cacheado is not None:
            return [_desde_dict(datos) for datos in json.loads(cacheado)]

        documentos = await self._repository.listar(limit=limit, offset=offset)
        await self._guardar(clave, [_a_dict(documento) for documento in documentos])
        return documentos

    async def contar(self) -> int:
        cacheado = await self._cache.get("pdf:total")
        if cacheado is not None:
            return json.loads(cacheado)

        total = await self._repository.contar()
        await self._guardar("pdf:total", total)
        return total

    async def _documento_cacheado(
        self,
        clave: str,
        consultar: Callable[[], Awaitable[PdfDocument | None]],
    ) -> PdfDocument | None:
        cacheado = await self._cache.get(clave)
        if cacheado is not None:
            return _desde_dict(json.loads(cacheado))

        documento = await consultar()
        # Un documento ausente no se cachea: podría crearse dentro del TTL y quedaría
        # invisible hasta que la entrada venza.
        if documento is not None:
            await self._guardar(clave, _a_dict(documento))
        return documento

    async def _guardar(self, clave: str, valor: object) -> None:
        await self._cache.set(clave, json.dumps(valor), self._ttl_seconds)


def _a_dict(documento: PdfDocument) -> dict:
    return {
        **asdict(documento),
        "created_at": documento.created_at.isoformat(),
        "updated_at": documento.updated_at.isoformat(),
    }


def _desde_dict(datos: dict) -> PdfDocument:
    return PdfDocument(
        **{
            **datos,
            "created_at": datetime.fromisoformat(datos["created_at"]),
            "updated_at": datetime.fromisoformat(datos["updated_at"]),
        }
    )
