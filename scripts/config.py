import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
MODEL = os.getenv("DIGEST_MODEL", "anthropic/claude-sonnet-4.5")

QUARTER = "2026Q1"

COMPANIES = {
    "bkng": {"name": "Booking Holdings",  "ticker": "BKNG", "raw_quarter": "2026Q1"},
    "expe": {"name": "Expedia Group",     "ticker": "EXPE", "raw_quarter": "2025Q4"},
    "tcom": {"name": "Trip.com Group",    "ticker": "TCOM", "raw_quarter": "2025Q4"},
    "mmyt": {"name": "MakeMyTrip",        "ticker": "MMYT", "raw_quarter": "2026Q3"},
    "trip": {"name": "Tripadvisor",       "ticker": "TRIP", "raw_quarter": "2025Q4"},
}

RAW_DIR        = ROOT / "raw"
TRANSCRIPT_DIR = ROOT / "transcripts"
PROMPT_DIR     = ROOT / "prompts"
OUTPUT_DIR     = ROOT / "output"

EXTRACT_PROMPT_PATH    = PROMPT_DIR / "extract.md"
SYNTHESIZE_PROMPT_PATH = PROMPT_DIR / "synthesize.md"
