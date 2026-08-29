"""Gateway configuration via pydantic-settings."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class GatewaySettings(BaseSettings):
    """All gateway configuration loaded from environment variables."""

    # Server
    port: int = 3100
    debug: bool = False
    log_level: Literal["debug", "info", "warn", "error"] = "info"

    # Auth
    jwt_secret: str = Field(description="JWT signing secret — required")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 480  # 8 hours
    auth_provider: Literal["local", "oidc"] = "local"
    # Optional "user:pass,user2:pass2" allowlist. Empty = any non-empty creds (lab).
    local_users: str | None = None
    vault_url: str | None = None
    vault_role_id: str | None = Field(
        default=None,
        description="AppRole role_id — when set with vault_secret_id, hydrate secrets from Vault",
    )
    vault_secret_id: str | None = Field(
        default=None,
        description="AppRole secret_id for optional Vault hydration",
    )

    # Upstream services
    wazuh_api_url: str = Field(description="Wazuh Manager API URL — required")
    wazuh_api_user: str = "wazuh-wui"
    wazuh_api_password: str = Field(default="", description="Wazuh API password")
    ai_inference_url: str = "http://ai-inference:8000"
    athena_agents_url: str = "http://athena-agents:8080"
    # Object store: MinIO (lab) or Cloudflare R2 (prod). Same access/secret/bucket envs.
    object_store_backend: Literal["minio", "r2"] = "minio"
    object_store_region: str | None = None  # R2: "auto"; MinIO: usually unset
    r2_account_id: str | None = None  # required when backend=r2 unless minio_endpoint set
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = Field(description="S3 access key (MinIO or R2) — required")
    minio_secret_key: str = Field(description="S3 secret key (MinIO or R2) — required")
    minio_secure: bool = False
    minio_bucket: str = "nexus-memory"
    # Host:port the browser uses to fetch pre-signed URLs (rewritten from minio_endpoint).
    minio_public_endpoint: str | None = None
    # D1 metadata index (via nexus-metadata Worker). Optional — unset in MinIO lab.
    d1_proxy_url: str | None = None
    d1_api_key: str | None = None

    # CORS
    cors_allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Rate limiting
    login_rate_limit: str = "10/minute"

    # Service registry
    service_registry_path: str = "/app/config/services.json"

    model_config = {
        "env_prefix": "NEXUS_GW_",
        "env_file": ".env",
    }


@lru_cache
def get_settings() -> GatewaySettings:
    """Cached settings singleton — fails fast if required vars are missing."""
    from src.vault_secrets import hydrate_env_from_vault

    hydrate_env_from_vault()
    return GatewaySettings()
