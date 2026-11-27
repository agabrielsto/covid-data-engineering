from unittest.mock import Mock

import pytest

from src.utils.s3 import validate_bucket_access


def test_validate_bucket_access_succeeds():
    client = Mock()
    validate_bucket_access(client, "bronze")
    client.head_bucket.assert_called_once_with(Bucket="bronze")


def test_validate_bucket_access_fails_for_missing_bucket():
    client = Mock()
    client.head_bucket.side_effect = RuntimeError("bucket unavailable")

    with pytest.raises(RuntimeError, match="bronze"):
        validate_bucket_access(client, "bronze")
