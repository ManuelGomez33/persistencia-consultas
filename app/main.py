import logging
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.controllers import health_controller, pdf_controller
from app.core.composition import cerrar_conexiones, obtener_settings
from app.core.exceptions import DomainError
from app.core.logs import configurar_logs, correlation_id_actual
from app.schemas.error import ErrorDetail, ErrorResponse

CABECERA_CORRELATION_ID = "X-Correlation-ID"

configurar_logs()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Construir Settings acá hace que una configuración incompleta falle al arrancar
    # y no en la primera consulta.
    obtener_settings()
    yield
    await cerrar_conexiones()


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
    token = correlation_id_actual.set(correlation_id)
    inicio = time.perf_counter()
    try:
        respuesta = await call_next(request)
        respuesta.headers[CABECERA_CORRELATION_ID] = correlation_id
        logger.info(
            "method=%s path=%s status=%s duracion_ms=%.1f",
            request.method,
            request.url.path,
            respuesta.status_code,
            (time.perf_counter() - inicio) * 1000,
        )
        return respuesta
    finally:
        correlation_id_actual.reset(token)


def responder_error(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict,
    exc_info: BaseException | None = None,
) -> JSONResponse:
    """Formato común de errores del contrato. La cabecera y el contexto del log se fijan
    acá porque el handler de Exception corre fuera del middleware de correlation ID."""
    correlation_id = request.state.correlation_id
    token = correlation_id_actual.set(correlation_id)
    logger.log(
        logging.ERROR if status_code >= 500 else logging.WARNING,
        "code=%s status=%s message=%s",
        code,
        status_code,
        message,
        exc_info=exc_info,
    )
    correlation_id_actual.reset(token)
    cuerpo = ErrorResponse(
        error=ErrorDetail(
            code=code, message=message, details=details, correlation_id=correlation_id
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=cuerpo.model_dump(),
        headers={CABECERA_CORRELATION_ID: correlation_id},
    )


@app.exception_handler(DomainError)
async def manejar_error_de_dominio(request: Request, error: DomainError) -> JSONResponse:
    return responder_error(request, error.status_code, error.code, error.message, error.details)


@app.exception_handler(StarletteHTTPException)
async def manejar_error_http(request: Request, error: StarletteHTTPException) -> JSONResponse:
    # Una ruta inexistente es un recurso no encontrado para el contrato. El resto de los
    # errores HTTP del framework (por ejemplo, 405) mantienen la respuesta por defecto.
    if error.status_code != 404:
        return await http_exception_handler(request, error)
    return responder_error(
        request, 404, "RESOURCE_NOT_FOUND", f"No existe la ruta {request.url.path}", {}
    )


@app.exception_handler(RequestValidationError)
async def manejar_request_invalido(request: Request, error: RequestValidationError) -> JSONResponse:
    return responder_error(
        request,
        400,
        "VALIDATION_ERROR",
        "Los parámetros de la consulta no son válidos",
        {"errors": jsonable_encoder(error.errors())},
    )


@app.exception_handler(Exception)
async def manejar_error_inesperado(request: Request, error: Exception) -> JSONResponse:
    # El detalle del fallo no viaja al cliente: puede exponer la topologia interna.
    # El correlation_id es lo que permite ubicarlo en los logs.
    return responder_error(
        request, 500, "INTERNAL_ERROR", "Error interno del servicio", {}, exc_info=error
    )
