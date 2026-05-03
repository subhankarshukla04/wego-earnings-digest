"""Pass 3: stitch all per-company briefs into the final digest, with an executive summary on top.

Usage:
    python -m scripts.compose
"""
import sys
from datetime import datetime, timezone

from .config import COMPANIES, QUARTER, OUTPUT_DIR
from .llm import call


def main():
    sections = []
    missing = []
    for slug, info in COMPANIES.items():
        path = OUTPUT_DIR / f"{slug}_{info['raw_quarter']}.md"
        if path.exists() and path.stat().st_size > 0:
            sections.append(path.read_text(encoding="utf-8").strip())
        else:
            missing.append(slug)

    if not sections:
        sys.exit("no per-company sections found in output/. run synthesize.py first.")

    if missing:
        print(f"[compose] missing sections: {missing} — running with {len(sections)}/5", file=sys.stderr)

    body = "\n\n---\n\n".join(sections)

    print("[compose] generating executive summary...", file=sys.stderr)
    summary_system = (
        "You are the Wego VP of Strategy & Planning's chief of staff. "
        "Read these per-company strategic briefs and write a 5-bullet executive summary "
        "for Ned Terziev (VP Strategy) to forward to Ross Veitch (CEO). "
        "Each bullet: 1 line of the most strategically important cross-cutting signal across the calls. "
        "Lead with the highest-impact bullet. No filler, no 'in summary' framing — just the 5 bullets."
    )
    summary_user = f"QUARTER: {QUARTER}\n\nPER-COMPANY BRIEFS:\n\n{body}\n"
    summary = call(summary_system, summary_user, max_tokens=900, temperature=0.3).strip()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    final = (
        f"# Wego Quarterly Strategic Digest · {QUARTER}\n\n"
        f"*Synthesised from public earnings call transcripts. "
        f"Read time: 8 minutes. Generated {today}.*\n\n"
        f"## Executive summary — five things Ross should know this quarter\n\n"
        f"{summary}\n\n---\n\n"
        f"{body}\n\n---\n\n"
        f"*Built by Subhankar Shukla. "
        f"Pipeline: public earnings transcripts → LLM extraction (Wego-relevance lenses) → "
        f"LLM synthesis (per-passage Wego implication) → composition. "
        f"Cadence: quarterly, ~5 minutes of compute per run.*\n"
    )

    out = OUTPUT_DIR / f"digest_{QUARTER}.md"
    out.write_text(final, encoding="utf-8")
    print(f"[compose] → {out.name} ({len(final):,} chars)", file=sys.stderr)


if __name__ == "__main__":
    main()
