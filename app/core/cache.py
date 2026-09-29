from abc import ABC, abstractmethod


class Cache(ABC):
    @abstractmethod
    async def get(self, clave: str) -> str | None: ...

    @abstractmethod
    async def set(self, clave: str, valor: str, ttl_seconds: int) -> None: ...
