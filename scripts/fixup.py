"""Pass 2.6: rewrite the implication paragraph of any flagged brief.

Takes <slug>_<quarter>.flagged.md + <slug>_<quarter>.critique.jsonl, runs the
fixup prompt, writes the result back to <slug>_<quarter>.md (clean name).
The .flagged.md and .critique.jsonl files are kept on disk for audit.

Usage:
    python -m scripts.fixup bkng
    python -m scripts.fixup all
"""
import sys
import json

from .config import COMPANIES, OUTPUT_DIR, PROMPT_DIR, MODEL
from .llm import call

FIXUP_PROMPT_PATH = PROMPT_DIR / "fixup.md"


def fixup_one(slug: str):
    info = COMPANIES[slug]
    flagged = OUTPUT_DIR / f"{slug}_{info['raw_quarter']}.flagged.md"
    critique = OUTPUT_DIR / f"{slug}_{info['raw_quarter']}.critique.jsonl"
    out_path = OUTPUT_DIR / f"{slug}_{info['raw_quarter']}.md"

    if not flagged.exists():
        return None
    if not critique.exists():
        print(f"[{slug}] SKIP — no critique notes", file=sys.stderr)
        return None

    brief = flagged.read_text(encoding="utf-8")
    issues = []
    for line in critique.read_text().splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                issues.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    high_issues = [i for i in issues if i.get("severity") == "high"]
    if not high_issues:
        flagged.rename(out_path)
        print(f"[{slug}] no high-severity issues — restored brief", file=sys.stderr)
        return out_path

    notes_text = "\n".join(
        f"- [{i['severity']}] \"{i.get('quote','')}\" — {i.get('issue','')}; fix: {i.get('fix','')}"
        for i in issues
    )

    system = FIXUP_PROMPT_PATH.read_text(encoding="utf-8")
    user = (
        f"COMPANY: {info['name']} ({info['ticker']})\n"
        f"QUARTER: {info['raw_quarter']}\n\n"
        f"CRITIQUE NOTES:\n{notes_text}\n\n"
        f"FLAGGED BRIEF:\n\n{brief}\n"
    )

    print(f"[{slug}] fixup pass on {len(high_issues)} high-severity issues...", file=sys.stderr)
    response = call(system, user, model=MODEL, max_tokens=6000, temperature=0.2)

    out_path.write_text(response, encoding="utf-8")
    print(f"[{slug}] → {out_path.name} (rewritten)", file=sys.stderr)
    return out_path


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    if target == "all":
        for slug in COMPANIES:
            fixup_one(slug)
    else:
        if target not in COMPANIES:
            sys.exit(f"unknown company: {target}. valid: {list(COMPANIES)}")
        fixup_one(target)


if __name__ == "__main__":
    main()
