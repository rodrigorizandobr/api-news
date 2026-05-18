import os
from datetime import date as date_type
from typing import Any

from google.cloud import bigquery


class BigQueryNewsError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 502,
        code: str = "UPSTREAM_ERROR",
        provider_status: str = "error",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.provider_status = provider_status


BIGQUERY_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "hyper-trader-492500")
BIGQUERY_SOURCE_PROJECT = os.getenv("BIGQUERY_SOURCE_PROJECT", "gdelt-bq")
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "gdeltv2")
BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE", "gkg_partitioned")
BIGQUERY_LOCATION = os.getenv("BIGQUERY_LOCATION", "US")
BIGQUERY_MAX_BYTES_BILLED = int(os.getenv("BIGQUERY_MAX_BYTES_BILLED", "175921860444"))

LANGUAGE_CODE_MAP = {
    "en": "eng",
    "pt": "por",
    "es": "spa",
    "fr": "fra",
    "de": "deu",
    "it": "ita",
}

SOURCE_COLLECTION_LABELS = {
    1: "web",
    2: "citation-only",
    3: "core",
    4: "dtic",
    5: "jstor",
    6: "nontextual-source",
}


def _escape_sql_literal(value: str) -> str:
    return value.replace("'", "''")


def _to_gdelt_language(language: str) -> str:
    normalized = language.strip().lower()
    return LANGUAGE_CODE_MAP.get(normalized, normalized)


def _parse_seendate(raw: str) -> str:
    """Convert YYYYMMDDHHMMSS integer string to ISO 8601."""
    if not raw or len(raw) < 8:
        return raw or ""
    try:
        year, month, day = raw[0:4], raw[4:6], raw[6:8]
        hour, minute, second = (raw[8:10], raw[10:12], raw[12:14]) if len(raw) >= 14 else ("00", "00", "00")
        return f"{year}-{month}-{day}T{hour}:{minute}:{second}Z"
    except Exception:
        return raw


def _parse_semicolon_key_value(raw: str | None) -> list[str]:
    """Parse 'NAME,offset;NAME2,offset2;...' into a deduplicated list of names."""
    if not raw:
        return []
    seen: set[str] = set()
    result: list[str] = []
    for part in raw.split(";"):
        part = part.strip()
        if not part:
            continue
        name = part.split(",")[0].strip()
        if name and name not in seen:
            seen.add(name)
            result.append(name)
    return result


def _parse_tone(raw: str | None) -> dict[str, Any]:
    """Parse V2Tone 'tone,pos,neg,polarity,activity_ref_density,self_ref_density,word_count'."""
    if not raw:
        return {}
    parts = raw.split(",")
    keys = ["tone", "positive_score", "negative_score", "polarity",
            "activity_ref_density", "self_ref_density", "word_count"]
    result: dict[str, Any] = {}
    for i, key in enumerate(keys):
        if i < len(parts):
            try:
                result[key] = float(parts[i])
            except ValueError:
                result[key] = parts[i]
    return result


def _parse_locations(raw: str | None) -> list[dict[str, Any]]:
    """Parse V2Locations semicolon-separated records into structured list.

    Each record: type#name#country_code#adm1code#adm2code#lat#lon#feature_id#offset
    """
    if not raw:
        return []
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for part in raw.split(";"):
        part = part.strip()
        if not part:
            continue
        fields = part.split("#")
        if len(fields) < 3:
            continue
        name = fields[1].strip() if len(fields) > 1 else ""
        key = name
        if key in seen:
            continue
        seen.add(key)
        entry: dict[str, Any] = {"name": name}
        if len(fields) > 2:
            entry["country_code"] = fields[2].strip()
        if len(fields) > 5:
            try:
                entry["lat"] = float(fields[5]) if fields[5] else None
            except ValueError:
                entry["lat"] = None
        if len(fields) > 6:
            try:
                entry["lon"] = float(fields[6]) if fields[6] else None
            except ValueError:
                entry["lon"] = None
        result.append(entry)
    return result


def _parse_amounts(raw: str | None) -> list[dict[str, Any]]:
    """Parse Amounts field: 'amount,description,offset;...'"""
    if not raw:
        return []
    result: list[dict[str, Any]] = []
    for part in raw.split(";"):
        part = part.strip()
        if not part:
            continue
        fields = part.split(",", 2)
        if len(fields) < 2:
            continue
        try:
            amount = float(fields[0])
        except ValueError:
            amount = fields[0]
        result.append({
            "amount": amount,
            "context": fields[1].strip() if len(fields) > 1 else "",
        })
    return result


def _parse_related_images(raw: str | None) -> list[str]:
    """Parse RelatedImages semicolon-separated URLs."""
    if not raw:
        return []
    return [u.strip() for u in raw.split(";") if u.strip()]


