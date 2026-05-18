from datetime import date

from app import bigquery_adapter


class FakeQueryJob:
    def __init__(self, rows):
        self.rows = rows
    
    def result(self):
        return self.rows


class FakeRow:
    def __init__(self, url, seendate, domain, record_id="FAKE-ID",
                 source_type=1, image="", related_images_raw="",
                 themes_raw="", tone_raw="1.5,3.0,1.5,4.5,10.0,0.0,200",
                 locations_raw="1#United States#US#US##39.8#-98.5#US#10",
                 persons_raw="", organizations_raw="",
                 quotations="", names_raw="", amounts_raw="",
                 translation_info="", counts_raw=""):
        self.record_id = record_id
        self.url = url
        self.seendate = seendate
        self.domain = domain
        self.source_type = source_type
        self.image = image
        self.related_images_raw = related_images_raw
        self.themes_raw = themes_raw
        self.tone_raw = tone_raw
        self.locations_raw = locations_raw
        self.persons_raw = persons_raw
        self.organizations_raw = organizations_raw
        self.quotations = quotations
        self.names_raw = names_raw
        self.amounts_raw = amounts_raw
        self.translation_info = translation_info
        self.counts_raw = counts_raw


def test_bigquery_sql_builder() -> None:
    """Test BigQuery SQL query construction."""
    sql = bigquery_adapter._build_bigquery_sql(
        keywords=["bitcoin", "ethereum"],
        exact_date=date(2026, 4, 9),
        language="pt",
        country="BR",
    )
    
    # Verify SQL contains required filters
    assert "bitcoin" in sql.lower()
    assert "ethereum" in sql.lower()
    assert "20260409" in sql
    assert "_partitiontime" in sql.lower()
    assert "2026-04-09" in sql
    assert "srclc:por" in sql.lower()
    assert "BR" in sql.upper()
    assert "gdelt-bq.gdeltv2.gkg_partitioned" in sql
    assert "LIMIT 1000" in sql


def test_fetch_bigquery_news_maps_response(monkeypatch) -> None:
    """Test BigQuery response mapping to API contract."""
    fake_rows = [
        FakeRow(
            url="https://example.com/news1",
            seendate="20260409120000",
            domain="example.com",
            themes_raw="ECON_BITCOIN,100;TAX_WORLDMAMMALS,200",
            persons_raw="Satoshi Nakamoto,50",
            organizations_raw="Bitcoin Foundation,80",
        ),
        FakeRow(
            url="https://example.com/news2",
            seendate="20260409150000",
            domain="example.com",
        ),
    ]
    captured: dict[str, object] = {}
    
    def fake_query(sql):
        return FakeQueryJob(fake_rows)
    
    def fake_client_init(project=None):
        class FakeClient:
            def query(self, sql, location=None, job_config=None):
                captured["location"] = location
                captured["max_bytes"] = getattr(job_config, "maximum_bytes_billed", None)
                return fake_query(sql)
        return FakeClient()
    
    monkeypatch.setattr(bigquery_adapter.bigquery, "Client", fake_client_init)
    
    response = bigquery_adapter.fetch_bigquery_news(
        keywords=["bitcoin"],
        exact_date=date(2026, 4, 9),
        language="pt",
        country="BR",
    )
    
    assert response["article_count"] == 2
    assert response["source"] == "bigquery-gdelt"
    assert len(response["articles"]) == 2
    first = response["articles"][0]
    assert first["url"] == "https://example.com/news1"
    assert first["language"] == "pt"
    assert first["published_at"] == "2026-04-09T12:00:00Z"
    assert first["domain"] == "example.com"
    assert "ECON_BITCOIN" in first["themes"]
    assert "Satoshi Nakamoto" in first["persons"]
    assert "Bitcoin Foundation" in first["organizations"]
    assert first["sentiment"]["tone"] == 1.5
    assert first["sentiment"]["word_count"] == 200.0
    assert first["locations"][0]["name"] == "United States"
    assert first["locations"][0]["country_code"] == "US"
    assert captured["location"] == bigquery_adapter.BIGQUERY_LOCATION
    assert captured["max_bytes"] == bigquery_adapter.BIGQUERY_MAX_BYTES_BILLED


def test_language_mapping_to_gdelt_code() -> None:
    sql = bigquery_adapter._build_bigquery_sql(
        keywords=["tesla"],
        exact_date=date(2026, 4, 9),
        language="en",
        country="US",
    )

    assert "srclc:eng" in sql.lower()
