import pytest
from src.silver.transform_covid import transform_data, validate_silver_data


def test_silver_creates_parquet_file(tmp_path):
    source_file = tmp_path / "bronze.csv"
    target_file = tmp_path / "silver.parquet"

    columns = [
        "country", "date", "total_cases", "new_cases",
        "new_cases_smoothed", "total_cases_per_million",
        "new_cases_per_million", "new_cases_smoothed_per_million",
        "total_deaths", "new_deaths", "new_deaths_smoothed",
        "total_deaths_per_million", "new_deaths_per_million",
        "new_deaths_smoothed_per_million", "excess_mortality",
        "excess_mortality_cumulative",
        "excess_mortality_cumulative_absolute",
        "excess_mortality_cumulative_per_million",
        "hosp_patients", "hosp_patients_per_million",
        "weekly_hosp_admissions",
        "weekly_hosp_admissions_per_million",
        "icu_patients", "icu_patients_per_million",
        "weekly_icu_admissions",
        "weekly_icu_admissions_per_million",
        "stringency_index", "reproduction_rate",
        "total_tests", "new_tests", "total_tests_per_thousand",
        "new_tests_per_thousand", "new_tests_smoothed",
        "new_tests_smoothed_per_thousand", "positive_rate",
        "tests_per_case", "total_vaccinations",
        "people_vaccinated", "people_fully_vaccinated",
        "total_boosters", "new_vaccinations",
        "new_vaccinations_smoothed",
        "total_vaccinations_per_hundred",
        "people_vaccinated_per_hundred",
        "people_fully_vaccinated_per_hundred",
        "total_boosters_per_hundred",
        "new_vaccinations_smoothed_per_million",
        "new_people_vaccinated_smoothed",
        "new_people_vaccinated_smoothed_per_hundred",
        "population", "population_density", "median_age",
        "life_expectancy", "gdp_per_capita", "extreme_poverty",
        "diabetes_prevalence", "handwashing_facilities",
        "hospital_beds_per_thousand", "human_development_index"
    ]

    values = {
        "country": "Brazil",
        "date": "2026-10-18",
        "total_cases": "37000000",
        "total_deaths": "700000",
        "population": "215000000"
    }

    source_file.write_text(
        ",".join(columns) + "\n"
        + ",".join(values.get(column, "") for column in columns)
        + "\n",
        encoding="utf-8"
    )

    rows = transform_data(source_file, target_file)

    assert target_file.exists()
    assert rows == 1

def test_silver_converts_numeric_and_date_types(tmp_path):
    import duckdb

    source_file = tmp_path / "bronze.csv"
    target_file = tmp_path / "silver.parquet"

    columns = [
        "country", "date", "total_cases", "total_deaths", "population"
    ]

    source_file.write_text(
        ",".join(columns) + "\n"
        "Brazil,2026-10-18,37000000,700000,215000000\n",
        encoding="utf-8"
    )

    # Complete the CSV schema expected by the Silver transformation.
    all_columns = [
        "country", "date", "total_cases", "new_cases",
        "new_cases_smoothed", "total_cases_per_million",
        "new_cases_per_million", "new_cases_smoothed_per_million",
        "total_deaths", "new_deaths", "new_deaths_smoothed",
        "total_deaths_per_million", "new_deaths_per_million",
        "new_deaths_smoothed_per_million", "excess_mortality",
        "excess_mortality_cumulative",
        "excess_mortality_cumulative_absolute",
        "excess_mortality_cumulative_per_million",
        "hosp_patients", "hosp_patients_per_million",
        "weekly_hosp_admissions",
        "weekly_hosp_admissions_per_million",
        "icu_patients", "icu_patients_per_million",
        "weekly_icu_admissions",
        "weekly_icu_admissions_per_million",
        "stringency_index", "reproduction_rate",
        "total_tests", "new_tests", "total_tests_per_thousand",
        "new_tests_per_thousand", "new_tests_smoothed",
        "new_tests_smoothed_per_thousand", "positive_rate",
        "tests_per_case", "total_vaccinations",
        "people_vaccinated", "people_fully_vaccinated",
        "total_boosters", "new_vaccinations",
        "new_vaccinations_smoothed",
        "total_vaccinations_per_hundred",
        "people_vaccinated_per_hundred",
        "people_fully_vaccinated_per_hundred",
        "total_boosters_per_hundred",
        "new_vaccinations_smoothed_per_million",
        "new_people_vaccinated_smoothed",
        "new_people_vaccinated_smoothed_per_hundred",
        "population", "population_density", "median_age",
        "life_expectancy", "gdp_per_capita", "extreme_poverty",
        "diabetes_prevalence", "handwashing_facilities",
        "hospital_beds_per_thousand", "human_development_index"
    ]

    values = {
        "country": "Brazil",
        "date": "2026-10-18",
        "total_cases": "37000000",
        "total_deaths": "700000",
        "population": "215000000"
    }

    source_file.write_text(
        ",".join(all_columns) + "\n"
        + ",".join(values.get(column, "") for column in all_columns)
        + "\n",
        encoding="utf-8"
    )

    transform_data(source_file, target_file)

    with duckdb.connect() as connection:
        result = connection.execute(
            """
            SELECT
                typeof(date),
                typeof(total_cases),
                typeof(total_deaths),
                typeof(population)
            FROM read_parquet(?)
            """,
            [str(target_file)]
        ).fetchone()

    assert result == ("DATE", "DOUBLE", "DOUBLE", "DOUBLE")

