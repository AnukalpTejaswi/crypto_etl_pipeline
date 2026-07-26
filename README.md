# Crypto ETL Pipeline

An automated ETL pipeline that pulls live cryptocurrency market data from the
[CoinGecko](https://www.coingecko.com/en/api) public REST API, cleans it with
Pandas, and loads it into PostgreSQL on a daily schedule via cron.

```
Extract (CoinGecko API)  -->  Transform (Pandas)  -->  Load (PostgreSQL)
   pagination + retries        cleaning + typing        upsert on conflict
```

## Project structure

```
crypto_etl_pipeline/
├── src/
│   ├── config.py       # loads settings from .env
│   ├── extract.py       # pulls paginated data from CoinGecko, with retries
│   ├── transform.py      # cleans/normalizes raw JSON into a DataFrame
│   ├── load.py           # upserts the DataFrame into Postgres
│   └── pipeline.py       # orchestrates extract -> transform -> load
├── db/
│   └── schema.sql        # creates the crypto_prices table
├── tests/
│   └── test_transform.py # unit tests for the transform stage
├── logs/                  # pipeline.log and cron.log land here
├── .env.example           # copy to .env and fill in your DB credentials
├── requirements.txt
├── cron_setup.md          # how to schedule the daily run
└── run_pipeline.sh        # wrapper script for cron
```

## 1. Setup

```bash
cd crypto_etl_pipeline
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configure your database

Copy the env template and fill in your local Postgres credentials:

```bash
cp .env.example .env
# edit .env with your DB_USER / DB_PASSWORD / etc.
```

Create the database and table:

```bash
createdb crypto_etl                       # or create it via psql/pgAdmin
psql -U postgres -d crypto_etl -f db/schema.sql
```

## 3. Run it manually

```bash
python3 -m src.pipeline
```

You should see log output in your terminal and in `logs/pipeline.log`, ending
with something like:

```
=== ETL pipeline run finished successfully: 1000 rows loaded in 4.3s ===
```

## 4. Verify the data

```sql
SELECT coin_id, name, current_price, last_updated
FROM crypto_prices
ORDER BY market_cap_rank
LIMIT 10;
```

## 5. Schedule it daily

See [`cron_setup.md`](./cron_setup.md) for step-by-step cron setup.

## 6. Run the tests

```bash
pytest tests/ -v
```

## Design notes

- **Pagination**: CoinGecko caps each request at 250 results, so
  `extract.py` walks through `CG_TOTAL_PAGES` pages to build a top-N list
  (defaults to top 1000 coins).
- **Resilience**: each request has a hard timeout (`CG_REQUEST_TIMEOUT`) and
  retries with exponential backoff on timeouts, connection errors, and
  HTTP 429 (rate limiting). A page that fails permanently is skipped and
  logged rather than crashing the whole run.
- **Idempotency**: the `crypto_prices` table has a unique constraint on
  `(coin_id, last_updated)`. Re-running the pipeline for the same data
  updates existing rows instead of creating duplicates — safe to re-run
  after a failure.
- **Time-series correctness**: all timestamps are normalized to UTC on
  ingestion so cross-day / cross-timezone comparisons are reliable.
- **Honest nulls**: fields that are legitimately unknown (e.g.
  `total_supply` for uncapped coins) are kept as real `NULL` values rather
  than being zeroed out, which would be misleading for analysis.

## Extending this project

- Add a second table for historical time-series (`/coins/{id}/market_chart`)
  to enable trend analysis over time.
- Add a Slack/email alert on pipeline failure.
- Containerize with Docker Compose (app + Postgres) for easier deployment.
- Add data quality checks (e.g. Great Expectations) before loading.

## A note on this sandbox

This project was built and unit-tested in a sandboxed environment that
doesn't have network access to `api.coingecko.com`, so the transform logic
was verified against a realistic mocked API payload instead of a live call.
The extract/load code follows CoinGecko's actual documented response shape,
but **run `python3 -m src.pipeline` on your own machine** to do a live
end-to-end test before scheduling it with cron.
