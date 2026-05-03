"""Pass 2: turn extracted passages into Wego implication bullets.

Usage:
    python -m scripts.synthesize bkng
    python -m scripts.synthesize all
"""
import sys

from .config import COMPANIES, TRANSCRIPT_DIR, OUTPUT_DIR, SYNTHESIZE_PROMPT_PATH
from .llm import call


def synthesize_one(slug: str):
    info = COMPANIES[slug]
    in_path = TRANSCRIPT_DIR / f"{slug}_{info['raw_quarter']}.jsonl"
    out_path = OUTPUT_DIR / f"{slug}_{info['raw_quarter']}.md"

    if not in_path.exists():
        print(f"[{slug}] SKIP — no extracted passages at {in_path.name}", file=sys.stderr)
        return None

    passages = in_path.read_text(encoding="utf-8")
    if not passages.strip():
        print(f"[{slug}] SKIP — empty passages file", file=sys.stderr)
        return None

    system = SYNTHESIZE_PROMPT_PATH.read_text(encoding="utf-8")
    user = (
        f"COMPANY: {info['name']} ({info['ticker']})\n"
        f"QUARTER: {info['raw_quarter']}\n\n"
        f"EXTRACTED PASSAGES (one JSON per line):\n{passages}\n\n"
        f"Begin output with markdown heading: "
        f"`## {info['name']} ({info['ticker']}) · {info['raw_quarter']}`\n"
        f"Add a one-line italic summary of the call's overall stance (<=20 words), "
        f"then the bullets per the system prompt format."
    )

    n = sum(1 for line in passages.splitlines() if line.strip())
    print(f"[{slug}] synthesizing {n} passages...", file=sys.stderr)
    response = call(system, user, max_tokens=4000, temperature=0.3)
    out_path.write_text(response, encoding="utf-8")
    print(f"[{slug}] → {out_path.name}", file=sys.stderr)
    return out_path


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target == "all":
        for slug in COMPANIES:
            synthesize_one(slug)
    else:
        if target not in COMPANIES:
            sys.exit(f"unknown company: {target}. valid: {list(COMPANIES)}")
        synthesize_one(target)


if __name__ == "__main__":
    main()
