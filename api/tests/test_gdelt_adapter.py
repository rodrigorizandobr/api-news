from datetime import date

from app import gdelt_adapter


class FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {"articles": []}


def test_fetch_provider_news_builds_cheap_gdelt_query(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_get(url, params, timeout):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(gdelt_adapter.requests, "get", fake_get)

    gdelt_adapter.fetch_provider_news(
        keywords=["bitcoin", "ethereum"],
        exact_date=date(2026, 4, 9),
        language="pt",
        country="BR",
    )

    assert captured["url"] == gdelt_adapter.GDELT_API_URL
    assert captured["timeout"] == 30
    assert captured["params"]["mode"] == "ArtList"
    assert captured["params"]["format"] == "json"
    assert captured["params"]["maxrecords"] == gdelt_adapter.GDELT_MAX_RECORDS
    assert captured["params"]["startdatetime"] == "20260409000000"
    assert captured["params"]["enddatetime"] == "20260409235959"
    assert "sourcelang:pt" in captured["params"]["query"]
    assert "sourcecountry:BR" in captured["params"]["query"]