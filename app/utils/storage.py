"""
Storage abstraction for local and cloud storage.
"""
from pathlib import Path
from typing import BinaryIO
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class StorageService:
    """Abstraction for file storage (local or S3)."""

    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        self.storage_path = Path(settings.STORAGE_PATH)

    def save(self, file_path: str, content: BinaryIO) -> str:
        """
        Save file to storage.
        
        Args:
            file_path: Relative path for the file
            content: File content as binary stream
            
        Returns:
            Full path or URL to saved file
        """
        if self.storage_type == "local":
            return self._save_local(file_path, content)
        elif self.storage_type == "s3":
            return self._save_s3(file_path, content)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")

    def _save_local(self, file_path: str, content: BinaryIO) -> str:
        """Save file to local filesystem."""
        full_path = self.storage_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as f:
            f.write(content.read())
        
        logger.info(f"File saved locally: {full_path}")
        return str(full_path)

    def _save_s3(self, file_path: str, content: BinaryIO) -> str:
        """Save file to AWS S3."""
        # TODO: Implement S3 upload
        import boto3
        
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        
        bucket = settings.AWS_S3_BUCKET
        s3_client.upload_fileobj(content, bucket, file_path)
        
        url = f"https://{bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{file_path}"
        logger.info(f"File uploaded to S3: {url}")
        return url

    def get_url(self, file_path: str) -> str:
        """
        Get URL to access file.
        
        Args:
            file_path: Relative file path
            
        Returns:
            URL to access file
        """
        if self.storage_type == "local":
            return f"/files/{file_path}"
        elif self.storage_type == "s3":
            bucket = settings.AWS_S3_BUCKET
            return f"https://{bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{file_path}"
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
