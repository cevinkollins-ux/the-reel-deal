#!/usr/bin/env python3
"""
Companion debug script for The Reel Deal.

Workflow:
  1. In the app, turn on Sandbox mode.
  2. Click "Copy API call" next to an actor, or click a film title inside a
     "See All" popup (cell or actor). Either copies a snippet to your
     clipboard and shows a confirmation in the status line.
  3. Paste that snippet into api_call_to_review below, replacing whatever
     is there.
  4. Run: python3 inspect_tmdb.py
     It fetches the matching raw TMDb response(s), prints a summary of the
     fields relevant to this app's filtering logic (vote_count, video,
     genre_ids, etc.), and saves the full JSON under tmdb_inspect_output/.

Needs a TMDb v3 API key. Checked in this order:
  1. TMDB_API_KEY environment variable.
  2. A file named tmdb_api_key.txt next to this script (just the key, nothing else).
  3. If neither is set, you'll be prompted for it.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ---- Paste the snippet copied from Sandbox mode here ----
api_call_to_review = "person_id=287&person_name=Ryan%20Gosling"
# -----------------------------------------------------------

TMDB_BASE = "https://api.themoviedb.org/3"
SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "tmdb_inspect_output"


def get_api_key():
    key = os.environ.get("TMDB_API_KEY")
    if key:
        return key.strip()
    key_file = SCRIPT_DIR / "tmdb_api_key.txt"
    if key_file.exists():
        return key_file.read_text().strip()
    return input("Paste your TMDb API key (v3 auth): ").strip()


def tmdb_get(path, api_key, params=None):
    params = dict(params or {})
    params["api_key"] = api_key
    url = f"{TMDB_BASE}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"TMDb returned HTTP {e.code} for {path}: {body}")
        sys.exit(1)


def save_json(name, data):
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Saved -> {path}")
    return path


def print_field(label, value):
    print(f"  {label:<18}: {value}")


def main():
    fields = urllib.parse.parse_qs(api_call_to_review, keep_blank_values=True)
    person_id = (fields.get("person_id") or [None])[0]
    person_name = (fields.get("person_name") or [None])[0]
    movie_id = (fields.get("movie_id") or [None])[0]
    movie_title = (fields.get("movie_title") or [None])[0]

    if not person_id and not movie_id:
        print("api_call_to_review didn't contain a person_id or movie_id — nothing to look up.")
        print(f"Got: {api_call_to_review!r}")
        sys.exit(1)

    api_key = get_api_key()
    ts = time.strftime("%Y%m%d-%H%M%S")

    if person_id:
        label = person_name or person_id
        print(f"\nFetching /person/{person_id}/movie_credits  ({label})")
        credits = tmdb_get(f"/person/{person_id}/movie_credits", api_key)
        save_json(f"person_{person_id}_{ts}", credits)
        cast = credits.get("cast", [])
        print(f"  {len(cast)} cast credits returned")

        if movie_id:
            match = next((m for m in cast if str(m.get("id")) == str(movie_id)), None)
            if match:
                print(f"\nRaw credit entry for movie_id={movie_id} in this actor's cast list:")
                print_field("title", match.get("title"))
                print_field("id", match.get("id"))
                print_field("release_date", match.get("release_date"))
                print_field("vote_count", match.get("vote_count"))
                print_field("vote_average", match.get("vote_average"))
                print_field("popularity", match.get("popularity"))
                print_field("video", match.get("video"))
                print_field("genre_ids", match.get("genre_ids"))
                print_field("adult", match.get("adult"))
            else:
                print(f"\nNo credit with movie_id={movie_id} found in this actor's cast list.")

    if movie_id:
        label = movie_title or movie_id
        print(f"\nFetching /movie/{movie_id}?append_to_response=credits  ({label})")
        details = tmdb_get(f"/movie/{movie_id}", api_key, {"append_to_response": "credits"})
        save_json(f"movie_{movie_id}_{ts}", details)
        print_field("title", details.get("title"))
        print_field("vote_count", details.get("vote_count"))
        print_field("vote_average", details.get("vote_average"))
        print_field("popularity", details.get("popularity"))
        print_field("video", details.get("video"))
        print_field("genres", [g["name"] for g in details.get("genres", [])])
        print_field("release_date", details.get("release_date"))
        collection = details.get("belongs_to_collection") or {}
        print_field("collection", collection.get("name"))
        crew = details.get("credits", {}).get("crew", [])
        directors = [c["name"] for c in crew if c.get("job") == "Director"]
        print_field("director(s)", directors)

    print("\nDone. Full raw JSON saved under tmdb_inspect_output/.")


if __name__ == "__main__":
    main()
