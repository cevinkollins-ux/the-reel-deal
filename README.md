# The Reel Deal

A single-file, browser-based movie trivia grid: 3 actors × 3 categories, and you name a film that satisfies each actor/category pairing. Play the Daily (one grid shared by everyone that day, so you can compete with friends), or deal a new grid whenever you want.

## How it works

- Open `index.html` directly in a browser — no build step, no server required.
- Paste a free [TMDb](https://www.themoviedb.org) API key (v3 auth) into the setup box. It's saved only in that browser's `localStorage`.
- Click **Deal a new puzzle** to get 3 random actors and 3 random categories. Every actor × category cell is checked against real TMDb filmographies before the puzzle is shown, so you're never stuck on an impossible pairing (if a trio of actors can't yield 3 solvable categories, it re-samples a new trio automatically).
- Type a film title into a cell — an autocomplete dropdown (powered by TMDb search) helps you pick the right one. Submit to check it.
- Scoring per correct cell: 50 points for a valid answer + 1–50 rarity points on a log scale of the film's TMDb vote count (obscure picks score higher). Each film can only be used once per grid.
- A solved cell becomes the film's poster (TMDb's `poster_path`, served from `image.tmdb.org`) with the cell's score badged in the top-right corner. Click the badge for the breakdown: completeness, rarity, and the vote count the rarity came from. If TMDb has no poster on file for that film — or the file 404s — the cell falls back to showing the title.
- Release years show up everywhere a specific film is named — a solved cell's poster tooltip and points breakdown, the "Used so far" list, and every See All popup — except the autocomplete dropdown while you're still typing (kept minimal there so it stays fast and uncluttered; year only appears there if 2+ results share the exact same title, to disambiguate).
- **Ready to see answers**: once a puzzle is dealt, click this to reveal a **See All** button on each of the 9 grid boxes and on each of the 3 actors — whether or not you've already answered that cell.
  - A grid box's **See All** pops up every valid film for that actor × category pairing, sorted by votes descending, with your own pick marked if you made one — so you can check whether a higher-scoring answer existed.
  - An actor's **See All** pops up that actor's entire filmography, sorted by votes descending — no category filter, just everything they're credited in.
  - Both tables open sorted by **Votes**, most first, every time. Click any column header to re-sort that table; click it again to flip the order.

## Daily puzzle

**Today's Daily** deals one grid that's the same for everyone that day, so friends can play the same puzzle and compare scores. Once your key is saved, the page opens straight to it.

- The day rolls over at **midnight New York time** for everyone, wherever they are. Dailies are numbered from Daily #1 on 2026-09-23 (`DAILY_EPOCH`).
- There's no server: every browser deals the Daily itself, using a random-number generator seeded by the date (`seededRng("daily:YYYY-MM-DD#attempt")`) in place of `Math.random()`. Same seed means the same picks, so everyone lands on the same grid.
- Your progress is saved in the browser. Refreshing, dealing a random puzzle, or closing the tab and coming back later brings you back to where you left off; only today's Daily is kept.
- **Ready to see answers** ends your Daily: it asks for confirmation, then locks any unanswered cells (the lock is saved too), so nobody can peek and keep going.
- Wrong guesses aren't penalized.
- **The one catch:** the dealer still checks every pick against live TMDb data. If TMDb answered a check differently for two players (it re-ranks films by popularity every day, which can move a film in or out of the 50-film window Director/Franchise checks use), their grids could come out different. The grid code above the grid (e.g. `grid XTSX`) makes that obvious at a glance. If yours doesn't match a friend's, open their share link (below).

## Share grid links

**Share grid** copies a link to the exact grid on screen, plus your score and a 🟩/⬜ board (Wordle-style) to paste into a group chat. Opening the link rebuilds that grid instantly, with no dealing and no TMDb lookups, so it works for random deals and Sandbox grids too.

