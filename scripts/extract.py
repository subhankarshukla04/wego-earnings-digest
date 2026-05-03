"""Pass 1: extract Wego-relevant passages from a raw transcript.

Usage:
    python -m scripts.extract bkng
    python -m scripts.extract all
"""
import sys

from .config import COMPANIES, RAW_DIR, TRANSCRIPT_DIR, EXTRACT_PROMPT_PATH
from .llm import call


def extract_one(slug: str):
    info = COMPANIES[slug]
    raw_path = RAW_DIR / f"{slug}_{info['raw_quarter']}.txt"
    out_path = TRANSCRIPT_DIR / f"{slug}_{info['raw_quarter']}.jsonl"

    if not raw_path.exists():
        print(f"[{slug}] SKIP — no transcript at {raw_path.name}", file=sys.stderr)
        return None

    transcript = raw_path.read_text(encoding="utf-8", errors="ignore")
    if len(transcript) < 1000:
        print(f"[{slug}] SKIP — transcript suspiciously short ({len(transcript)} chars)", file=sys.stderr)
        return None

    system = EXTRACT_PROMPT_PATH.read_text(encoding="utf-8")
    user = (
        f"COMPANY: {info['name']} ({info['ticker']})\n"
        f"QUARTER: {info['raw_quarter']}\n\n"
        f"TRANSCRIPT:\n{transcript}\n"
    )

    print(f"[{slug}] extracting ({len(transcript):,} chars)...", file=sys.stderr)
    response = call(system, user, max_tokens=6000, temperature=0.1)

    lines = [l.strip() for l in response.splitlines()
             if l.strip().startswith("{") and l.strip().endswith("}")]

    if not lines:
        out_path.write_text(response, encoding="utf-8")
        sys.exit(f"[{slug}] no JSONL parsed; raw response saved to {out_path}")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[{slug}] {len(lines)} passages → {out_path.name}", file=sys.stderr)
    return out_path


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target == "all":
        for slug in COMPANIES:
            extract_one(slug)
    else:
        if target not in COMPANIES:
            sys.exit(f"unknown company: {target}. valid: {list(COMPANIES)}")
        extract_one(target)


if __name__ == "__main__":
    main()
