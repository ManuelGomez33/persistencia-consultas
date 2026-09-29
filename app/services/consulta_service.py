from app.core.exceptions import ParametrosInvalidos, RecursoNoEncontrado
from app.core.repository import PdfRepository
from app.models.pdf_document import PdfDocument

LIMITE_MAXIMO = 100


class ConsultaPdfService:
    def __init__(self, repository: PdfRepository) -> None:
        self._repository = repository

    async def obtener_por_id(self, documento_id: str) -> PdfDocument:
        documento = await self._repository.get_by_id(documento_id)
        return self._asegurar_encontrado(documento, f"id {documento_id}")

    async def obtener_por_checksum(self, checksum: str) -> PdfDocument:
        documento = await self._repository.get_by_checksum(checksum)
        return self._asegurar_encontrado(documento, f"checksum {checksum}")

    async def listar(self, limit: int, offset: int) -> tuple[list[PdfDocument], int]:
        self._validar_paginacion(limit, offset)
        documentos = await self._repository.listar(limit=limit, offset=offset)
        total = await self._repository.contar()
        return documentos, total

    @staticmethod
    def _asegurar_encontrado(documento: PdfDocument | None, buscado_por: str) -> PdfDocument:
        if documento is None:
            raise RecursoNoEncontrado(f"No existe un documento con {buscado_por}")
        return documento

    @staticmethod
    def _validar_paginacion(limit: int, offset: int) -> None:
        if not 1 <= limit <= LIMITE_MAXIMO:
            raise ParametrosInvalidos(
                f"limit debe estar entre 1 y {LIMITE_MAXIMO}", {"limit": limit}
            )
        if offset < 0:
            raise ParametrosInvalidos("offset no puede ser negativo", {"offset": offset})
