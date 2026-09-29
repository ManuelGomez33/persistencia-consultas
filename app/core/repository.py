from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from app.models.pdf_document import PdfDocument

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    @abstractmethod
    async def get_by_id(self, documento_id: str) -> T | None: ...

    @abstractmethod
    async def listar(self, limit: int, offset: int) -> list[T]: ...

    @abstractmethod
    async def contar(self) -> int: ...


class PdfRepository(Repository[PdfDocument]):
    @abstractmethod
    async def get_by_checksum(self, checksum: str) -> PdfDocument | None: ...
