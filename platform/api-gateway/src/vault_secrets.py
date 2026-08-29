"""Optional Vault AppRole hydration for gateway env secrets."""
from __future__ import annotations

import os

import httpx


def _kv_data(payload: dict) -> dict:
    data = payload.get("data") or {}
    # KV v2 nests under data.data
    if isinstance(data.get("data"), dict):
        return data["data"]
    return data if isinstance(data, dict) else {}


def hydrate_env_from_vault() -> bool:
    """
    If NEXUS_GW_VAULT_ROLE_ID + NEXUS_GW_VAULT_SECRET_ID are set, log in to Vault
    and populate missing NEXUS_GW_* secrets from KV.

    Intended paths (nexus-hashistack seeds):
      secret/nexus/dev  → JWT + MinIO
      secret/soc/wazuh  → Wazuh API password (when role allows)
    """
    role_id = os.getenv("NEXUS_GW_VAULT_ROLE_ID")
    secret_id = os.getenv("NEXUS_GW_VAULT_SECRET_ID")
    if not role_id or not secret_id:
        return False

    vault_url = (
        os.getenv("NEXUS_GW_VAULT_URL")
        or os.getenv("VAULT_ADDR")
        or "http://127.0.0.1:8200"
    ).rstrip("/")

    with httpx.Client(base_url=vault_url, timeout=10.0) as client:
        login = client.post(
            "/v1/auth/approle/login",
            json={"role_id": role_id, "secret_id": secret_id},
        )
        login.raise_for_status()
        token = login.json()["auth"]["client_token"]
        headers = {"X-Vault-Token": token}

        def read_kv(path: str) -> dict:
            resp = client.get(f"/v1/secret/data/{path}", headers=headers)
            if resp.status_code == 403 or resp.status_code == 404:
                return {}
            resp.raise_for_status()
            return _kv_data(resp.json())

        nexus_dev = read_kv("nexus/dev")
        soc = read_kv("soc/wazuh")

    mapping = {
        "NEXUS_GW_JWT_SECRET": nexus_dev.get("NEXUS_GW_JWT_SECRET"),
        "NEXUS_GW_MINIO_ACCESS_KEY": nexus_dev.get("NEXUS_GW_MINIO_ACCESS_KEY"),
        "NEXUS_GW_MINIO_SECRET_KEY": nexus_dev.get("NEXUS_GW_MINIO_SECRET_KEY"),
        "NEXUS_GW_WAZUH_API_PASSWORD": soc.get("WAZUH_API_PASSWORD"),
    }
    applied = False
    for key, value in mapping.items():
        if value and not os.getenv(key):
            os.environ[key] = str(value)
            applied = True
        elif value and os.getenv("NEXUS_GW_VAULT_OVERWRITE") == "1":
            os.environ[key] = str(value)
            applied = True
    return applied
