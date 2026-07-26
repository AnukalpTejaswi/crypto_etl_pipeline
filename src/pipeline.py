"""
Orchestrates the full ETL run: extract -> transform -> load.

Run manually:
    python -m src.pipeline

Run daily via cron (see cron_setup.md).
"""
import logging
import os
import sys
import time

from src import config
from src.extract import extract_market_data, ExtractionError
from src.transform import transform_market_data
from src.load import load_market_data


def _setup_logging() -> None:
    os.makedirs(config.LOG_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler(sys.stdout),
        ],
    )


def run() -> None:
    logger = logging.getLogger("pipeline")
    start = time.time()
    logger.info("=== ETL pipeline run started ===")

    try:
        raw_records = extract_market_data()
        clean_df = transform_market_data(raw_records)
        rows_loaded = load_market_data(clean_df)

        elapsed = time.time() - start
        logger.info(
            "=== ETL pipeline run finished successfully: %d rows loaded in %.1fs ===",
            rows_loaded, elapsed,
        )
    except ExtractionError as exc:
        logger.error("Pipeline aborted during extraction: %s", exc)
        sys.exit(1)
    except Exception:
        logger.exception("Pipeline failed with an unexpected error.")
        sys.exit(1)


if __name__ == "__main__":
    _setup_logging()
    run()
