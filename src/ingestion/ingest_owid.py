import os
import csv
from pathlib import Path
from datetime import datetime, timezone

import boto3
import requests
from dotenv import load_dotenv
from botocore.config import Config

from src.utils.observability import get_logger, log_stage


load_dotenv()

SOURCE_URL = "https://catalog.ourworldindata.org/garden/covid/latest/compact/compact.csv"
BUCKET_NAME = "bronze"

EXTRACTED_AT = datetime.now(timezone.utc)
INGESTION_DATE = EXTRACTED_AT.strftime("%Y-%m-%d")
TIMESTAMP = EXTRACTED_AT.strftime("%Y%m%dT%H%M%SZ")

LOCAL_DIR = Path("data/bronze")
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

FILE_NAME = f"owid_covid_compact_{TIMESTAMP}.csv"
LOCAL_FILE = LOCAL_DIR / FILE_NAME

OBJECT_KEY = (
    f"owid/covid/ingestion_date={INGESTION_DATE}/{FILE_NAME}"
)

logger = get_logger(__name__)

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION"),
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "path"}
    )
)


def download_data():
    print("Downloading COVID-19 dataset from OWID...")

    with requests.get(
        SOURCE_URL,
        stream=True,
        timeout=(15, 180)
    ) as response:
        response.raise_for_status()

        with LOCAL_FILE.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

    with LOCAL_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        columns = next(csv.reader(file), [])

    required_columns = {"country", "date"}

    if not required_columns.issubset(columns):
        LOCAL_FILE.unlink(missing_ok=True)
        raise ValueError(
            f"Invalid dataset structure. Columns found: {columns}"
        )

    size_mb = LOCAL_FILE.stat().st_size / (1024 * 1024)

    print(f"Download completed: {LOCAL_FILE}")
    print(f"File size: {size_mb:.2f} MB")


def upload_to_bronze():
    print("Uploading dataset to Bronze layer...")

    s3.upload_file(
        str(LOCAL_FILE),
        BUCKET_NAME,
        OBJECT_KEY,
        ExtraArgs={
            "ContentType": "text/csv",
            "Metadata": {
                "source": "our-world-in-data",
                "extracted_at": EXTRACTED_AT.isoformat()
            }
        }
    )

    print(f"Upload completed: s3://{BUCKET_NAME}/{OBJECT_KEY}")


def main():
    try:
        with log_stage(logger, "bronze_ingestion"):
            with log_stage(logger, "download_owid_csv"):
                download_data()
            with log_stage(logger, "upload_bronze_object"):
                upload_to_bronze()

            logger.info(
                "event=ingestion_metrics file=%s size_bytes=%d",
                LOCAL_FILE.name,
                LOCAL_FILE.stat().st_size,
            )
        print("Ingestion pipeline completed successfully.")

    except Exception:
        logger.exception("event=pipeline_failed pipeline=bronze_ingestion")
        raise


if __name__ == "__main__":
    main()
