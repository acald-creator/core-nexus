"""Factory review webhook and merged approvals."""
import pytest
from httpx import AsyncClient

from src.services import factory_approvals


@pytest.fixture(autouse=True)
def clear_factory_store():
    factory_approvals.reset_store()
    yield
    factory_approvals.reset_store()


@pytest.fixture
def webhook_token(monkeypatch):
    monkeypatch.setenv("NEXUS_GW_FACTORY_WEBHOOK_TOKEN", "factory-test-token")
    from src.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_factory_webhook_creates_approval(client: AsyncClient, webhook_token):
    response = await client.post(
        "/api/v1/factory/reviews",
        headers={"X-Factory-Webhook-Token": "factory-test-token"},
        json={
            "repo": "nebucloud/core-nexus",
            "head_sha": "abc123def456",
            "risk_max": "critical",
            "summary": "2 finding(s); max risk=critical",
            "pr_number": 42,
            "check_run_url": "https://github.com/o/r/runs/1",
            "findings": [{"id": "h-1", "title": "secret in diff", "risk": "critical"}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["accepted"] is True
    assert data["approval"]["id"].startswith("factory-")
    assert data["approval"]["source"] == "factory"


@pytest.mark.asyncio
async def test_factory_webhook_rejects_low_risk(client: AsyncClient, webhook_token):
    response = await client.post(
        "/api/v1/factory/reviews",
        headers={"Authorization": "Bearer factory-test-token"},
        json={
            "repo": "nebucloud/core-nexus",
            "head_sha": "abc123def456",
            "risk_max": "low",
            "summary": "clean",
        },
    )
    assert response.status_code == 200
    assert response.json()["accepted"] is False


@pytest.mark.asyncio
async def test_approvals_list_merges_factory(
    client: AsyncClient, app, make_token, webhook_token
):
    await client.post(
        "/api/v1/factory/reviews",
        headers={"X-Factory-Webhook-Token": "factory-test-token"},
        json={
            "repo": "nebucloud/factory-agents",
            "head_sha": "deadbeef",
            "risk_max": "high",
            "summary": "needs review",
        },
    )
    app.state.athena_client.get_approvals.return_value = [
        {
            "id": "athena-1",
            "sessionId": "sess",
            "proposedTool": "nmap",
            "target": "10.0.0.1",
            "argumentsSummary": "scan",
            "submittedAt": "2026-01-01T00:00:00Z",
            "status": "pending",
        }
    ]
    token = make_token()
    response = await client.get(
        "/api/v1/approvals?status=pending",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert "athena-1" in ids
    assert any(i.startswith("factory-") for i in ids)


@pytest.mark.asyncio
async def test_factory_approval_decision(client: AsyncClient, make_token, webhook_token):
    created = await client.post(
        "/api/v1/factory/reviews",
        headers={"X-Factory-Webhook-Token": "factory-test-token"},
        json={
            "repo": "nebucloud/factory-agents",
            "head_sha": "deadbeef",
            "risk_max": "high",
            "summary": "needs review",
        },
    )
    approval_id = created.json()["approval"]["id"]
    token = make_token()
    response = await client.post(
        f"/api/v1/approvals/{approval_id}/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={"decision": "approve"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
