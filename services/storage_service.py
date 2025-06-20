"""Storage service abstractions and implementations.

This module defines IStorageService interface and two concrete implementations:
- GCSStorageService: Google Cloud Storage for production.
- LocalStorageService: local filesystem fallback primarily for tests.

The service is intentionally stateless aside from the bucket/directory names,
allowing easy mocking and testing.
"""

from __future__ import annotations

import abc
import os
import typing as _t
from pathlib import Path

from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError

__all__ = [
    "IStorageService",
    "GCSStorageService",
    "LocalStorageService",
    "get_storage_service",
]


class IStorageService(abc.ABC):
    """Storage service contract."""

    @abc.abstractmethod
    def upload_file(self, *, file_path: Path | str, destination: str) -> str:  # noqa: D401
        """Upload a file and return its storage URI."""

    @abc.abstractmethod
    def download_file(self, *, source: str, target_path: Path | str) -> None:  # noqa: D401
        """Download a file from storage to *target_path*."""

    @abc.abstractmethod
    def delete_file(self, *, uri: str) -> None:  # noqa: D401
        """Delete a file by storage *uri*."""

    @abc.abstractmethod
    def generate_signed_url(self, *, uri: str, expiry_seconds: int = 3600) -> str:  # noqa: D401
        """Return a temporary signed URL for the given object."""


class GCSStorageService(IStorageService):
    """Google Cloud Storage implementation of :class:`IStorageService`."""

    def __init__(self, bucket_name: str, *, prefix: str | None = None) -> None:
        self._bucket_name: str = bucket_name
        self._prefix: str | None = prefix.strip("/") if prefix else None
        try:
            self._client = storage.Client()
            self._bucket = self._client.bucket(bucket_name)
        except GoogleAPIError as err:
            raise RuntimeError("Failed to initialise GCS client") from err

    # ---------------------------------------------------------------------
    # IStorageService API
    # ---------------------------------------------------------------------

    def upload_file(self, *, file_path: Path | str, destination: str) -> str:  # type: ignore[override]
        file_path = Path(file_path)
        blob_name = self._build_blob_name(destination)
        blob = self._bucket.blob(blob_name)
        blob.upload_from_filename(file_path.as_posix())
        return f"gs://{self._bucket_name}/{blob_name}"

    def download_file(self, *, source: str, target_path: Path | str) -> None:  # noqa: D401
        blob_name = self._blob_name_from_uri(source)
        blob = self._bucket.blob(blob_name)
        blob.download_to_filename(Path(target_path).as_posix())

    def delete_file(self, *, uri: str) -> None:  # noqa: D401
        blob_name = self._blob_name_from_uri(uri)
        blob = self._bucket.blob(blob_name)
        blob.delete()

    def generate_signed_url(self, *, uri: str, expiry_seconds: int = 3600) -> str:  # noqa: D401
        blob_name = self._blob_name_from_uri(uri)
        blob = self._bucket.blob(blob_name)
        return blob.generate_signed_url(expiration=expiry_seconds)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _blob_name_from_uri(self, uri: str) -> str:
        if not uri.startswith("gs://"):
            raise ValueError("Expected a gs:// URI")
        parts = uri.replace("gs://", "").split("/", 1)
        if parts[0] != self._bucket_name or len(parts) != 2:
            raise ValueError("URI bucket does not match configured bucket")
        return parts[1]

    def _build_blob_name(self, destination: str) -> str:
        if self._prefix:
            return f"{self._prefix}/{destination.lstrip('/')}"
        return destination.lstrip("/")


class LocalStorageService(IStorageService):
    """Local filesystem implementation of :class:`IStorageService`."""

    def __init__(self, root_dir: str | Path = "./storage", *, prefix: str | None = None) -> None:
        self._root_dir = Path(root_dir).expanduser().resolve()
        self._root_dir.mkdir(parents=True, exist_ok=True)
        self._prefix: str | None = prefix.strip("/") if prefix else None

    # ---------------------------------------------------------------------
    # IStorageService API
    # ---------------------------------------------------------------------

    def upload_file(self, *, file_path: Path | str, destination: str) -> str:  # type: ignore[override]
        file_path = Path(file_path)
        target_path = self._root_dir / self._build_blob_name(destination)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(file_path.read_bytes())
        return target_path.as_uri()

    def download_file(self, *, source: str, target_path: Path | str) -> None:  # noqa: D401
        source_path = Path(source)
        if source_path.as_uri().startswith("file://"):
            source_path = Path(source_path.path)
        Path(target_path).write_bytes(source_path.read_bytes())

    def delete_file(self, *, uri: str) -> None:  # noqa: D401
        Path(uri.replace("file://", "")).unlink(missing_ok=True)

    def generate_signed_url(self, *, uri: str, expiry_seconds: int = 3600) -> str:  # noqa: D401
        # Local files don't need signed URLs. Return the path.
        return uri

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_blob_name(self, destination: str) -> str:
        if self._prefix:
            return f"{self._prefix}/{destination.lstrip('/')}"
        return destination.lstrip("/")


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------


def get_storage_service() -> IStorageService:
    """Return the appropriate storage service based on env variables."""

    bucket_name = os.getenv("GCS_BUCKET", "")
    if bucket_name:
        return GCSStorageService(bucket_name=bucket_name)

    # Fallback to local storage
    return LocalStorageService() 