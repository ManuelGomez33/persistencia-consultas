from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.core.composition import obtener_servicio_salud
from app.schemas.health import HealthResponse
from app.services.salud_service import SaludService

router = APIRouter(tags=["health"])

ServicioDeSalud = Annotated[SaludService, Depends(obtener_servicio_salud)]


@router.get(
    "/health",
    responses={503: {"model": HealthResponse, "description": "MongoDB no responde."}},
)
async def health(servicio: ServicioDeSalud, response: Response) -> HealthResponse:
    estado = await servicio.estado()
    if not estado.ok:
        response.status_code = 503
    return HealthResponse(status="ok" if estado.ok else "error", dependencias=estado.dependencias)
