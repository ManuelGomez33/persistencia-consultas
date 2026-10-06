from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.cache import Cache
from app.core.exceptions import CacheNoDisponible


class RedisCache(Cache):
    def __init__(self, cliente: Redis) -> None:
        self._cliente = cliente

    async def get(self, clave: str) -> str | None:
        try:
            return await self._cliente.get(clave)
        except RedisError as error:
            raise CacheNoDisponible("Redis no está disponible") from error

    async def set(self, clave: str, valor: str, ttl_seconds: int) -> None:
        try:
            await self._cliente.set(clave, valor, ex=ttl_seconds)
        except RedisError as error:
            raise CacheNoDisponible("Redis no está disponible") from error
