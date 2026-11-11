# To-do: next session

Notes for picking back up: findings and an approach for each, written while
the context was fresh. Items marked **Done** have since been built.

## 1. Rarity score: votes vs. popularity vs. a blend

Current `rarityScore()` ([index.html:2064](index.html:2064)) is purely a
log10 curve over `vote_count`. TMDb also returns `popularity` (a
recency-weighted activity score TMDb computes from views, votes, watchlist
adds, etc. — it's not just "more votes = more popular", it moves faster and
resets/decays over time, which is a fundamentally different signal than a
cumulative vote count).

Things to weigh before picking an approach:

- `vote_count` is stable/cumulative — a 1985 cult classic and a movie that
  was trending last month can have similar vote counts, but very different
  `popularity` right now. Pure `popularity` would probably make the rarity
  score noisier/less predictable session to session (a movie's popularity
  can spike for reasons unrelated to how "obscure" it actually is — a recent
  re-release, an actor's unrelated news cycle, a meme).
   - Because of this, popularity might actually reward oddly *modern viral*
    picks with the same "rare" score as truly obscure films, if used alone.
- `vote_count` is more of a stable "how many people have ever logged an
  opinion on this" — probably still the better sole proxy for "obscure",
  but a blend might reward genuinely rare-but-currently-buzzy answers a bit
  differently than a pure vote-count curve does. Worth deciding if that's
  actually a desirable effect for this game or just noise.
- If blending, need to decide the combination function (e.g. weighted
  average of two independently-normalized log curves, or use `popularity`
  only as a tie-breaker/modifier on top of the existing vote-based score)
  and re-tune the constants in `rarityScore()` (currently tuned so ~4 votes
  → 50, ~20,000 votes → 1, see [index.html:2064](index.html:2064)) so
  the output range and feel don't change unexpectedly for existing plays.
- Whatever's decided, update the FAQ entry that documents the formula
  (`FAQ_ITEMS`, "How is the rarity score calculated?" around
  [index.html:982](index.html:982)) to match.
- Good first step next time: pull `popularity` values for a range of known
  answers (a few blockbusters, a few genuinely obscure ones) via
  `inspect_tmdb.py` and eyeball whether it actually tracks "obscurity" the
  way we want before committing to a formula.

## 2. More category types

**Done (2026-11-08):** each category type is now one entry in
`CATEGORY_TYPES` in `index.html`. The dealer, solvability checks, See All,
guess checking, Sandbox and share links all read from that table, so adding a
type means adding one entry (the comment above the table lists its fields),
plus a line in the FAQ (`FAQ_ITEMS`) and the README's Categories table.

New types go at the **end** of the table, and get a `dealsFrom` date. A deal
draws its random values in table order, and the Daily's picks come from a
date-seeded randomizer, so a type added anywhere else, or without a start
date, would change Dailies people are already playing.

**Done (2026-11-08):** a dealt grid has at most one category of each type
(`ONE_CATEGORY_PER_TYPE_FROM`, Dailies from 2026-11-10 on). Open question:
Decade and Release-year range are separate types, so a grid can still have
"Released in the 2010s" next to "Released 2011–2016". Same for the two
title-letter types. If that feels repetitive, group them as one "family" for
this rule.

### Title and release-year ideas (added 2026-11-08)

- **Done:** Title starts with a letter range, 7–10 letters wide (e.g. "D–M").
- **Done:** Title contains F, V, W or Y. A common category on other movie
  grids, and a good mix of fairly rare letters.
- **Done:** Released within a year range of 5–10 years (e.g. "Released
  2010–2016").
- Released before 2000, and a matching "2000 or later". The same pair could
  work for other cutoff years (e.g. before/after 1990).
- 1-word title.
- 2-word title.
- 3-word title.
- More than 3 words in the title.
  - For all four word counts, articles and "and" don't count as words
    ("the", "a", "an", "and"), so "The Dark Knight" is 2 words.
- Title contains a number, written as digits or spelled out ("3" and
  "Three" both count).

All of these need only the title or release date, which every credit
already has, so they cost no extra TMDb calls.

### "Starts with [letter range]" — **Done** (built at 7–10 letters wide)

- Pick a random contiguous range of the alphabet 7–13 letters wide (e.g. "E–M"),
  label it like `Starts with E–M`.
- **Strip leading articles before checking the first letter** — "The Matrix"
  should count as "M", not "T", or the category will be quietly biased
  toward whatever range contains T/A. Use something like
  `title.replace(/^(the|a|an)\s+/i, "")[0].toUpperCase()`.
- No extra TMDb data needed — works directly off `title`, so it's as cheap
  as genre/decade (no per-movie detail fetch required).
- Also apply the same 5-match minimum used for genre/decade
  (`MIN_MATCHES_FOR_BROAD_CATEGORY`, [index.html:777](index.html:777)) since
  this is another broad category — an actor could otherwise have exactly one
  film starting with a rare letter combination.

### Other ideas worth considering

Cheap — no extra API calls (data already on the person `movie_credits` /
search cast objects, e.g. `vote_average`, confirmed present at that level
from earlier inspection):

- **"Critically acclaimed" (vote_average ≥ 7.5, say)** — straightforward
  numeric filter, same shape as genre/decade.
- **"Panned / so-bad-it's-notable" (vote_average ≤ 4, with a reasonable
  vote_count floor so it's not just 1-vote noise)** — fun contrast category,
  same shape.

Cheap-ish — needs a per-movie detail fetch, but can piggyback on the fetch
`actorHasDirector`/`actorHasCollection` already do via
`getMovieDirectorCollection()` ([index.html:746](index.html:746)), which
already hits `/movie/{id}` for every candidate up to `MOVIE_LOOKUP_CAP`. That
function currently only extracts `directors` and `collection` from the
response and caches it — cheap to also stash `runtime`,
`original_language`, and `production_countries` on the same cached object
since the fetch is already happening:

- **Runtime bucket** (e.g. "Runtime under 90 min" / "over 150 min").
- **Not in English** (`original_language !== "en"`) — "Foreign-language film".
- **Country of production** (e.g. "Made in the UK") from
  `production_countries`.

More involved / worth flagging as open questions rather than committing to:

- **Awards** (Oscar winner/nominee, etc.) — TMDb's API has no awards data at
  all, so this would need a different data source entirely. Skip unless
  we're open to adding a second API.
- **Keywords/themes** (e.g. "time travel", "based on a true story") via
  `/movie/{id}/keywords` — doable but yet another per-movie call on top of
  the details fetch; only worth it if we fold it into the same
  `getMovieDirectorCollection`-style cached lookup rather than a separate
  round trip.
- **Same release year** (as opposed to decade) — probably too narrow per
  actor to reliably hit the 5-match minimum; would likely need to stay at
  the 1-match floor like director/collection.

## 3. Require well-known films in each category (added 2026-11-11)

Idea: a category is only dealt if each actor has **at least 2 matching films
with 5,000+ TMDb votes**.

The problem: today the only bar is a match count — 5 films for broad types
(`MIN_MATCHES_FOR_BROAD_CATEGORY`) and 1 for director, collection and costar
(`minMatches` on each `CATEGORY_TYPES` entry). An actor can pass with 10
films in a category that each have 3–50 votes. Nobody has heard of any of
them, so the square is technically solvable but not fun.

Things to work out:

- **Where to check.** The deal's solvability check already gets each actor's
  matches from `matches(profile, v)`, and those credits carry `vote_count`.
  So this can be a second test next to `minMatches`, e.g.
  `matches.filter(m => m.vote_count >= 5000).length >= 2`. No extra TMDb
  calls needed.
- **Thresholds.** 2 films and 5,000 votes are starting guesses. Check some
  real deals with `inspect_tmdb.py` to see how often categories still get
  dealt, especially for older or international actors, whose films tend to
  have fewer TMDb votes. If too few deal, try a lower vote floor
  (1,000–2,000) or 1 film for director/collection/costar.
- **Constants.** Name them like the existing ones (e.g.
  `MIN_WELL_KNOWN_MATCHES`, `WELL_KNOWN_VOTE_COUNT`), or put them on each
  `CATEGORY_TYPES` entry if types need different values.
- **Dailies.** This changes which categories get dealt, so it would change
  Dailies people are already playing. Gate it behind a start date the same
  way `ONE_CATEGORY_PER_TYPE_FROM` is gated.
- **Rarity still works.** This only decides whether a category is dealt.
  Obscure films still count as answers and still score high rarity.
- **Docs.** Update the FAQ entry on minimum matches (`FAQ_ITEMS`) and the
  README to match.
