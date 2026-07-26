"""
EXTRACT stage.

Pulls live market data from the CoinGecko public REST API.

Handles:
  - Pagination (CoinGecko returns max 250 coins per page)
  - Network timeouts (each request has a hard timeout)
  - Transient failures (retries with exponential backoff)
  - Rate limiting (CoinGecko's free tier throttles aggressive polling)
"""
import logging
import time
from typing import List, Dict, Any

import requests

from src import config

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Raised when a page of data cannot be fetched after all retries."""


def _fetch_page(session: requests.Session, page: int) -> List[Dict[str, Any]]:
    """Fetch a single page of coin market data, retrying on failure."""
    params = {
        "vs_currency": config.CG_VS_CURRENCY,
        "order": "market_cap_desc",
        "per_page": config.CG_PER_PAGE,
        "page": page,
        "sparkline": "false",
        "price_change_percentage": "24h",
    }
    url = f"{config.CG_BASE_URL}/coins/markets"

    backoff = config.CG_RETRY_BACKOFF
    last_exception = None

    for attempt in range(1, config.CG_MAX_RETRIES + 1):
        try:
            response = session.get(
                url, params=params, timeout=config.CG_REQUEST_TIMEOUT
            )

            # CoinGecko returns 429 when rate limited -- back off and retry
            if response.status_code == 429:
                logger.warning(
                    "Rate limited on page %s (attempt %s/%s). Backing off %ss.",
                    page, attempt, config.CG_MAX_RETRIES, backoff,
                )
                time.sleep(backoff)
                backoff *= 2
                continue

            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                raise ExtractionError(f"Unexpected response shape on page {page}: {data}")

            logger.info("Fetched page %s (%d records).", page, len(data))
            return data

        except (requests.Timeout, requests.ConnectionError) as exc:
            last_exception = exc
            logger.warning(
                "Network error on page %s (attempt %s/%s): %s. Retrying in %ss.",
                page, attempt, config.CG_MAX_RETRIES, exc, backoff,
            )
            time.sleep(backoff)
            backoff *= 2

        except requests.HTTPError as exc:
            last_exception = exc
            logger.error("HTTP error on page %s: %s", page, exc)
            break  # don't retry on non-429 HTTP errors (e.g. 404, 400)

    raise ExtractionError(
        f"Failed to fetch page {page} after {config.CG_MAX_RETRIES} attempts"
    ) from last_exception


def extract_market_data() -> List[Dict[str, Any]]:
    """
    Fetch live market data for the top N coins (N = CG_TOTAL_PAGES * CG_PER_PAGE),
    walking through all pages. Skips a page (logs + continues) rather than
    failing the whole run if one page permanently fails, so a single bad page
    doesn't block the rest of the day's ingestion.
    """
    all_records: List[Dict[str, Any]] = []

    with requests.Session() as session:
        session.headers.update({"Accept": "application/json"})

        for page in range(1, config.CG_TOTAL_PAGES + 1):
            try:
                page_data = _fetch_page(session, page)
                all_records.extend(page_data)
            except ExtractionError as exc:
                logger.error("Skipping page %s: %s", page, exc)
                continue

    if not all_records:
        raise ExtractionError("No data extracted from any page. Aborting pipeline run.")

    logger.info("Extraction complete: %d total records.", len(all_records))
    return all_records
