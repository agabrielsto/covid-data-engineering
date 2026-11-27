
import duckdb
import pytest

from src.gold.build_country_indicators import (
    build_country_indicators,
    get_latest_silver_file,
)


def test_gold_creates_parquet_file(
    sample_covid_data,
    tmp_path
):
    silver_file = tmp_path / "silver.parquet"
    gold_file = tmp_path / "gold.parquet"

    sample_covid_data.execute(
        f"COPY covid_data TO '{silver_file}' (FORMAT PARQUET)"
    )

    total_rows = build_country_indicators(
        silver_file=silver_file,
        gold_file=gold_file
    )

    assert gold_file.exists()
    assert total_rows == 3


def test_gold_selects_latest_record(
    sample_covid_data,
    tmp_path
):
    silver_file = tmp_path / "silver.parquet"
    gold_file = tmp_path / "gold.parquet"

    sample_covid_data.execute(
        f"COPY covid_data TO '{silver_file}' (FORMAT PARQUET)"
    )

    build_country_indicators(silver_file, gold_file)

    with duckdb.connect() as connection:
        result = connection.execute(
            """
            SELECT total_cases, total_deaths, last_updated
            FROM read_parquet(?)
            WHERE code = 'BRA'
            """,
            [str(gold_file)]
        ).fetchone()

    assert result[0] == 37000000
    assert result[1] == 700000
    assert str(result[2]) == "2026-10-18"


def test_gold_calculates_indicators(
    sample_covid_data,
    tmp_path
):
    silver_file = tmp_path / "silver.parquet"
    gold_file = tmp_path / "gold.parquet"

    sample_covid_data.execute(
        f"COPY covid_data TO '{silver_file}' (FORMAT PARQUET)"
    )

    build_country_indicators(silver_file, gold_file)

    with duckdb.connect() as connection:
        result = connection.execute(
            """
            SELECT
                cases_per_million,
                deaths_per_million,
                fatality_rate
            FROM read_parquet(?)
            WHERE code = 'BRA'
            """,
            [str(gold_file)]
        ).fetchone()

    assert abs(result[0] - (37000000 / 215000000 * 1000000)) < 0.01
    assert abs(result[1] - (700000 / 215000000 * 1000000)) < 0.01
    assert abs(result[2] - (700000 / 37000000 * 100)) < 0.01


def test_gold_excludes_invalid_records(
    sample_covid_data,
    tmp_path
):
    silver_file = tmp_path / "silver.parquet"
    gold_file = tmp_path / "gold.parquet"

    sample_covid_data.execute("""
        INSERT INTO covid_data VALUES
        ('Invalid Country', NULL, 'Europe', '2026-10-18', 1000, 10, 10000),
        ('Unknown Continent', 'UNK', NULL, '2026-10-18', 1000, 10, 10000)
    """)

    sample_covid_data.execute(
        f"COPY covid_data TO '{silver_file}' (FORMAT PARQUET)"
    )

    total_rows = build_country_indicators(silver_file, gold_file)

    assert total_rows == 3


def test_gold_discovers_latest_silver_file(tmp_path):
    silver_dir = tmp_path / "silver"
    silver_dir.mkdir()

    older = silver_dir / "owid_covid_silver_20261125T100000Z.parquet"
    newer = silver_dir / "owid_covid_silver_20261126T100000Z.parquet"
    ignored = silver_dir / "unrelated.parquet"

    older.touch()
    newer.touch()
    ignored.touch()

    import os
    os.utime(older, (100, 100))
    os.utime(newer, (200, 200))

    assert get_latest_silver_file(silver_dir) == newer


def test_gold_raises_when_silver_directory_is_empty(tmp_path):
    with pytest.raises(FileNotFoundError, match="No Silver Parquet files"):
        get_latest_silver_file(tmp_path)
