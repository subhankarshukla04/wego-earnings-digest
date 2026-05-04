"""Flask reader for the Wego Earnings Digest."""
from __future__ import annotations
import json
import re
import subprocess
import sys
import threading
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import markdown as md
from flask import Flask, abort, jsonify, render_template, redirect, request, url_for

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.config import (  # noqa: E402
    COMPANIES, QUARTER, OUTPUT_DIR, RAW_DIR,
    USER_COMPANIES_PATH, FLAGS_PATH, DATA_DIR,
)

app = Flask(__name__, static_folder="static", template_folder="templates")

_PIPELINE_STATE: dict = {
    "running": False, "step": None, "log": [],
    "started_at": None, "ended_at": None,
}

PIPELINE_STEPS = [
    ("fetch",      ["scripts.fetch", "all"],      "Pull latest transcripts"),
    ("extract",    ["scripts.extract", "all"],    "Filter Wego-relevant passages"),
    ("synthesize", ["scripts.synthesize", "all"], "Write per-company briefs"),
    ("critique",   ["scripts.critique", "all"],   "Hallucination check"),
    ("fixup",      ["scripts.fixup", "all"],      "Rewrite flagged claims"),
    ("compose",    ["scripts.compose"],           "Stitch the digest"),
]


def _list_editions() -> list[dict]:
    out = []
    for f in sorted(OUTPUT_DIR.glob("digest_*.md")):
        m = re.match(r"digest_(\d{4}Q\d)\.md$", f.name)
        if not m:
            continue
        out.append({
            "quarter": m.group(1),
            "mtime": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc),
            "size_kb": f.stat().st_size // 1024,
        })
    return list(reversed(out))


def _age_days(date_str: str | None) -> int | None:
    if not date_str:
        return None
    try:
        d = datetime.fromisoformat(date_str)
    except ValueError:
        return None
    today = datetime.now(timezone.utc).date()
    return (today - d.date()).days


def _list_companies(quarter: str) -> list[dict]:
    out = []
    for slug, info in COMPANIES.items():
        path = OUTPUT_DIR / f"{slug}_{info['raw_quarter']}.md"
        flagged = OUTPUT_DIR / f"{slug}_{info['raw_quarter']}.flagged.md"
        critique = OUTPUT_DIR / f"{slug}_{info['raw_quarter']}.critique.jsonl"
        critique_n = high_n = 0
        if critique.exists():
            for line in critique.read_text().splitlines():
                line = line.strip()
                if not line.startswith("{"):
                    continue
                critique_n += 1
                try:
                    if json.loads(line).get("severity") == "high":
                        high_n += 1
                except json.JSONDecodeError:
                    pass
        synthesized = path.exists()
        had_flag = flagged.exists()
        age = _age_days(info.get("call_date"))
        out.append({
            "slug": slug,
            "name": info["name"],
            "ticker": info["ticker"],
            "quarter": info["raw_quarter"],
            "call_date": info.get("call_date"),
            "age_days": age,
            "freshness": (
                "fresh" if age is not None and age <= 60 else
                "aging" if age is not None and age <= 120 else
                "stale" if age is not None else "unknown"
            ),
            "synthesized": synthesized,
            "was_flagged": had_flag,
            "still_flagged": had_flag and not synthesized,
            "critique_count": critique_n,
            "high_count": high_n,
            "user_added": info.get("user_added", False),
        })
    return out


def _md(text: str) -> str:
    return md.markdown(text, extensions=["fenced_code", "tables", "nl2br"])


def _split_brief(markdown_src: str) -> dict:
    sections = {"heading": "", "stance": "", "firm": "", "wego": "", "appendix": ""}
    lines = markdown_src.splitlines()
    i = 0
    while i < len(lines) and not lines[i].startswith("## "):
        i += 1
    if i < len(lines):
        sections["heading"] = lines[i].lstrip("# ").strip()
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i < len(lines) and lines[i].strip().startswith("*") and lines[i].strip().endswith("*"):
        sections["stance"] = lines[i].strip().strip("*").strip()
        i += 1
    rest = "\n".join(lines[i:])

    def grab(label: str, src: str) -> tuple[str, str]:
        m = re.search(rf"###\s+{re.escape(label)}\s*\n(.*?)(?=\n###\s+|\Z)", src, re.DOTALL)
        if not m:
            return "", src
        return m.group(1).strip(), src.replace(m.group(0), "", 1)

    sections["firm"], rest = grab("What the firm said", rest)
    sections["wego"], rest = grab("What this means for Wego", rest)
    sections["appendix"], _ = grab("Quote appendix", rest)
    return sections


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "", name.lower())
    return s[:8] or "company"


