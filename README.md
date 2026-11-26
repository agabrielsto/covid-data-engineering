# COVID-19 Data Engineering

Pipeline de Engenharia de Dados desenvolvido em Python para ingestão, processamento, transformação e armazenamento de dados globais da COVID-19, utilizando arquitetura Medallion (Bronze, Silver e Gold).

O projeto utiliza dados do [Our World in Data (OWID)](https://ourworldindata.org/coronavirus) e constrói uma camada analítica preparada para consultas SQL e visualização no Power BI.

## Objetivos

- Desenvolver um pipeline ETL completo.
- Aplicar arquitetura Medallion.
- Praticar processamento de dados com DuckDB e SQL.
- Implementar armazenamento de objetos compatível com S3.
- Construir uma camada analítica em PostgreSQL.
- Aplicar testes automatizados e validações de qualidade.

## Arquitetura

```text
Our World in Data (OWID)
          |
          v
    Python Ingestion
          |
          v
   Bronze — CSV
      (SILO/S3)
          |
          v
   DuckDB Processing
          |
          v
   Silver — Parquet
      (SILO/S3)
          |
          v
   DuckDB + SQL
          |
          v
    Gold — Parquet
          |
          v
    Python + Psycopg
          |
          v
   PostgreSQL
          |
          v
      Power BI
```

## Tecnologias utilizadas

| Tecnologia | Aplicação |
|---|---|
| Python | Desenvolvimento do pipeline ETL |
| SQL | Consultas e transformações |
| DuckDB | Processamento analítico |
| Pandas | Análise exploratória |
| PostgreSQL | Armazenamento analítico |
| Psycopg | Integração Python/PostgreSQL |
| SILO | Armazenamento compatível com S3 |
| Docker | Infraestrutura em containers |
| Pytest | Testes automatizados |
| Power BI | Visualização dos indicadores (próxima etapa) |

## Estrutura do projeto

```text
covid-data-engineering/
│
├── src/
│   ├── ingestion/
│   ├── silver/
│   ├── gold/
│   ├── analysis/
│   └── utils/
│
├── tests/
│   ├── test_gold.py
│   ├── test_postgres.py
│   ├── test_s3_connection.py
│   └── test_silver.py
│
├── sql/
│   ├── 01_create_schema.sql
│   ├── 02_validation_queries.sql
│   └── 03_analysis_queries.sql
│
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   └── data_quality.md
│
├── data/
├── docker/
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Camadas de dados

### Bronze

- Ingestão dos dados do OWID.
- Preservação do arquivo original em CSV.
- Armazenamento no SILO, em bucket compatível com S3.

### Silver

- Leitura e processamento com DuckDB.
- Conversão e padronização de tipos.
- Remoção de duplicidades.
- Tratamento de registros inválidos.
- Armazenamento em Parquet.

### Gold

- Seleção do registro mais recente por país.
- Cálculo de indicadores epidemiológicos.
- Geração de dataset analítico em Parquet.
- Preparação dos dados para consultas e visualização.

## Indicadores analíticos

A camada Gold disponibiliza:

- Total acumulado de casos.
- Total acumulado de mortes.
- População.
- Casos por milhão de habitantes.
- Mortes por milhão de habitantes.
- Taxa de letalidade.

A tabela analítica final é `gold.country_indicators`, armazenada no PostgreSQL.

## Qualidade e testes

O projeto utiliza Pytest para validar as transformações e a integração com os serviços de armazenamento.

**Última execução validada:**

- 12 testes aprovados.
- 0 testes reprovados.
- 239 registros na camada Gold.
- 239 códigos de países distintos.

Para executar os testes:

```bash
python -m pytest -v
```

## Como executar o projeto

### 1. Clonar o repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd covid-data-engineering
```

### 2. Criar ambiente virtual

```bash
python -m venv .venv
```

Ativar no Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto, utilizando `.env.example` como referência.

Configure as credenciais do SILO e PostgreSQL conforme sua infraestrutura local.

### 5. Inicializar os serviços

```bash
docker compose up -d
```

### 6. Executar o pipeline

Execute os scripts na seguinte ordem:

```bash
python src/ingestion/ingest_owid.py
python src/silver/transform_covid.py
python src/gold/build_country_indicators.py
python src/gold/load_gold_postgres.py
```

### 7. Executar os testes

```bash
python -m pytest -v
```

## Documentação

Documentação técnica disponível em `docs/`:

- [Arquitetura](docs/architecture.md)
- [Dicionário de dados](docs/data_dictionary.md)
- [Qualidade dos dados](docs/data_quality.md)

Consultas SQL disponíveis em `sql/`.

## Próximas evoluções

- Construção de dashboard interativo no Power BI.
- Aprimoramento do monitoramento e logging.
- Ampliação das validações de qualidade.
- Implementação futura de orquestração automatizada.

---

**Projeto desenvolvido para fins de aprendizado e portfólio em Engenharia de Dados.**