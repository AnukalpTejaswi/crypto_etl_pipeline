-- Run this once to set up the database schema:
--   psql -U postgres -d crypto_etl -f db/schema.sql

CREATE TABLE IF NOT EXISTS crypto_prices (
    id                  BIGSERIAL PRIMARY KEY,
    coin_id             TEXT        NOT NULL,        -- e.g. "bitcoin"
    symbol              TEXT        NOT NULL,        -- e.g. "btc"
    name                TEXT        NOT NULL,        -- e.g. "Bitcoin"
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
    last_updated        TIMESTAMPTZ,                 -- timestamp from CoinGecko
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT now(), -- when we pulled it

    -- one row per coin per day (dedupe on repeated daily runs)
    UNIQUE (coin_id, last_updated)
);

-- Speeds up time-series queries per coin
CREATE INDEX IF NOT EXISTS idx_crypto_prices_coin_time
    ON crypto_prices (coin_id, last_updated DESC);

-- Speeds up "give me today's snapshot for all coins" queries
CREATE INDEX IF NOT EXISTS idx_crypto_prices_ingested_at
    ON crypto_prices (ingested_at DESC);