@app.route("/")
def index():
    editions = _list_editions()
    companies = _list_companies(QUARTER)
    return render_template(
        "index.html",
        editions=editions,
        current_quarter=QUARTER,
        companies=companies,
        running=_PIPELINE_STATE["running"],
        last_run=_PIPELINE_STATE["ended_at"] or _PIPELINE_STATE["started_at"],
        steps=PIPELINE_STEPS,
    )


@app.route("/edition/<quarter>")
def edition(quarter: str):
    path = OUTPUT_DIR / f"digest_{quarter}.md"
    if not path.exists():
        abort(404)
    body_md = path.read_text(encoding="utf-8")
    return render_template(
        "edition.html",
        quarter=quarter,
        body_html=_md(body_md),
        body_text=body_md,
        companies=_list_companies(quarter),
    )


@app.route("/company/<slug>")
def company(slug: str):
    if slug not in COMPANIES:
        abort(404)
    info = COMPANIES[slug]
    path = OUTPUT_DIR / f"{slug}_{info['raw_quarter']}.md"
    flagged = OUTPUT_DIR / f"{slug}_{info['raw_quarter']}.flagged.md"
    critique_path = OUTPUT_DIR / f"{slug}_{info['raw_quarter']}.critique.jsonl"

    src = path if path.exists() else (flagged if flagged.exists() else None)
    if not src:
        abort(404)

    issues = []
    if critique_path.exists():
        for line in critique_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    issues.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    raw_md = src.read_text(encoding="utf-8")
    sections = _split_brief(raw_md)
    nav_companies = [c for c in _list_companies(QUARTER) if c["synthesized"] or c["was_flagged"]]
    age = _age_days(info.get("call_date"))
    return render_template(
        "company.html",
        info=info,
        sections={
            "heading": sections["heading"],
            "stance": sections["stance"],
            "firm_html": _md(sections["firm"]),
            "wego_html": _md(sections["wego"]),
            "appendix_html": _md(sections["appendix"]),
        },
        body_text=raw_md,
        is_flagged=src.name.endswith(".flagged.md"),
        issues=issues,
        nav_companies=nav_companies,
        current_slug=slug,
        call_date=info.get("call_date"),
        age_days=age,
    )


@app.route("/about")
def about():
    return render_template("about.html", steps=PIPELINE_STEPS)


