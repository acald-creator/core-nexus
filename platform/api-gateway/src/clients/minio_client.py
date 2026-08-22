"""Wrapper around minio SDK for object listing and pre-signed URLs."""
from datetime import timedelta
from minio import Minio


class MinIOClient:
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool,
        bucket: str,
        public_endpoint: str | None = None,
    ):
        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        self._bucket = bucket
        self._endpoint = endpoint
        self._public_endpoint = public_endpoint

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
