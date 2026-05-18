import io
from uuid import uuid4
from minio import Minio
from minio.error import S3Error
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
    return _client


async def init_storage() -> None:
    client = get_minio_client()
    try:
        if not client.bucket_exists(settings.MINIO_BUCKET):
            client.make_bucket(settings.MINIO_BUCKET)
            logger.info("bucket_created", bucket=settings.MINIO_BUCKET)
        else:
            logger.info("bucket_exists", bucket=settings.MINIO_BUCKET)
    except S3Error as e:
        logger.error("storage_init_failed", error=str(e))
        raise


def upload_file(
    file_data: bytes,
    content_type: str = "application/octet-stream",
    filename: str | None = None,
    folder: str = "uploads",
) -> str:
    client = get_minio_client()
    ext = filename.split(".")[-1] if filename and "." in filename else "bin"
    object_name = f"{folder}/{uuid4()}.{ext}"

    client.put_object(
        bucket_name=settings.MINIO_BUCKET,
        object_name=object_name,
        data=io.BytesIO(file_data),
        length=len(file_data),
        content_type=content_type,
    )
    logger.info("file_uploaded", key=object_name, size=len(file_data))
    return object_name


def download_file(object_name: str) -> bytes:
    client = get_minio_client()
    response = client.get_object(settings.MINIO_BUCKET, object_name)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def delete_file(object_name: str) -> None:
    client = get_minio_client()
    client.remove_object(settings.MINIO_BUCKET, object_name)
    logger.info("file_deleted", key=object_name)


def get_presigned_url(object_name: str, expires_hours: int = 1) -> str:
    from datetime import timedelta
    client = get_minio_client()
    return client.presigned_get_object(
        settings.MINIO_BUCKET,
        object_name,
        expires=timedelta(hours=expires_hours),
    )
