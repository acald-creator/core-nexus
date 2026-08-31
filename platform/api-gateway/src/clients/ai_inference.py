"""Client for the AI triage inference service."""
from __future__ import annotations

from typing import Any

import httpx


def to_console_triage(data: dict[str, Any]) -> dict[str, Any]:
    """Map ai-inference payload to Console/TriageResponse camelCase fields."""
    score = data.get("confidenceScore", data.get("score", 0.0))
    try:
        score_f = float(score)
    except (TypeError, ValueError):
        score_f = 0.0
    return {
        "confidenceScore": score_f,
        "recommendedAction": str(
            data.get("recommendedAction") or data.get("recommended_action") or ""
        ),
        "reasoningExcerpt": str(
            data.get("reasoningExcerpt") or data.get("reason") or ""
        ),
    }


class AIInferenceClient:
    def __init__(self, base_url: str):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(10.0, connect=5.0),
        )

    async def get_triage(self, alert_id: str) -> dict | None:
        """Get persisted AI triage for an alert id. Returns Console-shaped dict or None."""
        try:
            response = await self._client.get(f"/v1/triage/{alert_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return to_console_triage(response.json())
        except httpx.TimeoutException:
            raise
        except httpx.HTTPStatusError:
            return None

    async def create_triage(self, event: dict[str, Any]) -> dict[str, Any]:
        """POST an event for scoring; returns Console-shaped triage dict."""
        response = await self._client.post("/v1/triage", json=event)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            if not data:
                raise ValueError("empty triage batch response")
            data = data[0]
        if not isinstance(data, dict):
            raise ValueError("invalid triage response")
        return to_console_triage(data)

    async def close(self) -> None:
        await self._client.aclose()
