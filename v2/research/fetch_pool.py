#!/usr/bin/env python3
"""Pull everything TMDB says about the actor pool, the way the app asks for it.

    python3 v2/research/fetch_pool.py <out.json>

For every name in ACTORS (read from the root index.html): /search/person (the
app trusts results[0]) and that person's /movie_credits. Responses are cached
under v2/.cache/, so a re-run within a day costs no API calls.
"""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import tmdbcache  # noqa: E402


def js_string_array(html, name):
    block = re.search(r"const %s = \[(.*?)\];" % name, html, re.S).group(1)
    return json.loads("[" + block + "]")


def person(name):
    search = tmdbcache.get("/search/person", {"query": name})
    results = search.get("results") or []
    if not results:
        return {"name": name, "hit": None, "others": [], "cast": []}
    hit = results[0]
    credits = tmdbcache.get("/person/%d/movie_credits" % hit["id"])
    slim = lambda r: {k: r.get(k) for k in ("id", "name", "popularity", "known_for_department")}
    return {
        "name": name,
        "hit": {**slim(hit), "known_for": [k.get("title") or k.get("name") for k in hit.get("known_for", [])]},
        "others": [slim(r) for r in results[1:4]],
        "cast": credits.get("cast", []),
        "crew_director": [c["id"] for c in credits.get("crew", []) if c.get("job") == "Director"],
    }


if __name__ == "__main__":
    out = Path(sys.argv[1])
    html = (tmdbcache.ROOT / "index.html").read_text(encoding="utf-8")
    actors = js_string_array(html, "ACTORS")
    directors = js_string_array(html, "DIRECTORS")
    collections = js_string_array(html, "COLLECTIONS")
    with ThreadPoolExecutor(12) as ex:
        people = list(ex.map(person, actors))
    genres = tmdbcache.get("/genre/movie/list")["genres"]
    out.write_text(json.dumps({"actors": people, "directors": directors,
                               "collections": collections, "genres": genres}))
    n = sum(len(p["cast"]) for p in people)
    print("actors: %d, cast credits: %d, written to %s" % (len(people), n, out))
