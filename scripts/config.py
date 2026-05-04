import os
import json
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
MODEL = os.getenv("DIGEST_MODEL", "openai/gpt-oss-120b:free")
CRITIQUE_MODEL = os.getenv("CRITIQUE_MODEL", MODEL)

QUARTER = "2026Q1"

# Built-in roster. Manual additions live in data/companies_user.json and merge over this.
COMPANIES_BUILTIN = {
    "bkng": {"name": "Booking Holdings", "ticker": "BKNG", "raw_quarter": "2026Q1",  "call_date": "2026-04-30"},
    "expe": {"name": "Expedia Group",    "ticker": "EXPE", "raw_quarter": "2025Q4",  "call_date": "2026-02-06"},
    "mmyt": {"name": "MakeMyTrip",       "ticker": "MMYT", "raw_quarter": "2026Q3",  "call_date": "2026-01-22"},
    "trip": {"name": "Tripadvisor",      "ticker": "TRIP", "raw_quarter": "2025Q4",  "call_date": "2026-02-13"},
}

ROOT = ROOT  # keep
RAW_DIR        = ROOT / "raw"
TRANSCRIPT_DIR = ROOT / "transcripts"
PROMPT_DIR     = ROOT / "prompts"
OUTPUT_DIR     = ROOT / "output"
DATA_DIR       = ROOT / "data"

EXTRACT_PROMPT_PATH    = PROMPT_DIR / "extract.md"
SYNTHESIZE_PROMPT_PATH = PROMPT_DIR / "synthesize.md"
CRITIQUE_PROMPT_PATH   = PROMPT_DIR / "critique.md"

USER_COMPANIES_PATH = DATA_DIR / "companies_user.json"
FLAGS_PATH          = DATA_DIR / "flags.jsonl"


def _load_user_companies() -> dict:
    if not USER_COMPANIES_PATH.exists():
        return {}
    try:
        return json.loads(USER_COMPANIES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


COMPANIES: dict = {**COMPANIES_BUILTIN, **_load_user_companies()}
