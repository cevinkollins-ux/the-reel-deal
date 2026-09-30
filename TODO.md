# To-do: next session

Notes for picking back up. Nothing here is implemented yet — just findings and
an approach for each, written while the context was fresh.

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

Current pool is built in `buildCategoryPool()` ([index.html:511](index.html:511))
from `GENRES` (15), `DECADES` (4: 1990/2000/2010/2020),
`DIRECTORS` ([index.html:496](index.html:496)), `COLLECTIONS` (20 franchises,
[index.html:504](index.html:504)), plus 15 sampled co-stars. Adding a new
category type touches four spots:

1. Add to/generate candidates in `buildCategoryPool()`.
2. Add a solvability check in `categoryValidForAll()` ([index.html:818](index.html:818)).
3. Add a match-lister in `getValidFilms()` ([index.html:847](index.html:847)) (powers "See All").
4. Add the submit-time check in `submitGuess()` ([index.html:2114](index.html:2114) onward).

### "Starts with [letter range]" (the one you asked about)

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
