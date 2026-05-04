"""Pass 2.5: hallucination check on per-company brief.

Reads each output/<slug>_<quarter>.md, runs the critique prompt, writes
output/<slug>_<quarter>.critique.jsonl with any flagged issues.

If the critique flags HIGH-severity issues, the original brief is renamed to
<slug>_<quarter>.flagged.md so it does not appear in the digest until a human
reviews and renames it back.

Usage:
    python -m scripts.critique bkng
    python -m scripts.critique all
"""
import sys
import json

from .config import COMPANIES, OUTPUT_DIR, CRITIQUE_PROMPT_PATH, CRITIQUE_MODEL
from .llm import call


def critique_one(slug: str):
    info = COMPANIES[slug]
    md_path = OUTPUT_DIR / f"{slug}_{info['raw_quarter']}.md"
    out_path = OUTPUT_DIR / f"{slug}_{info['raw_quarter']}.critique.jsonl"

    if not md_path.exists():
        print(f"[{slug}] SKIP — no brief at {md_path.name}", file=sys.stderr)
        return None

    brief = md_path.read_text(encoding="utf-8")
    system = CRITIQUE_PROMPT_PATH.read_text(encoding="utf-8")
    user = (
        f"COMPANY: {info['name']} ({info['ticker']})\n"
        f"QUARTER: {info['raw_quarter']}\n\n"
        f"BRIEF:\n\n{brief}\n"
    )

    print(f"[{slug}] critiquing brief ({len(brief):,} chars)...", file=sys.stderr)
    response = call(system, user, model=CRITIQUE_MODEL, max_tokens=2000, temperature=0.0)

    lines = [l.strip() for l in response.splitlines() if l.strip()]
    issues = []
    for line in lines:
        if line.startswith("{") and line.endswith("}"):
            try:
                issues.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    out_path.write_text(
        ("\n".join(json.dumps(i) for i in issues) + "\n") if issues else "",
        encoding="utf-8",
    )

    high = [i for i in issues if i.get("severity") == "high"]
    med = [i for i in issues if i.get("severity") == "medium"]
    low = [i for i in issues if i.get("severity") == "low"]
    print(
        f"[{slug}] critique :: {len(high)} high / {len(med)} medium / {len(low)} low",
        file=sys.stderr,
    )

    if high:
        flagged = OUTPUT_DIR / f"{slug}_{info['raw_quarter']}.flagged.md"
        md_path.rename(flagged)
        print(
            f"[{slug}] HIGH-severity issues — brief moved to {flagged.name}",
            file=sys.stderr,
        )
    return out_path


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target == "all":
        for slug in COMPANIES:
            critique_one(slug)
    else:
        if target not in COMPANIES:
            sys.exit(f"unknown company: {target}. valid: {list(COMPANIES)}")
        critique_one(target)


if __name__ == "__main__":
    main()
