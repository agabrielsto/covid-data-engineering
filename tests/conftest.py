
import pytest
import duckdb


@pytest.fixture
def duckdb_connection():
    connection = duckdb.connect(":memory:")
    yield connection
    connection.close()


@pytest.fixture
def sample_covid_data(duckdb_connection):
    duckdb_connection.execute("""
        CREATE TABLE covid_data (
            country VARCHAR,
            code VARCHAR,
            continent VARCHAR,
            date DATE,
            total_cases DOUBLE,
            total_deaths DOUBLE,
            population DOUBLE
        )
    """)

    duckdb_connection.execute("""
        INSERT INTO covid_data VALUES
        ('Brazil', 'BRA', 'South America', '2026-10-18', 37000000, 700000, 215000000),
        ('Brazil', 'BRA', 'South America', '2026-10-17', 36900000, 699000, 215000000),
        ('Germany', 'DEU', 'Europe', '2026-10-18', 38000000, 175000, 84000000),
        ('Japan', 'JPN', 'Asia', '2026-10-18', 33000000, 74000, 125000000)
    """)

    return duckdb_connection
