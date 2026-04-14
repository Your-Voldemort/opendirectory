---
name: google-trends-api
description: Query Google Trends data via SerpApi for search trend analysis, keyword discovery, topic comparison, and geographic interest patterns. Use when users need trending keyword data, want to compare search terms, or need Google Trends insights for content planning.
license: MIT
compatibility: Requires network access and a SerpApi API key (SERPAPI_KEY environment variable). Free tier provides 250 searches/month.
metadata:
  author: farizanjum
  version: "2.0"
  api-provider: serpapi
allowed-tools: Bash(curl:*) Bash(python:*) Read
---

# Google Trends API Skill

Query Google Trends data through SerpApi to discover trending keywords, compare topics, and analyze search interest patterns.

## Prerequisites

- **API Key**: Set `SERPAPI_KEY` environment variable with your SerpApi key
- **Free Tier**: 250 searches/month (no credit card required)
- **Sign Up**: https://serpapi.com/

## API Basics

**Base URL**: `https://serpapi.com/search`

Every request requires these parameters:
- `engine=google_trends`
- `api_key` — your SerpApi private key
- `q` — 1-5 comma-separated queries (max 100 chars each)
- `data_type` — one of the types below

## Data Types

| Type | Max Queries | Purpose |
|------|-------------|---------|
| `RELATED_QUERIES` | 1 | Discover related search queries (rising + top) |
| `RELATED_TOPICS` | 1 | Discover related topics searched by same users |
| `TIMESERIES` | 5 | Track interest over time, compare terms |
| `GEO_MAP_0` | 1 | Regional interest for a single query |
| `GEO_MAP` | 5 | Regional comparison of multiple queries |

## Common Parameters

### Time Ranges (`date`)

| Value | Period | Best For |
|-------|--------|----------|
| `today 3-m` | Past 3 months | Current trends, SEO research |
| `today 12-m` | Past year | Trend validation |
| `today 5-y` | Past 5 years | Seasonal patterns |
| `now 7-d` | Last 7 days | Breaking trends |
| `all` | 2004-present | Historical analysis |

### Geographic (`geo`)

- `""` (empty) = Worldwide
- `US` = United States, `GB` = United Kingdom, `CA` = Canada
- `US-CA` = California (state-level)

### Region Granularity (`region`)

`COUNTRY` | `REGION` | `DMA` | `CITY`

### Platform (`gprop`)

- *(empty)* = Web Search (default)
- `youtube` | `news` | `images` | `froogle` (Shopping)

## Making Requests

### RELATED_QUERIES — Find related searches

```bash
curl -s "https://serpapi.com/search?engine=google_trends&q=kubernetes&data_type=RELATED_QUERIES&date=today+3-m&api_key=$SERPAPI_KEY"
```

**Response structure** — see [references/api-responses.md](references/api-responses.md) for full details:

```json
{
  "related_queries": {
    "rising": [
      {"query": "kubernetes vs docker", "formatted_value": "Breakout"},
      {"query": "kubernetes tutorial 2024", "formatted_value": "+180%"}
    ],
    "top": [
      {"query": "kubernetes deployment", "value": 100}
    ]
  }
}
```

- **"Breakout"** = 5000%+ growth — highest opportunity
- **"+N%"** = year-over-year growth percentage

### RELATED_TOPICS — Find related topics

```bash
curl -s "https://serpapi.com/search?engine=google_trends&q=kubernetes&data_type=RELATED_TOPICS&date=today+3-m&api_key=$SERPAPI_KEY"
```

Returns rising and top topics with titles and types.

### TIMESERIES — Interest over time

```bash
curl -s "https://serpapi.com/search?engine=google_trends&q=react,vue,angular&data_type=TIMESERIES&date=today+12-m&api_key=$SERPAPI_KEY"
```

Supports up to 5 comma-separated queries for comparison. Returns timeline data with interest values (0-100 scale).

### GEO_MAP_0 — Regional interest (single query)

```bash
curl -s "https://serpapi.com/search?engine=google_trends&q=kubernetes&data_type=GEO_MAP_0&geo=US&region=REGION&api_key=$SERPAPI_KEY"
```

### GEO_MAP — Regional comparison (multi-query)

```bash
curl -s "https://serpapi.com/search?engine=google_trends&q=react,vue&data_type=GEO_MAP&geo=US&region=REGION&api_key=$SERPAPI_KEY"
```

## Error Handling

Always check `search_metadata.status` in the response:

```python
if response.get("search_metadata", {}).get("status") != "Success":
    error = response.get("error", "Unknown error")
    # Handle: invalid key, rate limit, malformed query, etc.
```

Common errors:
- **"Invalid API key"** — check SERPAPI_KEY is set correctly
- **"No results"** — query too niche, try broader terms
- **"Monthly limit exceeded"** — 250 free searches used up

## Rate Limit & Budget

- **Free tier**: 250 searches/month
- Failed searches are automatically refunded
- No strict per-second rate limit, but space requests reasonably
- Cache results for 7-14 days (trends don't change hourly)
- Batch up to 5 queries in TIMESERIES/GEO_MAP calls to save credits

## Example Script

Run the discovery script for a quick keyword lookup:

```bash
python scripts/discover_keywords.py "your topic here"
```

See [scripts/discover_keywords.py](scripts/discover_keywords.py) for the full implementation.

## References

- [references/api-responses.md](references/api-responses.md) — Full response structures for all data types
- [SerpApi Docs](https://serpapi.com/google-trends-api) — Official API documentation
- [API Playground](https://serpapi.com/playground?engine=google_trends) — Test queries interactively
- [Dashboard](https://serpapi.com/dashboard) — Track API usage
