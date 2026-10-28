import json
from pathlib import Path

import httpx
import pytest

from app.core import consul_registry
from app.core.config import Settings
from app.core.consul_registry import ConsulRegistry


def crear_settings(tmp_path: Path) -> Settings:
    token_file = tmp_path / "microservices.token"
    token_file.write_text("test-token", encoding="utf-8")
    return Settings(
        mongo_uri="mongodb://mongo:27017",
        mongo_database="pdfs",
        mongo_collection="pdfs",
        redis_url="redis://redis:6379/0",
        redis_ttl_seconds=300,
        consul_enabled=True,
        consul_http_addr="http://consul:8500",
        consul_http_token_file=str(token_file),
        consul_service_address="persistencia-consultas",
        consul_service_port=8000,
    )


@pytest.mark.asyncio
async def test_registra_la_instancia_con_health_check_y_datos_traefik(tmp_path):
    requests = []

    async def responder(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200)

    registry = ConsulRegistry(
        settings=crear_settings(tmp_path),
        instance_id="persistencia-consultas-instance-a",
        transport=httpx.MockTransport(responder),
    )

    await registry.register()

    assert len(requests) == 1
    request = requests[0]
    assert request.method == "PUT"
    assert str(request.url) == "http://consul:8500/v1/agent/service/register"
    assert request.headers["X-Consul-Token"] == "test-token"
    assert json.loads(request.content) == {
        "ID": "persistencia-consultas-instance-a",
        "Name": "persistencia-consultas",
        "Address": "persistencia-consultas",
        "Port": 8000,
        "Tags": [
            "traefik.enable=true",
            "traefik.http.routers.persistencia-consultas.entrypoints=https",
            "traefik.http.routers.persistencia-consultas.rule=Host(`persistencia-consultas.localhost`)",
            "traefik.http.routers.persistencia-consultas.tls=true",
            "traefik.http.services.persistencia-consultas.loadbalancer.server.port=8000",
        ],
        "Checks": [
            {
                "Name": "HTTP health check",
                "HTTP": "http://persistencia-consultas:8000/health",
                "Interval": "10s",
                "Timeout": "3s",
                "DeregisterCriticalServiceAfter": "1m",
            }
        ],
    }


@pytest.mark.asyncio
async def test_deregistra_la_instancia(tmp_path):
    requests = []

    async def responder(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200)

    registry = ConsulRegistry(
        settings=crear_settings(tmp_path),
        instance_id="persistencia-consultas-instance-a",
        transport=httpx.MockTransport(responder),
    )

    await registry.deregister()

    assert len(requests) == 1
    request = requests[0]
    assert request.method == "PUT"
    assert str(request.url).endswith(
        "/v1/agent/service/deregister/persistencia-consultas-instance-a"
    )
    assert request.headers["X-Consul-Token"] == "test-token"


@pytest.mark.asyncio
async def test_usa_la_ip_docker_cuando_no_se_configura_la_direccion(tmp_path, monkeypatch):
    requests = []

    async def responder(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200)

    monkeypatch.setattr(consul_registry.socket, "gethostname", lambda: "instance-a")
    monkeypatch.setattr(consul_registry.socket, "gethostbyname", lambda _: "172.20.0.15")
    settings = crear_settings(tmp_path).model_copy(update={"consul_service_address": None})
    registry = ConsulRegistry(
        settings=settings,
        instance_id="persistencia-consultas-instance-a",
        transport=httpx.MockTransport(responder),
    )

    await registry.register()

    payload = json.loads(requests[0].content)
    assert payload["Address"] == "172.20.0.15"
    assert payload["Checks"][0]["HTTP"] == "http://172.20.0.15:8000/health"
