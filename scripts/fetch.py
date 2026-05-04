"""
Earnings call transcript fetcher.

Tries multiple public sources in order, returns first success.
Writes to raw/<ticker>_<quarter>.txt.

Usage:
    python -m scripts.fetch <ticker>          # fetch one
    python -m scripts.fetch all               # fetch all configured

Sources tried, in order:
    1. Motley Fool transcript pages
    2. Investing.com transcript pages
    3. Seeking Alpha (often 403, included as last resort)

A transcript is accepted if it has >= 4000 chars AND contains at least
two of: "Operator", "Question", "earnings call", "thank you", a known speaker.
"""

from __future__ import annotations
import sys
import ssl
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Iterable
import certifi
from bs4 import BeautifulSoup

from .config import COMPANIES, RAW_DIR

_SSL_CTX = ssl.create_default_context(cafile=certifi.where())
_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
MIN_LEN = 4000
ACCEPT_MARKERS = ("Operator", "Question", "earnings call", "thank you", "Q&A")


def _http_get(url: str, timeout: int = 30) -> str | None:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": _UA,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX) as r:
            charset = r.headers.get_content_charset() or "utf-8"
            return r.read().decode(charset, errors="ignore")
    except urllib.error.HTTPError as e:
        print(f"    [{e.code}] {url}", file=sys.stderr)
    except Exception as e:
        print(f"    [err] {url} :: {e}", file=sys.stderr)
    return None


def _html_to_text(html: str, container_selector: str | None = None) -> str:
    soup = BeautifulSoup(html, "html.parser")
    if container_selector:
        node = soup.select_one(container_selector)
        if node:
            soup = node
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    text = soup.get_text("\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _accept(text: str) -> bool:
    if len(text) < MIN_LEN:
        return False
    hits = sum(1 for m in ACCEPT_MARKERS if m.lower() in text.lower())
    return hits >= 2


def _try_motley_fool(ticker: str, quarter: str) -> str | None:
    yr = quarter[:4]
    q = quarter[-2:].lower()
    candidates = [
        f"https://www.fool.com/earnings/call-transcripts/{yr}/{ticker.lower()}-{q}-{yr}-earnings-call-transcript/",
        f"https://www.fool.com/earnings/call-transcripts/{yr}/{ticker.lower()}-q{q[-1]}-{yr}-earnings-call-transcript/",
    ]
    for url in candidates:
        html = _http_get(url)
        if not html:
            continue
        text = _html_to_text(html, "article")
        if _accept(text):
            return text
    return None


def _try_investing(ticker: str, quarter: str) -> str | None:
    qslug = quarter.replace("Q", "-q").lower()
    candidates = [
        f"https://www.investing.com/news/transcripts/earnings-call-transcript-{ticker.lower()}-{qslug}",
        f"https://www.investing.com/news/stock-market-news/earnings-call-transcript-{ticker.lower()}-{qslug}",
    ]
    for url in candidates:
        html = _http_get(url)
        if not html:
            continue
        text = _html_to_text(html, "article")
        if _accept(text):
            return text
    return None


def _try_seeking_alpha(ticker: str, quarter: str) -> str | None:
    qnum = quarter[-2:].lower()
    yr = quarter[:4]
    url = (
        f"https://seekingalpha.com/article/"
        f"{ticker.lower()}-{qnum}-{yr}-earnings-call-transcript"
    )
    html = _http_get(url)
    if not html:
        return None
    text = _html_to_text(html, "article")
    if _accept(text):
        return text
    return None


SOURCES = (_try_motley_fool, _try_investing, _try_seeking_alpha)


def fetch_one(slug: str) -> Path | None:
    cfg = COMPANIES.get(slug)
    if not cfg:
        sys.exit(f"unknown slug: {slug}")
    ticker = cfg["ticker"]
    quarter = cfg["raw_quarter"]
    out_path = RAW_DIR / f"{slug}_{quarter}.txt"
    if out_path.exists() and out_path.stat().st_size > MIN_LEN:
        print(f"✓ {slug} :: already on disk ({out_path.stat().st_size} bytes)")
        return out_path

    print(f"→ fetching {ticker} {quarter}")
    for fn in SOURCES:
        text = fn(ticker, quarter)
        if text:
            RAW_DIR.mkdir(parents=True, exist_ok=True)
            out_path.write_text(text, encoding="utf-8")
            print(f"  ✓ {fn.__name__} :: {len(text)} chars → {out_path.name}")
            return out_path
        time.sleep(1)
    print(f"  ✗ {slug} :: all sources failed — fetch transcript manually")
    return None


def fetch_all() -> list[Path]:
    paths: list[Path] = []
    for slug in COMPANIES:
        p = fetch_one(slug)
        if p:
            paths.append(p)
    return paths


def main(argv: Iterable[str]) -> None:
    args = list(argv)
    if not args:
        sys.exit("usage: python -m scripts.fetch <ticker|all>")
    if args[0] == "all":
        fetch_all()
    else:
        fetch_one(args[0])


if __name__ == "__main__":
    main(sys.argv[1:])
