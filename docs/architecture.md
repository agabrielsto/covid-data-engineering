# Arquitetura do Projeto — COVID-19 Data Engineering

## 1. Visão geral

Este projeto implementa um pipeline de Engenharia de Dados (ETL) para ingestão, processamento, transformação e armazenamento de dados relacionados à COVID-19.

O objetivo é construir um fluxo de dados organizado em camadas, utilizando ferramentas de processamento analítico e armazenamento, aplicando boas práticas de Engenharia de Dados.

A fonte de dados utilizada é o **Our World in Data (OWID)**.

## 2. Arquitetura Medallion

O pipeline segue a arquitetura Medallion, dividida em três camadas:

### Bronze — Dados brutos

Responsável pela ingestão e armazenamento dos dados originais.

- Fonte: Our World in Data (OWID).
- Linguagem: Python.
- Armazenamento: SILO (compatível com S3).
- Formato: CSV.
- Objetivo: preservar os dados recebidos da fonte original.

### Silver — Dados tratados

Responsável pela limpeza, padronização e validação dos dados.

- Processamento: DuckDB.
- Linguagem: Python e SQL.
- Formato de saída: Parquet.
- Principais transformações:
  - Conversão de tipos de dados.
  - Tratamento de valores inválidos.
  - Remoção de registros duplicados.
  - Padronização de datas e colunas numéricas.
  - Validação de chaves e registros.

### Gold — Dados analíticos

Responsável pela criação de indicadores preparados para análise.

- Processamento: DuckDB e SQL.
- Formato: Parquet.
- Granularidade: um registro por país.
- Principais indicadores:
  - Total de casos.
  - Total de mortes.
  - População.
  - Casos por milhão de habitantes.
  - Mort