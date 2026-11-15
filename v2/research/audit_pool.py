#!/usr/bin/env python3
"""Audit the ORIGINAL game's actor and category pools against live TMDB data.

    python3 v2/research/audit_pool.py

Reads ACTORS, DIRECTORS and COLLECTIONS from the root index.html, asks TMDB what
the page itself would ask, and prints the numbers quoted in v2/FINDINGS.md:

  1. pool names TMDB spells differently (every answer for them is rejected)
  2. names whose first search hit is the wrong person
  3. directors and franchises that can never match
  4. what the "valid" credits are made of (documentaries, archive footage, ...)
  5. how v1's rarity score is spread, and what the top of the scale is
  6. famous films outside the 50-most-popular window
  7. how many well-known films each actor has, v1 rule vs v2 rule

Responses are cached under v2/.cache/ for a day.
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

ROOT = tmdbcache.ROOT
TODAY = datetime.now(ZoneInfo("America/New_York")).date().isoformat()


def js_string_array(html, name):
    return json.loads("[" + re.search(r"const %s = \[(.*?)\];" % name, html, re.S).group(1) + "]")


def normalize_name(n):  # v1's normalizeName()
    return re.sub(r"[^a-z]", "", n.lower())


def person(name):
    results = tmdbcache.get("/search/person", {"query": name}).get("results") or []
    if not results:
        return {"name": name, "hit": None, "others": [], "cast": []}
    hit = results[0]
    cast = tmdbcache.get("/person/%d/movie_credits" % hit["id"]).get("cast", [])
    return {"name": name, "hit": hit, "others": results[1:4], "cast": cast}


def main():
    v1 = (ROOT / "index.html").read_text(encoding="utf-8")
    v2 = (ROOT / "v2" / "index.html").read_text(encoding="utf-8")
    actors = js_string_array(v1, "ACTORS")
    directors = js_string_array(v1, "DIRECTORS")
    collections_ = js_string_array(v1, "COLLECTIONS")
    table = model.YearTable(json.loads(re.search(r"^const YEAR_VOTES = (.*);$", v2, re.M).group(1)))
    with ThreadPoolExecutor(10) as ex:
        people = list(ex.map(person, actors))

    print("== 1. Pool names TMDB spells differently ==")
    for p in people:
        if p["hit"] and p["hit"]["name"].lower() != p["name"].lower() and p["hit"].get("known_for_department") == "Acting":
            print("   pool %-18r TMDB %r" % (p["name"], p["hit"]["name"]))

    print("\n== 2. First search hit is not the actor ==")
    for p in people:
        h = p["hit"]
        if not h:
            print("   %s: no hit at all" % p["name"])
        elif h.get("known_for_department") != "Acting":
            better = [o["name"] for o in p["others"] if o.get("known_for_department") == "Acting"]
            print("   %s -> %s (%s), %d credits; the actor is probably %s" % (
                p["name"], h["name"], h.get("known_for_department"), len(p["cast"]), better[:1]))

    print("\n== 3. Directors and franchises that can never match ==")
    for d in directors:
        hits = tmdbcache.get("/search/person", {"query": d}).get("results") or []
        if not any(normalize_name(h["name"]) == normalize_name(d) for h in hits[:5]):
            print("   director %-30r TMDB has: %s" % (d, [h["name"] for h in hits[:2]] or "nobody by that name"))
    for c in collections_:
        q = c.lower()
        short = q.split(":")[0].strip()
        found = []
        for query in {c, short}:
            found += tmdbcache.get("/search/collection", {"query": query}).get("results", [])
        names = sorted({r["name"] for r in found if short in r["name"].lower() or q in r["name"].lower()})
        if not names:
            print("   franchise %-28r matches no TMDB collection name" % c)
        elif len(names) > 1:
            print("   franchise %-28r also matches: %s" % (c, "; ".join(names[1:4])))

    pairs = [(p["name"], m) for p in people for m in p["cast"]]
    valid = [(n, m) for n, m in pairs if model.real_v1(m)]
    print("\n== 4. What v1's %d valid actor-film credits are ==" % len(valid))
    reasons = collections.Counter(model.ineligible_reason(n, m, TODAY) or "counts in v2" for n, m in valid)
    for reason, count in reasons.most_common():
        print("   %-14s %6d  %4.1f%%" % (reason, count, 100 * count / len(valid)))

    print("\n== 5. v1 rarity (1-50) across valid credits ==")
    buckets = collections.Counter((model.rarity_v1(m["vote_count"]) - 1) // 10 for _, m in valid)
    for b in range(5):
        print("   rarity %2d-%2d: %5.1f%%" % (b * 10 + 1, b * 10 + 10, 100 * buckets[b] / len(valid)))
    top = [(n, m) for n, m in valid if model.rarity_v1(m["vote_count"]) >= 45]
    junk = sum(1 for n, m in top if model.ineligible_reason(n, m, TODAY))
    print("   scoring 95+ points: %d credits, of which %d (%.0f%%) are not roles in a released film" % (
        len(top), junk, 100 * junk / len(top)))

    print("\n== 6. Films with 5,000+ votes outside an actor's 50 most popular ==")
    missed, total = [], 0
    for p in people:
        ranked = sorted([m for m in p["cast"] if model.real_v1(m)], key=lambda m: -(m.get("popularity") or 0))
        window = {m["id"] for m in ranked[:50]}
        for m in ranked:
            if m["vote_count"] >= 5000:
                total += 1
                if m["id"] not in window:
                    missed.append((m["vote_count"], p["name"], m["title"]))
    print("   %d of %d" % (len(missed), total))
    for votes, name, title in sorted(missed, reverse=True)[:10]:
        print("   %-18s %s (%d votes)" % (name, title, votes))
    slots = sum(min(50, sum(1 for m in p["cast"] if model.real_v1(m))) for p in people)
    low = sum(1 for p in people for m in sorted([m for m in p["cast"] if model.real_v1(m)],
              key=lambda m: -(m.get("popularity") or 0))[:50] if m["vote_count"] < 50)
    print("   window slots held by films with under 50 votes: %d of %d" % (low, slots))

    print("\n== 7. Well-known films per actor ==")
    v1_counts, v2_counts = [], []
    for p in people:
        v1_counts.append(sum(1 for m in p["cast"] if model.real_v1(m) and m["vote_count"] >= 5000))
        creds = model.eligible_credits(p["name"], p["cast"], TODAY)
        v2_counts.append(sum(1 for m in creds if model.link_strength(table, m) >= model.KNOWN_LINK))
    for label, counts in (("v1: 5,000+ votes", v1_counts), ("v2: link >= %d" % model.KNOWN_LINK, v2_counts)):
        print("   %-18s median %2d; actors with none: %d, fewer than 3: %d" % (
            label, statistics.median(counts), counts.count(0), sum(1 for c in counts if c < 3)))
    print("   v1 actors with no film at 5,000 votes (never dealable since the well-known rule): %s" % (
        ", ".join(p["name"] for p, c in zip(people, v1_counts) if c == 0)))


if __name__ == "__main__":
    main()