def _build_bigquery_sql(
    keywords: list[str],
    exact_date: date_type,
    language: str,
    country: str,
) -> str:
    """Build BigQuery SQL query to search GDELT public dataset."""
    date_str = exact_date.strftime("%Y%m%d")
    partition_date = exact_date.strftime("%Y-%m-%d")
    language_3 = _to_gdelt_language(language)
    country_code = _escape_sql_literal(country.strip().upper())

    keyword_conditions = " OR ".join(
        [
            "LOWER(IFNULL(DocumentIdentifier, '')) LIKE '%{kw}%'"
            " OR LOWER(IFNULL(SourceCommonName, '')) LIKE '%{kw}%'"
            " OR LOWER(IFNULL(V2Themes, '')) LIKE '%{kw}%'"
            " OR LOWER(IFNULL(AllNames, '')) LIKE '%{kw}%'".format(
                kw=_escape_sql_literal(keyword.strip().lower())
            )
            for keyword in keywords
            if keyword.strip()
        ]
    )

    language_condition = (
        "(IFNULL(TranslationInfo, '') = '' "
        f"OR LOWER(IFNULL(TranslationInfo, '')) LIKE '%srclc:{_escape_sql_literal(language_3)}%'"
        ")"
    )

    sql = f"""
    SELECT
        GKGRECORDID          AS record_id,
        CAST(DATE AS STRING) AS seendate,
        SourceCollectionIdentifier AS source_type,
        IFNULL(SourceCommonName, '')    AS domain,
        IFNULL(DocumentIdentifier, '') AS url,
        IFNULL(V2Themes, '')       AS themes_raw,
        IFNULL(V2Tone, '')         AS tone_raw,
        IFNULL(V2Locations, '')    AS locations_raw,
        IFNULL(V2Persons, '')      AS persons_raw,
        IFNULL(V2Organizations, '') AS organizations_raw,
        IFNULL(SharingImage, '')   AS image,
        IFNULL(RelatedImages, '')  AS related_images_raw,
        IFNULL(Quotations, '')     AS quotations,
        IFNULL(AllNames, '')       AS names_raw,
        IFNULL(Amounts, '')        AS amounts_raw,
        IFNULL(TranslationInfo, '') AS translation_info,
        IFNULL(V2Counts, '')       AS counts_raw
    FROM
        `{BIGQUERY_SOURCE_PROJECT}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}`
    WHERE
        _PARTITIONTIME = TIMESTAMP('{partition_date}')
        AND SUBSTR(CAST(DATE AS STRING), 1, 8) = '{date_str}'
        AND {language_condition}
        AND UPPER(IFNULL(V2Locations, '')) LIKE '%#{country_code}#%'
        AND ({keyword_conditions})
    LIMIT 1000
    """
    return sql


def _row_to_article(row: Any, language: str, country: str) -> dict[str, Any]:
    """Map a BigQuery row to the full article structure."""
    tone = _parse_tone(row.tone_raw or None)
    return {
        "record_id": row.record_id or "",
        "url": row.url or "",
        "domain": row.domain or "",
        "published_at": _parse_seendate(row.seendate or ""),
        "language": language.strip().lower(),
        "source_country": country.strip().upper(),
        "source_type": SOURCE_COLLECTION_LABELS.get(row.source_type, "unknown"),
        "image": row.image or "",
        "related_images": _parse_related_images(row.related_images_raw or None),
        "themes": _parse_semicolon_key_value(row.themes_raw or None),
        "persons": _parse_semicolon_key_value(row.persons_raw or None),
        "organizations": _parse_semicolon_key_value(row.organizations_raw or None),
        "locations": _parse_locations(row.locations_raw or None),
        "names": _parse_semicolon_key_value(row.names_raw or None),
        "amounts": _parse_amounts(row.amounts_raw or None),
        "quotations": row.quotations or "",
        "counts": row.counts_raw or "",
        "translation_info": row.translation_info or "",
        "sentiment": tone,
    }


def fetch_bigquery_news(
    keywords: list[str],
    exact_date: date_type,
    language: str,
    country: str,
) -> dict[str, Any]:
    """Fetch news articles from BigQuery GDELT dataset."""
    try:
        client = bigquery.Client(project=BIGQUERY_PROJECT)
        sql = _build_bigquery_sql(keywords, exact_date, language, country)
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=BIGQUERY_MAX_BYTES_BILLED,
            use_query_cache=True,
        )

        query_job = client.query(sql, location=BIGQUERY_LOCATION, job_config=job_config)
        results = query_job.result()

        articles = [_row_to_article(row, language, country) for row in results]

        return {
            "query": " OR ".join(keywords),
            "article_count": len(articles),
            "articles": articles,
            "source": "bigquery-gdelt",
        }
    except Exception as exc:
        raise BigQueryNewsError(
            f"Failed to fetch from BigQuery: {str(exc)}",
            status_code=502,
            code="UPSTREAM_ERROR",
        ) from exc


# Backward compatible alias
def fetch_provider_news_bigquery(
    keywords: list[str],
    exact_date: date_type,
    language: str,
    country: str,
) -> dict[str, Any]:
    """Backward compatible alias for fetch_bigquery_news."""
    return fetch_bigquery_news(
        keywords=keywords,
        exact_date=exact_date,
        language=language,
        country=country,
    )
