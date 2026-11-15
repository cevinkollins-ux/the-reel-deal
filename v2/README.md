# The Reel Deal v2: notes, research and tools

v2 is now the game. The game itself is [`index.html`](../index.html) at the repo
root (still one file, no build step), which is what GitHub Pages serves at
<https://cevinkollins-ux.github.io/the-reel-deal/>. The original game is kept,
unchanged, at [`v1/index.html`](../v1/index.html), playable at `/the-reel-deal/v1/`.
This folder holds the research and tooling behind v2.

- **What was found, and why v2 does what it does:** [FINDINGS.md](FINDINGS.md)

## Trying it

**Without pasting a key** (uses the key in the repo's `.env`):

```bash
python3 v2/tools/dev_server.py
```

Then open <http://localhost:8744/>. The same server also shows the original
game at <http://localhost:8744/v1/> for side-by-side checks, and the original
with the optional hotfix at <http://localhost:8744/v1-hotfix/>. Neither changes
any file.

**The usual way:** open `index.html` in a browser and paste a TMDb key. On the
live site the game is at the root and the original is at `/v1/`. They share the
saved key, so nobody has to paste it twice, but their Dailies are saved
separately.

## What's different from the original

| | Original | v2 |
|---|---|---|
| Points | 50 + 1–50 by raw TMDb votes | 50 + 0–50 **deep-cut bonus**: the film's votes adjusted for its release year × the actor's billing |
| Who the actor is | First hit of a name search, then names compared | TMDb person id, checked by id |
| What counts | Any cast credit with a vote | A role in a released feature: no documentaries-as-self, archive footage, shorts or unreleased films |
| A typed title | First hit of TMDb's search | The actor's own filmography first |
| Director / franchise | The actor's 50 most popular films, one lookup each | The director's or franchise's full film list |
| "Well known" (dealer) | 5,000 raw votes | Link strength of 3,000: famous for its year *and* a real role |
| Category mix | First three categories that pass, so mostly genre + decade | Grid shape chosen first; usually one of director / franchise / co-star |
| Whole-grid check | None | Nine different well-known films must exist |
| The Daily | Dealt live in each browser | Next 60 days dealt ahead and stored in the page; live dealing after that |
| TMDb calls per deal | about 120 (up to 795) | about 13 (up to 33) |

Also new: a **Scoring lab** (footer link) that shows any actor's films with old
and new points and lets you move the scoring sliders, a guess counter, a
phone-sized typing box, arrow keys in the suggestion list, and a message that
names the film that was checked.

## Keeping it current

Three things in the root `index.html` are snapshots of TMDb and want refreshing every
month or two, and whenever `ACTORS`, `DIRECTORS` or `COLLECTIONS` change:

```bash
python3 v2/research/build_data.py --write
```

That rewrites the `<generated-data>` block: actor and director ids, franchise
definitions, the votes-by-year table behind the scoring, and the lists the
dealer uses to pick promising actor trios. Adding a franchise means adding it
to `FRANCHISES` at the top of that script as well as to `COLLECTIONS`.

**Pre-dealt Dailies** run out on 2027-01-14. To add more, open the Scoring lab,
expand "Deal upcoming Dailies ahead of time", and paste the block it prints
over `PREDEALT_DAILIES`. With the dev server running, the same list can be
written without copying by hand (see `/__save/` in `tools/dev_server.py`). A
date that isn't listed is simply dealt live, as in the original.

**Tuning.** Scoring constants are in `SCORING`, the dealer's mix in `DEAL`,
both near the top of the script with comments. Try a scoring change in the lab
first. If you change a scoring constant, change it in `research/model.py` too,
then run `research/crosscheck.py` to confirm the page and the script agree.

## What's in here

```
../index.html              the game (v2), served by GitHub Pages
../v1/index.html           the original game, kept as it was
FINDINGS.md                the audit and the scoring write-up
patches/v1-hotfix.patch    optional three-line fix for the original (not applied;
                           apply with: git apply --directory=v1 v2/patches/v1-hotfix.patch)
tools/dev_server.py        local server: static files + TMDb proxy that adds the key
tools/tmdbcache.py         TMDb client with a one-day disk cache (v2/.cache/, ignored by git)
research/build_data.py     builds the <generated-data> block in index.html
research/model.py          the scoring model in Python, mirroring the page
research/crosscheck.py     confirms the page's scoring and model.py agree
research/audit_pool.py     re-runs the audit of the original's actor and category pools
research/check_title_search.py   how often a typed title finds the wrong film
research/compare_scoring.py      old vs new points for example films, and pool-wide stats
research/fetch_pool.py, fetch_year_table.py   raw data pulls used early in the research
```

## Letting friends play without a key

The page has one hook for this. If whatever serves it sets
`window.REEL_DEAL_TMDB_PROXY` to the address of a proxy that adds the TMDb key
itself, the key box disappears and everything goes through the proxy. The dev
server does exactly that locally. Hosting such a proxy publicly (a small
serverless function would do) would let friends open a link and play. That
part isn't built: it needs somewhere to run and a decision about putting your
key behind a public endpoint.
