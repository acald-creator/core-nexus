"""Client for athena-agents service."""
from typing import AsyncIterator
import httpx


class AthenaClient:
    def __init__(self, base_url: str):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(10.0, connect=5.0),
        )

    async def get_sessions(self) -> list[dict]:
        """List active/recent agent sessions."""
        response = await self._client.get("/sessions")
        response.raise_for_status()
        return response.json()

    async def get_event_stream(self) -> AsyncIterator[dict]:
        """Stream OPAR events from athena-agents."""
        import json
        async with self._client.stream("GET", "/events") as response:
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data:
                        yield json.loads(data)

    async def get_approvals(self, status: str | None = "pending") -> list[dict]:
        """Get approval actions, optionally filtered by status."""
        params = {}
        if status:
            params["status"] = status
        response = await self._client.get("/approvals", params=params)
        response.raise_for_status()
        return response.json()

    async def submit_decision(self, approval_id: str, decision: str) -> dict:
        """Submit approve/reject decision."""
        response = await self._client.post(
            f"/approvals/{approval_id}/decision",
            json={"decision": decision},
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
