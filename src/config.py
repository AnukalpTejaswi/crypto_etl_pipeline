"""
Loads all configuration from environment variables (via a .env file).
Keeping config in one place makes the rest of the pipeline easy to test
and to point at different databases/APIs without touching code.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # reads .env in the project root, if present


def _get_int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


# --- Database ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "crypto_etl")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# --- CoinGecko API ---
CG_BASE_URL = os.getenv("CG_BASE_URL", "https://api.coingecko.com/api/v3")
CG_VS_CURRENCY = os.getenv("CG_VS_CURRENCY", "usd")
CG_PER_PAGE = _get_int("CG_PER_PAGE", 250)       # CoinGecko max is 250
CG_TOTAL_PAGES = _get_int("CG_TOTAL_PAGES", 4)   # 4 pages * 250 = top 1000 coins
CG_REQUEST_TIMEOUT = _get_int("CG_REQUEST_TIMEOUT", 10)  # seconds
CG_MAX_RETRIES = _get_int("CG_MAX_RETRIES", 3)
CG_RETRY_BACKOFF = _get_int("CG_RETRY_BACKOFF", 2)  # seconds, doubles each retry

# --- Logging ---
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "pipeline.log")
