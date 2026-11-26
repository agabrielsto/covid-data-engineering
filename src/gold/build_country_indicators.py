
from pathlib import Path

import duckdb


SILVER_FILE = Path(
    "data/silver/owid_covid_silver_20261125T182624Z.parquet"
)

GOLD_FILE = Path("data/gold/country_indicators.parquet")


def build_country_indicators(
    silver_file: Path = SILVER_FILE,
    gold_file: Path = GOLD_FILE
):
    silver_file = Path(silver_file)
    gold_file = Path(gold_file)

    if not silver_file.exists():
        raise FileNotFoundError(
            f"Silver dataset not found: {silver_file}"
        )

    gold_file.parent.mkdir(parents=True, exist_ok=True)

    print("Starting Gold transformation...")

    query = f"""
        COPY (
            WITH latest_data AS (
                SELECT *
                FROM read_parquet('{silver_file.as_posix()}')
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
        TO '{gold_file.as_posix()}'
        (FORMAT PARQUET, COMPRESSION ZSTD);
    """

    with duckdb.connect() as connection:
        connection.execute(query)

        total_rows = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet('{gold_file.as_posix()}')
            """
        ).fetchone()[0]

    print(f"Gold transformation completed: {total_rows:,} countries")
    print(f"Output: {gold_file}")

    return total_rows


def main():
    try:
        build_country_indicators()
        print("Gold pipeline completed successfully.")

    except Exception as error:
        print(f"Gold pipeline failed: {error}")
        raise


if __name__ == "__main__":
    main()
