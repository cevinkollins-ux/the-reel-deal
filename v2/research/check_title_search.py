#!/usr/bin/env python3
"""How often does typing a film's exact title find a different film?

    python3 v2/research/check_title_search.py [min_votes]     (default 2000)

The original game turns a typed title into a film by taking the first hit of
TMDB's /search/movie. This runs that search for every well-known film in the
actor pool's filmographies, using the film's exact title, and counts how often
the first hit is some other film (a sequel, a remake, a newer film with a
longer title). Each of those is a correct answer the game would have checked
against the wrong film.
"""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tmdbcache  # noqa: E402
import model  # noqa: E402

WEEK = 7 * 24 * 3600


def main():
    min_votes = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    html = (tmdbcache.ROOT / "v2" / "index.html").read_text(encoding="utf-8")
    ids = json.loads(re.search(r"^const ACTOR_IDS = (.*);$", html, re.M).group(1))
    films, who = {}, {}
    with ThreadPoolExecutor(10) as ex:
        casts = list(ex.map(lambda pid: tmdbcache.get("/person/%d/movie_credits" % pid).get("cast", []), ids.values()))
    for name, cast in zip(ids, casts):
        for m in cast:
            if model.real_v1(m) and m["vote_count"] >= min_votes:
                films[m["id"]] = m
                who.setdefault(m["id"], []).append(name)

    def first_hit(m):
        results = tmdbcache.get("/search/movie", {"query": m["title"]}, max_age=WEEK).get("results") or []
        return m, (results[0] if results else None)

    wrong = []
    with ThreadPoolExecutor(6) as ex:
        for m, hit in ex.map(first_hit, films.values()):
            if not hit or hit["id"] != m["id"]:
                wrong.append((m["vote_count"], m["title"], (m.get("release_date") or "")[:4], who[m["id"]][0],
                              "%s (%s)" % (hit["title"], (hit.get("release_date") or "")[:4]) if hit else "nothing"))
    wrong.sort(reverse=True)
    print("%d of %d films with %d+ votes (%.1f%%): the exact title finds a different film first" % (
        len(wrong), len(films), min_votes, 100 * len(wrong) / len(films)))
    for votes, title, year, actor, found in wrong[:40]:
        print("   %-44s %s  (%s)  ->  %s" % (title[:44], year, actor, found))


if __name__ == "__main__":
    main()
