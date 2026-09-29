from dataclasses import asdict
from datetime import datetime

from pydantic import BaseModel

from app.models.pdf_document import PdfDocument


class PdfDocumentResponse(BaseModel):
    id: str
    nombre: str
    checksum: str
    texto: str
    tamano_bytes: int
    paginas: int | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, documento: PdfDocument) -> "PdfDocumentResponse":
        return cls(**asdict(documento))


class PdfListResponse(BaseModel):
    items: list[PdfDocumentResponse]
    total: int
    limit: int
    offset: int
