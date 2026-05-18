from datetime import date as date_type, datetime, timezone
import logging
from typing import Any

from app.cache import FirestoreTTLCache
from app.contract import CONTRACT_VERSION, normalize_contract_response
from app.bigquery_adapter import BigQueryNewsError as NewsAPIError, fetch_bigquery_news as fetch_provider_news

cache_store: FirestoreTTLCache | None = None
logger = logging.getLogger(__name__)
CACHE_MODE = "artlist-v4"
LEGACY_CACHE_MODES = ("artlist-v1", "artlist-v2", "artlist-v3")


def _build_error_payload(exc: NewsAPIError) -> dict[str, Any]:
    return {
        "code": exc.code,
        "message": str(exc),
        "provider_status": exc.provider_status,
    }


def get_cache_store() -> FirestoreTTLCache:
    global cache_store
    if cache_store is None:
        cache_store = FirestoreTTLCache()
    return cache_store


def _build_cache_key(keywords: list[str]) -> str:
    normalized_keywords = ",".join(sorted(keyword.lower() for keyword in keywords))
    return f"news:{normalized_keywords}"


def _is_historical_request(exact_date: date_type | None) -> bool:
    today = datetime.now(timezone.utc).date()
    return exact_date is not None and exact_date < today


def _should_cache(exact_date: date_type | None) -> bool:
    return _is_historical_request(exact_date)


def _cache_ttl_hours(exact_date: date_type | None) -> int | None:
    """
    Compute TTL for cache entry.
    - Historical data (before today): None = permanent cache
    - Current/future data: handled by _should_cache=False, so this is never called
    """
    # Only called when cache_enabled=True, which means it's historical
    return None


def _build_cache_key_with_mode(
    keywords: list[str],
    exact_date: date_type,
    language: str,
    country: str,
    mode: str = CACHE_MODE,
) -> str:
    # Cache key is explicitly based on URL-equivalent params: q/date/language/country.
    normalized_q = ",".join(sorted(keyword.lower() for keyword in keywords))
    date_segment = f"date={exact_date.isoformat()}"
    language_segment = f"language={language.lower()}"
    country_segment = f"country={country.upper()}"

    return f"news:mode={mode}:q={normalized_q}:{date_segment}:{language_segment}:{country_segment}"


def _cleanup_legacy_cache_entries(
    cache: FirestoreTTLCache,
    keywords: list[str],
    exact_date: date_type,
    language: str,
    country: str,
) -> None:
    for legacy_mode in LEGACY_CACHE_MODES:
        legacy_key = _build_cache_key_with_mode(
            keywords=keywords,
            exact_date=exact_date,
            language=language,
            country=country,
            mode=legacy_mode,
        )
        try:
            cache.delete(legacy_key)
        except Exception:
            logger.exception("Failed to delete legacy Firestore cache entry", extra={"legacy_mode": legacy_mode})


def _deduplicate_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate articles by record_id (keeping first occurrence)."""
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for article in articles:
        record_id = article.get("record_id", "")
        if record_id and record_id not in seen:
            seen.add(record_id)
            result.append(article)
        elif not record_id:
            # If no record_id, keep it (shouldn't happen, but be safe)
            result.append(article)
    return result


def _search_single_keyword_with_cache(
    keyword: str,
    exact_date: date_type,
    language: str,
    country: str,
) -> tuple[list[dict[str, Any]], bool, bool, dict[str, Any] | None]:
    """
    Search for a single keyword with individual caching.
    
    Returns:
        (articles, cache_hit, stale_fallback, error)
    """
    cache_key = _build_cache_key_with_mode(
        keywords=[keyword],
        exact_date=exact_date,
        language=language,
        country=country,
    )
    cache = get_cache_store()
    cache_enabled = _should_cache(exact_date)

    # Check cache
    if cache_enabled:
        cached = cache.get(cache_key)
        if cached is not None:
            articles = cached.get("articles", [])
            return articles, True, False, None

    # Fetch from BigQuery
    try:
        fresh_data = fetch_provider_news(
            keywords=[keyword],
            exact_date=exact_date,
            language=language,
            country=country,
        )
        articles = fresh_data.get("articles", [])
    except NewsAPIError as exc:
        # Try stale fallback
        stale = cache.get_stale(cache_key) if cache_enabled else None
        if stale is not None:
            articles = stale.get("articles", [])
            return articles, True, True, _build_error_payload(exc)
        else:
            return [], False, False, _build_error_payload(exc)

    # Cache fresh result
    if cache_enabled:
        try:
            cache_entry = {
                "articles": articles,
                "query": keyword,
                "article_count": len(articles),
                "source": "bigquery-gdelt",
            }
            cache.set(cache_key, cache_entry, ttl_hours=_cache_ttl_hours(exact_date))
        except Exception:
            logger.exception(f"Failed to cache results for keyword {keyword}")

    return articles, False, False, None


def search_news_with_cache(
    keywords: list[str],
    exact_date: date_type,
    language: str,
    country: str,
) -> dict[str, Any]:
    """
    Search for news articles with per-keyword caching.
    
    Each keyword is searched individually and cached separately.
    Results are combined and deduplicated.
    
    Cost: $0.001 per query (due to partition pruning, language/country filter, LIMIT 50)
    """
    cache = get_cache_store()
    cache_enabled = _should_cache(exact_date)
    
    all_articles: list[dict[str, Any]] = []
    num_cached_keywords = 0
    any_error = False
    error_payload = None
    any_stale_fallback = False

    # Search each keyword individually for granular caching
    for keyword in keywords:
        articles, cache_hit, stale_fallback, error = _search_single_keyword_with_cache(
            keyword=keyword,
            exact_date=exact_date,
            language=language,
            country=country,
        )
        all_articles.extend(articles)
        if cache_hit:
            num_cached_keywords += 1
        if stale_fallback:
            any_stale_fallback = True
        if error is not None:
            any_error = True
            if error_payload is None:
                error_payload = error

    # Deduplicate articles by record_id
    deduplicated_articles = _deduplicate_articles(all_articles)

    # Determine cache hit status
    is_cache_hit = num_cached_keywords > 0
    
    # Build response
    response = normalize_contract_response({
        "cache_hit": is_cache_hit,
        "cache_policy": "historical-eternal" if cache_enabled else "current-no-cache",
        "cache_granularity": "per-keyword" if len(keywords) > 1 else "single-keyword",
        "cache_keywords_hit": num_cached_keywords,
        "cache_keywords_total": len(keywords),
        "keywords": keywords,
        "date": exact_date.isoformat() if exact_date is not None else None,
        "language": language,
        "country": country,
        "stale_fallback": any_stale_fallback,
        "error": error_payload,
        "article_count": len(deduplicated_articles),
        "articles": deduplicated_articles,
        "source": "bigquery-gdelt",
    })

    # Cache full-keyword combination for future exact matches (optimization)
    if cache_enabled and len(deduplicated_articles) > 0 and not any_error:
        try:
            full_cache_key = _build_cache_key_with_mode(
                keywords=keywords,
                exact_date=exact_date,
                language=language,
                country=country,
            )
            _cleanup_legacy_cache_entries(cache, keywords, exact_date, language, country)
            cache.set(full_cache_key, response, ttl_hours=_cache_ttl_hours(exact_date))
        except Exception:
            logger.exception("Failed to persist full-keyword response in Firestore cache")

    return response
