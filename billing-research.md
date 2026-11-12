# Billing-order research: does the actor "own" the film?

*Notes from 2026-11-11. Nothing in the app has changed yet.*

## The problem

The 5,000-vote rule (`WELL_KNOWN_VOTE_COUNT` in `index.html`) makes sure people
know the **film**. It doesn't make sure they link **that actor** to it.

Example: a deal with Emma Thompson put *I Am Legend* at the top of See All
(sorted by votes). She's in it for about two minutes, as the doctor whose cure
starts the outbreak. Will Smith is the film.

## What TMDB gives us

- Every cast credit has an **`order`** field: billing position, 0-based
  (0 = top-billed). Usually it follows the poster or opening credits, but
  volunteers enter it, so it can be uneven for older or less popular films.
- It's already in the `/person/{id}/movie_credits` response the app fetches.
  We drop it in the `.map()` in the person-lookup code.
- There is **no screen-time data**. Billing order is the only signal.
- `/search/person`, which the app already calls, returns a **`known_for`**
  list. It's TMDB's top 3 films for that person, leaning toward recent
  popularity. For Emma Thompson it's Brave, Cruella and Saving Mr. Banks.

## Emma Thompson case study

"Billed" is 1-based. "Cast size" is the length of TMDB's cast list for the film,
and "Position" is billed ÷ cast size. ★ = one of IMDb's four "Known for" films.

| Votes | Billed | Cast size | Position | Film | Role |
|---|---|---|---|---|---|
| 23,971 | 11th | 59 | 19% | Harry Potter and the Prisoner of Azkaban | Trelawney |
| 22,729 | 67th | 107 | 63% | Harry Potter and the Deathly Hallows: Part 2 | Trelawney |
| 21,474 | 20th | 87 | 23% | Harry Potter and the Order of the Phoenix | Trelawney |
| 17,552 | 7th | 63 | 11% | I Am Legend | Dr. Alice Krippin |
| 16,309 | 12th | 139 | 9% | Beauty and the Beast | Mrs. Potts |
| 14,579 | 2nd | 31 | 6% | Brave | Elinor (voice) |
| 11,328 | 5th | 79 | 6% | Men in Black 3 | Agent O |
| 10,441 | 2nd | 69 | 3% | Cruella | The Baroness |
| 7,676 | 3rd | 124 | 2% | Love Actually | Karen |
| 5,599 | 6th | 55 | 11% | Men in Black: International | Agent O |
| ★ 3,597 | 1st | 37 | 3% | Saving Mr. Banks (2013) | P.L. Travers |
| ★ 1,938 | 1st | 25 | 4% | Sense and Sensibility (1995) | Elinor Dashwood |
| ★ 1,576 | 2nd | 33 | 6% | The Remains of the Day (1993) | Miss Kenton |
| ★ 617 | 1st | 50 | 2% | Howards End (1992) | Margaret Schlegel |

## Findings

1. **Billing order catches extreme cases.** Billed 67th in *Deathly Hallows 2*
   clearly means "you won't link her to this."
2. **Percent position doesn't work well.** Cast-list length depends on how many
   uncredited extras volunteers entered ("Military Driver"), not on how big the
   real cast is. *I Am Legend* comes out at 11%, which looks like a real
   supporting role, the same as her Agent O in *MIB: International*.
   *Beauty and the Beast*'s 139-entry list flatters Mrs. Potts (12th) to 9%.
3. **A fixed count works better on this sample.** "Billed in the top 5–6"
   catches *I Am Legend* and the Harry Potter films, and keeps *Brave*,
   *Cruella*, *MIB 3* and *Love Actually*.
4. **The 5k rule leaves out her signature films.** All four IMDb "Known for"
   films are under 5,000 votes, and she's billed 1st or 2nd in every one. The
   rule leans toward blockbusters, where a big name is often supporting or a
   cameo. Her best-known films are prestige dramas with fewer votes.
5. Raw billing can also hide memorable supporting roles in big ensembles
   (Trelawney is billed 11th–20th, but many people do picture her in Harry Potter).

## Candidate approaches

1. **Combined score instead of two separate cutoffs.** `votes × billing weight`,
   e.g. weight 1.0 for billed 1st–2nd, dropping to about 0.3 by 10th and near 0
   after that. *I Am Legend* (17,552 × about 0.4) would then score about the same
   as *Saving Mr. Banks* (3,597 × 1.0) instead of far ahead, and
   *Deathly Hallows 2* would score close to zero. This could also drive the
   See All sort.
2. **Lower the vote cutoff for top billing.** A film counts as well-known if it
   has ≥5k votes and the actor is billed in the top 6, **or** ≥1.5k votes and the
   actor is billed 1st–2nd. That would bring in 3 of her 4 IMDb films (not
   *Howards End*).
3. **Use TMDB `known_for` as a check.** It's too short (3 films) to use on its
   own, but when tuning #1 or #2, an actor's `known_for` films should come out
   near the top.
4. **Cheap first step:** add a "Billed" column to the See All table so we can
   see how often this happens in real deals before choosing a rule.

## Open questions / next steps

- [ ] Run this same table for 4–5 actors of different types (an action lead
      like Will Smith, a character actor, an ensemble regular). Emma Thompson
      is an unusually strong example because her fame comes from 90s period
      dramas. For many leads there may be little gap between top-billed films
      and most-voted films.
- [ ] **Do older films get far fewer votes?** Our guess: yes, on both sites,
      and especially on TMDB, whose users skew younger and which only started
      in 2008, while IMDb began in 1990. Her 1990s films are a hint:
      *Howards End* (617) and *Sense and Sensibility* (1,938) on TMDB.
      Things to look at:
  - Median `vote_count` by release decade for well-known films (e.g. Best
    Picture winners or AFI Top 100) on TMDB vs. IMDb.
  - Whether a fixed 5k cutoff should scale with release year (e.g. a lower
    bar for pre-2000 films), or use percentile within the decade instead.
  - Whether `popularity` or `vote_average` changes this differently from
    `vote_count`.
