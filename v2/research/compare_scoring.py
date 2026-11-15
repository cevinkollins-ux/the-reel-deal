#!/usr/bin/env python3
"""Old points next to new points for named actor + film pairs, and pool-wide stats.

    python3 v2/research/compare_scoring.py

The tables in v2/FINDINGS.md come from this. For browsing one actor's whole
filmography interactively, use the Scoring lab in the page instead.
"""
import collections
import json
import re
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tmdbcache  # noqa: E402
import model  # noqa: E402

TODAY = datetime.now(ZoneInfo("America/New_York")).date().isoformat()
html = (tmdbcache.ROOT / "index.html").read_text(encoding="utf-8")
grab = lambda name: json.loads(re.search(r"^const %s = (.*);$" % name, html, re.M).group(1))
TABLE = model.YearTable(grab("YEAR_VOTES"))
IDS = grab("ACTOR_IDS")

EXAMPLES = {
    "Emma Thompson": ["Brave", "Love Actually", "I Am Legend", "Harry Potter and the Prisoner of Azkaban",
                      "Sense and Sensibility", "The Remains of the Day", "Howards End", "Saving Mr. Banks",
                      "Harry Potter and the Deathly Hallows: Part 2", "Carrington"],
    "Tom Hanks": ["Forrest Gump", "Toy Story", "Big", "Splash", "The 'Burbs", "Joe Versus the Volcano",
                  "The Man with One Red Shoe", "Nothing in Common", "The Simpsons Movie", "Ithaca"],
    "Samuel L. Jackson": ["Pulp Fiction", "Jurassic Park", "Coming to America", "GoodFellas", "Iron Man",
                          "Do the Right Thing", "The Red Violin", "Out of Sight"],
    "Brad Pitt": ["Fight Club", "Thelma & Louise", "True Romance", "Deadpool 2", "Being John Malkovich",
                  "Johnny Suede", "Kalifornia"],
}


def cast_of(name):
    return tmdbcache.get("/person/%d/movie_credits" % IDS[name]).get("cast", [])


def row(m):
    year = model.year_of(m)
    votes = m["vote_count"]
    link = model.link_strength(TABLE, m)
    return (m["title"][:42], year, votes, round(TABLE.rank(votes, year)), (m.get("order") or 0) + 1,
            round(link), 50 + model.rarity_v1(votes), 50 + model.deep_cut_bonus(link))


def main():
    for name, titles in EXAMPLES.items():
        creds = {m["title"]: m for m in sorted(model.eligible_credits(name, cast_of(name), TODAY),
                                               key=lambda m: m["vote_count"])}
        print("\n%s" % name)
        print("  %-42s %4s %6s %5s %6s %7s %4s %4s" % ("film", "year", "votes", "#year", "billed", "link", "v1", "v2"))
        for r in sorted((row(creds[t]) for t in titles if t in creds), key=lambda r: -r[5]):
            print("  %-42s %4s %6d %5d %6d %7d %4d %4d" % r)

    with ThreadPoolExecutor(10) as ex:
        casts = dict(zip(IDS, ex.map(cast_of, IDS)))
    all_v2, known_pts, by_decade = [], [], collections.defaultdict(list)
    for name, cast in casts.items():
        for m in model.eligible_credits(name, cast, TODAY):
            link = model.link_strength(TABLE, m)
            pts = 50 + model.deep_cut_bonus(link)
            all_v2.append(pts)
            if link >= model.KNOWN_LINK:
                known_pts.append(pts)
            year = model.year_of(m)
            if year and m["vote_count"] >= 20:
                by_decade[year // 10 * 10].append((50 + model.rarity_v1(m["vote_count"]), pts,
                                                   TABLE.rank(m["vote_count"], year)))
    print("\nPool-wide, films that count in v2: %d" % len(all_v2))
    print("  at the 100-point cap: %.0f%%;  median %d;  well-known films: median %d, range %d-%d" % (
        100 * sum(1 for p in all_v2 if p == 100) / len(all_v2), statistics.median(all_v2),
        statistics.median(known_pts), min(known_pts), max(known_pts)))
    print("\nSame fame for its year, different decade (films ranked 30th-60th in their year):")
    print("  decade   films   v1 median   v2 median")
    for decade in sorted(by_decade):
        band = [(a, b) for a, b, rank in by_decade[decade] if 30 <= rank <= 60]
        if len(band) >= 15:
            print("  %ds   %5d   %9d   %9d" % (decade, len(band), statistics.median(a for a, _ in band),
                                               statistics.median(b for _, b in band)))


if __name__ == "__main__":
    main()
