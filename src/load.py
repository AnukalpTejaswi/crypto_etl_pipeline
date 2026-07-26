"""
LOAD stage.

Writes the cleaned DataFrame into PostgreSQL using an "upsert" (INSERT ...
ON CONFLICT DO UPDATE) so that re-running the pipeline for the same day
updates existing rows instead of creating duplicates.
"""
import logging
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src import config

logger = logging.getLogger(__name__)

_UPSERT_SQL = text("""
    INSERT INTO crypto_prices (
        coin_id, symbol, name, current_price, market_cap, market_cap_rank,
        total_volume, price_change_24h, price_change_pct_24h, high_24h,
        low_24h, circulating_supply, total_supply, ath, ath_change_pct,
        last_updated
    ) VALUES (
        :coin_id, :symbol, :name, :current_price, :market_cap, :market_cap_rank,
        :total_volume, :price_change_24h, :price_change_pct_24h, :high_24h,
        :low_24h, :circulating_supply, :total_supply, :ath, :ath_change_pct,
        :last_updated
    )
    ON CONFLICT (coin_id, last_updated)
    DO UPDATE SET
        current_price = EXCLUDED.current_price,
        market_cap = EXCLUDED.market_cap,
        market_cap_rank = EXCLUDED.market_cap_rank,
        total_volume = EXCLUDED.total_volume,
        price_change_24h = EXCLUDED.price_change_24h,
        price_change_pct_24h = EXCLUDED.price_change_pct_24h,
        high_24h = EXCLUDED.high_24h,
        low_24h = EXCLUDED.low_24h,
        circulating_supply = EXCLUDED.circulating_supply,
        total_supply = EXCLUDED.total_supply,
        ath = EXCLUDED.ath,
        ath_change_pct = EXCLUDED.ath_change_pct,
        ingested_at = now();
""")


def get_engine() -> Engine:
    return create_engine(config.DATABASE_URL)


def load_market_data(df: pd.DataFrame, engine: Optional[Engine] = None) -> int:
    """
    Upsert every row of `df` into the crypto_prices table.
    Returns the number of rows written.
    """
    if df.empty:
        logger.warning("load_market_data received an empty DataFrame. Nothing to load.")
        return 0

    engine = engine or get_engine()
    records = df.to_dict(orient="records")

    with engine.begin() as conn:
        conn.execute(_UPSERT_SQL, records)

    logger.info("Loaded %d rows into crypto_prices.", len(records))
    return len(records)
