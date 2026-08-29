"""Cloudflare D1 metadata index via the nexus-metadata Worker proxy."""
from __future__ import annotations

from typing import Any

import httpx

from src.config import GatewaySettings


class MetadataIndexClient:
    """Optional artifact/run index. Disabled when proxy URL or API key unset."""

    def __init__(self, base_url: str | None, api_key: str | None):
        self._enabled = bool(base_url and api_key)
        self._base = (base_url or "").rstrip("/")
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    @classmethod
    def from_settings(cls, settings: GatewaySettings) -> MetadataIndexClient:
        return cls(settings.d1_proxy_url, settings.d1_api_key)

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def health(self) -> bool:
        if not self._enabled:
            return False
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self._base}/healthz")
            return resp.status_code == 200

    async def list_artifacts(
        self, category: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        if not self._enabled:
            return []
        params: dict[str, str | int] = {"limit": limit}
        if category:
            params["category"] = category
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self._base}/v1/artifacts",
                headers=self._headers,
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else []

    async def upsert_artifact(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._enabled:
            raise RuntimeError("metadata index is not configured")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._base}/v1/artifacts",
                headers=self._headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def create_run(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._enabled:
            raise RuntimeError("metadata index is not configured")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._base}/v1/runs",
                headers=self._headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_run(self, run_id: str) -> dict[str, Any]:
        if not self._enabled:
            raise RuntimeError("metadata index is not configured")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self._base}/v1/runs/{run_id}",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()
