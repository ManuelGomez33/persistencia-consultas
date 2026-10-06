import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.exceptions import CacheNoDisponible
from app.core.redis_cache import RedisCache


class RedisCaido:
    """Doble del cliente de redis.asyncio: cada operación falla como sin conexión."""

    async def get(self, *_args, **_kwargs):
        raise RedisConnectionError("redis no responde")

    async def set(self, *_args, **_kwargs):
        raise RedisConnectionError("redis no responde")


async def test_traduce_la_caida_de_redis_al_leer():
    with pytest.raises(CacheNoDisponible):
        await RedisCache(RedisCaido()).get("pdf:id:1")


async def test_traduce_la_caida_de_redis_al_escribir():
    with pytest.raises(CacheNoDisponible):
        await RedisCache(RedisCaido()).set("pdf:id:1", "{}", 300)
