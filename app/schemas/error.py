from pydantic import BaseModel

from app.core.exceptions import DomainError


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict
    correlation_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail

    @classmethod
    def desde_error(cls, error: DomainError, correlation_id: str) -> "ErrorResponse":
        return cls(
            error=ErrorDetail(
                code=error.code,
                message=error.message,
                details=error.details,
                correlation_id=correlation_id,
            )
        )
