import sys
import json
import time
import urllib.request
import urllib.error
from .config import OPENROUTER_API_KEY, OPENROUTER_BASE, MODEL


def call(system: str, user: str, *, model: str = MODEL, max_tokens: int = 4096, temperature: float = 0.2) -> str:
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY.startswith("placeholder"):
        sys.exit("OPENROUTER_API_KEY missing or placeholder. Add real key to .env")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    req = urllib.request.Request(
        OPENROUTER_BASE + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/subhankarshukla04/wego-earnings-digest",
            "X-Title": "Wego Earnings Digest",
        },
        method="POST",
    )

    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body = json.loads(r.read().decode("utf-8"))
                return body["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:200]}"
        except Exception as e:
            last_err = str(e)
        time.sleep(2 * (attempt + 1))
    sys.exit(f"OpenRouter call failed after 3 attempts: {last_err}")
