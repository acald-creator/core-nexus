"""S3-compatible object store client (MinIO lab, Cloudflare R2 prod).

Uses the MinIO Python SDK against any S3 API. Backend is selected via
NEXUS_GW_OBJECT_STORE_BACKEND=minio|r2 — credentials stay on the same
NEXUS_GW_MINIO_* env vars (access/secret/bucket) so Vault paths and
sync scripts do not fork.
"""
from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from minio import Minio

if TYPE_CHECKING:
    from src.config import GatewaySettings


class ObjectStoreClient:
    """List objects and mint browser-reachable pre-signed GET URLs."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool,
        bucket: str,
        public_endpoint: str | None = None,
        region: str | None = None,
    ):
        kwargs: dict = {
            "endpoint": endpoint,
            "access_key": access_key,
            "secret_key": secret_key,
            "secure": secure,
        }
        if region:
            kwargs["region"] = region
        self._client = Minio(**kwargs)
        self._bucket = bucket
        self._endpoint = endpoint
        self._public_endpoint = public_endpoint

    @classmethod
    def from_settings(cls, settings: GatewaySettings) -> ObjectStoreClient:
        """Build a client for MinIO (lab) or Cloudflare R2 (prod)."""
        backend = settings.object_store_backend
        if backend == "r2":
            account = settings.r2_account_id
            default_lab = settings.minio_endpoint in ("minio:9000", "localhost:9000", "")
            if settings.minio_endpoint and not default_lab:
                endpoint = settings.minio_endpoint
            elif account:
                endpoint = f"{account}.r2.cloudflarestorage.com"
            else:
                raise ValueError(
                    "NEXUS_GW_R2_ACCOUNT_ID (or a non-lab NEXUS_GW_MINIO_ENDPOINT) "
                    "is required when NEXUS_GW_OBJECT_STORE_BACKEND=r2"
                )
            endpoint = endpoint.removeprefix("https://").removeprefix("http://")
            return cls(
                endpoint=endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=True,
                bucket=settings.minio_bucket,
                public_endpoint=settings.minio_public_endpoint,
                region=settings.object_store_region or "auto",
            )

        return cls(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
            bucket=settings.minio_bucket,
            public_endpoint=settings.minio_public_endpoint,
            region=settings.object_store_region or None,
        )

    def bucket_exists(self) -> bool:
        """Check if the configured bucket exists."""
        return self._client.bucket_exists(self._bucket)

    def list_objects(self, prefix: str) -> list[dict]:
        """List objects under a prefix."""
        objects = self._client.list_objects(self._bucket, prefix=prefix, recursive=True)
        results = []
        for obj in objects:
            results.append({
                "key": obj.object_name,
                "name": obj.object_name.split("/")[-1],
                "size": obj.size,
                "lastModified": obj.last_modified.isoformat() if obj.last_modified else "",
            })
        return results

    def get_presigned_url(self, key: str, expires_minutes: int = 15) -> str:
        """Generate a pre-signed download URL reachable from the browser."""
        url = self._client.presigned_get_object(
            self._bucket, key, expires=timedelta(minutes=expires_minutes)
        )
        if self._public_endpoint and self._endpoint != self._public_endpoint:
            url = url.replace(self._endpoint, self._public_endpoint, 1)
        return url

    def get_object_content(self, key: str) -> str:
        """Get object content as string."""
        response = self._client.get_object(self._bucket, key)
        try:
            return response.read().decode("utf-8")
        finally:
            response.close()
            response.release_conn()


# Back-compat alias — routes and tests historically imported MinIOClient.
MinIOClient = ObjectStoreClient
