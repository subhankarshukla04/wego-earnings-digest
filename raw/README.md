# raw/ — earnings call transcripts

This folder is intentionally empty in the public repo. Transcripts are sourced from third-party financial-news sites (Investing.com, Seeking Alpha, etc.) and are not redistributed here for copyright reasons.

To reproduce the pipeline:

1. Pull the latest earnings call transcript for each ticker in `scripts/config.py`.
2. Save each as `raw/<slug>_<quarter>.txt` (e.g. `raw/bkng_2026Q1.txt`).
3. Run `make digest`.

The `transcripts/` folder (intermediate JSONL extractions) and `output/` folder (synthesized markdown briefs) ship in the repo so the strategic content is readable without re-running the pipeline.
