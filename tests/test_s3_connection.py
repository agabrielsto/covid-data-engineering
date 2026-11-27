import os

import boto3
from botocore.config import Config
from dotenv import load_dotenv

# Load local configuration when running outside CI.
load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION"),
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "path"},
    ),
)


def test_connection():
    response = s3.list_buckets()

    print("SILO connection successful!")
    print("\nBuckets found:")

    for bucket in response["Buckets"]:
        print(f"- {bucket['Name']}")

    assert "Buckets" in response
