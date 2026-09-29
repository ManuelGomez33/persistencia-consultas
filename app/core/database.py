from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from redis.asyncio import Redis

from app.core.config import Settings


def crear_cliente_mongo(settings: Settings) -> AsyncIOMotorClient:
    # tz_aware hace que las fechas vuelvan con zona horaria y se serialicen como UTC.
    return AsyncIOMotorClient(settings.mongo_uri, tz_aware=True)


def obtener_coleccion(cliente: AsyncIOMotorClient, settings: Settings) -> AsyncIOMotorCollection:
    return cliente[settings.mongo_database][settings.mongo_collection]


def crear_cliente_redis(settings: Settings) -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)
