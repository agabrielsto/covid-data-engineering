# Qualidade de Dados — COVID-19 Data Engineering

## 1. Objetivo

Este documento registra as regras de qualidade implementadas no pipeline e os testes automatizados utilizados para verificar suas principais etapas. Os resultados de execução devem ser interpretados como uma evidência pontual: novas ingestões podem alterar os dados e as métricas.

## 2. Regras por camada

### Bronze — ingestão

O processo de ingestão:

- Verifica se a requisição HTTP foi concluída com sucesso.
- Confere a presença das colunas obrigatórias `country` e `date` no CSV.
- Interrompe o processo se a estrutura mínima esperada não estiver presente.
- Armazena o arquivo original no bucket Bronze, preservando o CSV de origem.

### Silver — tratamento

A transformação aplica as seguintes regras:

- Converte `date` para DATE e campos numéricos para DOUBLE usando conversões tolerantes (`TRY_CAST`).
- Remove linhas sem `country` ou `date` válidos.
- Identifica duplicatas pela chave lógica `country` + `date`.
- Remove registros somente quando todas as colunas são idênticas.
- Interrompe a transformação se a mesma chave país/data possuir registros com valores divergentes.
- Valida se o Parquet gerado não está vazio e se não há chaves duplicadas ou valores nulos de país/data.
- Faz o upload para o bucket Silver somente após a transformação e a validação.

### Gold — indicadores

A construção da camada Gold:

- Seleciona a observação mais recente por país.
- Exclui registros sem país, código ou continente.
- Calcula casos e mortes por milhão de habitantes.
- Calcula a taxa de letalidade.
- Utiliza `NULLIF` para evitar divisão por zero.

### PostgreSQL

A carga:

- Cria o schema e a tabela quando ainda não existem.
- Define o código do país como chave primária.
- Define país e continente como campos obrigatórios.
- Substitui o conteúdo anterior da tabela com `TRUNCATE` antes de inserir o novo conjunto.
- Retorna a quantidade de registros carregados.

O teste de integração verifica a carga em uma tabela de teste e consulta um registro inserido. Ele não substitui uma auditoria completa de todas as regras de negócio no banco.

## 3. Testes automatizados

O projeto utiliza Pytest. Os testes estão organizados por etapa:

| Arquivo | Escopo |
|---|---|
| `tests/test_silver.py` | Transformação, duplicatas, conflitos e validação Silver |
| `tests/test_gold.py` | Geração Gold e descoberta do arquivo Silver |
| `tests/test_postgres.py` | Leitura do Parquet e integração com PostgreSQL |
| `tests/test_s3_connection.py` | Conectividade com o armazenamento compatível com S3 |

### Resultado validado

Na execução completa do GitHub Actions associada à branch `feature/pipeline-stability-step-1`:

- **17 testes aprovados**
- **0 testes reprovados**
- Inicialização do PostgreSQL aprovada
- Inicialização e verificação de disponibilidade do SILO aprovadas

O workflow está definido em `.github/workflows/ci.yml`. A execução é feita em ambiente Linux, com os serviços de integração iniciados pelo próprio workflow.

Para executar os testes localmente:

```powershell
python -m pytest -v
```

Os testes que dependem de PostgreSQL ou S3 exigem serviços ativos e variáveis de ambiente válidas. Se essas dependências não estiverem configuradas, o teste de integração PostgreSQL poderá ser ignorado conforme a configuração do teste.

## 4. Limitações e próximos controles

As validações atuais cobrem as regras explicitamente descritas acima, mas não representam uma garantia completa de qualidade estatística ou epidemiológica dos dados.

Evoluções recomendadas:

- Validar faixas plausíveis para indicadores e população.
- Monitorar variações abruptas na quantidade de registros por execução.
- Registrar métricas de qualidade por data de processamento.
- Validar a presença e acessibilidade dos buckets esperados antes da ingestão.
- Ampliar a verificação de consistência entre Parquet Gold e PostgreSQL.
