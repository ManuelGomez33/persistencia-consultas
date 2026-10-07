from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import NoBackoff

from app.core.config import Settings


def crear_cliente_mongo(settings: Settings) -> AsyncIOMotorClient:
    # tz_aware hace que las fechas vuelvan con zona horaria y se serialicen como UTC.
    return AsyncIOMotorClient(settings.mongo_uri, tz_aware=True)


def obtener_coleccion(cliente: AsyncIOMotorClient, settings: Settings) -> AsyncIOMotorCollection:
    return cliente[settings.mongo_database][settings.mongo_collection]


# Redis es solo caché: si no responde, la consulta sigue contra MongoDB. Con la
# configuración por defecto de redis-py eso costaba ~4 s por consulta; con timeouts
# cortos y sin reintentos se degrada enseguida. Mismo criterio que
# persistencia-actualizaciones. Fijo en el código: el contrato no define una variable.
REDIS_TIMEOUT_SEGUNDOS = 1.0


def crear_cliente_redis(settings: Settings) -> Redis:
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=REDIS_TIMEOUT_SEGUNDOS,
        socket_timeout=REDIS_TIMEOUT_SEGUNDOS,
        retry=Retry(NoBackoff(), 0),
    )
