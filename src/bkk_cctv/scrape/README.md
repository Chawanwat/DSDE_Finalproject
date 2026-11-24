# Additional data sources (required task)

Need **3 simple sources** (requests / APIs) **or 1 interactive source** (Playwright).
One module per source. Each exposes `fetch() -> pandas.DataFrame` and saves to
`data/external/<source>.parquet`.

| Module | Source | Status |
|---|---|---|
| `weather.py` | Hourly weather (rain affects traffic) | stub |
| `holidays.py` | Thai public holidays | stub |
| `source3.py` | TBD (e.g. events, PM2.5, traffic incidents) | stub |
