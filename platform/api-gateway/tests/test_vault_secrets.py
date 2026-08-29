"""Tests for optional Vault AppRole hydration."""
from __future__ import annotations

import os

import httpx

from src.vault_secrets import hydrate_env_from_vault


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None):
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "err",
                request=httpx.Request("GET", "http://x"),
                response=httpx.Response(self.status_code),
            )

    def json(self) -> dict:
        return self._payload


def test_hydrate_noop_without_approle(monkeypatch):
    monkeypatch.delenv("NEXUS_GW_VAULT_ROLE_ID", raising=False)
    monkeypatch.delenv("NEXUS_GW_VAULT_SECRET_ID", raising=False)
    assert hydrate_env_from_vault() is False


def test_hydrate_sets_missing_env_from_kv(monkeypatch):
    monkeypatch.setenv("NEXUS_GW_VAULT_ROLE_ID", "role")
    monkeypatch.setenv("NEXUS_GW_VAULT_SECRET_ID", "secret")
    monkeypatch.setenv("NEXUS_GW_VAULT_URL", "http://vault.test")
    monkeypatch.delenv("NEXUS_GW_JWT_SECRET", raising=False)
    monkeypatch.delenv("NEXUS_GW_MINIO_ACCESS_KEY", raising=False)
    monkeypatch.delenv("NEXUS_GW_MINIO_SECRET_KEY", raising=False)
    monkeypatch.delenv("NEXUS_GW_WAZUH_API_PASSWORD", raising=False)

    calls: list[str] = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def post(self, path, json=None):
            calls.append(path)
            assert path == "/v1/auth/approle/login"
            return _FakeResponse(200, {"auth": {"client_token": "t"}})

        def get(self, path, headers=None):
            calls.append(path)
            if path.endswith("/nexus/dev"):
                return _FakeResponse(
                    200,
                    {
                        "data": {
                            "data": {
                                "NEXUS_GW_JWT_SECRET": "from-vault-jwt",
                                "NEXUS_GW_MINIO_ACCESS_KEY": "vault-access",
                                "NEXUS_GW_MINIO_SECRET_KEY": "vault-secret",
                            }
                        }
                    },
                )
            if path.endswith("/soc/wazuh"):
                return _FakeResponse(
                    200,
                    {"data": {"data": {"WAZUH_API_PASSWORD": "vault-wazuh"}}},
                )
            return _FakeResponse(404, {})

    monkeypatch.setattr(httpx, "Client", FakeClient)
    assert hydrate_env_from_vault() is True
    assert os.environ["NEXUS_GW_JWT_SECRET"] == "from-vault-jwt"
    assert os.environ["NEXUS_GW_MINIO_ACCESS_KEY"] == "vault-access"
    assert os.environ["NEXUS_GW_MINIO_SECRET_KEY"] == "vault-secret"
    assert os.environ["NEXUS_GW_WAZUH_API_PASSWORD"] == "vault-wazuh"
    assert "/v1/auth/approle/login" in calls