def test_silver_removes_duplicate_country_date(tmp_path):
    source_file = tmp_path / "bronze.csv"
    target_file = tmp_path / "silver.parquet"

    columns = [
        "country", "date", "total_cases", "total_deaths", "population"
    ]

    rows = [
        "Brazil,2026-10-18,37000000,700000,215000000",
        "Brazil,2026-10-18,37000000,700000,215000000",
        "Germany,2026-10-18,38000000,175000,84000000"
    ]

    all_columns = [
        "country", "date", "total_cases", "new_cases",
        "new_cases_smoothed", "total_cases_per_million",
        "new_cases_per_million", "new_cases_smoothed_per_million",
        "total_deaths", "new_deaths", "new_deaths_smoothed",
        "total_deaths_per_million", "new_deaths_per_million",
        "new_deaths_smoothed_per_million", "excess_mortality",
        "excess_mortality_cumulative",
        "excess_mortality_cumulative_absolute",
        "excess_mortality_cumulative_per_million",
        "hosp_patients", "hosp_patients_per_million",
        "weekly_hosp_admissions",
        "weekly_hosp_admissions_per_million",
        "icu_patients", "icu_patients_per_million",
        "weekly_icu_admissions",
        "weekly_icu_admissions_per_million",
        "stringency_index", "reproduction_rate",
        "total_tests", "new_tests", "total_tests_per_thousand",
        "new_tests_per_thousand", "new_tests_smoothed",
        "new_tests_smoothed_per_thousand", "positive_rate",
        "tests_per_case", "total_vaccinations",
        "people_vaccinated", "people_fully_vaccinated",
        "total_boosters", "new_vaccinations",
        "new_vaccinations_smoothed",
        "total_vaccinations_per_hundred",
        "people_vaccinated_per_hundred",
        "people_fully_vaccinated_per_hundred",
        "total_boosters_per_hundred",
        "new_vaccinations_smoothed_per_million",
        "new_people_vaccinated_smoothed",
        "new_people_vaccinated_smoothed_per_hundred",
        "population", "population_density", "median_age",
        "life_expectancy", "gdp_per_capita", "extreme_poverty",
        "diabetes_prevalence", "handwashing_facilities",
        "hospital_beds_per_thousand", "human_development_index"
    ]

    source_file.write_text(
        ",".join(all_columns) + "\n"
        + "\n".join(
            ",".join(
                dict(zip(columns, row.split(","))).get(column, "")
                for column in all_columns
            )
            for row in rows
        )
        + "\n",
        encoding="utf-8"
    )

    total_rows = transform_data(source_file, target_file)

    assert total_rows == 2


def test_silver_blocks_conflicting_country_date_records(tmp_path):
    source_file = tmp_path / "bronze.csv"
    target_file = tmp_path / "silver.parquet"

    columns = [
        "country", "date", "total_cases", "total_deaths", "population"
    ]

    rows = [
        "Brazil,2026-10-18,37000000,700000,215000000",
        "Brazil,2026-10-18,36999999,699999,215000000",
        "Germany,2026-10-18,38000000,175000,84000000"
    ]

    all_columns = [
        "country", "date", "total_cases", "new_cases",
        "new_cases_smoothed", "total_cases_per_million",
        "new_cases_per_million", "new_cases_smoothed_per_million",
        "total_deaths", "new_deaths", "new_deaths_smoothed",
        "total_deaths_per_million", "new_deaths_per_million",
        "new_deaths_smoothed_per_million", "excess_mortality",
        "excess_mortality_cumulative",
        "excess_mortality_cumulative_absolute",
        "excess_mortality_cumulative_per_million",
        "hosp_patients", "hosp_patients_per_million",
        "weekly_hosp_admissions",
        "weekly_hosp_admissions_per_million",
        "icu_patients", "icu_patients_per_million",
        "weekly_icu_admissions",
        "weekly_icu_admissions_per_million",
        "stringency_index", "reproduction_rate",
        "total_tests", "new_tests", "total_tests_per_thousand",
        "new_tests_per_thousand", "new_tests_smoothed",
        "new_tests_smoothed_per_thousand", "positive_rate",
        "tests_per_case", "total_vaccinations",
        "people_vaccinated", "people_fully_vaccinated",
        "total_boosters", "new_vaccinations",
        "new_vaccinations_smoothed",
        "total_vaccinations_per_hundred",
        "people_vaccinated_per_hundred",
        "people_fully_vaccinated_per_hundred",
        "total_boosters_per_hundred",
        "new_vaccinations_smoothed_per_million",
        "new_people_vaccinated_smoothed",
        "new_people_vaccinated_smoothed_per_hundred",
        "population", "population_density", "median_age",
        "life_expectancy", "gdp_per_capita", "extreme_poverty",
        "diabetes_prevalence", "handwashing_facilities",
        "hospital_beds_per_thousand", "human_development_index"
    ]

    source_file.write_text(
        ",".join(all_columns) + "\n"
        + "\n".join(
            ",".join(
                dict(zip(columns, row.split(","))).get(column, "")
                for column in all_columns
            )
            for row in rows
        )
        + "\n",
        encoding="utf-8"
    )

    with pytest.raises(ValueError, match="Conflicting records found"):
        transform_data(source_file, target_file)

    assert not target_file.exists()

