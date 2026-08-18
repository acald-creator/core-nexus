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
    auth_provider: Literal["local", "vault"] = "local"
    vault_url: str | None = None

    # Upstream services
    wazuh_api_url: str = Field(description="Wazuh Manager API URL — required")
    wazuh_api_user: str = "wazuh-wui"
    wazuh_api_password: str = Field(default="", description="Wazuh API password")
    ai_inference_url: str = "http://ai-inference:8000"
    athena_agents_url: str = "http://athena-agents:8080"
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = Field(description="MinIO access key — required")
    minio_secret_key: str = Field(description="MinIO secret key — required")
    minio_secure: bool = False
    minio_bucket: str = "nexus-memory"

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
    return GatewaySettings()
