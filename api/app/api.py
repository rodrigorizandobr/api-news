from datetime import date as date_type
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import ValidationError

from app.auth import AuthConfig, verify_auth
from app.bigquery_adapter import fetch_bigquery_usage_panel
from app.config import NewsQueryParams
from app.contract import normalize_contract_response
from app.gdelt_adapter import NewsAPIError
from app.rate_limit import limiter, HEALTH_RATE_LIMIT, NEWS_RATE_LIMIT
from app.service import search_news_with_cache

app = FastAPI(title="api-news", version="1.0.0")
app.state.limiter = limiter

# Load authentication configuration
auth_config = AuthConfig.from_env()


@app.get("/health")
@limiter.limit(HEALTH_RATE_LIMIT)
def health(request: Request) -> dict[str, Any]:
    return {
        "status": "ok",
        "bigquery_panel": fetch_bigquery_usage_panel(),
    }


@app.get("/news")
@limiter.limit(NEWS_RATE_LIMIT)
async def get_news(
    request: Request,
    q: str = Query(..., description="Comma-separated keywords (required)"),
    date: date_type = Query(..., description="Specific UTC date filter in YYYY-MM-DD format (required)"),
    language: str = Query(..., description="Language filter (e.g. en, pt) (required)"),
    country: str = Query(..., description="Country filter (e.g. US, BR) (required)"),
    start_date: str | None = Query(None, include_in_schema=False),
    end_date: str | None = Query(None, include_in_schema=False),
) -> dict:
    # Verify authentication
    await verify_auth(request, auth_config)

    if start_date is not None or end_date is not None:
        raise HTTPException(status_code=400, detail="Use only date (YYYY-MM-DD). start_date/end_date are not supported")

    try:
        params = NewsQueryParams(
            q=q,
            date=date,
            language=language,
            country=country,
        )
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    keywords = params.keywords
    if not keywords:
        raise HTTPException(status_code=400, detail="At least one keyword is required in q")

    try:
        return normalize_contract_response(
            search_news_with_cache(
                keywords=keywords,
                exact_date=params.date,
                language=params.language,
                country=params.country,
            )
        )
    except NewsAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
