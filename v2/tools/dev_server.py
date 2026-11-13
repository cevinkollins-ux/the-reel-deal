#!/usr/bin/env python3
"""Local dev server for The Reel Deal v2.

    python3 v2/tools/dev_server.py [port]      (default 8744)

  /            v2/index.html, with a one-line hook injected so the page talks
               to the local TMDB proxy instead of needing a key pasted in
  /v1/         the ORIGINAL root index.html, patched in memory the same way
               (the file on disk is never touched), for side-by-side checks
  /tmdb/...    proxy to api.themoviedb.org/3, key added server-side from .env,
               responses cached on disk under v2/.cache/ (24h)
  /__stats     how many TMDB calls the page has made (hits vs cache)

The key never reaches the browser. Binds to 127.0.0.1 only.
"""
import json
import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tmdbcache  # noqa: E402

ROOT = tmdbcache.ROOT
V2 = ROOT / "v2"
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".json": "application/json", ".css": "text/css", ".md": "text/plain; charset=utf-8",
         ".svg": "image/svg+xml", ".png": "image/png"}

stats = {"requests": 0, "cache_hits": 0, "upstream": 0, "errors": 0}
stats_lock = threading.Lock()

V1_BASE_LINE = 'const TMDB_BASE = "https://api.themoviedb.org/3";'
V1_KEY_LINE = 'let apiKey = safeStorageGet("tmdb_key") || "";'


def v1_patched():
    """The original page, pointed at the proxy. Two exact-line swaps, in memory."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    if V1_BASE_LINE not in html or V1_KEY_LINE not in html:
        return None
    html = html.replace(V1_BASE_LINE, 'const TMDB_BASE = location.origin + "/tmdb";')
    # v1 keeps its Daily in localStorage["reel_daily"]; same origin as v2 here,
    # but v2 uses its own keys, so the two don't collide.
    return html.replace(V1_KEY_LINE, 'let apiKey = "dev-proxy";')


def v2_page(name):
    html = (V2 / name).read_text(encoding="utf-8")
    hook = '<script>window.REEL_DEAL_TMDB_PROXY = location.origin + "/tmdb";</script>'
    return html.replace("<head>", "<head>\n" + hook, 1)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # quiet: TMDB traffic is counted in /__stats
        if not self.path.startswith("/tmdb/"):
            sys.stderr.write("%s\n" % (fmt % args))

    def send(self, status, body, ctype="text/plain; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        path = urllib.parse.unquote(parsed.path)

        if path.startswith("/tmdb/"):
            params = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
            max_age = 0 if params.pop("_fresh", None) else 24 * 3600
            status, body, cached = tmdbcache.fetch(path[len("/tmdb"):], params, max_age)
            with stats_lock:
                stats["requests"] += 1
                stats["cache_hits" if cached else "upstream"] += 1
                if status != 200:
                    stats["errors"] += 1
            return self.send(status, body, "application/json")

        if path == "/__stats":
            with stats_lock:
                snap = dict(stats)
                if parsed.query == "reset":
                    for k in stats:
                        stats[k] = 0
            return self.send(200, json.dumps(snap), "application/json")

        if path in ("/v1", "/v1/", "/v1/index.html"):
            html = v1_patched()
            if html is None:
                return self.send(500, "Root index.html no longer has the lines the v1 patch swaps.")
            return self.send(200, html, TYPES[".html"])

        rel = path.lstrip("/") or "index.html"
        target = (V2 / rel).resolve()
        if V2.resolve() not in target.parents or not target.is_file() or "/." in "/" + rel:
            return self.send(404, "Not found")
        if target.suffix == ".html":
            return self.send(200, v2_page(rel), TYPES[".html"])
        return self.send(200, target.read_bytes(), TYPES.get(target.suffix, "application/octet-stream"))


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8744
    tmdbcache.load_key()
    print("Reel Deal dev server: http://127.0.0.1:%d/  (v1 at /v1/)" % port, flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
