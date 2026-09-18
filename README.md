# Automated API-to-Database ETL Pipeline

An automated Python ETL pipeline that extracts live crypto market data from the CoinGecko
REST API, transforms it with Pandas, and loads it into a PostgreSQL database — running
unattended on a daily cron schedule.

## Tech Stack
Python · Pandas · PostgreSQL · REST APIs (CoinGecko) · Cron

## About

**What:** A fully automated ETL pipeline that extracts ~1,000 daily JSON records from the
CoinGecko REST API, transforms them with Pandas (temporal normalization, feature generation,
missing-value imputation), and loads clean, structured data into PostgreSQL — running
unattended via cron.

**Why:** Real-world data pipelines don't just move data — they have to survive pagination
limits, network timeouts, inconsistent API responses, and missing values without breaking.
This project was built to practice designing a pipeline that handles those failure points
gracefully end to end, rather than working from a clean CSV handed to you upfront.

**Use case:** Produces a continuously growing, analysis-ready historical dataset of crypto
market metrics — the kind of foundation needed for trend analysis, price-movement research,
or feeding into a downstream dashboard or ML model, without anyone manually re-running
scripts every day.

## Architecture

```
CoinGecko API  -->  extract.py  -->  Pandas transform  -->  PostgreSQL
   (JSON)         (pagination,        (clean, normalize,      (daily table)
                  retry/timeout        impute, engineer
                    handling)           features)
                        |
                        v
                  cron (daily trigger)
```

## Data Pipeline

1. **Extract** — Pulls market data from the CoinGecko API (e.g. `/coins/markets`), handling
   pagination across multiple pages and retrying on network timeouts or rate-limit responses.
2. **Transform** — Uses Pandas to:
   - Normalize timestamps to a consistent timezone/format
   - Generate derived features (e.g. day-over-day % change, rolling averages)
   - Impute or flag missing values (e.g. missing `market_cap` or `total_volume`)
3. **Load** — Inserts the cleaned records into PostgreSQL, appending to a historical table
   keyed by coin ID and date.
4. **Schedule** — A cron job runs the pipeline once daily, fully unattended.

## Project Structure

```
.
├── extract.py          # Pulls raw JSON data from CoinGecko API
├── transform.py         # Pandas cleaning, normalization, feature engineering
├── load.py              # Loads transformed data into PostgreSQL
├── pipeline.py           # Orchestrates extract -> transform -> load
├── schema.sql            # PostgreSQL table definition(s)
├── config.py             # API endpoint, DB connection settings (no secrets committed)
├── requirements.txt      # Python dependencies
└── README.md
```

## Schema

```sql
CREATE TABLE IF NOT EXISTS crypto_prices (
    id                  BIGSERIAL PRIMARY KEY,
    coin_id             TEXT        NOT NULL,
    symbol              TEXT        NOT NULL,
    name                TEXT        NOT NULL,
    current_price       NUMERIC(24, 8),
    market_cap          NUMERIC(24, 2),
    market_cap_rank     INTEGER,
    total_volume        NUMERIC(24, 2),
    price_change_24h    NUMERIC(24, 8),
    price_change_pct_24h NUMERIC(10, 4),
    high_24h            NUMERIC(24, 8),
    low_24h              NUMERIC(24, 8),
    circulating_supply  NUMERIC(30, 4),
    total_supply        NUMERIC(30, 4),
    ath                 NUMERIC(24, 8),
    ath_change_pct      NUMERIC(10, 4),
    last_updated        TIMESTAMPTZ,
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (coin_id, last_updated)
);
```

## Data Quality Handling

- **Pagination** — Loops through all result pages until the API returns an empty page.
- **Network timeouts** — Retries failed requests with exponential backoff before giving up.
- **Missing values** — Numeric fields (e.g. `market_cap`) are imputed or explicitly flagged
  rather than silently dropped, so downstream analysis knows what's estimated vs. real.
- **Duplicate prevention** — `(coin_id, date_recorded)` as a composite primary key prevents
  the same coin/day from being loaded twice if the cron job re-runs.

## How to Reproduce

```bash
# 1. Clone and install dependencies
git clone <repo-url>
cd coingecko-etl-pipeline
pip install -r requirements.txt

# 2. Set up the database
createdb coingecko_data
psql -U postgres -d coingecko_data -f schema.sql

# 3. Configure API and DB settings
cp config.example.py config.py
# edit config.py with your DB credentials

# 4. Run the pipeline manually once to verify
python pipeline.py

# 5. Schedule it to run daily via cron
crontab -e
# add: 0 6 * * * /usr/bin/python3 /path/to/pipeline.py >> /path/to/logs/etl.log 2>&1
```

## Future Improvements

- Add data validation checks (e.g. Great Expectations) before load
- Containerize with Docker for easier deployment
- Add alerting (email/Slack) on pipeline failure
- Expand to historical backfill via `/coins/{id}/market_chart`
