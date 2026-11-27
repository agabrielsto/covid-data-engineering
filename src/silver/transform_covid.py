
import os
from datetime import datetime, timezone
from pathlib import Path

import boto3
import duckdb
from botocore.config import Config
from dotenv import load_dotenv


load_dotenv()

SOURCE_BUCKET = "bronze"
TARGET_BUCKET = "silver"
SOURCE_PREFIX = "owid/covid/"
TARGET_PREFIX = "owid/covid/"

EXTRACTED_AT = datetime.now(timezone.utc)
PROCESSING_DATE = EXTRACTED_AT.strftime("%Y-%m-%d")
TIMESTAMP = EXTRACTED_AT.strftime("%Y%m%dT%H%M%SZ")

LOCAL_DIR = Path("data/silver")
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

LOCAL_SOURCE = LOCAL_DIR / "source.csv"
LOCAL_TARGET = LOCAL_DIR / f"owid_covid_silver_{TIMESTAMP}.parquet"

TARGET_KEY = (
    f"{TARGET_PREFIX}processing_date={PROCESSING_DATE}/"
    f"owid_covid_silver_{TIMESTAMP}.parquet"
)

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


def get_latest_bronze_object():
    paginator = s3.get_paginator("list_objects_v2")

    objects = (
        obj
        for page in paginator.paginate(
            Bucket=SOURCE_BUCKET,
            Prefix=SOURCE_PREFIX,
        )
        for obj in page.get("Contents", [])
        if obj["Key"].endswith(".csv")
    )

    latest = max(objects, key=lambda obj: obj["LastModified"], default=None)

    if latest is None:
        raise FileNotFoundError("No CSV file found in the Bronze bucket.")

    return latest["Key"]


def download_bronze_data(object_key):
    print("Downloading Bronze dataset...")

    s3.download_file(
        SOURCE_BUCKET,
        object_key,
        str(LOCAL_SOURCE),
    )

    print(f"Downloaded: {object_key}")


def transform_data(
    source_file: Path = LOCAL_SOURCE,
    target_file: Path = LOCAL_TARGET
):
    source_file = Path(source_file)
    target_file = Path(target_file)

    if not source_file.exists():
        raise FileNotFoundError(
            f"Bronze dataset not found: {source_file}"
        )

    target_file.parent.mkdir(parents=True, exist_ok=True)

    print("Starting Silver transformation...")

    source_path = source_file.resolve().as_posix().replace("'", "''")
    target_path = target_file.resolve().as_posix().replace("'", "''")

    query = f"""
        CREATE OR REPLACE TEMP TABLE cleaned_data AS
        {cte_placeholder{"}"};
    """.replace("${cte_placeholder}", cte)

    with duckdb.connect() as connection:
        connection.execute(query)

        conflicting_keys = connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT country, date
                FROM (SELECT DISTINCT * FROM cleaned_data)
                GROUP BY country, date
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]

        if conflicting_keys:
            raise ValueError(
                "Conflicting records found for "
                f"{conflicting_keys} country/date key(s). "
                "Silver transformation was stopped."
            )

        connection.execute(
            f"""
            COPY (
                SELECT DISTINCT *
                FROM cleaned_data
            )
            TO '{target_path}'
            (FORMAT PARQUET, COMPRESSION ZSTD);
            """
        )

        row_count = connection.execute(
            "SELECT COUNT(*) FROM read_parquet(?)",
            [target_path],
        ).fetchone()[0]

    print(f"Transformation completed: {row_count:,} rows")
    print(f"Output: {target_file}")
    return row_count



def upload_silver_data():
    print("Uploading Silver dataset...")

    s3.upload_file(
        str(LOCAL_TARGET),
        TARGET_BUCKET,
        TARGET_KEY,
        ExtraArgs={
            "ContentType": "application/vnd.apache.parquet",
            "Metadata": {
                "source": "our-world-in-data",
                "processing_date": PROCESSING_DATE,
                "format": "parquet",
            },
        },
    )

    print(f"Uploaded: s3://{TARGET_BUCKET}/{TARGET_KEY}")

def validate_silver_data(file_path):
    print("Validating Silver dataset...")

    file_path = Path(file_path).resolve().as_posix()

    with duckdb.connect() as connection:
        result = connection.execute(
            """
            SELECT
                COUNT(*) AS total_rows,
                COUNT(DISTINCT country) AS total_countries,
                MIN(date) AS min_date,
                MAX(date) AS max_date,
                COUNT(*) FILTER (WHERE country IS NULL) AS null_countries,
                COUNT(*) FILTER (WHERE date IS NULL) AS null_dates,
                COUNT(*) - COUNT(DISTINCT (country, date)) AS duplicate_keys
            FROM read_parquet(?)
            """,
            [file_path],
        ).fetchone()

    metrics = {
        "total_rows": result[0],
        "total_countries": result[1],
        "min_date": result[2],
        "max_date": result[3],
        "null_countries": result[4],
        "null_dates": result[5],
        "duplicate_keys": result[6],
    }

    for name, value in metrics.items():
        print(f"{name}: {value}")

    failures = []
    if metrics["total_rows"] == 0:
        failures.append("dataset is empty")
    if metrics["null_countries"]:
        failures.append("null country values found")
    if metrics["null_dates"]:
        failures.append("null date values found")
    if metrics["duplicate_keys"]:
        failures.append("duplicate country/date keys found")

    if failures:
        raise ValueError(
            "Silver data quality validation failed: " + "; ".join(failures)
        )

    return metrics

def main():
    try:
        source_key = get_latest_bronze_object()
        download_bronze_data(source_key)
        transform_data()
        validate_silver_data(LOCAL_TARGET)
        upload_silver_data()

        print("Silver pipeline completed successfully.")

    except Exception as error:
        print(f"Silver pipeline failed: {error}")
        raise


if __name__ == "__main__":
    main()
