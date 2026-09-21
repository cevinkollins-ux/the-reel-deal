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
- Unchecking Sandbox mode converts the current grid into a normal playable one (same actors/categories, fresh score) — but only once all 3 actors and 3 categories are set; otherwise it tells you to finish (or click Fill in grid) first.
- Actor and category values are drawn from the same curated pools used for random dealing (`ACTOR_POOL`, `GENRES`, `DECADES`, `DIRECTORS`, `COLLECTIONS`) via dropdowns, rather than free-text TMDb search — simpler and more robust, at the cost of not being able to hand-pick an actor or director outside those lists.

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

## Getting a TMDb API key

1. Create a free account at [themoviedb.org/signup](https://www.themoviedb.org/signup).
2. Go to your profile → **Settings** → **API**.
3. Click **Create** under "Request an API Key," choose **Developer**, and fill in the short form (any personal/non-commercial description works).
4. Copy the **API Key (v3 auth)** string and paste it into the app.

## Notes / known limitations

- Data comes from TMDb, not IMDb — TMDb has no direct IMDb review-count equivalent, so rarity is based on TMDb's own vote count.
- TMDb's "movie" catalog includes non-feature entries (making-of featurettes, behind-the-scenes shorts, bonus clips) credited alongside real films — e.g. "Blade Runner 2049: Behind the Scenes" shows up in Ryan Gosling's credits. These almost always have 0 TMDb votes, which the rarity formula would otherwise treat as *maximum* rarity, making junk entries look like the best possible answer. `isRealFeatureCredit()` filters anything with 0 votes or a title matching common bonus-content patterns (behind the scenes, making of, bloopers, deleted scenes, featurette, etc.) — applied everywhere a film is considered valid: profile fetching, autocomplete, and submit validation. A genuinely obscure real film with even 1 TMDb vote still counts.
- The actor pool (~235 names, all with substantial film work from ~1990 to today) and category pool are hardcoded near the top of the `<script>` in `index.html` — edit the `ACTORS`, `DIRECTORS`, and `COLLECTIONS` arrays to tune who/what shows up.
- Director/collection solvability checks and a grid box's "See All" only look at each actor's ~20 most popular films, not their full filmography — an obscure director credit outside that window won't be suggested or counted toward solvability, even though typing it in yourself would still score. (An actor's own "See All" isn't affected by this — it lists their complete filmography.)
- Franchise/collection matching is a loose string match against TMDb's `belongs_to_collection` field and can occasionally miss films TMDb doesn't tag into a collection.
- No award-based categories (e.g. Oscar nominations) since TMDb doesn't track those — would need a separate static dataset to add them.

## Open issues / to revisit

- **The vote-count filter (`MIN_VOTE_COUNT = 1`) is a heuristic, not a guarantee.** It's plausible a popular "behind the scenes" or "making of" special picks up enough TMDb votes to slip past the filter and the title-pattern denylist (e.g. one not phrased like the usual "X: Behind the Scenes" pattern). If a junk non-feature title turns up again as a valid answer, the next step is inspecting the *raw* TMDb `/person/{id}/movie_credits` response for that actor to see what actually distinguishes real features from bonus content in the fields TMDb returns (e.g. `video`, `genre_ids`, `popularity` — not yet explored) — Claude's sandbox can reach the TMDb API directly, but doesn't hold a key, so this needs either the user running a `curl` command and pasting back the JSON, or a screenshot/copy of a specific offending entry from a See All popup (which already exposes title + vote count, as it did for the Blade Runner 2049 case).
