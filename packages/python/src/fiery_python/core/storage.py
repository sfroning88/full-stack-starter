"""
Author: Sean Froning
Created Date: 8.20.2026
Process-local S3 clients
"""

from dataclasses import dataclass
from typing import Any, Optional
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from .config import config
from .logging import logging
from ..resources import SyncLazyResource

logger = logging.get_logger(__name__)


@dataclass(frozen=True)
class _S3ClientEnv:
    endpoint_url: str
    access_key_id: str
    secret_access_key: str
    region: str
    missing_message: str


class _S3ClientStorage:
    """Lazy boto3 S3 client bound to one credential set"""

    def __init__(self, env: _S3ClientEnv) -> None:
        self._env = env
        self._client = SyncLazyResource(self._build_client)

    def _resolve_credentials(self) -> tuple[str, str, str, Optional[str]]:
        """Read endpoint and credentials for this instance"""
        key_id = config.get(self._env.access_key_id)
        key_secret = config.get(self._env.secret_access_key)
        if not key_id or not key_secret:
            raise RuntimeError(self._env.missing_message)
        url = config.get(self._env.endpoint_url)
        endpoint = url.rstrip("/") if url else None
        region = config.get(self._env.region) or "us-east-1"
        return key_id, key_secret, region, endpoint

    def _build_client(self) -> Any:
        """Build the S3 client once on first access"""
        key_id, key_secret, region, endpoint = self._resolve_credentials()
        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id=key_id,
            aws_secret_access_key=key_secret,
            config=Config(
                signature_version="s3v4",
                retries={"max_attempts": 3},
                request_checksum_calculation="when_required",
                response_checksum_validation="when_required",
            ),
        )

    def get_client(self) -> Any:
        """Lazy-load shared S3 client (cached per worker process)"""
        return self._client.get()

    def close(self) -> None:
        """Close shared S3 client during shutdown"""
        client = self._client.pop()
        if client is None:
            return
        try:
            client.close()
        except Exception as err:
            logger.warning("storage_client_close_failed", error=str(err))

    def reset(self) -> None:
        """Drop the cached client so a forked child rebuilds its own"""
        self._client.reset()

    def put_bytes(
        self,
        bucket: str,
        key: str,
        body: bytes,
        *,
        content_type: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> None:
        """Upload bytes to the given bucket at the given key"""
        if not key or not body:
            raise ValueError("Storage key and body are required")
        params: dict[str, Any] = {"Bucket": bucket, "Key": key, "Body": body}
        if content_type:
            params["ContentType"] = content_type
        if metadata:
            params["Metadata"] = metadata
        try:
            self.get_client().put_object(**params)
        except ClientError as err:
            meta = err.response.get("ResponseMetadata") or {}
            logger.warning(
                "storage_upload_failed",
                bucket=bucket,
                key=key,
                error=str(err),
                error_code=(err.response.get("Error") or {}).get("Code"),
                http_status=meta.get("HTTPStatusCode"),
                request_id=meta.get("RequestId"),
            )
            raise
        except Exception as err:
            logger.warning(
                "storage_upload_failed", bucket=bucket, key=key, error=str(err)
            )
            raise

    def get_object(self, bucket: str, key: str) -> dict[str, Any]:
        """Download the raw S3 object response (Body + Metadata)"""
        if not key:
            raise ValueError("Storage key is required")
        try:
            return self.get_client().get_object(Bucket=bucket, Key=key)
        except ClientError as err:
            meta = err.response.get("ResponseMetadata") or {}
            logger.warning(
                "storage_download_failed",
                bucket=bucket,
                key=key,
                error=str(err),
                error_code=(err.response.get("Error") or {}).get("Code"),
                http_status=meta.get("HTTPStatusCode"),
                request_id=meta.get("RequestId"),
            )
            raise
        except Exception as err:
            logger.warning(
                "storage_download_failed", bucket=bucket, key=key, error=str(err)
            )
            raise

    def get_bytes(self, bucket: str, key: str) -> bytes:
        """Download object body from the given bucket"""
        body = self.get_object(bucket, key)["Body"]
        try:
            return body.read()
        finally:
            body.close()

    def head_object(self, bucket: str, key: str) -> dict[str, Any]:
        """HEAD the object; return the raw S3 response (Metadata)"""
        if not key:
            raise ValueError("Storage key is required")
        try:
            return self.get_client().head_object(Bucket=bucket, Key=key)
        except Exception as err:
            logger.warning(
                "storage_head_failed", bucket=bucket, key=key, error=str(err)
            )
            raise

    def exists(self, bucket: str, key: str) -> bool:
        """Return True if the object exists"""
        if not key:
            raise ValueError("Storage key is required")
        try:
            self.head_object(bucket, key)
            return True
        except ClientError as err:
            code = str(err.response.get("Error", {}).get("Code", ""))
            if code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise


models_s3 = _S3ClientStorage(
    _S3ClientEnv(
        endpoint_url="S3_BUCKET_URL",
        access_key_id="MODELS_BUCKET_KEY_ID",
        secret_access_key="MODELS_BUCKET_KEY_SECRET",
        region="S3_BUCKET_REGION",
        missing_message="Models bucket credentials not configured",
    )
)

r2_s3 = _S3ClientStorage(
    _S3ClientEnv(
        endpoint_url="R2_BUCKET_URL",
        access_key_id="R2_BUCKET_KEY_ID",
        secret_access_key="R2_BUCKET_KEY_SECRET",
        region="R2_BUCKET_REGION",
        missing_message="R2 credentials not configured",
    )
)
