# News Proxy API (FastAPI + Cloud Functions)

API proxy com contrato de resposta estável para busca de notícias, usando GDELT como fonte e Firestore como cache.

## Endpoints

### `GET /news`

Busca artigos no GDELT BigQuery.

**Parâmetros obrigatórios:**
| Parâmetro | Tipo | Exemplo | Descrição |
|-----------|------|---------|-----------|
| `q` | string | `tesla,spacex` | Palavras-chave separadas por vírgula |
| `date` | string | `2026-04-09` | Data no formato `YYYY-MM-DD` |
| `language` | string | `en` | Código de idioma (`en`, `pt`, `es`, `fr`, `de`, `it`) |
| `country` | string | `US` | Código de país ISO 3166-1 alpha-2 (`US`, `BR`, `GB`, etc.) |

**Exemplo:**
```bash
curl "https://api-news-f7b2cp4vla-uc.a.run.app/news?q=tesla,spacex&date=2026-04-09&language=en&country=US"
```

### `GET /health`

Retorna `{"status": "ok"}`.

---

## Estrutura da resposta

```json
{
  "cache_hit": false,
  "cache_policy": "historical-eternal",
  "keywords": ["tesla", "spacex"],
  "date": "2026-04-09",
  "language": "en",
  "country": "US",
  "query": "tesla OR spacex",
  "article_count": 50,
  "articles": [ ... ],
  "contract_version": "v1"
}
```

---

## Campos de cada artigo

Cada objeto dentro de `articles` contém os seguintes campos, todos originados do dataset público GDELT `gdelt-bq.gdeltv2.gkg_partitioned`:

### Identificação e fonte

| Campo | Origem GDELT | Descrição |
|-------|-------------|-----------|
| `record_id` | `GKGRECORDID` | ID único do registro no GDELT (ex: `20260409044500-512`) |
| `url` | `DocumentIdentifier` | URL completo do artigo original |
| `domain` | `SourceCommonName` | Nome do domínio da fonte (ex: `autoconnectedcar.com`) |
| `source_type` | `SourceCollectionIdentifier` | Tipo de fonte: `web`, `citation-only`, `core`, `dtic`, `jstor`, `nontextual-source` |
| `published_at` | `DATE` | Data e hora da publicação em ISO 8601 (ex: `2026-04-09T04:45:00Z`) |
| `language` | parâmetro da query | Código ISO 639-1 do idioma consultado (ex: `en`) |
| `source_country` | parâmetro da query | Código ISO 3166-1 do país consultado (ex: `US`) |
| `translation_info` | `TranslationInfo` | Informação de tradução, quando o artigo foi traduzido (ex: `srclc:zho;eng:GT-ZHO 1.0`). Vazio para artigos nativos no idioma |

### Mídia

| Campo | Origem GDELT | Descrição |
|-------|-------------|-----------|
| `image` | `SharingImage` | URL da imagem de compartilhamento do artigo (Open Graph) |
| `related_images` | `RelatedImages` | Lista de URLs de imagens relacionadas encontradas no artigo |

### Entidades extraídas pelo GDELT

