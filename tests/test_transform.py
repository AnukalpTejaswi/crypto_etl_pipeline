"""
Unit tests for the transform stage. Run with:
    pytest tests/
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from src.transform import transform_market_data


SAMPLE_RAW = [
    {
        "id": "bitcoin", "symbol": "BTC", "name": " Bitcoin ",
        "current_price": 65000.12, "market_cap": 1280000000000,
        "market_cap_rank": 1, "total_volume": 25000000000,
        "price_change_24h": 500.5, "price_change_percentage_24h": 0.77,
        "high_24h": 65500, "low_24h": 64000,
        "circulating_supply": 19700000, "total_supply": 21000000,
        "ath": 73000, "ath_change_percentage": -10.9,
        "last_updated": "2026-07-23T11:40:00.000Z",
    },
    {
        "id": "ethereum", "symbol": "eth", "name": "Ethereum",
        "current_price": 3400.5, "market_cap": 410000000000,
        "market_cap_rank": 2, "total_volume": 12000000000,
        "price_change_24h": None, "price_change_percentage_24h": None,
        "high_24h": 3450, "low_24h": 3350,
        "circulating_supply": 120000000, "total_supply": None,
        "ath": 4800, "ath_change_percentage": -29.2,
        "last_updated": "2026-07-23T11:40:00.000Z",
    },
]


def test_transform_returns_expected_row_count():
    df = transform_market_data(SAMPLE_RAW)
    assert len(df) == 2


def test_drops_records_missing_coin_id():
    broken = SAMPLE_RAW + [{"id": None, "last_updated": "2026-07-23T11:40:00.000Z"}]
    df = transform_market_data(broken)
    assert len(df) == 2  # broken record dropped


def test_timestamps_are_utc():
    df = transform_market_data(SAMPLE_RAW)
    assert str(df["last_updated"].dt.tz) == "UTC"


def test_text_fields_normalized():
    df = transform_market_data(SAMPLE_RAW)
    row = df[df["coin_id"] == "bitcoin"].iloc[0]
    assert row["symbol"] == "btc"        # lowercased
    assert row["name"] == "Bitcoin"      # whitespace stripped


def test_empty_input_returns_empty_dataframe():
    df = transform_market_data([])
    assert df.empty


def test_null_total_supply_preserved_not_zeroed():
    # Ethereum has no fixed supply cap -> CoinGecko sends null. We should
    # keep that as a real NULL, not silently turn it into a fake 0.
    df = transform_market_data(SAMPLE_RAW)
    eth_row = df[df["coin_id"] == "ethereum"].iloc[0]
    assert pd.isna(eth_row["total_supply"])
