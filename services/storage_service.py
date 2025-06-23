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
from typing import Protocol
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from dotenv import load_dotenv

__all__ = [
    "IStorageService",
    "GCSStorageService",
    "LocalStorageService",
    "get_storage_service",
]

# 加载环境变量
load_dotenv()

class IStorageService(Protocol):
    """Protocol for storage service implementations."""

    def save_uploaded_file(self, uploaded_file, filename: str) -> str:
        """Save an uploaded file and return its URI."""
        ...

    def save_file(self, file_path: Path) -> str:
        """Save a file and return its URI."""
        ...

    def save_report(self, report_content: str, original_filename: str) -> str:
        """Save a report string to a file and return its URI."""
        ...

    def download_file(self, *, source: str, target_path: Path | str) -> None:
        """Download a file from the storage service."""
        ...


class LocalStorageService:
    """Local file system implementation of :class:`IStorageService`."""

    def __init__(self, *, base_path: Path | str | None = None) -> None:
        self._base_path: Path = Path(base_path or "storage")
        self._base_path.mkdir(parents=True, exist_ok=True)

    def save_uploaded_file(self, uploaded_file, filename: str) -> str:
        """Save uploaded file to local storage and return file path."""
        file_path = self._base_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
        
        return str(file_path)

    def save_file(self, file_path: Path) -> str:
        """Copy file to storage directory and return the new path."""
        target_path = self._base_path / file_path.name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 复制文件到存储目录
        import shutil
        shutil.copy2(file_path, target_path)
        
        return str(target_path)

    def save_report(self, report_content: str, original_filename: str) -> str:
        """Save report content to a local file."""
        report_dir = self._base_path / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_filename = f"report_{Path(original_filename).stem}.txt"
        report_path = report_dir / report_filename
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        return str(report_path)

    def download_file(self, *, source: str, target_path: Path | str) -> None:
        """Copy file from storage to target path."""
        source_path = Path(source)
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy2(source_path, target)


class GCSStorageService:
    """Google Cloud Storage implementation of :class:`IStorageService`."""

    def __init__(self, bucket_name: str = None, project_id: str = None):
        # 使用环境变量或传入的参数
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT', 'auditai-final-try')
        self.bucket_name = bucket_name or os.getenv('STORAGE_BUCKET', 'auditai-claims-bucket1')
        
        try:
            print(f"🔗 尝试连接到Google Cloud Storage")
            print(f"   项目: {self.project_id}")
            print(f"   存储桶: {self.bucket_name}")
            
            # 移除服务账户密钥，使用Application Default Credentials (ADC)
            # 这将使用用户的gcloud凭据，避免JWT签名错误
            self.client = storage.Client(project=self.project_id)
            self._bucket = self.client.bucket(self.bucket_name)
            
            # 测试bucket访问权限
            if self._bucket.exists():
                print(f"✅ 成功连接到Google Cloud Storage bucket: {self.bucket_name}")
            else:
                raise RuntimeError(f"Bucket {self.bucket_name} does not exist")
                
        except Exception as e:
            print(f"⚠️ Google Cloud Storage连接失败: {e}")
            raise e
    
    def save_uploaded_file(self, uploaded_file, filename: str) -> str:
        """上传文件到GCS并返回GS URI"""
        # 重置文件指针到开头
        uploaded_file.seek(0)
        
        blob_name = f"uploaded/{filename}"
        blob = self._bucket.blob(blob_name)
        blob.upload_from_file(uploaded_file, content_type='application/pdf')
        return f"gs://{self.bucket_name}/{blob_name}"

    # ---------------------------------------------------------------------
    # IStorageService protocol methods
    # ---------------------------------------------------------------------

    def save_file(self, file_path: Path) -> str:  # noqa: D401
        """Upload a file to GCS and return its GS URI."""
        blob_name = f"files/{file_path.name}"
        blob = self._bucket.blob(blob_name)
        blob.upload_from_filename(file_path.as_posix())
        return f"gs://{self.bucket_name}/{blob_name}"

    def save_report(self, report_content: str, original_filename: str) -> str:
        """Save report content to GCS and return its GS URI."""
        report_filename = f"report_{Path(original_filename).stem}.txt"
        blob_name = f"reports/{report_filename}"
        
        blob = self._bucket.blob(blob_name)
        blob.upload_from_string(report_content, content_type="text/plain; charset=utf-8")
        
        return f"gs://{self.bucket_name}/{blob_name}"

    def download_file(self, *, source: str, target_path: Path | str) -> None:  # noqa: D401
        """Download a file from GCS."""
        blob_name = self._extract_blob_name(source)
        blob = self._bucket.blob(blob_name)
        blob.download_to_filename(target_path)

    def _extract_blob_name(self, uri: str) -> str:
        """Extract the blob name from a GS URI."""
        if not uri.startswith("gs://"):
            raise ValueError("Expected a gs:// URI")
        parts = uri.replace("gs://", "").split("/", 1)
        if parts[0] != self.bucket_name or len(parts) != 2:
            raise ValueError("URI bucket does not match configured bucket")
        return parts[1]


def get_storage_service() -> IStorageService:
    """Factory function to get the appropriate storage service."""
    try:
        # 尝试使用Google Cloud Storage
        return GCSStorageService()
    except Exception as e:
        print(f"🔄 自动切换到本地存储: {e}")
        return LocalStorageService() 