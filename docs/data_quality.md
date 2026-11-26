# Qualidade de Dados — COVID-19 Data Engineering

## 1. Objetivo

Este documento apresenta as regras e verificações de qualidade aplicadas ao pipeline de dados da COVID-19.

O objetivo é garantir que os dados processados sejam consistentes, íntegros e adequados para análises na camada Gold e no PostgreSQL.

## 2. Validações por camada

### Bronze

- Verificação da disponibilidade da fonte OWID.
- Validação da estrutura do arquivo CSV.
- Verificação da presença das colunas obrigatórias `country` e `date`.
- Armazenamento do arquivo original no SILO.

### Silver

- Conversão de datas para o tipo DATE.
- Conversão de colunas numéricas para tipos apropriados.
- Remoção de registros sem país ou data válidos.
- Remoção de duplicidades considerando a combinação `country` e `date`.
- Geração do arquivo Parquet.

### Gold

- Seleção do registro mais recente de cada país.
- Exclusão de registros sem país, código ou continente.
- Cálculo de indicadores por milhão de habitantes.
- Cálculo da taxa de letalidade.
- Prevenção de divisões por zero utilizando `NULLIF`.

### PostgreSQL

- Verificação da quantidade de registros carregados.
- Verificação da unicidade dos códigos dos países.
- Verificação de valores nulos em campos obrigatórios.
- Verificação de valores negativos em casos e mortes.
- Verificação de populações inválidas.

## 3. Resultados da validação

Na execução validada do projeto, foram obtidos os seguintes resultados:

| Verificação | Resultado |
|---|---:|
| Registros na camada Gold | 239 |
| Códigos de países distintos | 239 |
| Países nulos | 0 |
| Códigos nulos | 0 |
| Continentes nulos | 0 |
| Casos negativos | 0 |
| Mortes negativas | 0 |
| Populações inválidas | 0 |

**Período observado na camada Gold:**

- Data mais antiga: 20/04/2022.
- Data mais recente: 18/10/2026.

As datas representam os registros mais recentes disponíveis por país, não necessariamente um intervalo contínuo comum a todos os países.

## 4. Testes automatizados

O projeto utiliza Pytest para validar as principais funcionalidades.

| Arquivo | Quantidade de testes | Objetivo |
|---|---:|---|
| test_silver.py | 4 | Validar limpeza e transformação Silver |
| test_gold.py | 4 | Validar indicadores e regras Gold |
| test_postgres.py | 3 | Validar leitura Parquet e integração PostgreSQL |
| test_s3_connection.py | 1 | Validar conexão com armazenamento S3 |

**Resultado da última execução:**

- Total de testes: 12.
- Testes aprovados: 12.
- Testes reprovados: 0.

## 5. Considerações

As verificações realizadas demonstram que o pipeline atende às regras de qualidade implementadas no projeto.

Os resultados apresentados correspondem à execução validada em 26/11/2026. Novas ingestões ou alterações na fonte podem modificar os indicadores e resultados das verificações.

A qualidade dos dados deve ser monitorada continuamente em futuras execuções do pipeline.
