# News Data Sources: GDELT API vs BigQuery

## Overview

The API supports two data sources for searching GDELT news articles:

### 1. **GDELT API (Default)**
- **File**: `api/app/gdelt_adapter.py`
- **Endpoint**: `https://api.gdeltproject.org/api/v2/doc/doc`
- **Cost**: Free (no per-query charges)
- **Latency**: 30 seconds per query (configured timeout)
- **Max records**: 50 per query
- **Best for**: Real-time queries, ad-hoc searches, low volume

**Query format**:
```
(keyword1 OR keyword2) AND sourcelang:pt AND sourcecountry:BR
```

---

### 2. **BigQuery GDELT Dataset**
- **File**: `api/app/bigquery_adapter.py`
- **Dataset**: `gdelt_full.events_articles`
- **Cost**: ~$6 per 1TB scanned (~$0.60 per full table scan)
- **Latency**: 5-15 seconds per query
- **Max records**: Configurable (up to millions)
- **Best for**: Batch processing, historical analysis, high volume

**Query format** (SQL):
```sql
SELECT url, title, seendate, domain, language, sourcecountry
FROM gdelt_full.events_articles
WHERE DATE(PARSE_TIMESTAMP('%Y%m%d%H%M%S', seendate)) = DATE('2026-04-09')
  AND LOWER(language) = 'pt'
  AND UPPER(sourcecountry) = 'BR'
  AND (LOWER(title) LIKE '%bitcoin%' OR LOWER(title) LIKE '%ethereum%')
LIMIT 50;
```

---

## Configuration

### Environment Variables

#### For GDELT API:
```bash
GDELT_API_URL=https://api.gdeltproject.org/api/v2/doc/doc
GDELT_MAX_RECORDS=50
```

#### For BigQuery:
```bash
GOOGLE_CLOUD_PROJECT=hyper-trader-492500
BIGQUERY_DATASET=gdelt_full          # Default: gdelt_full
BIGQUERY_TABLE=events_articles        # Default: events_articles
```

---

## Switching Between Sources

### Current Setup (GDELT API - Default)
The `service.py` imports from `gdelt_adapter.py`:
```python
from app.gdelt_adapter import NewsAPIError, fetch_provider_news
```

### To Switch to BigQuery
1. Update `service.py`:
```python
from app.bigquery_adapter import BigQueryNewsError as NewsAPIError
from app.bigquery_adapter import fetch_bigquery_news as fetch_provider_news
```

2. Update environment variables in `.env` or `terraform.tfvars`:
```bash
BIGQUERY_DATASET=gdelt_full
BIGQUERY_TABLE=events_articles
```

3. No code changes needed in `api.py` or `config.py` (interface is identical).

---

## Cost Comparison

### GDELT API
- **Per query**: $0 (free)
- **100k queries/month**: ~$0 (only Firestore cache costs ~$1.50-$2.50)
- **Advantage**: No BigQuery fees

### BigQuery
- **Per query**: ~$0.0000060 (typical 10MB scan)
- **100k queries/month**: ~$0.60 BigQuery + Firestore cache ~$1.50-$2.50 = **~$2.10/month**
- **Advantage**: Faster queries, more data control, better for analytics

---

## Performance Characteristics

| Metric | GDELT API | BigQuery |
|--------|-----------|----------|
| Latency | ~30s | ~5-15s |
| Cold start | Yes (network) | No (faster) |
| Throughput | ~2 requests/sec | ~10 requests/sec |
| Scalability | Limited by API | Near-infinite with caching |
| Analytics capability | Poor | Excellent |

---

## Required Filters (All Mandatory)

Both adapters require the same filters:
- **keywords** (`q`): Comma-separated list (e.g., "bitcoin,ethereum")
- **date**: Single date in YYYY-MM-DD format
- **language**: ISO 639-1 code (e.g., "pt", "en")
- **country**: ISO 3166-1 alpha-2 code (e.g., "BR", "US")

Example request:
```
GET /news?q=bitcoin,ethereum&date=2026-04-09&language=pt&country=BR
```

---

## Pre-built Queries

SQL queries are available in: `api/queries/bigquery_gdelt.sql`

1. **Query 1**: Search by keywords, language, country, date (main query)
2. **Query 2**: Summary stats by country and language
3. **Query 3**: Top domains for a keyword
4. **Query 4**: Multi-day date range search

---

## Testing

### Test GDELT Adapter
```bash
PYTHONPATH=api python -m pytest api/tests/test_gdelt_adapter.py -v
```

### Test BigQuery Adapter
```bash
PYTHONPATH=api python -m pytest api/tests/test_bigquery_adapter.py -v
```

---

## Authentication & Permissions

### GDELT API
- No authentication required (public API)

### BigQuery
- Requires Google Cloud credentials (service account or user)
- IAM role: `roles/bigquery.dataViewer` (read-only)
- Project: `hyper-trader-492500`

---

## Recommendations

- **Start with GDELT API** for simplicity and cost (free)
- **Switch to BigQuery** when you need:
  - Lower latency requirements (<10s)
  - Higher throughput (>1000 req/hour)
  - Historical analysis or aggregations
  - Complex filtering beyond keywords
