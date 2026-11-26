# Dicionário de Dados — COVID-19 Data Engineering

## 1. Visão geral

Este documento descreve as colunas disponíveis na tabela analítica `gold.country_indicators`, construída a partir dos dados tratados na camada Silver.

A tabela possui granularidade de um registro por país, considerando o registro mais recente disponível para cada país.

**Formato de armazenamento:** Parquet e PostgreSQL.

**Schema PostgreSQL:** `gold`

**Tabela:** `country_indicators`

## 2. Estrutura dos dados

| Coluna | Tipo | Descrição |
|---|---|---|
| country | VARCHAR | Nome do país ou território. |
| code | VARCHAR | Código identificador do país. Utilizado como chave primária. |
| continent | VARCHAR | Continente ao qual o país pertence. |
| last_updated | DATE | Data do último registro disponível para o país. |
| total_cases | DOUBLE PRECISION | Total acumulado de casos confirmados de COVID-19. |
| total_deaths | DOUBLE PRECISION | Total acumulado de mortes atribuídas à COVID-19. |
| population | DOUBLE PRECISION | População utilizada como referência nos indicadores. |
| cases_per_million | DOUBLE PRECISION | Casos acumulados por milhão de habitantes. |
| deaths_per_million | DOUBLE PRECISION | Mortes acumuladas por milhão de habitantes. |
| fatality_rate | DOUBLE PRECISION | Percentual de mortes em relação ao total de casos. |

## 3. Indicadores calculados

### Casos por milhão de habitantes

Representa a quantidade acumulada de casos para cada milhão de habitantes.

**Fórmula:**

`(total_cases / population) * 1.000.000`

### Mortes por milhão de habitantes

Representa a quantidade acumulada de mortes para cada milhão de habitantes.

**Fórmula:**

`(total_deaths / population) * 1.000.000`

### Taxa de letalidade

Representa o percentual de mortes em relação ao total de casos confirmados.

**Fórmula:**

`(total_deaths / total_cases) * 100`

Quando o denominador é zero, o indicador retorna NULL para evitar divisão por zero.

## 4. Regras de negócio

- Cada país possui apenas um registro na camada Gold.
- É selecionado o registro mais recente disponível por país.
- Registros sem país, código ou continente são excluídos.
- Divisões por zero são tratadas utilizando `NULLIF`.
- Os indicadores são calculados com base nos valores acumulados disponíveis na fonte.

## 5. Observações analíticas

- Os totais de casos e mortes representam valores acumulados, não casos ativos.
- Indicadores por milhão permitem comparações considerando diferenças populacionais.
- A taxa de letalidade não representa necessariamente o risco individual de morte.
- Valores nulos indicam ausência de informação ou impossibilidade de cálculo; não devem ser interpretados automaticamente como zero.
- Os dados refletem a última atualização disponível para cada país, podendo existir diferenças entre as datas de referência.
