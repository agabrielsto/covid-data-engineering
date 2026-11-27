from pathlib import Path

import duckdb

from src.utils.observability import get_logger, log_stage


SILVER_DIR = Path("data/silver")
SILVER_PATTERN = "owid_covid_silver_*.parquet"
GOLD_FILE = Path("data/gold/country_indicators.parquet")
logger = get_logger(__name__)


def get_latest_silver_file(silver_dir: Path = SILVER_DIR) -> Path:
    """Return the most recently modified Silver Parquet file."""
    silver_dir = Path(silver_dir)
    candidates = list(silver_dir.glob(SILVER_PATTERN))

    if not candidates:
        raise FileNotFoundError(
            f"No Silver Parquet files found in: {silver_dir}"
        )

    return max(candidates, key=lambda path: path.stat().st_mtime)


def build_country_indicators(
    silver_file: Path | None = None,
    gold_file: Path = GOLD_FILE
):
    silver_file = (
        get_latest_silver_file()
        if silver_file is None
        else Path(silver_file)
    )
    gold_file = Path(gold_file)

    if not silver_file.exists():
        raise FileNotFoundError(
            f"Silver dataset not found: {silver_file}"
        )

    gold_file.parent.mkdir(parents=True, exist_ok=True)

    silver_path = silver_file.resolve().as_posix().replace("'", "''")
    gold_path = gold_file.resolve().as_posix().replace("'", "''")

    print("Starting Gold transformation...")
    print(f"Silver input: {silver_file}")

    query = f"""
        COPY (
            WITH latest_data AS (
                SELECT *
                FROM read_parquet('{silver_path}')
                QUALIFY ROW_NUMBER() OVER (
                    PARTITION BY country
                    ORDER BY date DESC
                ) = 1
            )

            SELECT
                country,
                code,
                continent,
                date AS last_updated,
                total_cases,
                total_deaths,
                population,

                total_cases / NULLIF(population, 0)
                    * 1000000 AS cases_per_million,

                total_deaths / NULLIF(population, 0)
                    * 1000000 AS deaths_per_million,

                total_deaths / NULLIF(total_cases, 0)
                    * 100 AS fatality_rate

            FROM latest_data
            WHERE country IS NOT NULL
              AND code IS NOT NULL
              AND continent IS NOT NULL
        )
        TO '{gold_path}'
        (FORMAT PARQUET, COMPRESSION ZSTD);
    """

    with duckdb.connect() as connection:
        connection.execute(query)

        total_rows = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet('{gold_path}')
            """
        ).fetchone()[0]

    logger.info(
        "event=gold_build_metrics countries=%d output_file=%s source_file=%s",
        total_rows,
        gold_file,
        silver_file,
    )
    print(f"Gold transformation completed: {total_rows:,} countries")
    print(f"Output: {gold_file}")

    return total_rows


def main():
    try:
        with log_stage(logger, "gold_pipeline"):
            with log_stage(logger, "build_country_indicators"):
                build_country_indicators()
        print("Gold pipeline completed successfully.")

    except Exception:
        logger.exception("event=pipeline_failed pipeline=gold")
        raise


if __name__ == "__main__":
    main()
