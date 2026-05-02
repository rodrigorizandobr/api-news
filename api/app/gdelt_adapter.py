import os
from datetime import date as date_type
from typing import Any
from urllib.parse import urlparse

import requests


class NewsAPIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 502,
        code: str = "UPSTREAM_ERROR",
        provider_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.provider_status = provider_status


GDELT_API_URL = os.getenv("GDELT_API_URL", "https://api.gdeltproject.org/api/v2/doc/doc")
GDELT_MAX_RECORDS = int(os.getenv("GDELT_MAX_RECORDS", "50"))


def _build_keyword_query(keywords: list[str]) -> str:
    """Build keyword query with OR logic between terms."""
    quoted_terms = [f'"{term}"' if " " in term else term for term in keywords]
    return " OR ".join(quoted_terms)


def _sanitize_filter(value: str) -> str:
    cleaned = "".join(char for char in value.strip() if char.isalnum() or char in {"_", "-"})
    return cleaned


def _extract_domain(url: str) -> str:
    if not url:
        return ""
    return urlparse(url).netloc.lower()


def _map_provider_article_to_contract(article: dict[str, Any]) -> dict[str, str]:
    """Map provider-specific article payload to the stable API contract."""
    article_url = article.get("url") or ""
    seen_date = article.get("seendate") or ""

    return {
        "url": article_url,
        "url_mobile": "",
        "title": article.get("title") or "",
        "seendate": seen_date,
        "socialimage": article.get("socialimage") or "",
        "domain": article.get("domain") or _extract_domain(article_url),
        "language": article.get("language") or "",
        "sourcecountry": article.get("sourcecountry") or "",
    }


def _build_date_range(exact_date: date_type | None) -> tuple[str, str]:
    if exact_date is None:
        raise NewsAPIError(
            "Date filter is required for news queries.",
            status_code=400,
            code="VALIDATION_ERROR",
        )

    day_str = exact_date.isoformat()
    compact = day_str.replace("-", "")
    return f"{compact}000000", f"{compact}235959"


def _build_gdelt_query(
    keywords: list[str],
    language: str,
    country: str,
) -> str:
    keyword_query = _build_keyword_query(keywords)
    filters = [
        f"({keyword_query})",
        f"sourcelang:{_sanitize_filter(language).lower()}",
        f"sourcecountry:{_sanitize_filter(country).upper()}",
    ]

    return " AND ".join(filters)


def fetch_provider_news(
    keywords: list[str],
    exact_date: date_type,
    language: str,
    country: str,
) -> dict[str, Any]:
    from_timestamp, to_timestamp = _build_date_range(exact_date)
    query = _build_gdelt_query(keywords=keywords, language=language, country=country)

    try:
        response = requests.get(
            GDELT_API_URL,
            params={
                "query": query,
                "mode": "ArtList",
                "format": "json",
                "maxrecords": GDELT_MAX_RECORDS,
                "startdatetime": from_timestamp,
                "enddatetime": to_timestamp,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        provider_status = exc.response.status_code if getattr(exc, "response", None) is not None else None
        raise NewsAPIError(
            f"Failed to fetch from GDELT API: {str(exc)}",
            status_code=502,
            code="UPSTREAM_ERROR",
            provider_status=provider_status,
        ) from exc

    articles = [_map_provider_article_to_contract(article) for article in data.get("articles", [])]

    return {
        "query": query,
        "article_count": len(articles),
        "articles": articles,
        "source": "gdelt",
    }


def fetch_gdelt_news(
    keywords: list[str],
    fulltext: bool | None = None,
    exact_date: date_type | None = None,
    language: str | None = None,
    country: str | None = None,
) -> dict[str, Any]:
    """Backward compatible alias kept to avoid breaking external imports."""
    _ = fulltext
    return fetch_provider_news(
        keywords=keywords,
        exact_date=exact_date,
        language=language,
        country=country,
    )
