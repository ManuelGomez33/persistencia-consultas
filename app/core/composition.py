from functools import lru_cache

from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis

from app.core.cached_repository import CachedPdfRepository
from app.core.config import Settings
from app.core.database import crear_cliente_mongo, crear_cliente_redis, obtener_coleccion
from app.core.mongo_repository import MongoPdfRepository
from app.core.redis_cache import RedisCache
from app.services.consulta_service import ConsultaPdfService


@lru_cache
def obtener_settings() -> Settings:
    return Settings()


@lru_cache
def obtener_cliente_mongo() -> AsyncIOMotorClient:
    return crear_cliente_mongo(obtener_settings())


@lru_cache
def obtener_cliente_redis() -> Redis:
    return crear_cliente_redis(obtener_settings())


@lru_cache
def obtener_servicio() -> ConsultaPdfService:
    """Único lugar donde se eligen las implementaciones concretas. Los tests la
    sustituyen con app.dependency_overrides."""
    settings = obtener_settings()
    coleccion = obtener_coleccion(obtener_cliente_mongo(), settings)
    repositorio = CachedPdfRepository(
        MongoPdfRepository(coleccion),
        RedisCache(obtener_cliente_redis()),
        settings.redis_ttl_seconds,
    )
    return ConsultaPdfService(repositorio)


async def cerrar_conexiones() -> None:
    """Cierra los clientes que se hayan abierto. Los tests sustituyen el servicio, así
    que en la suite no se abre ninguno."""
    if obtener_cliente_mongo.cache_info().currsize:
        obtener_cliente_mongo().close()
    if obtener_cliente_redis.cache_info().currsize:
        await obtener_cliente_redis().aclose()