@app.route("/paste", methods=["POST"])
def paste_transcript():
    """Manual transcript paste — universal entry point for any company."""
    name = (request.form.get("name") or "").strip()
    ticker = (request.form.get("ticker") or "").strip().upper()
    quarter = (request.form.get("quarter") or "").strip().upper()
    call_date = (request.form.get("call_date") or "").strip()
    transcript = (request.form.get("transcript") or "").strip()

    if not all([name, ticker, quarter, transcript]):
        return redirect(url_for("index", _anchor="paste"))
    if not re.match(r"^\d{4}Q[1-4]$", quarter):
        return redirect(url_for("index", _anchor="paste"))
    if len(transcript) < 1000:
        return redirect(url_for("index", _anchor="paste"))

    slug = _slugify(name)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    user_companies = {}
    if USER_COMPANIES_PATH.exists():
        try:
            user_companies = json.loads(USER_COMPANIES_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            user_companies = {}
    user_companies[slug] = {
        "name": name, "ticker": ticker, "raw_quarter": quarter,
        "call_date": call_date or None, "user_added": True,
    }
    USER_COMPANIES_PATH.write_text(json.dumps(user_companies, indent=2), encoding="utf-8")
    COMPANIES[slug] = user_companies[slug]

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / f"{slug}_{quarter}.txt"
    raw_path.write_text(transcript, encoding="utf-8")

    def worker():
        _PIPELINE_STATE.update({
            "running": True, "step": f"extract:{slug}", "log": [f"→ pasted {ticker} {quarter}"],
            "started_at": datetime.now(timezone.utc).isoformat(), "ended_at": None,
        })
        for stage, args in [
            ("extract",    ["scripts.extract", slug]),
            ("synthesize", ["scripts.synthesize", slug]),
            ("critique",   ["scripts.critique", slug]),
            ("fixup",      ["scripts.fixup", slug]),
            ("compose",    ["scripts.compose"]),
        ]:
            _PIPELINE_STATE["step"] = f"{stage}:{slug}"
            try:
                proc = subprocess.run(
                    [str(ROOT / ".venv" / "bin" / "python"), "-m", *args],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=600,
                )
                _PIPELINE_STATE["log"].extend((proc.stdout + proc.stderr).splitlines()[-10:])
            except subprocess.TimeoutExpired:
                _PIPELINE_STATE["log"].append(f"✗ {stage} timeout")
        _PIPELINE_STATE["running"] = False
        _PIPELINE_STATE["step"] = "done"
        _PIPELINE_STATE["ended_at"] = datetime.now(timezone.utc).isoformat()

    threading.Thread(target=worker, daemon=True).start()
    return redirect(url_for("index"))


@app.route("/flag", methods=["POST"])
def flag_implication():
    payload = request.get_json(silent=True) or {}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "slug": payload.get("slug", ""),
        "section": payload.get("section", ""),
        "quote": (payload.get("quote") or "")[:600],
        "note": (payload.get("note") or "")[:600],
    }
    with FLAGS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return jsonify({"ok": True})


@app.route("/forward/edition/<quarter>")
def forward_edition(quarter: str):
    path = OUTPUT_DIR / f"digest_{quarter}.md"
    if not path.exists():
        abort(404)
    text = path.read_text(encoding="utf-8")
    subject = f"Wego Earnings Digest · {quarter}"
    body = text[:6000]
    mailto = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
    return redirect(mailto)


@app.route("/forward/company/<slug>")
def forward_company(slug: str):
    if slug not in COMPANIES:
        abort(404)
    info = COMPANIES[slug]
    path = OUTPUT_DIR / f"{slug}_{info['raw_quarter']}.md"
    if not path.exists():
        abort(404)
    text = path.read_text(encoding="utf-8")
    subject = f"{info['name']} ({info['ticker']}) — {info['raw_quarter']} brief"
    body = text[:6000]
    mailto = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
    return redirect(mailto)


@app.route("/run", methods=["POST", "GET"])
def run():
    if _PIPELINE_STATE["running"]:
        return redirect(url_for("index"))

    def worker():
        _PIPELINE_STATE.update({
            "running": True, "step": "fetch", "log": [],
            "started_at": datetime.now(timezone.utc).isoformat(), "ended_at": None,
        })
        for name, args, _label in PIPELINE_STEPS:
            _PIPELINE_STATE["step"] = name
            _PIPELINE_STATE["log"].append(f"→ {name}")
            try:
                proc = subprocess.run(
                    [str(ROOT / ".venv" / "bin" / "python"), "-m", *args],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=900,
                )
                _PIPELINE_STATE["log"].extend((proc.stdout + proc.stderr).splitlines()[-20:])
                if proc.returncode != 0:
                    _PIPELINE_STATE["log"].append(f"✗ {name} failed (exit {proc.returncode})")
            except subprocess.TimeoutExpired:
                _PIPELINE_STATE["log"].append(f"✗ {name} timeout")
        _PIPELINE_STATE["running"] = False
        _PIPELINE_STATE["step"] = "done"
        _PIPELINE_STATE["ended_at"] = datetime.now(timezone.utc).isoformat()

    threading.Thread(target=worker, daemon=True).start()
    return redirect(url_for("index"))


@app.route("/run/status")
def run_status():
    return jsonify(_PIPELINE_STATE)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5057, debug=False)
