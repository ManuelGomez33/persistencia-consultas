from fastapi import APIRouter, Depends

from app.core.composition import obtener_servicio
from app.schemas.pdf import PdfDocumentResponse, PdfListResponse
from app.services.consulta_service import ConsultaPdfService

router = APIRouter(prefix="/pdf", tags=["pdf"])


@router.get("")
async def listar(
    limit: int = 20,
    offset: int = 0,
    servicio: ConsultaPdfService = Depends(obtener_servicio),
) -> PdfListResponse:
    documentos, total = await servicio.listar(limit=limit, offset=offset)
    return PdfListResponse(
        items=[PdfDocumentResponse.from_domain(documento) for documento in documentos],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/checksum/{checksum}")
async def buscar_por_checksum(
    checksum: str,
    servicio: ConsultaPdfService = Depends(obtener_servicio),
) -> PdfDocumentResponse:
    return PdfDocumentResponse.from_domain(await servicio.obtener_por_checksum(checksum))


@router.get("/{documento_id}")
async def buscar_por_id(
    documento_id: str,
    servicio: ConsultaPdfService = Depends(obtener_servicio),
) -> PdfDocumentResponse:
    return PdfDocumentResponse.from_domain(await servicio.obtener_por_id(documento_id))
