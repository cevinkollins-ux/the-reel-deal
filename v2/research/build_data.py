#!/usr/bin/env python3
"""Build the static data block that v2/index.html carries, and write it into the page.

    python3 v2/research/build_data.py            # print a summary, change nothing
    python3 v2/research/build_data.py --write    # replace the <generated-data> block

What it builds (all from TMDB, cached under v2/.cache/ for a day):

  ACTOR_IDS         TMDB person id for every name in ACTORS, so the page never
                    has to trust the first hit of a name search
  DIRECTOR_IDS      same for DIRECTORS (a value may be several people: the Coens)
  FRANCHISE_DEFS    which TMDB collections / keyword / extra films make up each
                    entry in COLLECTIONS
  YEAR_VOTES        vote count at fixed ranks within each release year: the table
                    behind "famous for its year"
  DEALABLE          pool actors with enough well-known films to carry a grid row
  CONNECTIONS       for each director, franchise and co-star: which pool actors
                    have a well-known film with them. The dealer uses this only
                    to pick promising trios; every pick is still checked live.

Re-run it every month or two (vote counts drift, new films come out), and
whenever ACTORS, DIRECTORS or COLLECTIONS change.
"""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tmdbcache  # noqa: E402
import model  # noqa: E402

PAGE = tmdbcache.ROOT / "v2" / "index.html"
FIRST_YEAR = 1915
MIN_KNOWN_TO_DEAL = 4   # an actor needs this many well-known films to be dealt at random

# Names whose first search hit is not the person we mean.
PERSON_ID_OVERRIDES = {"Elliot Page": 27578}
DIRECTOR_ID_OVERRIDES = {"Coen Brothers": [1223, 1224]}  # Joel Coen, Ethan Coen

# What each COLLECTIONS entry means on TMDB. v1 matched on the collection's
# name, which never matched "Marvel Cinematic Universe" (TMDB has no such
# collection) or "Fast & Furious" (it's "The Fast and the Furious Collection"),
# and matched "Rocky" to The Rocky Horror Picture Show.
FRANCHISES = {
    "Marvel Cinematic Universe": {"keyword": 180547},
    "Star Wars": {"collections": [10], "films": [330459, 348350, 12180]},  # + Rogue One, Solo, The Clone Wars
    "Harry Potter": {"collections": [1241]},
    "Fast & Furious": {"collections": [9485]},
    "James Bond": {"collections": [645]},
    "Mission: Impossible": {"collections": [87359]},
    "The Lord of the Rings": {"collections": [119]},
    "X-Men": {"collections": [748, 453993, 448150], "films": [340102]},  # + Wolverine, Deadpool, The New Mutants
    "Jurassic Park": {"collections": [328]},
    "Ocean's": {"collections": [304], "films": [402900]},  # + Ocean's Eight
    "The Dark Knight": {"collections": [263]},
    "Shrek": {"collections": [2150]},
    "Toy Story": {"collections": [10194]},
    "Rocky": {"collections": [1575, 553717]},  # + Creed
    "Transformers": {"collections": [8650], "films": [424783, 667538]},  # + Bumblebee, Rise of the Beasts
    "The Hunger Games": {"collections": [131635, 1701563]},
    "Pirates of the Caribbean": {"collections": [295]},
    "John Wick": {"collections": [404609], "films": [541671]},  # + Ballerina
    "Spider-Man": {"collections": [556, 531241, 573436, 125574]},
    "The Matrix": {"collections": [2344]},
}


def js_string_array(html, name):
    block = re.search(r"const %s = \[(.*?)\];" % name, html, re.S).group(1)
    return json.loads("[" + block + "]")


def find_person(name, want_department=None):
    if name in PERSON_ID_OVERRIDES:
        return PERSON_ID_OVERRIDES[name]
    results = tmdbcache.get("/search/person", {"query": name}).get("results") or []
    if not results:
        raise SystemExit("No TMDB person found for %r" % name)
    hit = results[0]
    if want_department and hit.get("known_for_department") != want_department:
        print("  note: %r resolves to %r, known for %s" % (name, hit["name"], hit.get("known_for_department")))
    return hit["id"]


def cast_credits(pid):
    return tmdbcache.get("/person/%d/movie_credits" % pid).get("cast", [])


def directed_film_ids(pid):
    crew = tmdbcache.get("/person/%d/movie_credits" % pid).get("crew", [])
    return {c["id"] for c in crew if c.get("job") == "Director"}


def franchise_film_ids(spec):
    ids = set(spec.get("films", []))
    for cid in spec.get("collections", []):
        ids |= {p["id"] for p in tmdbcache.get("/collection/%d" % cid).get("parts", [])}
    if "keyword" in spec:
        page = 1
        while True:
            js = tmdbcache.get("/discover/movie", {"with_keywords": spec["keyword"], "include_adult": "false",
                                                   "sort_by": "vote_count.desc", "page": page})
            ids |= {m["id"] for m in js["results"]}
            if page >= js["total_pages"] or page >= 10:
                break
            page += 1
    return ids


