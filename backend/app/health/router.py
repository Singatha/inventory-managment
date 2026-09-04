from fastapi import APIRouter

from app.health.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Check API liveness")
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="stockflow-api", version="0.1.0")

