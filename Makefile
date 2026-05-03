.PHONY: install extract synthesize compose digest clean

install:
	python3 -m venv .venv
	. .venv/bin/activate && pip install python-dotenv

extract:
	. .venv/bin/activate && python -m scripts.extract all

synthesize:
	. .venv/bin/activate && python -m scripts.synthesize all

compose:
	. .venv/bin/activate && python -m scripts.compose

digest: extract synthesize compose
	@echo "→ output/digest_2026Q1.md"

clean:
	rm -rf transcripts/*.jsonl output/*.md
