from fastapi import APIRouter

from src.core.config import settings


router = APIRouter()


@router.get("/")
def health() -> dict[str, str]:
    return {"status": "ok", "project": "{{project_name}}", "env": settings.env}
