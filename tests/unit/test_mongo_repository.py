from datetime import datetime, timezone

from app.core.mongo_repository import documento_desde_mongo

CREADO = datetime(2026, 9, 14, 18, 0, tzinfo=timezone.utc)


def datos_de_mongo(**campos) -> dict:
    valores = {
        "_id": "identificador-interno-de-mongo",
        "id": "8f6f7c3e-12d5-4f57-9c6c-123456789abc",
        "nombre": "contrato.pdf",
        "checksum": "a7f5f35426b927411fc9231b56382173",
        "texto": "Contenido extraído del PDF",
        "tamano_bytes": 245760,
        "paginas": 3,
        "created_at": CREADO,
        "updated_at": CREADO,
    }
    return {**valores, **campos}


def test_mapea_los_campos_del_contrato():
    documento = documento_desde_mongo(datos_de_mongo())

    assert documento.id == "8f6f7c3e-12d5-4f57-9c6c-123456789abc"
    assert documento.nombre == "contrato.pdf"
    assert documento.checksum == "a7f5f35426b927411fc9231b56382173"
    assert documento.texto == "Contenido extraído del PDF"
    assert documento.tamano_bytes == 245760
    assert documento.paginas == 3
    assert documento.created_at == CREADO
    assert documento.updated_at == CREADO


def test_descarta_el_identificador_interno_de_mongo():
    documento = documento_desde_mongo(datos_de_mongo())

    assert "identificador-interno-de-mongo" not in vars(documento).values()


def test_admite_un_documento_sin_paginas():
    datos = datos_de_mongo()
    del datos["paginas"]

    assert documento_desde_mongo(datos).paginas is None


def test_normaliza_fechas_sin_zona_horaria_a_utc():
    naive = datetime(2026, 9, 14, 18, 0)

    documento = documento_desde_mongo(datos_de_mongo(created_at=naive, updated_at=naive))

    assert documento.created_at == CREADO
    assert documento.updated_at == CREADO
