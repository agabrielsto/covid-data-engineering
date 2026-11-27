# Arquitetura — COVID-19 Data Engineering

## 1. Visão geral

O projeto implementa um pipeline ETL para coletar dados públicos sobre a COVID-19, tratar os registros, gerar indicadores por país e disponibilizar o conjunto analítico em PostgreSQL.

A fonte de dados é o [Our World in Data (OWID)](https://ourworldindata.org/coronavirus). O processamento é organizado em três camadas lógicas — Bronze, Silver e Gold — e utiliza arquivos CSV e Parquet, armazenamento de objetos compatível com S3 e banco de dados relacional.

## 2. Visão do fluxo

```text
Our World in Data (CSV)
        |
        v
Python / requests
        |
        v
Bronze — CSV original
        |
        v
SILO — bucket bronze
        |
        v
Python / Boto3 + DuckDB / SQL
        |
        v
Silver — Parquet tratado
        |
        v
SILO — bucket silver
        |
        v
DuckDB / SQL
        |
        v
Gold — country_indicators.parquet
        |
        v
Python / Psycopg
        |
        v
PostgreSQL — gold.country_indicators
        |
        v
Power BI — consumo analítico planejado
```

## 3. Camadas Medallion

### 3.1 Bronze — ingestão e preservação

**Implementação:** `src/ingestion/ingest_owid.py`

Responsabilidades:

- Baixar o CSV compacto publicado pelo OWID por meio de uma requisição HTTP com timeout.
- Validar a presença das colunas obrigatórias `country` e `date`.
- Salvar uma cópia local em `data/bronze/`.
- Enviar o arquivo original para o bucket `bronze` no SILO.
- Organizar o objeto por data de ingestão, com timestamp no nome do arquivo.

**Formato:** CSV.

**Armazenamento:** SILO, serviço compatível com API S3.

### 3.2 Silver — limpeza e validação

**Implementação:** `src/silver/transform_covid.py`

Responsabilidades:

- Listar os objetos do bucket Bronze e selecionar o CSV mais recentemente modificado.
- Baixar o arquivo selecionado para processamento local.
- Utilizar DuckDB e SQL para converter a data e os campos numéricos.
- Descartar linhas sem país ou data válidos.
- Remover duplicatas integralmente idênticas.
- Interromper a transformação quando houver registros divergentes para a mesma chave `country` + `date`.
- Gerar arquivo Parquet com compressão Zstandard.
- Validar se o resultado não está vazio, se país e data não são nulos e se a chave país/data não está duplicada.
- Enviar o Parquet validado ao bucket `silver`.

**Formato:** Parquet.

**Armazenamento:** local durante o processamento e SILO após validação.

### 3.3 Gold — indicadores por país

**Implementação:** `src/gold/build_country_indicators.py`

Responsabilidades:

- Localizar o arquivo Parquet Silver mais recentemente modificado em `data/silver/`.
- Permitir também que um arquivo Silver seja informado explicitamente pela função.
- Selecionar a observação mais recente de cada país.
- Excluir registros sem país, código ou continente.
- Calcular casos por milhão, mortes por milhão e taxa de letalidade.
- Gerar o arquivo `data/gold/country_indicators.parquet`.

**Granularidade:** uma linha por país selecionado.

**Formato:** Parquet.

### 3.4 PostgreSQL — camada de consumo

**Implementação:** `src/gold/load_gold_postgres.py`

Responsabilidades:

- Ler as colunas esperadas do Parquet Gold.
- Conectar ao PostgreSQL usando as variáveis de ambiente.
- Criar o schema `gold` e a tabela `country_indicators`, caso não existam.
- Substituir os registros existentes e inserir o conjunto atual.
- Retornar a quantidade de linhas carregadas.

**Tabela:** `gold.country_indicators`.

A carga atual utiliza `TRUNCATE` seguido de inserção. Portanto, a tabela representa o conjunto da execução mais recente, e não um histórico de snapshots.

### 3.5 Power BI — visualização

O PostgreSQL é a fonte prevista para conexão com o Power BI. A integração e a construção do dashboard são etapas de evolução do projeto; a documentação não considera o dashboard concluído.

## 4. Serviços e infraestrutura

O arquivo `docker-compose.yml` define os serviços locais:

| Serviço | Imagem | Finalidade |
|---|---|---|
| PostgreSQL | `postgres:16` | Banco relacional analítico |
| SILO | `pgsty/silo` | Armazenamento compatível com S3 |

Os serviços utilizam volumes Docker para persistência. As portas, nomes de banco e credenciais são configurados por variáveis de ambiente no arquivo local `.env`.

Os buckets `bronze` e `silver` precisam existir no SILO antes da execução das respectivas etapas.

## 5. Configuração e execução

1. Instalar as dependências de `requirements.txt`.
2. Criar o arquivo `.env` com base no `.env.example`.
3. Iniciar PostgreSQL e SILO com `docker compose up -d`.
4. Criar os buckets `bronze` e `silver` no SILO, se ainda não existirem.
5. Executar os scripts na sequência:

```powershell
python src/ingestion/ingest_owid.py
python src/silver/transform_covid.py
python src/gold/build_country_indicators.py
python src/gold/load_gold_postgres.py
```

## 6. Qualidade e integração contínua

Os testes automatizados estão em `tests/` e são executados com:

```powershell
python -m pytest -v
```

O workflow `.github/workflows/ci.yml` executa a suíte em Linux e inicializa PostgreSQL e SILO para os testes de integração. Na execução validada associada à branch desta entrega, todos os 17 testes foram aprovados.

As regras de qualidade e o escopo dos testes estão detalhados em [data_quality.md](data_quality.md).

## 7. Observabilidade\n\nOs módulos compartilhados em `src/utils/` fornecem recursos básicos de observabilidade:\n\n- Logs padronizados com timestamp, nível e nome do módulo.\n- Registro de início, conclusão e duração de cada etapa.\n- Registro de exceções com stack trace e propagação do erro para não mascarar falhas.\n- Métricas operacionais de linhas processadas, países gerados e linhas carregadas no PostgreSQL.\n- Verificação de acesso aos buckets Bronze e Silver antes do processamento correspondente.\n\nO nível de log pode ser configurado pela variável opcional `LOG_LEVEL`.\n\n## 8. Decisões e limitações atuais

- O projeto mantém Bronze como cópia do CSV original, enquanto Silver e Gold são produzidos em Parquet.
- A transformação Silver bloqueia conflitos de chave em vez de escolher arbitrariamente um registro.
- A descoberta automática do Silver considera o horário de modificação local do arquivo.
- A camada Gold mantém apenas a observação mais recente por país.
- A carga PostgreSQL substitui o conteúdo da tabela; não existe histórico de cargas nessa tabela.
- O Power BI é a camada de visualização planejada, ainda em desenvolvimento.
- Não há orquestrador de tarefas implementado nesta versão.

## 9. Evoluções planejadas

- Concluir o modelo semântico e o dashboard no Power BI.
- Implementar logging estruturado e métricas por execução.
- Ampliar as verificações de qualidade e consistência entre camadas.
- Avaliar orquestração e agendamento do pipeline.
