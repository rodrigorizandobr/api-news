from datetime import datetime, timedelta, timezone

from app import service
from app.bigquery_adapter import BigQueryNewsError as NewsAPIError


class FakeCacheStore:
    def __init__(self) -> None:
        self.data: dict[str, dict] = {}

    def get(self, key: str):
        return self.data.get(key)

    def set(self, key: str, value: dict, ttl_hours: int) -> None:
        self.data[key] = value

    def get_stale(self, key: str):
        return self.data.get(key)

    def delete(self, key: str) -> None:
        self.data.pop(key, None)


def test_cache_works(monkeypatch) -> None:
    calls = {"count": 0}
    fake_cache = FakeCacheStore()
    historical_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()

    def fake_fetch(keywords, exact_date=None, language=None, country=None):
        calls["count"] += 1
        return {
            "query": "petrobras",
            "mode": "ArtList",
            "article_count": 1,
            "articles": [{"title": "x"}],
        }

    monkeypatch.setattr(service, "fetch_provider_news", fake_fetch)
    monkeypatch.setattr(service, "get_cache_store", lambda: fake_cache)

    first = service.search_news_with_cache(["petrobras"], exact_date=historical_date, language="pt", country="BR")
    second = service.search_news_with_cache(["petrobras"], exact_date=historical_date, language="pt", country="BR")

    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert first["contract_version"] == "v1"
    assert second["contract_version"] == "v1"
    assert calls["count"] == 1


def test_historical_date_uses_cache_on_second_call(monkeypatch) -> None:
    calls = {"count": 0}
    fake_cache = FakeCacheStore()
    historical_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()

    def fake_fetch(keywords, exact_date=None, language=None, country=None):
        calls["count"] += 1
        return {
            "query": "petrobras",
            "mode": "ArtList",
            "article_count": 1,
            "articles": [{"title": f"x-{calls['count']}"}],
        }

    monkeypatch.setattr(service, "fetch_provider_news", fake_fetch)
    monkeypatch.setattr(service, "get_cache_store", lambda: fake_cache)

    first = service.search_news_with_cache(["petrobras"], exact_date=historical_date, language="pt", country="BR")
    refreshed = service.search_news_with_cache(["petrobras"], exact_date=historical_date, language="pt", country="BR")

    assert first["cache_hit"] is False
    assert refreshed["cache_hit"] is True
    assert refreshed["articles"][0]["title"] == "x-1"
    assert calls["count"] == 1


def test_current_date_does_not_cache(monkeypatch) -> None:
    calls = {"count": 0}
    fake_cache = FakeCacheStore()
    current_date = datetime.now(timezone.utc).date()

    def fake_fetch(keywords, exact_date=None, language=None, country=None):
        calls["count"] += 1
        return {
            "query": "bitcoin",
            "mode": "ArtList",
            "article_count": 1,
            "articles": [{"title": f"item-{calls['count']}"}],
        }

    monkeypatch.setattr(service, "fetch_provider_news", fake_fetch)
    monkeypatch.setattr(service, "get_cache_store", lambda: fake_cache)

    first = service.search_news_with_cache(["bitcoin"], exact_date=current_date, language="en", country="US")
    second = service.search_news_with_cache(["bitcoin"], exact_date=current_date, language="en", country="US")

    assert first["cache_policy"] == "current-no-cache"
    assert second["cache_policy"] == "current-no-cache"
    assert calls["count"] == 2


def test_stale_cache_fallback_on_upstream_error(monkeypatch) -> None:
    fake_cache = FakeCacheStore()

    seed = {
        "cache_hit": False,
        "cache_policy": "historical-eternal",
        "keywords": ["petrobras"],
        "query": "petrobras",
        "article_count": 1,
        "articles": [{"title": "cached-item"}],
        "source": "gdelt",
    }
    historical_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    key = service._build_cache_key_with_mode(["petrobras"], historical_date, "pt", "BR")
    fake_cache.set(key, seed, ttl_hours=None)

    def failing_fetch(keywords, exact_date=None, language=None, country=None):
        raise NewsAPIError("GNews API error. Retry in a few seconds.", status_code=429)

    monkeypatch.setattr(service, "fetch_provider_news", failing_fetch)
    monkeypatch.setattr(service, "get_cache_store", lambda: fake_cache)
    monkeypatch.setattr(fake_cache, "get", lambda key: None)

    response = service.search_news_with_cache(["petrobras"], exact_date=historical_date, language="pt", country="BR")

    assert response["cache_hit"] is True
    assert response["stale_fallback"] is True
    assert response["articles"][0]["title"] == "cached-item"
    assert response["error"]["code"] == "UPSTREAM_ERROR"


