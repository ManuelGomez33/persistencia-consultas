from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PdfDocument:
    id: str
    nombre: str
    checksum: str
    texto: str
    tamano_bytes: int
    created_at: datetime
    updated_at: datetime
    paginas: int | None = None
