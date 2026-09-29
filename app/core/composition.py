from functools import lru_cache

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
def obtener_servicio() -> ConsultaPdfService:
    """Único lugar donde se eligen las implementaciones concretas. Los tests la
    sustituyen con app.dependency_overrides."""
    settings = obtener_settings()
    coleccion = obtener_coleccion(crear_cliente_mongo(settings), settings)
    repositorio = CachedPdfRepository(
        MongoPdfRepository(coleccion),
        RedisCache(crear_cliente_redis(settings)),
        settings.redis_ttl_seconds,
    )
    return ConsultaPdfService(repositorio)
