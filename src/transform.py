"""
TRANSFORM stage.

Converts raw, semi-structured JSON from CoinGecko into a clean,
analytics-ready Pandas DataFrame that matches the `crypto_prices` table.
"""
import logging
from typing import List, Dict, Any

import pandas as pd

logger = logging.getLogger(__name__)

# Maps CoinGecko's raw field names -> our normalized column names
COLUMN_MAP = {
    "id": "coin_id",
    "symbol": "symbol",
    "name": "name",
    "current_price": "current_price",
    "market_cap": "market_cap",
    "market_cap_rank": "market_cap_rank",
    "total_volume": "total_volume",
    "price_change_24h": "price_change_24h",
    "price_change_percentage_24h": "price_change_pct_24h",
    "high_24h": "high_24h",
    "low_24h": "low_24h",
    "circulating_supply": "circulating_supply",
    "total_supply": "total_supply",
    "ath": "ath",
    "ath_change_percentage": "ath_change_pct",
    "last_updated": "last_updated",
}

NUMERIC_COLUMNS = [
    "current_price", "market_cap", "market_cap_rank", "total_volume",
    "price_change_24h", "price_change_pct_24h", "high_24h", "low_24h",
    "circulating_supply", "total_supply", "ath", "ath_change_pct",
]


def transform_market_data(raw_records: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Clean and normalize the raw list of coin dicts into a DataFrame ready
    for loading into PostgreSQL.
    """
    if not raw_records:
        logger.warning("transform_market_data received an empty list.")
        return pd.DataFrame(columns=list(COLUMN_MAP.values()))

    df = pd.DataFrame(raw_records)

    # Keep only the columns we care about (CoinGecko sometimes adds/removes fields)
    available_cols = [c for c in COLUMN_MAP if c in df.columns]
    df = df[available_cols].rename(columns=COLUMN_MAP)

    # --- Time-series standardization ---
    # Normalize all timestamps to UTC-aware datetimes so they compare
    # correctly regardless of the server's local timezone.
    df["last_updated"] = pd.to_datetime(df["last_updated"], utc=True, errors="coerce")

    # --- Null handling ---
    # Drop rows with no coin_id or no timestamp -- these aren't usable records.
    before = len(df)
    df = df.dropna(subset=["coin_id", "last_updated"])
    dropped = before - len(df)
    if dropped:
        logger.warning("Dropped %d record(s) missing coin_id/last_updated.", dropped)

    # Numeric fields: coerce bad values to NaN, then fill with 0 where it's
    # safe to assume "no data" == "none reported" (e.g. total_supply can be
    # legitimately absent for uncapped coins).
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # market_cap_rank has no meaningful "unknown" value, so 0 is fine there.
    # total_supply is intentionally NOT filled -- many coins (e.g. Ethereum) have
    # no fixed cap, and a real NULL in Postgres is more honest than a fake 0.
    df["market_cap_rank"] = df["market_cap_rank"].fillna(0)

    # Text fields: normalize case/whitespace for consistent joins/filtering downstream
    df["coin_id"] = df["coin_id"].str.strip().str.lower()
    df["symbol"] = df["symbol"].str.strip().str.lower()
    df["name"] = df["name"].str.strip()

    # Deduplicate: keep the latest record per (coin_id, last_updated) pair
    df = df.drop_duplicates(subset=["coin_id", "last_updated"], keep="last")

    logger.info("Transformation complete: %d clean records ready to load.", len(df))
    return df.reset_index(drop=True)
