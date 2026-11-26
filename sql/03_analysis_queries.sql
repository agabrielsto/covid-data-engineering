
-- Top 10 países por número de mortes
SELECT
    country,
    continent,
    total_deaths
FROM gold.country_indicators
WHERE total_deaths IS NOT NULL
ORDER BY total_deaths DESC
LIMIT 10;

-- Indicadores por continente
SELECT
    continent,
    COUNT(*) AS countries,
    SUM(total_cases) AS total_cases,
    SUM(total_deaths) AS total_deaths,
    AVG(cases_per_million) AS avg_cases_per_million,
    AVG(deaths_per_million) AS avg_deaths_per_million
FROM gold.country_indicators
GROUP BY continent
ORDER BY total_deaths DESC NULLS LAST;

-- Países com maior taxa de letalidade
SELECT
    country,
    continent,
    fatality_rate
FROM gold.country_indicators
WHERE fatality_rate IS NOT NULL
ORDER BY fatality_rate DESC
LIMIT 10;
