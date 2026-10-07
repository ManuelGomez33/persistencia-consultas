from app.services.salud_service import SaludService
from tests.dobles import DependenciaFija


async def test_con_todo_disponible_esta_ok():
    estado = await SaludService(DependenciaFija(True), DependenciaFija(True)).estado()

    assert estado.ok
    assert estado.dependencias == {"mongodb": "ok", "redis": "ok"}


async def test_redis_caido_no_lo_deja_fuera_de_servicio():
    # Fail-open (contrato 1.1.0): sin caché las consultas siguen contra MongoDB.
    estado = await SaludService(DependenciaFija(True), DependenciaFija(False)).estado()

    assert estado.ok
    assert estado.dependencias == {"mongodb": "ok", "redis": "caido"}


async def test_mongodb_caido_lo_deja_fuera_de_servicio():
    estado = await SaludService(DependenciaFija(False), DependenciaFija(True)).estado()

    assert not estado.ok
    assert estado.dependencias == {"mongodb": "caido", "redis": "ok"}
