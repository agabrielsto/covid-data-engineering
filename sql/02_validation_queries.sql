
-- Total de registros
SELECT COUNT(*) AS total_records
FROM gold.country_indicators;

-- Verificar códigos duplicados
SELECT
    code,
    COUNT(*) AS occurrences
FROM gold.country_indicators
GROUP BY code
HAVING COUNT(*) > 1;

-- Verificar valores ausentes
SELECT
    COUNT(*) FILTER (WHERE total_cases IS NULL) AS missing_cases,
    COUNT(*) FILTER (WHERE total_deaths IS NULL) AS missing_deaths,
    COUNT(*) FILTER (WHERE population IS NULL) AS missing_population
FROM gold.country_indicators;
