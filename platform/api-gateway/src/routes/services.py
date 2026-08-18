"""Service registry route."""
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.config import get_settings

router = APIRouter()

_registry_cache: list[dict] | None = None


def _load_registry() -> list[dict]:
    global _registry_cache
    if _registry_cache is not None:
        return _registry_cache

    settings = get_settings()
    path = Path(settings.service_registry_path)
    if not path.exists():
        raise HTTPException(status_code=500, detail="Service registry configuration not found")

    try:
        data = json.loads(path.read_text())
        _registry_cache = data.get("services", [])
        return _registry_cache
    except (json.JSONDecodeError, KeyError) as e:
        raise HTTPException(status_code=500, detail=f"Malformed service registry: {e}")


@router.get("/services")
async def list_services():
    """Return all configured platform service entries."""
    return _load_registry()
