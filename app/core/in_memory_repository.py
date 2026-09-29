from app.core.repository import PdfRepository
from app.models.pdf_document import PdfDocument


class InMemoryPdfRepository(PdfRepository):
    def __init__(self, documentos: list[PdfDocument]) -> None:
        self._documentos = sorted(documentos, key=lambda d: d.created_at, reverse=True)

    async def get_by_id(self, documento_id: str) -> PdfDocument | None:
        return next((d for d in self._documentos if d.id == documento_id), None)

    async def get_by_checksum(self, checksum: str) -> PdfDocument | None:
        return next((d for d in self._documentos if d.checksum == checksum), None)

    async def listar(self, limit: int, offset: int) -> list[PdfDocument]:
        return self._documentos[offset : offset + limit]

    async def contar(self) -> int:
        return len(self._documentos)
