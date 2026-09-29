from redis.asyncio import Redis

from app.core.cache import Cache


class RedisCache(Cache):
    def __init__(self, cliente: Redis) -> None:
        self._cliente = cliente

    async def get(self, clave: str) -> str | None:
        return await self._cliente.get(clave)

    async def set(self, clave: str, valor: str, ttl_seconds: int) -> None:
        await self._cliente.set(clave, valor, ex=ttl_seconds)
