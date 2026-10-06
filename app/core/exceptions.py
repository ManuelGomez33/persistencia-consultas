class DomainError(Exception):
    """Error de dominio con el código y el status del contrato común de errores."""

    code: str
    status_code: int

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class RecursoNoEncontrado(DomainError):
    code = "RESOURCE_NOT_FOUND"
    status_code = 404


class ParametrosInvalidos(DomainError):
    code = "VALIDATION_ERROR"
    status_code = 400


class BaseDeDatosNoDisponible(DomainError):
    code = "DATABASE_ERROR"
    status_code = 503
