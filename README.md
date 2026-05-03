# Wego Earnings Digest

Quarterly competitive-intelligence pipeline for Wego Strategy & Planning. Extracts MENA / India / SEA / AI-distribution / capital-flow signal from public earnings calls of five named competitors and synthesises a one-page-per-company strategic brief with explicit "implication for Wego" lines.

## What's in this repo

```
raw/                  # downloaded earnings transcripts (gitignored)
  bkng_2026Q1.txt     # Booking Holdings (Apr 28, 2026) — fully captured
  expe_2025Q4.txt     # Expedia Group (Feb 12, 2026) — captured
  mmyt_2026Q3.txt     # MakeMyTrip (Jan 21, 2026) — captured
  trip_2025Q4.txt     # Tripadvisor (Feb 12, 2026) — captured (partial verbatim)
  tcom_2025Q4.PENDING.md  # Trip.com — manual paste required (copyright filter blocked WebFetch)

scripts/
  config.py           # company list, paths, model
  llm.py              # OpenRouter wrapper with retry
  extract.py          # transcript → JSONL of Wego-relevant passages
  synthesize.py       # passages → per-company markdown brief
  compose.py          # stitch all + auto-generate exec summary

prompts/
  extract.md          # what to extract and how
  synthesize.md       # how to write Wego-implication bullets

transcripts/          # gitignored — extraction output
output/               # gitignored — synthesis + final digest
```

## Companies in scope (Q1 2026 cycle)

| Slug | Company | Quarter used | Why it matters for Wego |
|---|---|---|---|
| `bkng` | Booking Holdings | Q1 2026 (Apr 28) | Largest OTA globally; just cut FY guidance on Iran-war disruption; 2pp MENA hit |
| `expe` | Expedia Group | Q4 2025 (Feb 12) | Direct meta-distribution rival; agentic-browser commentary; OpenAI/Google AI partner |
| `tcom` | Trip.com Group | Q4 2025 (Feb 25) | APAC dominance; closest scale comp in Asia |
| `mmyt` | MakeMyTrip | Q3 FY2026 (Jan 21) | India outbound competitor; same GCC↔India corridor |
| `trip` | Tripadvisor | Q4 2025 (Feb 12) | Meta + reviews; AI-confidence-gap framing |

Note on quarters: only BKNG Q1 2026 is currently released. Others use the most recent available call (Q4 2025 / Q3 FY2026). Once TRIP, EXPE, TCOM, and MMYT publish their Q1 2026 results in May–Jun 2026, drop the new transcripts into `raw/` and rerun the pipeline.

## How to run

### One-time setup

```bash
cd ~/Desktop/wego-earnings-digest
make install                          # creates venv, installs python-dotenv
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY=sk-or-v1-... (real key)
```

### Add the missing TCOM transcript

```bash
# Open https://www.investing.com/news/transcripts/earnings-call-transcript-tripcom-q4-2025-beats-forecasts-stock-dips-93CH-4526362
# Select all, copy, paste into raw/tcom_2025Q4.txt
# Then delete tcom_2025Q4.PENDING.md
```

### Run the pipeline

```bash
make digest
# → output/digest_2026Q1.md
```

Or step by step:

```bash
make extract       # all 5 (or 4) companies → transcripts/*.jsonl
make synthesize    # → output/<slug>_<quarter>.md
make compose       # → output/digest_2026Q1.md
```

Or one company at a time (useful for prompt iteration):

```bash
.venv/bin/python -m scripts.extract bkng
.venv/bin/python -m scripts.synthesize bkng
```

## Output

The final `output/digest_2026Q1.md` contains:

1. A 5-bullet executive summary (auto-generated, cross-cutting signal across all calls)
2. One markdown section per company with:
   - Header: ticker, quarter, italic one-line stance summary
   - 6–10 strategic bullets, each: verbatim quote + speaker + Wego implication line

## Cost & cadence

- Per-run cost: ~$0.30–0.80 in OpenRouter credits (5 transcripts × 2 LLM passes + 1 compose pass with Sonnet)
- Quarterly cadence: drop in new transcripts, run `make digest`, edit output by hand if needed, share with Ned
- Wall time: ~5 minutes of compute

## Built by

Subhankar Shukla — interview deliverable for Wego NOC role with Nedyalko Terziev.
