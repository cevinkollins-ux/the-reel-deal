#!/usr/bin/env python3
"""Check that the page's JavaScript scoring and model.py agree.

    python3 v2/research/crosscheck.py "Emma Thompson" "Tom Hanks" ...

Prints, per actor: how many credits count, the sum of their points and of their
(rounded) link strengths. Paste the snippet it prints into the browser console
on the v2 page and compare the numbers. Shorts are counted on both sides
(the page rules them out with an extra TMDB call that model.py doesn't make).
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tmdbcache  # noqa: E402
import model  # noqa: E402

html = (tmdbcache.ROOT / "index.html").read_text(encoding="utf-8")
grab = lambda name: json.loads(re.search(r"^const %s = (.*);$" % name, html, re.M).group(1))
table = model.YearTable(grab("YEAR_VOTES"))
ids = grab("ACTOR_IDS")
today = datetime.now(ZoneInfo("America/New_York")).date().isoformat()

for name in sys.argv[1:] or ["Emma Thompson", "Tom Hanks", "Samuel L. Jackson"]:
    cast = tmdbcache.get("/person/%d/movie_credits" % ids[name]).get("cast", [])
    creds = model.eligible_credits(name, cast, today)
    pts = sum(model.BONUS_MAX + model.deep_cut_bonus(model.link_strength(table, m)) for m in creds)
    links = sum(round(model.link_strength(table, m)) for m in creds)
    known = sum(1 for m in creds if model.link_strength(table, m) >= model.KNOWN_LINK)
    print("%-20s credits=%d points=%d links=%d known=%d" % (name, len(creds), pts, links, known))

print("""
// paste into the browser console on the v2 page:
for (const name of %s) {
  const p = await getActorProfile(name);
  const all = [...p.credits, ...[...p.rejected.values()].filter(x => x.reason === "short").map(x => x.credit)];
  console.log(name, "credits=" + all.length, "points=" + all.reduce((s, m) => s + m.points, 0),
    "links=" + all.reduce((s, m) => s + Math.round(m.link), 0), "known=" + all.filter(isKnownLink).length);
}""" % json.dumps(sys.argv[1:] or ["Emma Thompson", "Tom Hanks", "Samuel L. Jackson"]))
