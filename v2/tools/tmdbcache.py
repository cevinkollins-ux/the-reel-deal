"""Tiny TMDB client with an on-disk cache, shared by the dev server and the
research scripts. Standard library only.

The key is read from (in order) the TMDB_API_KEY environment variable, the
repo's .env file (tmdb_api_key=...), or tmdb_api_key.txt. It is never printed.
"""
import hashlib
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "v2" / ".cache" / "tmdb"
API = "https://api.themoviedb.org/3"

_key = None
_lock = threading.Lock()


def load_key():
    global _key
    if _key:
        return _key
    key = os.environ.get("TMDB_API_KEY", "").strip()
    env = ROOT / ".env"
    if not key and env.exists():
        for line in env.read_text().splitlines():
            name, _, value = line.partition("=")
            if name.strip().lower() in ("tmdb_api_key", "tmdb_key"):
                key = value.strip().strip("\"'")
    txt = ROOT / "tmdb_api_key.txt"
    if not key and txt.exists():
        key = txt.read_text().strip()
    if not key:
        raise SystemExit("No TMDB key found (TMDB_API_KEY, .env or tmdb_api_key.txt).")
    _key = key
    return key


def _cache_path(path, params):
    canon = path + "?" + urllib.parse.urlencode(sorted(params.items()))
    digest = hashlib.sha1(canon.encode()).hexdigest()
    return CACHE_DIR / digest[:2] / (digest + ".json")


def fetch(path, params=None, max_age=24 * 3600, retries=5):
    """GET a TMDB path. Returns (status, body_bytes, from_cache)."""
    params = {k: str(v) for k, v in (params or {}).items() if k != "api_key"}
    cp = _cache_path(path, params)
    if max_age and cp.exists() and time.time() - cp.stat().st_mtime < max_age:
        return 200, cp.read_bytes(), True
    url = API + path + "?" + urllib.parse.urlencode({**params, "api_key": load_key()})
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                body = r.read()
            cp.parent.mkdir(parents=True, exist_ok=True)
            tmp = cp.with_suffix(".tmp%d" % threading.get_ident())
            tmp.write_bytes(body)
            tmp.replace(cp)
            return 200, body, False
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(1 + attempt * 2)
                last = (429, b'{"status_message":"rate limited"}')
                continue
            return e.code, e.read(), False
        except Exception as e:  # network hiccup
            last = (502, json.dumps({"status_message": str(e)}).encode())
            time.sleep(0.5 + attempt)
    return last[0], last[1], False


def get(path, params=None, max_age=24 * 3600):
    """Like fetch(), but returns parsed JSON and raises on a non-200."""
    status, body, _ = fetch(path, params, max_age)
    if status != 200:
        raise RuntimeError("TMDB %s -> %s" % (path, status))
    return json.loads(body)
