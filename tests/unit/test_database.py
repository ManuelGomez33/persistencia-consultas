from app.core.config import Settings
from app.core.database import crear_cliente_redis


def test_el_cliente_redis_falla_rapido_si_redis_no_responde():
    # Con la configuración por defecto de redis-py, cada consulta con Redis caído
    # esperaba ~4 s antes de seguir contra MongoDB. Igual que persistencia-actualizaciones:
    # timeouts cortos y sin reintentos propios del cliente.
    cliente = crear_cliente_redis(Settings())

    opciones = cliente.connection_pool.connection_kwargs
    assert opciones["socket_connect_timeout"] == 1.0
    assert opciones["socket_timeout"] == 1.0
    assert cliente.get_retry().get_retries() == 0
