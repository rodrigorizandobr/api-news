---
description: "Use when writing, reviewing, or modifying BigQuery queries, SQL adapters, cost analysis, or BigQuery schema changes. Enforces query cost limits and partition pruning rules."
applyTo: "api/**/*.py"
---
# BigQuery Rules

## ⛔ CUSTO MÁXIMO POR QUERY: $0.005 (0,5 centavo)

**Nenhuma query pode ser proposta, gerada ou deployed sem validar o custo estimado.**

- Pricing: $6,25 por TB processado (BigQuery on-demand, us-central1)
- Limite: 800 MB por query → ≤ $0.005
- Se o dry-run retornar > 800 MB, a query está **BLOQUEADA** — refatore antes de prosseguir.

---

## Partition Pruning — OBRIGATÓRIO

A tabela `gdelt-bq.gdeltv2.gkg_partitioned` é particionada por `_PARTITIONTIME` (não pela coluna `DATE`).

**SEMPRE** incluir como **primeiro filtro** do WHERE:

```sql
_PARTITIONTIME = TIMESTAMP('YYYY-MM-DD')
```

### Por que `DATE` não funciona?
- `DATE` é um campo INTEGER no formato `YYYYMMDDHHMMSS`
- `SUBSTR(CAST(DATE AS STRING),1,8)` força full table scan (~4 TB = $25,66/query)
- `_PARTITIONTIME` é a coluna de partição real — lê apenas 1 dia (~800 MB = $0,005/query)

### Template obrigatório de query:

```sql
SELECT <campos>
FROM `gdelt-bq.gdeltv2.gkg_partitioned`
WHERE
  _PARTITIONTIME = TIMESTAMP('{YYYY-MM-DD}')          -- partition pruning PRIMEIRO
  AND SUBSTR(CAST(DATE AS STRING), 1, 8) = '{YYYYMMDD}' -- filtro intra-dia secundário
  AND <demais filtros>
LIMIT <n>
```

---

## Checklist antes de qualquer mudança de query

1. `--dry_run` executado e bytes processados < 800 MB?
2. `_PARTITIONTIME = TIMESTAMP(...)` está como primeiro filtro do WHERE?
3. Nenhum `SUBSTR(CAST(DATE AS STRING))` como único filtro de data?
4. Cache key versionada (ex: `artlist-v5`) para invalidar resultados antigos?
5. Testes atualizados para verificar `_partitiontime` no SQL gerado?

---

## Validação de custo via dry-run

Sempre rodar antes de deploy:

```bash
bq query --dry_run --nouse_legacy_sql '<SQL>'
```

Calcular custo:

```
bytes / 1_099_511_627_776 * 6.25 = USD
```

Se resultado > $0.005 → **NÃO FAZER DEPLOY**. Refatorar a query.

---

## Padrões proibidos

| Padrão | Motivo | Alternativa |
|--------|--------|-------------|
| `WHERE SUBSTR(CAST(DATE AS STRING),1,8) = '...'` sem `_PARTITIONTIME` | Full scan ~4 TB | Adicionar `_PARTITIONTIME` antes |
| `WHERE DATE > 20260101` | Não usa partition column | `_PARTITIONTIME >= TIMESTAMP('2026-01-01')` |
| `SELECT *` | Lê todas as colunas, aumenta custo | Listar colunas explicitamente |
| `LIKE '%palavra%'` sem filtro de partição | Full scan | Sempre combinar com `_PARTITIONTIME` |

---

## Referência de custo

| Cenário | Bytes | Custo/query |
|---------|-------|-------------|
| Sem partition pruning (full scan) | ~4.1 TB | ~$25,66 ❌ |
| Com `_PARTITIONTIME` (1 dia) | ~800 MB | ~$0,005 ✅ |
| Com cache hit (Firestore) | 0 | ~$0,00003 ✅ |
| 1.000 queries/mês sem cache | — | ~$4,98 ✅ |
