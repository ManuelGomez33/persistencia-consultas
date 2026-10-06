from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.controllers import health_controller, pdf_controller
from app.core.composition import obtener_settings
from app.core.exceptions import DomainError
from app.schemas.error import ErrorDetail, ErrorResponse

CABECERA_CORRELATION_ID = "X-Correlation-ID"


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Construir Settings acá hace que una configuración incompleta falle al arrancar
    # y no en la primera consulta.
    obtener_settings()
    yield


app = FastAPI(
    title="persistencia-consultas",
    description="Consulta de documentos PDF con MongoDB y caché Redis.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health_controller.router)
app.include_router(pdf_controller.router)


@app.middleware("http")
async def propagar_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get(CABECERA_CORRELATION_ID) or str(uuid4())
    request.state.correlation_id = correlation_id
    respuesta = await call_next(request)
    respuesta.headers[CABECERA_CORRELATION_ID] = correlation_id
    return respuesta


@app.exception_handler(DomainError)
async def manejar_error_de_dominio(request: Request, error: DomainError) -> JSONResponse:
    cuerpo = ErrorResponse.desde_error(error, request.state.correlation_id)
    return JSONResponse(status_code=error.status_code, content=cuerpo.model_dump())


@app.exception_handler(RequestValidationError)
async def manejar_request_invalido(request: Request, error: RequestValidationError) -> JSONResponse:
    cuerpo = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Los parámetros de la consulta no son válidos",
            details={"errors": jsonable_encoder(error.errors())},
            correlation_id=request.state.correlation_id,
        )
    )
    return JSONResponse(status_code=400, content=cuerpo.model_dump())


@app.exception_handler(Exception)
async def manejar_error_inesperado(request: Request, error: Exception) -> JSONResponse:
    # El detalle del fallo no viaja al cliente: puede exponer la topologia interna.
    # El correlation_id es lo que permite ubicarlo en los logs.
    cuerpo = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_ERROR",
            message="Error interno del servicio",
            details={},
            correlation_id=request.state.correlation_id,
        )
    )
    return JSONResponse(status_code=500, content=cuerpo.model_dump())
