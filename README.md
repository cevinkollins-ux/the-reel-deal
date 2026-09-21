# The Reel Deal

A single-file, browser-based practice version of [MovieGrid.io](https://moviegrid.io)'s daily puzzle. Instead of waiting for one puzzle a day, deal a new 3×3 grid (3 actors × 3 categories) whenever you want and practice naming films that satisfy each actor/category pairing.

## How it works

- Open `index.html` directly in a browser — no build step, no server required.
- Paste a free [TMDb](https://www.themoviedb.org) API key (v3 auth) into the setup box. It's saved only in that browser's `localStorage`.
- Click **Deal a new puzzle** to get 3 random actors and 3 random categories. Every actor × category cell is checked against real TMDb filmographies before the puzzle is shown, so you're never stuck on an impossible pairing (if a trio of actors can't yield 3 solvable categories, it re-samples a new trio automatically).
- Type a film title into a cell — an autocomplete dropdown (powered by TMDb search) helps you pick the right one. Submit to check it.
- Scoring per correct cell: 50 points for a valid answer + 1–50 rarity points on a log scale of the film's TMDb vote count (obscure picks score higher). Each film can only be used once per grid.
- **Ready to see answers**: once a puzzle is dealt, click this to reveal a **See All** button on each of the 9 grid boxes and on each of the 3 actors — whether or not you've already answered that cell.
  - A grid box's **See All** pops up every valid film for that actor × category pairing, sorted by rarity points descending (title descending as a tiebreak), with your own pick marked if you made one — so you can check whether a higher-scoring answer existed.
  - An actor's **See All** pops up that actor's entire filmography, sorted by release year descending (title descending as a tiebreak) — no category filter, just everything they're credited in.

## Sandbox mode

Check **Sandbox mode** (next to Deal a new puzzle) to build a grid by hand instead of dealing one randomly — useful for testing specific actor/category combinations or setting up a puzzle for someone else to play.

- Checking it asks for confirmation (it clears whatever grid is currently up), then replaces the grid with pickers: a dropdown per row to choose an actor, and a category-type + category-value dropdown pair per column.
- As soon as both a row's actor and a column's category are set, that cell shows a live count of valid answers plus a **See All** button — the same popup used in normal play — so you can see immediately whether a pairing is trivial, impossible, or interesting before committing to it.
- **Fill in grid** randomly completes whatever actors/categories you haven't set yet, trying to keep the result solvable against anything you *did* set by hand. It never touches or second-guesses your manual picks, even ones with few or zero valid answers — Sandbox mode is meant for exploring those too.
- Unchecking Sandbox mode converts the current grid into a normal playable one (same actors/categories, fresh score) — but only once all 3 actors and 3 categories are set; otherwise it tells you to finish (or click Fill in grid) first. If every cell is set but at least one has 0 valid answers, you get a warning listing which cell(s) — you can still proceed, you'll just know going in that at least one box isn't solvable.
- Actor and category values are drawn from the same curated pools used for random dealing (`ACTOR_POOL`, `GENRES`, `DECADES`, `DIRECTORS`, `COLLECTIONS`) via dropdowns, rather than free-text TMDb search — simpler and more robust, at the cost of not being able to hand-pick an actor or director outside those lists.

### Inspecting the raw TMDb data (`inspect_tmdb.py`)

Sandbox mode also gives you a way to see exactly what TMDb returns for an actor (or a specific actor + film), for cases like the "Blade Runner 2049: Behind the Scenes" one — no API key ever touches this app's own network calls from a debugging tool, and Claude never handles your key either.

1. In Sandbox mode, click **Copy API call** next to an actor (for their whole filmography), or click any film title inside a **See All** popup (for that specific actor + film) — the status line confirms it copied.
2. Paste the copied snippet into `api_call_to_review` at the top of [`inspect_tmdb.py`](inspect_tmdb.py), replacing whatever is there.
3. Run `python3 inspect_tmdb.py`.

It fetches `/person/{id}/movie_credits` (and `/movie/{id}` too, if a film was included), prints the fields relevant to this app's filtering (`vote_count`, `video`, `genre_ids`, `popularity`, director, collection, etc.), and saves the full raw JSON under `tmdb_inspect_output/` for a closer look.

The script needs its own TMDb API key (separate from the one in the browser page) — same free key works fine. It checks, in order: a `TMDB_API_KEY` environment variable, a `tmdb_api_key.txt` file next to the script (gitignored), or it'll just prompt you at runtime.

## Categories

Every category comes from one of five fixed types, defined near the top of the `<script>` in `index.html`:

| Type | Example | Source array |
|---|---|---|
| Genre | "Comedy" | `GENRES` |
| Decade | "Released in the 2000s" | `DECADES` |
| Director | "Directed by Christopher Nolan" | `DIRECTORS` |
| Franchise / collection | "Marvel Cinematic Universe" | `COLLECTIONS` |
| Co-star | "Co-starred with Tom Hanks" | sampled from the actor pool itself |

A deal picks 3 categories at random from the combined pool of all five types (co-star candidates are limited to a random 15 other actors per deal, to keep the solvability check fast).

## Methodology / FAQ

**Does a film need any TMDb votes to count as an answer?**
Yes — at least 1 (`MIN_VOTE_COUNT` in `index.html`). TMDb's movie catalog includes non-feature entries (making-of featurettes, behind-the-scenes shorts, bonus clips) credited to actors right alongside real films, and these almost always sit at 0 TMDb votes — e.g. "Blade Runner 2049: Behind the Scenes" under Ryan Gosling. `isRealFeatureCredit()` rejects anything with 0 votes, plus anything matching a title-pattern denylist ("behind the scenes," "making of," "bloopers," "deleted scenes," "featurette," etc.) as a second line of defense. This is a heuristic, not a guarantee — see "Open issues" below if one slips through.

**How is the rarity score (1–50) calculated?**
`rarityScore()` maps a film's TMDb `vote_count` onto a 1–50 scale on a log10 curve: roughly 4 votes or fewer scores the maximum (50), roughly 20,000 votes or more scores the minimum (1), and everything in between is interpolated smoothly on the log scale — so the gap between 10 and 100 votes moves the score a lot more than the gap between 10,000 and 20,000 does. A correct cell is worth 50 points (for a valid answer) + that rarity score, so 51–100 points total per cell.

**Why isn't rarity based on IMDb instead?**
IMDb has no public API at all, and TMDb has no direct equivalent of an IMDb review count — this app only ever talks to TMDb, so rarity is TMDb's own vote count, not IMDb's.

**Why didn't a film I know an actor is in get accepted for a Director or Franchise/Collection category?**
Those two category types only check each actor's ~20 most popular films (`MOVIE_LOOKUP_CAP`) — checking every film's director/collection for every actor on every deal would mean far too many TMDb calls. An obscure film outside that window won't be suggested by "See All" or counted toward solvability, but it'll still be accepted if you type its exact title yourself and it actually satisfies the category.

**How does the app guarantee a dealt puzzle is actually solvable?**
Before showing a puzzle, it fetches real filmographies for the 3 sampled actors and tests category candidates one at a time against all three, only keeping a category once it's confirmed to have a valid answer for every actor. If a trio of actors can't yield 3 solvable categories after enough tries, it resamples a new trio (up to 6 attempts) rather than ever showing an unsolvable grid. (Sandbox mode deliberately bypasses this guarantee — see above.)

## Getting a TMDb API key

1. Create a free account at [themoviedb.org/signup](https://www.themoviedb.org/signup).
2. Go to your profile → **Settings** → **API**.
3. Click **Create** under "Request an API Key," choose **Developer**, and fill in the short form (any personal/non-commercial description works).
4. Copy the **API Key (v3 auth)** string and paste it into the app.

## Notes / known limitations

- See the Methodology / FAQ above for how rarity is scored, why a film needs at least 1 TMDb vote to count, and why Director/Collection categories only look at an actor's ~20 most popular films.
- The actor pool (~235 names, all with substantial film work from ~1990 to today) and category pool are hardcoded near the top of the `<script>` in `index.html` — edit the `ACTORS`, `DIRECTORS`, and `COLLECTIONS` arrays to tune who/what shows up.
- An actor's own "See All" (as opposed to a grid box's) isn't affected by the ~20-most-popular-films cap — it lists their complete filmography.
- Franchise/collection matching is a loose string match against TMDb's `belongs_to_collection` field and can occasionally miss films TMDb doesn't tag into a collection.
- No award-based categories (e.g. Oscar nominations) since TMDb doesn't track those — would need a separate static dataset to add them.

## Open issues / to revisit

- **The vote-count filter (`MIN_VOTE_COUNT = 1`) is a heuristic, not a guarantee.** It's plausible a popular "behind the scenes" or "making of" special picks up enough TMDb votes to slip past the filter and the title-pattern denylist (e.g. one not phrased like the usual "X: Behind the Scenes" pattern). If a junk non-feature title turns up again as a valid answer, use `inspect_tmdb.py` (see above) on that actor/film to see the raw TMDb fields and figure out a better rule.
  - Already checked via `inspect_tmdb.py` on Ryan Gosling's real credit list: TMDb's `video` field is **not** a useful signal — it's `false` on obvious junk ("Fight Club: Behind the Scenes," "DC Insiders Run Amuck," fake/hoax listings like "Ocean's Fourteen") *and* on legitimate films, so it can't distinguish the two. Every junk entry checked had `vote_count: 0`, so the current filter is doing its job on that sample. Also verified `MIN_VOTE_COUNT = 1` doesn't over-reject: Uma Thurman's "Kill Bill: The Whole Bloody Affair" (a genuinely rare, festival-only 4-hour cut) has `vote_count: 1423` and passes fine.