def year_rows(last_year):
    pages = sorted({(r - 1) // 20 + 1 for r in model.RANKS})

    def fetch(args):
        year, p = args
        js = tmdbcache.get("/discover/movie", {
            "primary_release_year": year, "sort_by": "vote_count.desc",
            "include_adult": "false", "include_video": "false", "page": p})
        return year, p, [m["vote_count"] for m in js["results"]]

    got = {}
    with ThreadPoolExecutor(10) as ex:
        for year, p, votes in ex.map(fetch, [(y, p) for y in range(FIRST_YEAR, last_year + 1) for p in pages]):
            got[(year, p)] = votes
    rows = {}
    for y in range(FIRST_YEAR, last_year + 1):
        row = []
        for r in model.RANKS:
            votes = got[(y, (r - 1) // 20 + 1)]
            i = (r - 1) % 20
            row.append(votes[i] if i < len(votes) else 0)
        rows[y] = model.clean_row(row)
    return rows


def compact(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def main():
    html = PAGE.read_text(encoding="utf-8")
    actors = js_string_array(html, "ACTORS")
    directors = js_string_array(html, "DIRECTORS")
    collections = js_string_array(html, "COLLECTIONS")
    missing = [c for c in collections if c not in FRANCHISES]
    if missing:
        raise SystemExit("Add these to FRANCHISES in build_data.py: %s" % missing)
    today = date.today().isoformat()

    with ThreadPoolExecutor(10) as ex:
        actor_ids = list(ex.map(lambda n: find_person(n, "Acting"), actors))
        casts = list(ex.map(cast_credits, actor_ids))
    if len(set(actor_ids)) != len(actor_ids):
        raise SystemExit("Two ACTORS names resolve to the same TMDB person.")

    director_ids = {d: DIRECTOR_ID_OVERRIDES.get(d) or [find_person(d)] for d in directors}
    table = model.YearTable(year_rows(date.today().year))

    # Each actor's eligible credits, and which of them are well-known links.
    eligible, known = [], []
    for name, cast in zip(actors, casts):
        creds = model.eligible_credits(name, cast, today)
        eligible.append({m["id"] for m in creds})
        known.append({m["id"] for m in creds if model.link_strength(table, m) >= model.KNOWN_LINK})
    dealable = [i for i in range(len(actors)) if len(known[i]) >= MIN_KNOWN_TO_DEAL]

    directed = {d: set().union(*[directed_film_ids(p) for p in ids]) for d, ids in director_ids.items()}
    franchise = {c: franchise_film_ids(FRANCHISES[c]) for c in collections}
    connections = {
        "director": {d: [i for i in dealable if known[i] & films] for d, films in directed.items()},
        "collection": {c: [i for i in dealable if known[i] & films] for c, films in franchise.items()},
        # For co-star C: actors with a well-known film that C is also (eligibly) in.
        "costar": {str(c): [i for i in dealable if i != c and known[i] & eligible[c]] for c in range(len(actors))},
    }

    lines = [
        "// <generated-data>",
        "// Built by v2/research/build_data.py from live TMDb data. Don't edit by hand;",
        "// re-run the script (see its docstring) to refresh.",
        'const DATA_BUILT_ON = "%s";' % today,
        "const ACTOR_IDS = %s;" % compact(dict(zip(actors, actor_ids))),
        "const DIRECTOR_IDS = %s;" % compact(director_ids),
        "const FRANCHISE_DEFS = %s;" % compact(FRANCHISES),
        "// Vote count of the film ranked 1st, 3rd, 5th ... 1000th by votes among each year's releases.",
        "const YEAR_RANKS = %s;" % compact(model.RANKS),
        "const YEAR_VOTES = %s;" % compact({str(y): r for y, r in table.years.items()}),
        "// Indexes into ACTORS. DEALABLE: actors with at least %d well-known films." % MIN_KNOWN_TO_DEAL,
        "const DEALABLE = %s;" % compact(dealable),
        "// For each director, franchise and co-star (by ACTORS index): the dealable actors who",
        "// have a well-known film with them. Only a hint for picking trios; every deal is checked live.",
        "const CONNECTIONS = %s;" % compact(connections),
        "// </generated-data>",
    ]
    block = "\n".join(lines)

    print("actors %d (dealable %d), directors %d, franchises %d, years %d-%d" % (
        len(actors), len(dealable), len(directors), len(collections), table.first, table.last))
    not_dealable = [actors[i] for i in range(len(actors)) if i not in dealable]
    print("not dealable (fewer than %d well-known films): %s" % (MIN_KNOWN_TO_DEAL, ", ".join(not_dealable)))
    for kind in ("director", "collection"):
        sizes = sorted((len(v), k) for k, v in connections[kind].items())
        print("%s -> actors linked: %s" % (kind, ", ".join("%s %d" % (k, n) for n, k in sizes)))
    co = sorted(len(v) for v in connections["costar"].values())
    print("co-star lists: median %d actors, max %d, empty %d" % (co[len(co) // 2], co[-1], co.count(0)))
    print("block size: %.1f KB" % (len(block.encode()) / 1024))

    if "--write" in sys.argv:
        new, n = re.subn(r"// <generated-data>.*?// </generated-data>", lambda _: block, html, flags=re.S)
        if n != 1:
            raise SystemExit("Expected exactly one <generated-data> block in v2/index.html")
        PAGE.write_text(new, encoding="utf-8")
        print("written to %s" % PAGE)


if __name__ == "__main__":
    main()
