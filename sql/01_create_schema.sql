
CREATE SCHEMA IF NOT EXISTS gold;

CREATE TABLE IF NOT EXISTS gold.country_indicators (
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
);