def test_empty_payload_when_upstream_fails_without_stale(monkeypatch) -> None:
    fake_cache = FakeCacheStore()

    def failing_fetch(keywords, exact_date=None, language=None, country=None):
        raise NewsAPIError("GNews API returned invalid response.", status_code=502)

    monkeypatch.setattr(service, "fetch_provider_news", failing_fetch)
    monkeypatch.setattr(service, "get_cache_store", lambda: fake_cache)

    response = service.search_news_with_cache(["bitcoin"], exact_date=(datetime.now(timezone.utc) - timedelta(days=1)).date(), language="en", country="US")

    assert response["error"]["code"] == "UPSTREAM_ERROR"
    assert response["article_count"] == 0
    assert response["articles"] == []


def test_cache_write_failure_does_not_fail_response(monkeypatch) -> None:
    fake_cache = FakeCacheStore()
    historical_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()

    def fake_fetch(keywords, exact_date=None, language=None, country=None):
        return {
            "query": "(petrobras)",
            "mode": "ArtList",
            "article_count": 1,
            "articles": [{"title": "ok"}],
        }

    def failing_set(key: str, value: dict, ttl_hours: int | None) -> None:
        raise RuntimeError("firestore document too large")

    monkeypatch.setattr(service, "fetch_provider_news", fake_fetch)
    monkeypatch.setattr(service, "get_cache_store", lambda: fake_cache)
    monkeypatch.setattr(fake_cache, "set", failing_set)

    response = service.search_news_with_cache(["petrobras"], exact_date=historical_date, language="pt", country="BR")


def test_stale_response_strips_deprecated_fields(monkeypatch) -> None:
    fake_cache = FakeCacheStore()
    historical_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()
    key = service._build_cache_key_with_mode(["petrobras"], historical_date, "pt", "BR")
    fake_cache.set(
        key,
        {
            "cache_hit": False,
            "keywords": ["petrobras"],
            "fulltext": False,
            "start_date": None,
            "end_date": None,
            "date_filter": {
                "date": historical_date.isoformat(),
                "start_date": None,
                "end_date": None,
            },
            "articles": [],
            "article_count": 0,
        },
        ttl_hours=None,
    )

    def failing_fetch(keywords, exact_date=None, language=None, country=None):
        raise NewsAPIError("upstream unavailable", status_code=502)

    monkeypatch.setattr(service, "fetch_provider_news", failing_fetch)
    monkeypatch.setattr(service, "get_cache_store", lambda: fake_cache)
    monkeypatch.setattr(fake_cache, "get", lambda key: None)

    response = service.search_news_with_cache(["petrobras"], exact_date=historical_date, language="pt", country="BR")

    assert "fulltext" not in response
    assert "start_date" not in response
    assert "end_date" not in response
    assert "date_filter" not in response
    assert "mode" not in response
    assert "available_fields" not in response


def test_historical_cache_write_removes_legacy_modes(monkeypatch) -> None:
    fake_cache = FakeCacheStore()
    historical_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()

    for mode in service.LEGACY_CACHE_MODES:
        legacy_key = service._build_cache_key_with_mode(["petrobras"], historical_date, "pt", "BR", mode=mode)
        fake_cache.set(legacy_key, {"legacy": True}, ttl_hours=None)

    def fake_fetch(keywords, exact_date=None, language=None, country=None):
        return {
            "query": "petrobras",
            "mode": "ArtList",
            "article_count": 1,
            "articles": [{"title": "fresh"}],
        }

    monkeypatch.setattr(service, "fetch_provider_news", fake_fetch)
    monkeypatch.setattr(service, "get_cache_store", lambda: fake_cache)

    service.search_news_with_cache(["petrobras"], exact_date=historical_date, language="pt", country="BR")

    for mode in service.LEGACY_CACHE_MODES:
        legacy_key = service._build_cache_key_with_mode(["petrobras"], historical_date, "pt", "BR", mode=mode)
        assert legacy_key not in fake_cache.data

    current_key = service._build_cache_key_with_mode(["petrobras"], historical_date, "pt", "BR")
    assert current_key in fake_cache.data
