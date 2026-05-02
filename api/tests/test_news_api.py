import os

# JWT bearer auth for testing
os.environ["AUTH_JWT_SECRET"] = "test-jwt-secret-1234567890-abcdef"
os.environ["AUTH_JWT_EXPIRY_HOURS"] = "24"

import pytest
from fastapi.testclient import TestClient

from app import api as api_module
from app.auth import generate_jwt_token


client = TestClient(api_module.app)


def _auth_headers() -> dict[str, str]:
    token = generate_jwt_token(api_module.auth_config.jwt_secret, expiry_hours=24)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    api_module.app.state.limiter.reset()


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_news_rejects_empty_keywords() -> None:
    response = client.get("/news?q=,,,&date=2026-04-10&language=pt&country=BR", headers=_auth_headers())
    assert response.status_code == 400


def test_news_query_params_are_forwarded(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_search_news_with_cache(*, keywords, exact_date, language, country):
        captured.update(
            {
                "keywords": keywords,
                "exact_date": exact_date,
                "language": language,
                "country": country,
            }
        )
        return {"cache_hit": False, "contract_version": "v1", "articles": []}

    monkeypatch.setattr(api_module, "search_news_with_cache", fake_search_news_with_cache)

    response = client.get("/news?q=petrobras&date=2026-04-10&language=pt&country=BR", headers=_auth_headers())

    assert response.status_code == 200
    assert captured == {
        "keywords": ["petrobras"],
        "exact_date": api_module.date_type(2026, 4, 10),
        "language": "pt",
        "country": "BR",
    }


def test_date_query_param_is_forwarded(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_search_news_with_cache(*, keywords, exact_date, language, country):
        captured.update(
            {
                "keywords": keywords,
                "exact_date": exact_date.isoformat() if exact_date is not None else None,
                "language": language,
                "country": country,
            }
        )
        return {"cache_hit": False, "contract_version": "v1", "articles": []}

    monkeypatch.setattr(api_module, "search_news_with_cache", fake_search_news_with_cache)

    response = client.get("/news?q=bitcoin&date=2026-04-10&language=en&country=US", headers=_auth_headers())

    assert response.status_code == 200
    assert captured == {
        "keywords": ["bitcoin"],
        "exact_date": "2026-04-10",
        "language": "en",
        "country": "US",
    }


def test_rejects_start_and_end_date_params() -> None:
    response = client.get(
        "/news?q=bitcoin&date=2026-04-10&language=en&country=US&start_date=2026-04-01&end_date=2026-04-10",
        headers=_auth_headers(),
    )
    assert response.status_code == 400


def test_date_filter_is_required() -> None:
    response = client.get("/news?q=bitcoin&language=pt&country=BR", headers=_auth_headers())
    assert response.status_code == 422  # Missing date parameter


def test_language_is_required() -> None:
    response = client.get("/news?q=bitcoin&date=2026-04-10&country=BR", headers=_auth_headers())
    assert response.status_code == 422  # Missing language parameter


def test_country_is_required() -> None:
    response = client.get("/news?q=bitcoin&date=2026-04-10&language=pt", headers=_auth_headers())
    assert response.status_code == 422  # Missing country parameter


def test_route_strips_legacy_fields_from_response(monkeypatch) -> None:
    def fake_search_news_with_cache(*, keywords, exact_date, language, country):
        return {
            "available_fields": ["domain"],
            "date": exact_date.isoformat(),
            "article_count": 1,
            "end_date": None,
            "date_filter": {
                "date": exact_date.isoformat(),
                "start_date": None,
                "end_date": None,
            },
            "fulltext": False,
            "mode": "ArtList",
            "cache_policy": "historical-eternal",
            "cache_hit": True,
            "source": "gdelt",
            "query": "bitcoin OR ethereum",
            "start_date": None,
            "keywords": keywords,
            "language": language,
            "country": country,
            "stale_fallback": False,
            "articles": [{"title": "x"}],
        }

    monkeypatch.setattr(api_module, "search_news_with_cache", fake_search_news_with_cache)

    response = client.get("/news?q=bitcoin,ethereum&date=2026-04-09&language=pt&country=BR", headers=_auth_headers())

    assert response.status_code == 200
    payload = response.json()
    assert payload["contract_version"] == "v1"
    assert "available_fields" not in payload
    assert "date_filter" not in payload
    assert "fulltext" not in payload
    assert "mode" not in payload
    assert "start_date" not in payload
    assert "end_date" not in payload
