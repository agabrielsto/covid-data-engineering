# COVID-19 Data Engineering

Pipeline de Engenharia de Dados desenvolvido em Python para ingestão, processamento, transformação e disponibilização de dados globais sobre a COVID-19. O projeto utiliza a arquitetura Medallion (Bronze, Silver e Gold), com dados do [Our World in Data (OWID)](https://ourworldindata.org/coronavirus).

O objetivo é demonstrar um fluxo ETL completo, boas práticas de qualidade de dados, armazenamento em objeto compatível com S3, processamento analítico e integração com PostgreSQL. A conexão com o Power BI faz parte da etapa de visualização do projeto.

## Arquitetura

```text
Our World in Data (OWID)
          |
          v
Python — ingestão
          |
          v
Bronze — CSV original
          |
          v
SILO (armazenamento compatível com S3)
          |
          v
DuckDB + SQL — limpeza e validação
          |
          v
Silver — Parquet
          |
          v
DuckDB + SQL — indicadores por país
          |
          v
Gold — Parquet
          |
          v
Python + Psycopg
          |
          v
PostgreSQL — gold.country_indicators
          |
          v
Power BI — camada de visualização
```

## Tecnologias

| Tecnologia | Utilização |
|---|---|
| Python | Ingestão, transformação e integração |
| SQL | Consultas e regras de transformação |
| DuckDB | Processamento analítico e geração de Parquet |
| Pandas | Análise exploratória |
| Parquet | Armazenamento colunar |
| SILO | Armazenamento de objetos compatível com S3 |
| Boto3 | Comunicação com a API S3 |
| PostgreSQL | Armazenamento da camada analítica |
| Psycopg | Conexão Python/PostgreSQL |
| Docker Compose | Execução dos serviços PostgreSQL e SILO |
| Pytest | Testes automatizados |
| GitHub Actions | Integração contínua |
| Power BI | Visualização dos indicadores (etapa de integração) |

## Estrutura do repositório

```text
covid-data-engineering/
├── .github/
│   └── workflows/
│       └── ci.yml
├── data/                  # Dados locais (não versionados)
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   └── data_quality.md
├── scripts/
│   └── inspect_silver.py
├── sql/
│   ├── 01_create_schema.sql
│   ├── 02_validation_queries.sql
│   └── 03_analysis_queries.sql
├── src/
│   ├── analysis/
│   ├── gold/
│   ├── ingestion/
│   └── silver/
├── tests/
│   ├── conftest.py
│   ├── test_gold.py
│   ├── test_postgres.py
│   ├── test_s3_connection.py
│   └── test_silver.py
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Fluxo de dados

### 1. Bronze — ingestão

O script `src/ingestion/ingest_owid.py`:

- Baixa o CSV compacto disponibilizado pelo OWID.
- Confere a presença das colunas obrigatórias `country` e `date`.
- Salva uma cópia local em `data/bronze/`.
- Envia o arquivo original para o bucket `bronze` no armazenamento S3.

### 2. Silver — tratamento

O script `src/silver/transform_covid.py`:

- Localiza o objeto CSV mais recente na camada Bronze.
- Faz o download para processamento local.
- Utiliza DuckDB e SQL para converter datas e campos numéricos.
- Descarta registros sem país ou data válidos.
- Remove apenas duplicatas integralmente idênticas.
- Interrompe a transformação quando encontra registros diferentes para a mesma chave `country` + `date`.
- Gera um arquivo Parquet e valida campos obrigatórios e unicidade da chave antes do upload para o bucket `silver`.

### 3. Gold — indicadores

O script `src/gold/build_country_indicators.py`:

- Identifica o arquivo Parquet Silver mais recentemente modificado.
- Seleciona o registro mais recente de cada país.
- Calcula indicadores por milhão de habitantes e taxa de letalidade.
- Gera `data/gold/country_indicators.parquet`.

### 4. PostgreSQL — disponibilização analítica

O script `src/gold/load_gold_postgres.py` lê o Parquet Gold e carrega os registros na tabela `gold.country_indicators`. A conexão utiliza as variáveis de ambiente definidas no arquivo `.env`.

### 5. Power BI — visualização

O PostgreSQL é a fonte planejada para o modelo analítico no Power BI. A construção e finalização do dashboard são etapas de evolução do projeto; não são apresentadas aqui como concluídas.

## Indicadores da camada Gold

A tabela `gold.country_indicators` contém um registro por país, considerando a observação mais recente disponível:

| Campo | Descrição |
|---|---|
| `country` | País ou território |
| `code` | Código do país |
| `continent` | Continente |
| `last_updated` | Data da observação selecionada |
| `total_cases` | Total acumulado de casos |
| `total_deaths` | Total acumulado de mortes |
| `population` | População de referência |
| `cases_per_million` | Casos por milhão de habitantes |
| `deaths_per_million` | Mortes por milhão de habitantes |
| `fatality_rate` | Mortes como percentual dos casos |

Consulte o [dicionário de dados](docs/data_dictionary.md) para definições e fórmulas.

## Como executar localmente

### Pré-requisitos

- Git
- Python 3.14
- Docker Desktop com Docker Compose
- Acesso à internet para obter os dados do OWID

### 1. Clonar o repositório

```powershell
git clone https://github.com/agabrielsto/covid-data-engineering.git
cd covid-data-engineering
```

### 2. Criar e ativar o ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar dependências

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar as variáveis de ambiente

Crie o arquivo `.env` a partir do modelo:

```powershell
Copy-Item .env.example .env
```

Edite o `.env` com credenciais locais. Não compartilhe nem versione esse arquivo. O `.env.example` contém apenas valores ilustrativos.

### 5. Iniciar PostgreSQL e SILO

```powershell
docker compose up -d
docker compose ps
```

O PostgreSQL fica disponível na porta definida em `PG_PORT`. O endpoint S3 do SILO utiliza a porta 9000 e o console web utiliza a porta 9001.

Antes da ingestão, crie no console do SILO os buckets `bronze` e `silver`, usando as credenciais configuradas no `.env`.

### 6. Executar as etapas do pipeline

Execute os comandos na ordem:

```powershell
python -m src.ingestion.ingest_owid
python -m src.silver.transform_covid
python -m src.gold.build_country_indicators
python -m src.gold.load_gold_postgres
```

Cada etapa depende dos artefatos gerados pela etapa anterior. A ingestão e a transformação Silver também dependem dos buckets S3 estarem disponíveis.

### 7. Executar os testes

```powershell
python -m pytest -v
```

Os testes de integração com PostgreSQL e S3 precisam dos serviços e das variáveis de ambiente correspondentes. A integração contínua executa a suíte em Linux com PostgreSQL e SILO inicializados como serviços.

## Observabilidade\n\nO módulo `src/utils/observability.py` padroniza logs com data/hora, nível e nome do módulo. Cada etapa registra início, conclusão, duração em segundos e exceções com rastreamento. As etapas também registram métricas operacionais, como quantidade de linhas processadas ou carregadas.\n\nO módulo `src/utils/s3.py` verifica a disponibilidade e o acesso aos buckets necessários antes da ingestão e transformação Silver. O nível de log pode ser ajustado pela variável opcional `LOG_LEVEL` (por exemplo, `INFO` ou `DEBUG`).\n\nOs scripts devem ser executados como módulos (`python -m ...`) a partir da raiz do repositório para manter os imports do pacote `src` consistentes.\n\n## Testes e integração contínua

A suíte automatizada é executada pelo Pytest. No estado atual da branch de desenvolvimento, a execução completa validada no GitHub Actions apresentou:

- **17 testes aprovados**
- **0 falhas**
- Serviços PostgreSQL e SILO inicializados com sucesso
- Etapa de testes concluída com sucesso

O workflow está em `.github/workflows/ci.yml` e é executado em pushes para `master` e branches `feature/**`, além de pull requests direcionados à `master`.

## Documentação adicional

- [Arquitetura técnica](docs/architecture.md)
- [Dicionário de dados](docs/data_dictionary.md)
- [Regras e validações de qualidade](docs/data_quality.md)
- [Consultas SQL](sql/)

## Próximas evoluções

- Concluir o modelo e o dashboard no Power BI.
- Expandir testes de qualidade e integração.
- Melhorar logging, observabilidade e tratamento de falhas.
- Avaliar uma ferramenta de orquestração para agendamento do pipeline.

---

Projeto de portfólio desenvolvido para praticar e demonstrar competências em Engenharia de Dados.
