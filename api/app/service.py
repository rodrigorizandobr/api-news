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
    date_segment = f":date:{exact_date.isoformat()}"
    language_segment = f":language:{language.lower()}"
    country_segment = f":country:{country.upper()}"

    return f"{_build_cache_key(keywords)}:mode:{mode}{date_segment}{language_segment}{country_segment}"


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


def search_news_with_cache(
    keywords: list[str],
    exact_date: date_type,
    language: str,
    country: str,
) -> dict[str, Any]:
    cache_key = _build_cache_key_with_mode(
        keywords,
        exact_date,
        language,
        country,
    )
    cache = get_cache_store()
    cache_enabled = _should_cache(exact_date)

    if cache_enabled:
        cached = cache.get(cache_key)
        if cached is not None:
            cached_response = normalize_contract_response(cached)
            cached_response["cache_hit"] = True
            return cached_response

    try:
        fresh_data = fetch_provider_news(
            keywords=keywords,
            exact_date=exact_date,
            language=language,
            country=country,
        )
    except NewsAPIError as exc:
        stale = cache.get_stale(cache_key) if cache_enabled else None
        if stale is None:
            return normalize_contract_response({
                "cache_hit": False,
                "cache_policy": "historical-eternal" if cache_enabled else "current-no-cache",
                "keywords": keywords,
                "date": exact_date.isoformat() if exact_date is not None else None,
                "language": language,
                "country": country,
                "stale_fallback": False,
                "error": _build_error_payload(exc),
                "article_count": 0,
                "articles": [],
                "source": "bigquery",
            })

        stale_response = normalize_contract_response(stale)
        stale_response["cache_hit"] = True
        stale_response["stale_fallback"] = True
        stale_response["error"] = _build_error_payload(exc)
        return stale_response

    response = normalize_contract_response({
        "cache_hit": False,
        "cache_policy": "historical-eternal" if cache_enabled else "current-no-cache",
        "keywords": keywords,
        "date": exact_date.isoformat() if exact_date is not None else None,
        "language": language,
        "country": country,
        "stale_fallback": False,
        **fresh_data,
    })
    if cache_enabled:
        try:
            _cleanup_legacy_cache_entries(cache, keywords, exact_date, language, country)
            cache.set(cache_key, response, ttl_hours=_cache_ttl_hours(exact_date))
        except Exception:
            logger.exception("Failed to persist response in Firestore cache; continuing without cache write")
    return response
