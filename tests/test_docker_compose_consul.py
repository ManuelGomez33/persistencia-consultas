from pathlib import Path


def test_compose_conecta_el_servicio_a_consul_sin_exponer_el_token():
    compose = (Path(__file__).parents[1] / "docker-compose.yml").read_text(encoding="utf-8")

    assert 'CONSUL_ENABLED: "true"' in compose
    assert "CONSUL_HTTP_ADDR: http://consul:8500" in compose
    assert "CONSUL_HTTP_TOKEN_FILE: /run/secrets/consul_microservices_token" in compose
    assert "- redutn" in compose
    assert "consul_microservices_token:" in compose
    assert "../dockers/consul/generated/microservices.token" in compose


def test_compose_usa_la_mongodb_y_el_redis_compartidos_de_la_infraestructura():
    # Una sola MongoDB y un solo Redis para las dos persistencias (../dockers): consultas
    # lee lo que escribe actualizaciones. Interno: sin puertos publicados en el host.
    compose = (Path(__file__).parents[1] / "docker-compose.yml").read_text(encoding="utf-8")

    assert "MONGO_URI: mongodb://mongodb:27017" in compose
    assert "REDIS_URL: redis://redis:6379/0" in compose
    assert "image: mongo" not in compose
    assert "image: redis" not in compose
    assert "ports:" not in compose
    assert "CONSUL_SERVICE_ADDRESS: persistencia-consultas" in compose
