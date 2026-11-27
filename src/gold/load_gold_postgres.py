
import os
from pathlib import Path
import duckdb
from dotenv import load_dotenv


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

load_dotenv(dotenv_path=ENV_FILE, override=True)
GOLD_FILE = Path("data/gold/country_indicators.parquet")

TABLE_NAME = "gold.country_indicators"


def load_parquet(gold_file: Path = GOLD_FILE):
    gold_file = Path(gold_file)

    print("Reading Gold dataset...")

    if not gold_file.exists():
        raise FileNotFoundError(
            f"Gold file not found: {gold_file}"
        )

    with duckdb.connect() as connection:
        rows = connection.execute(
            """
            SELECT
                country,
                code,
                continent,
                last_updated,
                total_cases,
                total_deaths,
                population,
                cases_per_million,
                deaths_per_million,
                fatality_rate
            FROM read_parquet(?)
            """,
            [str(gold_file)]        
            ).fetchall()

    print(f"Records read: {len(rows):,}")

    return rows



def load_into_postgres(
    rows,
    connection=None,
    schema_name="gold",
    table_name="country_indicators"
):
    print("Connecting to PostgreSQL...")

    # Load the PostgreSQL driver only when this function is actually used.
    import psycopg
    from psycopg import sql

    if connection is None:
        required_vars = [
            "PG_HOST",
            "PG_PORT",
            "PG_DATABASE",
            "PG_USER",
            "PG_PASSWORD",
        ]
        missing_vars = [
            var for var in required_vars
            if not os.getenv(var)
        ]
        if missing_vars:
            raise EnvironmentError(
                f"Missing environment variables: {missing_vars}"
            )

        with psycopg.connect(
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT"),
            dbname=os.getenv("PG_DATABASE"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD")
        ) as connection:
            return load_into_postgres(
                rows,
                connection,
                schema_name,
                table_name
            )

    schema_identifier = sql.Identifier(schema_name)
    table_identifier = sql.Identifier(
        schema_name,
        table_name
    )

    with connection.cursor() as cursor:

        cursor.execute(
            sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                schema_identifier
            )
        )

        cursor.execute(
            sql.SQL("""
                CREATE TABLE IF NOT EXISTS {} (
                    country VARCHAR NOT NULL,
                    code VARCHAR PRIMARY KEY,
                    continent VARCHAR NOT NULL,
                    last_updated DATE,
                    total_cases DOUBLE PRECISION,
                    total_deaths DOUBLE PRECISION,
                    population DOUBLE PRECISION,
                    cases_per_million DOUBLE PRECISION,
                    deaths_per_million DOUBLE PRECISION,
                    fatality_rate DOUBLE PRECISION
                )
            """).format(table_identifier)
        )

        cursor.execute(
            sql.SQL("TRUNCATE TABLE {}").format(
                table_identifier
            )
        )

        cursor.executemany(
            sql.SQL("""
                INSERT INTO {} (
                    country,
                    code,
                    continent,
                    last_updated,
                    total_cases,
                    total_deaths,
                    population,
                    cases_per_million,
                    deaths_per_million,
                    fatality_rate
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
            """).format(table_identifier),
            rows
        )

        cursor.execute(
            sql.SQL("SELECT COUNT(*) FROM {}").format(
                table_identifier
            )
        )

        total_rows = cursor.fetchone()[0]

    print(
        f"PostgreSQL load completed: {total_rows:,} records"
    )

    return total_rows


def main():
    try:
        rows = load_parquet()
        load_into_postgres(rows)

        print("Gold to PostgreSQL pipeline completed successfully.")

    except Exception as error:
        print(f"PostgreSQL load failed: {error}")
        raise


if __name__ == "__main__":
    main()
