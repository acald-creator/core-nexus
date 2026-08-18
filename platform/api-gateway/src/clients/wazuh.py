"""Async client for Wazuh Manager REST API."""
import httpx


class WazuhClient:
    def __init__(self, base_url: str, user: str, password: str):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            verify=False,
            timeout=httpx.Timeout(10.0, connect=5.0),
        )
        self._user = user
        self._password = password
        self._token: str | None = None

    async def authenticate(self) -> None:
        """Authenticate with Wazuh API and store token."""
        response = await self._client.post(
            "/security/user/authenticate",
            auth=(self._user, self._password),
        )
        response.raise_for_status()
        data = response.json()
        self._token = data.get("data", {}).get("token")

    async def get_alerts(
        self,
        severity: str | None = None,
        source: str | None = None,
        from_ts: str | None = None,
        to_ts: str | None = None,
        limit: int = 100,
    ) -> dict:
        """Fetch alerts from Wazuh API with optional filtering."""
        if not self._token:
            await self.authenticate()

        params: dict = {"limit": limit}
        if from_ts:
            params["older_than"] = from_ts
        # Wazuh API filtering is complex — simplified here
        headers = {"Authorization": f"Bearer {self._token}"}
        response = await self._client.get("/alerts", headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