- The whole grid lives in the link (`#g=` followed by base64-encoded JSON of the 3 actor names, the 3 `[type, value]` categories, and the Daily's date if it is one). Everything in a link is checked against the same fixed actor/category lists the dealer uses, and anything else is rejected.
- A link to **today's Daily** becomes your Daily, with progress saved as usual. That's the fix if your Daily ever came out different from a friend's. If you'd already answered cells on a different grid, it asks before replacing it.
- A link to an older Daily, or to any non-Daily grid, opens as a one-off **Shared grid**, and progress on it isn't saved.
- If someone opens a link before pasting their TMDb key, the grid loads as soon as they save one.

## Sandbox mode

Check **Sandbox mode** (next to Deal a new puzzle) to build a grid by hand instead of dealing one randomly — useful for testing specific actor/category combinations or setting up a puzzle for someone else to play.

- Checking it asks for confirmation (it clears whatever grid is currently up), then replaces the grid with pickers: a dropdown per row to choose an actor, and a category-type + category-value dropdown pair per column.
- As soon as both a row's actor and a column's category are set, that cell shows a live count of valid answers plus a **See All** button — the same popup used in normal play — so you can see immediately whether a pairing is trivial, impossible, or interesting before committing to it.
- **Fill in grid** randomly completes whatever actors/categories you haven't set yet, trying to keep the result solvable against anything you *did* set by hand. It never touches or second-guesses your manual picks, even ones with few or zero valid answers — Sandbox mode is meant for exploring those too.
- Unchecking Sandbox mode converts the current grid into a normal playable one (same actors/categories, fresh score), which you can then send to someone with **Share grid** — but only once all 3 actors and 3 categories are set; otherwise it tells you to finish (or click Fill in grid) first. If every cell is set but at least one has 0 valid answers, you get a warning listing which cell(s) — you can still proceed, you'll just know going in that at least one box isn't solvable.
- Actor and category values are drawn from the same curated pools used for random dealing (`ACTOR_POOL`, `GENRES`, `DECADES`, `DIRECTORS`, `COLLECTIONS`, plus every valid letter range, letter set and year range) via dropdowns, rather than free-text TMDb search — simpler and more robust, at the cost of not being able to hand-pick an actor or director outside those lists.

### Inspecting the raw TMDb data (`inspect_tmdb.py`)

Sandbox mode also gives you a way to see exactly what TMDb returns for an actor (or a specific actor + film), for cases like the "Blade Runner 2049: Behind the Scenes" one — no API key ever touches this app's own network calls from a debugging tool, and Claude never handles your key either.

1. In Sandbox mode, click **Copy API call** next to an actor (for their whole filmography), or click any film title inside a **See All** popup (for that specific actor + film) — the status line confirms it copied.
2. Paste the copied snippet into `api_call_to_review` at the top of [`inspect_tmdb.py`](inspect_tmdb.py), replacing whatever is there.
3. Run `python3 inspect_tmdb.py`.

It fetches `/person/{id}/movie_credits` (and `/movie/{id}` too, if a film was included), prints the fields relevant to this app's filtering (`vote_count`, `video`, `genre_ids`, `popularity`, director, collection, etc.), and saves the full raw JSON under `tmdb_inspect_output/` for a closer look.

The script needs its own TMDb API key (separate from the one in the browser page) — same free key works fine. It checks, in order: a `TMDB_API_KEY` environment variable, a `tmdb_api_key.txt` file next to the script (gitignored), or it'll just prompt you at runtime.

## Categories

Every category comes from one of eight fixed types. Each type is one entry in the `CATEGORY_TYPES` table in `index.html`, which says everything about it: its label, allowed values, what a deal tries, how matching films are found, and how a guess is checked. To add a type, add an entry at the end of the table (the comment above it lists the fields) with a `dealsFrom` date, so Dailies already in play don't change.

| Type | Example | Source array |
|---|---|---|
| Genre | "Comedy" | `GENRES` |
| Decade | "Released in the 2000s" | `DECADES` |
| Director | "Directed by Christopher Nolan" | `DIRECTORS` |
| Franchise / collection | "Marvel Cinematic Universe" | `COLLECTIONS` |
| Co-star | "Co-starred with Tom Hanks" | sampled from the actor pool itself |
| Title starts with | "Title starts with D–M" | any 7–10 letter span of the alphabet (`allLetterRanges()`) |
| Title contains | "Title contains F, V, W or Y" | `CONTAINS_LETTER_SETS` |
| Release-year range | "Released 2010–2016" | any 5–10 year span from 1980 to this year (`allYearRanges()`) |

A deal picks 3 categories at random from the combined pool of all eight types (co-star candidates are limited to a random 15 other actors per deal, to keep the solvability check fast; letter and year ranges are limited to 3 of each per deal, so the dozens of possible ranges don't crowd out the other types). A dealt grid never has two categories of the same type, so no Comedy + Drama and no two co-stars. Dailies follow this rule from 2026-11-10 on (`ONE_CATEGORY_PER_TYPE_FROM`). In Sandbox, your own picks can share a type, but **Fill in grid** never adds a repeat.

- **Title starts with** goes by a title's first letter, accents ignored. Each letter range is dealt with a random article rule, and the label always names it: "Title starts with P–Z" counts "The Big Short" as T; `(ignore "The")` skips a leading "The"; `(ignore "A/An")` skips a leading "A" or "An"; `(ignore articles)` skips all three. A title starting with a number fits no range. Dailies before 2026-11-12 (`ARTICLE_MODES_FROM`) always ignore articles, and now say so.
- **Title contains** checks the whole title, "The" included.
- **Release-year ranges** include both end years. A range that's exactly a decade (e.g. 2010–2019) is left out, since Decade covers it.
- Like Genre and Decade, these three need at least 5 matching films per actor before they're dealt. They use only a film's title and release date, so they cost no extra TMDb calls.
- These three types only appear in Dailies from 2026-11-09 on (`TITLE_YEAR_CATEGORIES_FROM`), so a Daily already in progress didn't change when they were added. Random deals and Sandbox have them now.

## Methodology / FAQ

This same content is also available inside the app itself — click **Methodology & FAQ** in the footer for an in-window popup, no scrolling through this file required.

**Does a film need any TMDb votes to count as an answer?**
Yes — at least 1 (`MIN_VOTE_COUNT` in `index.html`). TMDb's movie catalog includes non-feature entries (making-of featurettes, behind-the-scenes shorts, bonus clips, theme-park ride POV videos) credited to actors right alongside real films, and most sit at 0 TMDb votes — e.g. "Blade Runner 2049: Behind the Scenes" under Ryan Gosling. Some pick up a few votes anyway (a Disneyland "Star Wars: Rise of the Resistance" ride video under Adam Driver had 13), so `isRealFeatureCredit()` also rejects anything with a "|" in the title — TMDb consistently formats these as "Attraction Name | Venue," and real film titles don't contain a literal pipe character — plus anything matching a title-pattern denylist ("behind the scenes," "making of," "bloopers," "deleted scenes," "featurette," etc.). This is a heuristic, not a guarantee — see "Open issues" below if one slips through.

**What's the number in the corner of a solved cell?**
That's what the cell scored. A correct answer turns the cell into the film's poster with its score badged in the corner — click the badge for the breakdown (completeness + rarity, and the vote count the rarity came from). If TMDb has no poster on file for that film, the cell shows the title instead.

**How is the rarity score (1–50) calculated?**
`rarityScore()` maps a film's TMDb `vote_count` onto a 1–50 scale on a log10 curve: roughly 4 votes or fewer scores the maximum (50), roughly 20,000 votes or more scores the minimum (1), and everything in between is interpolated smoothly on the log scale — so the gap between 10 and 100 votes moves the score a lot more than the gap between 10,000 and 20,000 does. A correct cell is worth 50 points (for a valid answer) + that rarity score, so 51–100 points total per cell.

**Why isn't rarity based on IMDb instead?**
IMDb has no public API at all, and TMDb has no direct equivalent of an IMDb review count — this app only ever talks to TMDb, so rarity is TMDb's own vote count, not IMDb's.

**Why didn't a film I know an actor is in get accepted for a Director or Franchise/Collection category?**
Those two category types only check each actor's ~50 most popular films (`MOVIE_LOOKUP_CAP`) — checking every film's director/collection for every actor on every deal would mean far too many TMDb calls. (Those 50 lookups per actor run 10 at a time in parallel, and each film is only ever fetched once per session, so the cap costs little extra time.) An obscure film outside that window won't be suggested by "See All" or counted toward solvability, but it'll still be accepted if you type its exact title yourself and it actually satisfies the category.

**How does the app guarantee a dealt puzzle is actually solvable?**
Before showing a puzzle, it fetches real filmographies for the 3 sampled actors and tests category candidates one at a time against all three, only keeping a category once it's confirmed to have a valid answer for every actor. If a trio of actors can't yield 3 solvable categories after enough tries, it resamples a new trio (up to 6 attempts) rather than ever showing an unsolvable grid. (Sandbox mode deliberately bypasses this guarantee — see above.)

## Getting a TMDb API key

1. Create a free account at [themoviedb.org/signup](https://www.themoviedb.org/signup).
2. Go to your profile → **Settings** → **API**.
3. Click **Create** under "Request an API Key," choose **Developer**, and fill in the short form (any personal/non-commercial description works).
4. Copy the **API Key (v3 auth)** string and paste it into the app.

## Notes / known limitations

- See the Methodology / FAQ above for how rarity is scored, why a film needs at least 1 TMDb vote to count, and why Director/Collection categories only look at an actor's ~50 most popular films.
- The actor pool (~235 names, all with substantial film work from ~1990 to today) and category pool are hardcoded near the top of the `<script>` in `index.html` — edit the `ACTORS`, `GENRES`, `DIRECTORS`, and `COLLECTIONS` arrays to tune who/what shows up. Changing a list changes the Daily for anyone who hasn't dealt today's yet.
- An actor's own "See All" (as opposed to a grid box's) isn't affected by the ~50-most-popular-films cap — it lists their complete filmography.
- Franchise/collection matching is a loose string match against TMDb's `belongs_to_collection` field and can occasionally miss films TMDb doesn't tag into a collection.
- No award-based categories (e.g. Oscar nominations) since TMDb doesn't track those — would need a separate static dataset to add them.

## Open issues / to revisit

- **The junk-content filter is a set of heuristics, not a guarantee.** It's plausible some other kind of non-feature entry (not phrased like the usual denylist patterns, and without a "|" in the title) slips through with enough votes to count. If a junk non-feature title turns up again as a valid answer, use `inspect_tmdb.py` (see above) on that actor/film to see the raw TMDb fields and figure out a better rule.
  - Fixed so far: **0-vote entries** (`MIN_VOTE_COUNT = 1`) and **"|"-delimited theme-park/venue titles** (added after Adam Driver × Action returned "Star Wars: Rise of the Resistance | Disneyland Resort," a Disneyland ride POV video with 13 votes — vote count alone wasn't going to catch that one).
  - Checked via `inspect_tmdb.py` on Ryan Gosling's real credit list: TMDb's `video` field is **not** a useful signal — it's `false` on obvious junk ("Fight Club: Behind the Scenes," "DC Insiders Run Amuck," fake/hoax listings like "Ocean's Fourteen") *and* on legitimate films, so it can't distinguish the two.
  - Also verified the filter doesn't over-reject: Uma Thurman's "Kill Bill: The Whole Bloody Affair" (a genuinely rare, festival-only 4-hour cut, `vote_count: 1423`) passes fine.
