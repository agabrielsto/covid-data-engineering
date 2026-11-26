from pathlib import Path

import duckdb


file_path = Path(
    "data/silver/owid_covid_silver_20261125T180528Z.parquet"
).resolve()

with duckdb.connect() as connection:
    columns = connection.execute(
        """
        DESCRIBE
        SELECT *
        FROM read_parquet(?)
        """,
        [str(file_path)],
    ).fetchall()

print("Silver dataset schema:")

for column in columns:
    print(f"{column[0]}: {column[1]}")