import duckdb

from src.gold.load_gold_postgres import load_parquet


def test_load_parquet_reads_gold_data(tmp_path):
    gold_file = tmp_path / "gold.parquet"

    with duckdb.connect() as connection:
        connection.execute("""
            CREATE TABLE gold_test (
                country VARCHAR,
                code VARCHAR,
                continent VARCHAR,
                last_updated DATE,
                total_cases DOUBLE,
                total_deaths DOUBLE,
                population DOUBLE,
                cases_per_million DOUBLE,
                deaths_per_million DOUBLE,
                fatality_rate DOUBLE
            )
        """)

        connection.execute("""
            INSERT INTO gold_test VALUES (
                'Brazil', 'BRA', 'South America',
                '2026-10-18', 37000000, 700000,
                215000000, 172093.02, 3255.81, 1.89
            )
        """)

        connection.execute(
            f"COPY gold_test TO '{gold_file.as_posix()}' (FORMAT PARQUET)"
        )

    rows = load_parquet(gold_file)

    assert len(rows) == 1
    assert rows[0][0] == "Brazil"
    assert rows[0][1] == "BRA"
    assert rows[0][2] == "South America"

import pytest


def test_load_parquet_raises_error_when_file_not_found(tmp_path):
    gold_file = tmp_path / "nonexistent.parquet"

    with pytest.raises(FileNotFoundError):
        load_parquet(gold_file)


import os
import pytest

from src.gold.load_gold_postgres import load_into_postgres


def test_load_into_postgres():
    psycopg = pytest.importorskip(
        "psycopg",
        reason="PostgreSQL integration test requires a working psycopg installation",
    )

    rows = [
        (
            "Brazil", "BRA", "South America",
            "2026-10-18", 37000000, 700000,
            215000000, 172093.02, 3255.81, 1.89
        )
    ]

    with psycopg.connect(
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
        dbname=os.getenv("PG_DATABASE"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD")
    ) as connection:

        try:
            total_rows = load_into_postgres(
                rows,
                connection=connection,
                schema_name="test_gold"
            )

            assert total_rows == 1

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT country, code FROM test_gold.country_indicators"
                )
                result = cursor.fetchone()

            assert result == ("Brazil", "BRA")

        finally:
            connection.rollback()