| Campo | Origem GDELT | Descrição |
|-------|-------------|-----------|
| `themes` | `V2Themes` | Lista de temas e categorias GDELT (ex: `ECON_CURRENCY_EXCHANGE_RATE`, `WB_2120_SATELLITES`, `TAX_FNCACT_ANALYST`). Baseado no [dicionário de temas GDELT](http://data.gdeltproject.org/api/v2/guides/GDELT-Category-List.TXT) |
| `persons` | `V2Persons` | Pessoas mencionadas no artigo (ex: `["Elon Musk", "Jensen Huang"]`) |
| `organizations` | `V2Organizations` | Organizações mencionadas (ex: `["Tesla", "SpaceX", "Intel"]`) |
| `names` | `AllNames` | Todos os nomes próprios identificados no artigo — inclui pessoas, lugares e entidades não classificadas |
| `locations` | `V2Locations` | Locais georreferenciados mencionados. Cada item contém: `name` (nome), `country_code` (ISO), `lat` (latitude), `lon` (longitude) |

### Tom e sentimento

| Campo | Origem GDELT | Descrição |
|-------|-------------|-----------|
| `sentiment` | `V2Tone` | Objeto com análise de tom do artigo: |
| `sentiment.tone` | — | Tom geral: positivo (>0) ou negativo (<0) |
| `sentiment.positive_score` | — | Score de positividade (0–100) |
| `sentiment.negative_score` | — | Score de negatividade (0–100) |
| `sentiment.polarity` | — | Polaridade: soma de positivo + negativo (intensidade emocional total) |
| `sentiment.activity_ref_density` | — | Densidade de referências a ações/atividades no texto |
| `sentiment.self_ref_density` | — | Densidade de autorreferências no texto |
| `sentiment.word_count` | — | Total de palavras no artigo |

### Conteúdo adicional

| Campo | Origem GDELT | Descrição |
|-------|-------------|-----------|
| `amounts` | `Amounts` | Lista de valores numéricos mencionados no artigo. Cada item: `amount` (número) e `context` (trecho de contexto, ex: `{"amount": 20000000000, "context": "dollars"}`) |
| `quotations` | `Quotations` | Citações textuais diretas extraídas do artigo |
| `counts` | `V2Counts` | Contagens mencionadas no texto (ex: mortes, feridos, pessoas deslocadas) no formato GDELT |

> **Nota sobre título e conteúdo completo:** A tabela `gkg_partitioned` é um Knowledge Graph — extrai metadados, entidades e sentimentos, mas **não armazena o título nem o texto do artigo**. Para obter o título completo, é necessário acessar o `url` diretamente.

---

## Campos de tema (V2Themes) — principais prefixos

| Prefixo | Categoria |
|---------|-----------|
| `ECON_*` | Economia e mercados financeiros |
| `EPU_*` | Incerteza de política econômica |
| `TAX_FNCACT_*` | Funções e cargos (ex: `ANALYST`, `CEO`, `REPRESENTATIVE`) |
| `WB_*` | Categorias do Banco Mundial (infraestrutura, saúde, tecnologia, etc.) |
| `CRISISLEX_*` | Crises e eventos de emergência |
| `UNGP_*` | Temas de direitos humanos (ONU) |
| `ENV_*` | Meio ambiente e clima |
| `SOC_*` | Temas sociais |

---

## Run locally

```bash
make firestore-emulator
```

In a second terminal:

```bash
make dev
```

## Run tests

```bash
make test
```

## Cloud Functions

HTTP entrypoint: `handler` in `main.py`.

## Cache

Dados históricos (datas anteriores ao dia atual) são cacheados permanentemente no Firestore. Dados do dia atual nunca são cacheados.

### Estratégia: Cache por Termo Individual

A busca usa caching granular por termo com economia de custo:

1. **Query por termo**: Cada keyword é buscada individualmente no BigQuery
2. **Cache granular**: Cada termo é cacheado separadamente
3. **Reutilização**: Buscas subsequentes com termos repetidos vêm do cache
4. **Deduplicação**: Artigos duplicados (mesmo record_id) são removidos

**Otimização de custo:**
- Cada query custa **$0.001** (devido a partition pruning by date, language/country filter, LIMIT 50)
- Termos em cache não geram custo adicional

**Exemplo:**
```
Busca 1: q=petrobras,vale&date=2026-04-09&...
  → 2 queries ao BigQuery ($0.002 total)
  → Cacheia: petrobras, vale

Busca 2: q=petrobras,petroleo&date=2026-04-09&...
  → 1 query ao BigQuery ($0.001) [petroleo]
  → petrobras vem do cache (sem custo!)
  → Total economizado: $0.001 por overlap
```

**Campos de observabilidade na resposta:**
- `cache_hit`: true se qualquer termo veio do cache ou stale fallback
- `cache_keywords_hit`: número de keywords do cache
- `cache_keywords_total`: total de keywords buscadas
- `cache_granularity`: "single-keyword" ou "per-keyword"
- `stale_fallback`: true se usou cache desatualizado após erro upstream
