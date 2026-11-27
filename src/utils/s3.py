"""S3-compatible storage preflight checks."""

from src.utils.observability import get_logger


logger = get_logger(__name__)


def validate_bucket_access(s3_client, bucket_name: str) -> None:
    """Fail fast when a required bucket is missing or inaccessible."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except Exception as error:
        logger.exception(
            "event=s3_bucket_check_failed bucket=%s",
            bucket_name,
        )
        raise RuntimeError(
            f"Required S3 bucket is missing or inaccessible: {bucket_name}"
        ) from error

    logger.info("event=s3_bucket_check_succeeded bucket=%s", bucket_name)
