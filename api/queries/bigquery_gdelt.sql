-- GDELT BigQuery Queries for News Articles
-- Dataset: gdelt_full (or your custom BIGQUERY_DATASET)
-- Table: events_articles (or your custom BIGQUERY_TABLE)

-- ============================================================================
-- Query 1: Search by keywords, language, country, and specific date
-- ============================================================================
-- Parameters:
--   @keywords: List of keywords to search (e.g., ["bitcoin", "ethereum"])
--   @date: YYYY-MM-DD format (e.g., "2026-04-09")
--   @language: ISO 639-1 language code (e.g., "pt", "en")
--   @country: ISO 3166-1 alpha-2 country code (e.g., "BR", "US")

SELECT
    url,
    title,
    seendate,
    domain,
    language,
    sourcecountry,
    DATE(PARSE_TIMESTAMP('%Y%m%d%H%M%S', seendate)) as article_date,
    LOWER(title) as title_lower
FROM
    `gdelt_full.events_articles`
WHERE
    DATE(PARSE_TIMESTAMP('%Y%m%d%H%M%S', seendate)) = DATE('@date')
    AND LOWER(language) = LOWER('@language')
    AND UPPER(sourcecountry) = UPPER('@country')
    AND (
        LOWER(title) LIKE '%@keyword1%'
        OR LOWER(title) LIKE '%@keyword2%'
        OR LOWER(title) LIKE '%@keyword3%'
    )
ORDER BY
    seendate DESC
LIMIT 50;


-- ============================================================================
-- Query 2: Summary stats by country for a specific date
-- ============================================================================
SELECT
    sourcecountry,
    language,
    COUNT(*) as article_count,
    COUNT(DISTINCT domain) as unique_domains,
    MIN(seendate) as earliest_article,
    MAX(seendate) as latest_article
FROM
    `gdelt_full.events_articles`
WHERE
    DATE(PARSE_TIMESTAMP('%Y%m%d%H%M%S', seendate)) = DATE('@date')
    AND LOWER(language) = LOWER('@language')
    AND UPPER(sourcecountry) = UPPER('@country')
GROUP BY
    sourcecountry,
    language
ORDER BY
    article_count DESC;


-- ============================================================================
-- Query 3: Top domains for keyword search
-- ============================================================================
SELECT
    domain,
    COUNT(*) as article_count,
    COUNT(DISTINCT title) as unique_titles,
    ARRAY_AGG(DISTINCT language IGNORE NULLS LIMIT 5) as languages
FROM
    `gdelt_full.events_articles`
WHERE
    DATE(PARSE_TIMESTAMP('%Y%m%d%H%M%S', seendate)) = DATE('@date')
    AND LOWER(language) = LOWER('@language')
    AND UPPER(sourcecountry) = UPPER('@country')
    AND (LOWER(title) LIKE '%@keyword%')
GROUP BY
    domain
ORDER BY
    article_count DESC
LIMIT 20;


-- ============================================================================
-- Query 4: Articles with date range (alternative to single date)
-- ============================================================================
-- Note: Use this if you need multi-day searches
SELECT
    url,
    title,
    seendate,
    domain,
    language,
    sourcecountry
FROM
    `gdelt_full.events_articles`
WHERE
    DATE(PARSE_TIMESTAMP('%Y%m%d%H%M%S', seendate)) BETWEEN DATE('@start_date') AND DATE('@end_date')
    AND LOWER(language) = LOWER('@language')
    AND UPPER(sourcecountry) = UPPER('@country')
    AND LOWER(title) LIKE '%@keyword%'
ORDER BY
    seendate DESC
LIMIT 100;


-- ============================================================================
-- Notes
-- ============================================================================
-- 1. All keyword searches are case-insensitive using LOWER()
-- 2. Country codes are case-insensitive using UPPER()
-- 3. Seendate format in GDELT: YYYYMMDDHHMSS (20260409120000)
-- 4. LIMIT 50 matches GDELT_MAX_RECORDS config
-- 5. For production, use parameterized queries to prevent SQL injection
-- 6. Pricing: ~$6 per 1TB of data scanned. GDELT dataset is ~100GB, so expect $0.60 per full table scan
-- 7. Use partitioning/clustering on date, language, sourcecountry for cost optimization
