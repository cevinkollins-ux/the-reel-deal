#!/usr/bin/env python3
"""Vote counts at fixed ranks within each release year.

    python3 v2/research/fetch_year_table.py <out.json>

For each year, asks /discover/movie (sorted by vote_count, most first) for the
pages that hold ranks 1-60, 100, 200, 500 and 1000, and records the vote count
at each of RANKS. This is the table v2's "fame for its year" curve is built on:
a film's rank among films of its own year, instead of its raw vote count.
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import tmdbcache  # noqa: E402

FIRST_YEAR, LAST_YEAR = 1915, 2026
RANKS = [1, 3, 5, 10, 20, 30, 50, 100, 200, 500, 1000]
PAGES = sorted({(r - 1) // 20 + 1 for r in RANKS})


def page(args):
    year, p = args
    js = tmdbcache.get("/discover/movie", {
        "primary_release_year": year, "sort_by": "vote_count.desc",
        "include_adult": "false", "include_video": "false", "page": p})
    return year, p, [(m["vote_count"], m["title"]) for m in js["results"]], js["total_results"]


if __name__ == "__main__":
    out = Path(sys.argv[1])
    jobs = [(y, p) for y in range(FIRST_YEAR, LAST_YEAR + 1) for p in PAGES]
    got = {}
    totals = {}
    with ThreadPoolExecutor(12) as ex:
        for year, p, films, total in ex.map(page, jobs):
            got[(year, p)] = films
            totals[year] = total
    table = {}
    for y in range(FIRST_YEAR, LAST_YEAR + 1):
        row = []
        for r in RANKS:
            films = got[(y, (r - 1) // 20 + 1)]
            i = (r - 1) % 20
            row.append(films[i][0] if i < len(films) else 0)
        table[y] = {"votes_at_rank": row, "top": got[(y, 1)][0][1] if got[(y, 1)] else "",
                    "films": totals[y]}
    out.write_text(json.dumps({"ranks": RANKS, "years": table}, indent=0))
    for y in range(FIRST_YEAR, LAST_YEAR + 1, 5):
        print(y, table[y]["votes_at_rank"], table[y]["top"])
