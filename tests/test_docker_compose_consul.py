from pathlib import Path


def test_compose_conecta_el_servicio_a_consul_sin_exponer_el_token():
    compose = (Path(__file__).parents[1] / "docker-compose.yml").read_text(encoding="utf-8")

    assert 'CONSUL_ENABLED: "true"' in compose
    assert "CONSUL_HTTP_ADDR: http://consul:8500" in compose
    assert "CONSUL_HTTP_TOKEN_FILE: /run/secrets/consul_microservices_token" in compose
    assert "- redutn" in compose
    assert "consul_microservices_token:" in compose
    assert "../dockers/consul/generated/microservices.token" in compose
