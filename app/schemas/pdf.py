from dataclasses import asdict
from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, PlainSerializer

from app.models.pdf_document import PdfDocument


def _iso_utc_con_milisegundos(fecha: datetime) -> str:
    """ISO-8601 en UTC con sufijo Z y siempre 3 decimales, igual que
    persistencia-actualizaciones (A15): MongoDB guarda milisegundos."""
    return fecha.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


FechaUtc = Annotated[
    datetime,
    PlainSerializer(_iso_utc_con_milisegundos, return_type=str, when_used="json"),
]


class PdfDocumentResponse(BaseModel):
    id: str
    nombre: str
    checksum: str
    texto: str
    tamano_bytes: int
    paginas: int | None
    created_at: FechaUtc
    updated_at: FechaUtc

    @classmethod
    def from_domain(cls, documento: PdfDocument) -> "PdfDocumentResponse":
        return cls(**asdict(documento))


class PdfListResponse(BaseModel):
    items: list[PdfDocumentResponse]
    total: int
    limit: int
    offset: int
