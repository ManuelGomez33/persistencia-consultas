from app.core.cache import Cache


class InMemoryCache(Cache):
    """Caché en memoria para los tests. No simula el vencimiento por TTL: expirar
    entradas es responsabilidad de Redis y no hay reglas propias que verificar."""

    def __init__(self) -> None:
        self._entradas: dict[str, str] = {}

    async def get(self, clave: str) -> str | None:
        return self._entradas.get(clave)

    async def set(self, clave: str, valor: str, ttl_seconds: int) -> None:
        self._entradas[clave] = valor
