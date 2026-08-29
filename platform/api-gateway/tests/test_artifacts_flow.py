"""Console → Gateway → MinIO artifact flow with mocked MinIO."""
import pytest


CONSOLE_ORIGIN = "http://localhost:5173"


@pytest.mark.asyncio
async def test_list_artifacts_then_presigned_url(client, app, make_token):
    app.state.minio_client.list_objects.return_value = [
        {
            "key": "skills/red-team-allowlist-target-identity.md",
            "name": "red-team-allowlist-target-identity.md",
            "size": 128,
            "lastModified": "2026-08-22T09:00:00+00:00",
        }
    ]
    app.state.minio_client.get_presigned_url.return_value = (
        "http://localhost:9000/nexus-memory/skills/red-team-allowlist-target-identity.md"
        "?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires=900"
    )

    token = make_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Origin": CONSOLE_ORIGIN,
    }

    listed = await client.get("/api/v1/artifacts?category=skills", headers=headers)
    assert listed.status_code == 200
    assert listed.headers.get("access-control-allow-origin") == CONSOLE_ORIGIN
    body = listed.json()
    assert len(body) == 1
    assert body[0]["key"] == "skills/red-team-allowlist-target-identity.md"
    assert body[0]["category"] == "skills"

    download = await client.get(
        "/api/v1/artifacts/skills/red-team-allowlist-target-identity.md/download-url",
        headers=headers,
    )
    assert download.status_code == 200
    assert download.headers.get("access-control-allow-origin") == CONSOLE_ORIGIN
    url = download.json()["url"]
    assert url.startswith("http://localhost:9000/")
    assert "X-Amz-Algorithm" in url
    assert "minio:9000" not in url


def test_presigned_url_rewrites_internal_minio_host():
    from src.clients.minio_client import MinIOClient

    client = MinIOClient(
        endpoint="minio:9000",
        access_key="x",
        secret_key="y",
        secure=False,
        bucket="nexus-memory",
        public_endpoint="localhost:9000",
    )
    client._client = type(
        "Stub",
        (),
        {
            "presigned_get_object": staticmethod(
                lambda *args, **kwargs: "http://minio:9000/nexus-memory/pcaps/a.pcap?X-Amz-Expires=900"
            )
        },
    )()
    url = client.get_presigned_url("pcaps/a.pcap")
    assert url.startswith("http://localhost:9000/")
    assert "minio:9000" not in url


def test_from_settings_r2_uses_account_endpoint():
    from src.clients.minio_client import ObjectStoreClient
    from src.config import GatewaySettings

    settings = GatewaySettings(
        jwt_secret="x",
        wazuh_api_url="https://wazuh:55000",
        minio_access_key="ak",
        minio_secret_key="sk",
        object_store_backend="r2",
        r2_account_id="abc123",
        minio_endpoint="minio:9000",
    )
    client = ObjectStoreClient.from_settings(settings)
    assert client._endpoint == "abc123.r2.cloudflarestorage.com"
    assert client._bucket == "nexus-memory"