def test_silver_removes_invalid_records(tmp_path):
    source_file = tmp_path / "bronze.csv"
    target_file = tmp_path / "silver.parquet"

    columns = [
        "country", "date", "total_cases", "total_deaths", "population"
    ]

    rows = [
        "Brazil,2026-10-18,37000000,700000,215000000",
        ",2026-10-18,1000,10,10000",
        "Germany,invalid-date,38000000,175000,84000000"
    ]

    all_columns = [
        "country", "date", "total_cases", "new_cases",
        "new_cases_smoothed", "total_cases_per_million",
        "new_cases_per_million", "new_cases_smoothed_per_million",
        "total_deaths", "new_deaths", "new_deaths_smoothed",
        "total_deaths_per_million", "new_deaths_per_million",
        "new_deaths_smoothed_per_million", "excess_mortality",
        "excess_mortality_cumulative",
        "excess_mortality_cumulative_absolute",
        "excess_mortality_cumulative_per_million",
        "hosp_patients", "hosp_patients_per_million",
        "weekly_hosp_admissions",
        "weekly_hosp_admissions_per_million",
        "icu_patients", "icu_patients_per_million",
        "weekly_icu_admissions",
        "weekly_icu_admissions_per_million",
        "stringency_index", "reproduction_rate",
        "total_tests", "new_tests", "total_tests_per_thousand",
        "new_tests_per_thousand", "new_tests_smoothed",
        "new_tests_smoothed_per_thousand", "positive_rate",
        "tests_per_case", "total_vaccinations",
        "people_vaccinated", "people_fully_vaccinated",
        "total_boosters", "new_vaccinations",
        "new_vaccinations_smoothed",
        "total_vaccinations_per_hundred",
        "people_vaccinated_per_hundred",
        "people_fully_vaccinated_per_hundred",
        "total_boosters_per_hundred",
        "new_vaccinations_smoothed_per_million",
        "new_people_vaccinated_smoothed",
        "new_people_vaccinated_smoothed_per_hundred",
        "population", "population_density", "median_age",
        "life_expectancy", "gdp_per_capita", "extreme_poverty",
        "diabetes_prevalence", "handwashing_facilities",
        "hospital_beds_per_thousand", "human_development_index"
    ]

    source_file.write_text(
        ",".join(all_columns) + "\n"
        + "\n".join(
            ",".join(
                dict(zip(columns, row.split(","))).get(column, "")
                for column in all_columns
            )
            for row in rows
        )
        + "\n",
        encoding="utf-8"
    )

    total_rows = transform_data(source_file, target_file)

    assert total_rows == 1

def test_silver_validation_returns_metrics(tmp_path):
    import duckdb

    parquet_file = tmp_path / "silver.parquet"

    with duckdb.connect() as connection:
        connection.execute(
            """
            COPY (
                SELECT
                    'Brazil' AS country,
                    DATE '2026-10-18' AS date
            )
            TO '{parquet_file.as_posix()}'
            (FORMAT PARQUET)
            """
        )

    metrics = validate_silver_data(parquet_file)

    assert metrics["total_rows"] == 1
    assert metrics["total_countries"] == 1
    assert metrics["null_countries"] == 0
    assert metrics["null_dates"] == 0
    assert metrics["duplicate_keys"] == 0


def test_silver_validation_rejects_empty_dataset(tmp_path):
    import duckdb

    parquet_file = tmp_path / "empty.parquet"

    with duckdb.connect() as connection:
        connection.execute(
            """
            COPY (
                SELECT
                    CAST(NULL AS VARCHAR) AS country,
                    CAST(NULL AS DATE) AS date
                WHERE FALSE
            )
            TO ?
            (FORMAT PARQUET)
            """,
            [str(parquet_file)],
        )

    with pytest.raises(ValueError, match="dataset is empty"):
        validate_silver_data(parquet_file)
