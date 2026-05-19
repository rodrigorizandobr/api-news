"""
Integration tests for Cloud Functions deployment.

Run these tests against a deployed Cloud Function to validate:
- Endpoint connectivity
- Authentication modes
- Error handling
- Response format
- Cache behavior
"""

import requests
from datetime import datetime, timedelta, timezone
from typing import Optional


class CloudFunctionTester:
    def __init__(self, function_url: str, auth_token: Optional[str] = None):
        """
        Initialize tester for Cloud Function.

        Args:
            function_url: Base URL of deployed Cloud Function
            auth_token: Optional authentication token (JWT, API key, or Basic)
        """
        self.function_url = function_url.rstrip("/")
        self.session = requests.Session()
        if auth_token:
            self.session.headers.update({"Authorization": f"Bearer {auth_token}"})

    def test_health(self) -> bool:
        """Test /health endpoint returns 200."""
        resp = self.session.get(f"{self.function_url}/health")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        payload = resp.json()
        assert payload.get("status") == "ok", f"Unexpected response: {payload}"
        print("✓ Health check passed")
        return True

    def test_news_with_date(self, date_str: str = None) -> bool:
        """Test /news endpoint with specific date."""
        if date_str is None:
            # Use historical date to ensure cache works
            date_str = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")

        resp = self.session.get(
            f"{self.function_url}/news",
            params={"q": "bitcoin", "date": date_str, "country": "US"}
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

        data = resp.json()
        assert "keywords" in data, "Missing 'keywords' in response"
        assert "article_count" in data, "Missing 'article_count' in response"
        assert "articles" in data, "Missing 'articles' in response"
        assert "cache_hit" in data, "Missing 'cache_hit' in response"
        assert isinstance(data["articles"], list), "Articles should be a list"

        print(f"✓ News query passed (found {data['article_count']} articles, cache_hit={data['cache_hit']})")
        return True

    def test_rejects_date_range_params(self) -> bool:
        """Test /news endpoint rejects start_date/end_date params."""
        resp = self.session.get(
            f"{self.function_url}/news",
            params={
                "q": "tesla",
                "start_date": "2026-04-01",
                "end_date": "2026-04-10",
            }
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        print("✓ Date range params rejection passed")
        return True

    def test_news_contract_fields(self) -> bool:
        """Test that the API response keeps the stable contract fields."""
        date_str = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")

        resp = self.session.get(
            f"{self.function_url}/news",
            params={
                "q": "market",
                "date": date_str,
                "country": "US",
            }
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

        data = resp.json()
        assert "contract_version" in data, "Missing 'contract_version' in response"
        assert "articles" in data, "Missing 'articles' in response"
        if data["articles"]:
            first = data["articles"][0]
            for field in ["url", "url_mobile", "title", "seendate", "socialimage", "domain", "language", "sourcecountry"]:
                assert field in first, f"Missing contract field '{field}'"
        print(f"✓ Contract fields validation passed")
        return True

    def test_cache_hit_on_repeat(self) -> bool:
        """Test that repeat queries hit cache."""
        date_str = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")

        # First query
        resp1 = self.session.get(
            f"{self.function_url}/news",
            params={"q": "cache-test", "date": date_str, "country": "US"}
        )
        data1 = resp1.json()
        cache_hit_1 = data1.get("cache_hit", False)

        # Wait a moment
        import time
        time.sleep(1)

        # Second query (same parameters)
        resp2 = self.session.get(
            f"{self.function_url}/news",
            params={"q": "cache-test", "date": date_str, "country": "US"}
        )
        data2 = resp2.json()
        cache_hit_2 = data2.get("cache_hit", False)

        # For historical data, second query should be cache hit
        assert cache_hit_2, "Expected cache_hit=true on repeat query for historical data"
        print(f"✓ Cache hit on repeat query (first: {cache_hit_1}, second: {cache_hit_2})")
        return True

    def test_error_empty_keywords(self) -> bool:
        """Test that empty keywords returns 400."""
        resp = self.session.get(
            f"{self.function_url}/news",
            params={"q": "", "date": "2024-01-01", "country": "US"}
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print("✓ Empty keywords validation passed")
        return True

    def test_error_missing_date(self) -> bool:
        """Test that missing date filter returns 400."""
        resp = self.session.get(
            f"{self.function_url}/news",
            params={"q": "bitcoin", "country": "US"}
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print("✓ Missing date validation passed")
        return True

    def test_error_mutual_exclusive_filters(self) -> bool:
        """Test that sending unsupported date range fields returns 400."""
        resp = self.session.get(
            f"{self.function_url}/news",
            params={
                "q": "bitcoin",
                "date": "2024-01-15",
                "country": "US",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print("✓ Mutual exclusive date filter validation passed")
        return True

    def run_full_suite(self) -> bool:
        """Run all integration tests."""
        print(f"\n🚀 Running integration tests against: {self.function_url}\n")

        tests = [
            ("Health Check", self.test_health),
            ("News Query - Specific Date", self.test_news_with_date),
            ("News Query - Reject Date Range", self.test_rejects_date_range_params),
            ("News Query - Contract Fields", self.test_news_contract_fields),
            ("Cache Hit on Repeat", self.test_cache_hit_on_repeat),
            ("Validation - Empty Keywords", self.test_error_empty_keywords),
            ("Validation - Missing Date", self.test_error_missing_date),
            ("Validation - Mutual Exclusive Filters", self.test_error_mutual_exclusive_filters),
        ]

        passed = 0
        failed = 0

        for name, test_func in tests:
            try:
                print(f"Testing: {name}...", end=" ")
                test_func()
                passed += 1
            except AssertionError as e:
                print(f"✗ FAILED: {e}")
                failed += 1
            except Exception as e:
                print(f"✗ ERROR: {e}")
                failed += 1

        print(f"\n{'='*60}")
        print(f"Results: {passed} passed, {failed} failed")
        print(f"{'='*60}\n")

        return failed == 0


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python tests/test_cloud_function.py <FUNCTION_URL> [AUTH_TOKEN]")
        print("\nExample:")
        print("  python tests/test_cloud_function.py https://us-central1-myproject.cloudfunctions.net/api-news")
        print("  python tests/test_cloud_function.py https://us-central1-myproject.cloudfunctions.net/api-news 'Bearer YOUR_JWT'")
        sys.exit(1)

    function_url = sys.argv[1]
    auth_token = sys.argv[2] if len(sys.argv) > 2 else None

    tester = CloudFunctionTester(function_url, auth_token)
    success = tester.run_full_suite()

    sys.exit(0 if success else 1)
