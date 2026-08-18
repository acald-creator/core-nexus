"""Client for the AI triage inference service."""
import httpx


class AIInferenceClient:
    def __init__(self, base_url: str):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(10.0, connect=5.0),
        )

    async def get_triage(self, alert_id: str) -> dict | None:
        """Get AI triage result for an alert. Returns None if not found."""
        try:
            response = await self._client.get(f"/v1/triage/{alert_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise
        except httpx.HTTPStatusError:
            return None

    async def close(self) -> None:
        await self._client.aclose()
