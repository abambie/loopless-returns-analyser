"""Application configuration and shared visual constants.

The portfolio edition runs with a local SQLite database by default. MySQL is
still supported, but credentials must be supplied through environment
variables and are never stored in the repository.
"""

from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

CSV_PATH = Path(
    os.getenv(
        "LOOPLESS_CSV_PATH",
        str(DATA_DIR / "fashion_boutique_dataset_with_return_date.csv"),
    )
)
MODEL_DIR = Path(os.getenv("LOOPLESS_MODEL_DIR", str(BASE_DIR / "models")))

DB_BACKEND = os.getenv("LOOPLESS_DB_BACKEND", "sqlite").strip().lower()
if DB_BACKEND not in {"sqlite", "mysql"}:
    raise ValueError("LOOPLESS_DB_BACKEND must be either 'sqlite' or 'mysql'.")

SQLITE_PATH = Path(
    os.getenv("LOOPLESS_SQLITE_PATH", str(DATA_DIR / "loopless.db"))
)


def get_mysql_config() -> dict[str, str]:
    """Return validated MySQL settings sourced only from the environment."""

    values = {
        "host": os.getenv("LOOPLESS_MYSQL_HOST", ""),
        "user": os.getenv("LOOPLESS_MYSQL_USER", ""),
        "password": os.getenv("LOOPLESS_MYSQL_PASSWORD", ""),
        "database": os.getenv("LOOPLESS_MYSQL_DATABASE", ""),
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        names = ", ".join(f"LOOPLESS_MYSQL_{name.upper()}" for name in missing)
        raise RuntimeError(f"Missing MySQL environment variables: {names}")
    return values


REQUIRED_COLS = [
    "product_id",
    "category",
    "brand",
    "season",
    "size",
    "color",
    "original_price",
    "markdown_percentage",
    "current_price",
    "purchase_date",
    "stock_quantity",
    "customer_rating",
    "is_returned",
    "return_reason",
    "return_date",
]

# Shared colour palette
BG = "#264e3d"
BG_DARK = "#1a3d2e"
CARD = "#fffef2"
TEXT = "#1f2937"
TEXT_2 = "#374151"
TEXT_MUTED = "#9ca3af"
ACCENT_G = "#2d5f4a"
BORDER = "#e5e7eb"
HIGH = "#ec4899"
MEDIUM = "#f59e0b"
LOW = "#10b981"
TEAL = "#14b8a6"
WHITE = "#FFFFFF"

GREEN = ACCENT_G
CARD_BG = CARD
DARK_GREEN = BG_DARK
SIDEBAR_BG = BG_DARK
CONTENT_BG = BG
LIGHT = CARD
