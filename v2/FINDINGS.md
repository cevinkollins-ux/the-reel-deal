# The Reel Deal: audit and scoring review

*Written 2026-11-13 to 2026-11-15. Everything here was measured against live
TMDb data and, where it says "reproduced", in the real page. The original game
is kept unchanged at [`v1/index.html`](../v1/index.html). The fixes are in the
current game, [`index.html`](../index.html) at the repo root. (This was written
while the new game still lived in `v2/`; where it says "v2", it means the
current game.)*

## The short version

1. **Four actors can never be answered in the original game.** Every guess for
   Zoe Saldana, Salma Hayek, Priyanka Chopra or Zoe Kravitz is rejected, because
   TMDb spells their names differently. A replay of the Daily puts one of them
   in seven grids so far and upcoming, including #53 (Nov 14), #67 (Nov 28) and
   #69 (Nov 30).
2. **Typing a correct title checks the wrong film about 1 time in 20.** "Top
   Gun" checks *Top Gun: Maverick*, "Toy Story" checks *Toy Story 5*, "Deadpool"
   checks *Deadpool & Wolverine*.
3. **The points reward junk.** A fifth of all "valid" answers are documentary
   appearances, archive footage and the like, and they sit at the top of the
   scale: 46% of everything worth 95+ points isn't a role in a released film.
4. **The best categories almost never come up.** In 82 replayed Dailies,
   Director was dealt twice and Franchise never. Four of the 50 director and
   franchise entries can't match anything at all, including Marvel Cinematic
   Universe and Fast & Furious.
5. **See All crashes on a Genre cell** after a page reload or a share link.

v2 fixes all five, replaces the score with one that measures how unlikely
people are to connect *that actor* with *that film*, and deals a more varied
grid with about a tenth of the TMDb calls.

There is a three-line patch for items 1 and 5 in the original, tested but not
applied: see [If you keep the original](#if-you-keep-the-original).

---

## Part 1. Problems in the original game

Ordered by how much they affect a player. "Reproduced" means I saw it happen in
the original page, served unchanged through the local dev server.

### 1. Four actors reject every answer (reproduced)

`submitGuess` checks the actor by comparing the pool's name with the names in
TMDb's cast list. For four people the two never match:

| In `ACTORS` | On TMDb |
|---|---|
| Zoe Saldana | Zoe Saldaña |
| Salma Hayek | Salma Hayek Pinault |
| Priyanka Chopra | Priyanka Chopra Jonas |
| Zoe Kravitz | Zoë Kravitz |

Submitting *Avatar* for Zoe Saldana × "Released in the 2000s" returns "Zoe
Saldana isn't credited as an actor in that film", while See All for the same
cell lists 21 valid answers. The same comparison breaks "Co-starred with" any
of the four: *The Terminal* is rejected for Tom Hanks × "Co-starred with Zoe
Saldana".

Replaying every Daily from #1 with the game's own dealer (using today's TMDb
data, so a past grid may have differed slightly on the day) puts one of these
actors, and so three unanswerable cells, in:

| Daily | Date | Actors |
|---|---|---|
| #16 | Oct 8 | **Zoe Kravitz**, Kenneth Branagh, Ralph Fiennes |
| #31 | Oct 23 | Winona Ryder, Gary Oldman, **Zoe Kravitz** |
| #40 | Nov 1 | **Salma Hayek**, Lorraine Bracco, Susan Sarandon |
| #44 | Nov 5 | Tim Robbins, **Zoe Kravitz**, Eric Roberts |
| #53 | Nov 14 | Melissa McCarthy, Robert De Niro, **Zoe Saldana** |
| #67 | Nov 28 | Hugh Jackman, **Zoe Saldana**, Emma Thompson |
| #69 | Nov 30 | **Zoe Kravitz**, Miles Teller, Emily Watson |

v2 looks every actor up by TMDb person id and checks the cast by id.

### 2. A typed title often resolves to a different film (measured)

When a player types a title and presses Enter without picking from the
dropdown, the game takes the first hit of TMDb's search. For 98 of the 1,894
films in the pool's filmographies with 2,000+ votes (5.2%), searching the
film's exact title returns a different film first. Some of them:

| Typed | Film checked instead |
|---|---|
| Deadpool | Deadpool & Wolverine (2024) |
| Toy Story | Toy Story 5 (2026) |
| Top Gun | Top Gun: Maverick (2022) |
| Home Alone | Home Alone 3 (1997) |
| Blade Runner | Blade Runner 2049 (2017) |
| Batman | The Batman (2022) |
| Spider-Man | Spider-Man: Brand New Day (2026) |
| X-Men | X-Men: Apocalypse (2016) |
| The Lion King, Aladdin, Mulan, Beauty and the Beast | the other version |

The player sees "isn't credited in that film" or "doesn't satisfy the
category" for a correct answer, with nothing to say which film was checked.
New sequels and remakes keep adding to this list.

v2 matches a typed title against the actor's own filmography first, and the
message always names the film and year it checked. Reproduce the count with
`python3 v2/research/check_title_search.py`.

### 3. See All crashes on a Genre cell after a reload (reproduced)

The genre name→id map is only loaded while dealing. After a page reload (the
Daily is restored from storage) or a share link, nothing has dealt, so See All
on a Genre column shows "Cannot read properties of null (reading 'Fantasy')".
Genre is the most common category, so this hits most returning Daily players
who reveal answers. Sandbox has the same crash if Genre is picked before any
deal. v2 keeps the (fixed) genre ids in the page.

### 4. Categories that can never match

| Entry | Why it never matches |
|---|---|
| Marvel Cinematic Universe | TMDb has no collection by that name. MCU films sit in "Iron Man Collection", "The Avengers Collection" and so on. |
| Fast & Furious | TMDb's collection is "The Fast and the Furious Collection". |
| Coen Brothers | Compared against each director's name; no person is called that. |
| Alejandro González Iñárritu | TMDb credits him as "Alejandro G. Iñárritu". |

Loose name matching also lets the wrong films in: "Rocky" accepts *The Rocky
Horror Picture Show* (Susan Sarandon is in the pool), "Mission: Impossible"
matches any collection with "mission" in its name, "Star Wars" matches LEGO and
Robot Chicken collections.

Separately, some franchises have too few pool actors to fill three rows:
The Matrix has none and John Wick has two (**Keanu Reeves isn't in the
pool**), and Rocky and Toy Story have two each.

"Ellen Page" is a fifth broken name: the first search hit is a different
person with no credits, so the actor is never dealt and shows 0 answers
everywhere in Sandbox. TMDb lists the actor as Elliot Page.

v2 defines each franchise as a list of TMDb collections (plus a keyword for the
MCU), and each director as one or more person ids.

### 5. A fifth of the "valid" answers aren't roles

Of the 17,464 actor-film credits the original accepts across the pool:

| What the credit is | Share |
|---|---|
| A role in a released film | 81.9% |
| Appearing as themself in a documentary, award show or TV special | 14.2% |
| Archive footage only | 3.2% |
| Appearing as themself in a music/TV special or stand-up film | 0.6% |
| Not released yet | 0.1% |

Examples that currently count: *GoldenEye: The Secret Files – The Cast* for
Judi Dench, *Night of 100 Stars III* for Morgan Freeman, *100 Greatest Sexy
Moments* for Jeff Goldblum, *Spider-Man: No Way Home* for Jake Gyllenhaal
(archive footage), and *The Hunger Games: Sunrise on the Reaping* for Jennifer
Lawrence three days before its release, with 1 vote, for 100 points.

Shorts are a further problem. A person's credits carry no runtime, so See All
and the solvability check count shorts, and Submit then rejects them as "too
short". In a sample, 26% of credits with 1–4 votes and 13% of those with 10–24
were under 45 minutes.

The README says TMDb's `video` flag "is not a useful signal", but the code
rejects on it and the in-app FAQ says it catches most junk. Worth making those
agree.

### 6. The category mix

The dealer shuffles every category of every type into one pool and keeps the
first three that all three actors can answer. Genre and Decade nearly always
pass. Director, Franchise and Co-star nearly never do for three random actors.
Across the 82 replayed Dailies (246 category slots):

| Type | Slots | Share |
|---|---|---|
| Genre | 104 | 42% |
| Decade | 76 | 31% |
| Title starts with | 25 | 10% |
| Title contains | 21 | 9% |
| Year range | 11 | 4% |
| Co-star | 7 | 3% |
| Director | 2 | 1% |
| Franchise | 0 | 0% |

"Title contains F, V, W or Y" has a single value that almost always passes, so
since it was added it's in 19 of the 30 Dailies from Nov 14 to Dec 13.

### 7. The "well-known" rule (5,000 votes)

Since Nov 12 every cell needs a film with 5,000+ raw votes. Your
[billing-research.md](../billing-research.md) already questions this rule. Two
effects it doesn't mention:

- Five pool actors have no film at 5,000 votes and so can never be dealt:
  Constance Wu, Gaten Matarazzo, Regina King, Sofía Vergara (and Ellen Page).
  Twenty-one have fewer than three. Each time one is sampled, the dealer burns
  an attempt testing up to 60 categories.
- Kathleen Turner's only "well-known" film is *Who Framed Roger Rabbit*, an
  uncredited voice part. *Romancing the Stone*, *Body Heat* and *The War of
  the Roses* don't count.

### 8. Director and Franchise checks miss famous films

Those checks only look at an actor's 50 most *popular* films, and TMDb's
popularity is a what's-trending-today number. 24 of 2,248 actor-film pairs with
5,000+ votes fall outside the window, concentrated exactly where it matters:
*X-Men*, *X2* and *First Class* for Hugh Jackman, *Fast & Furious 6* for Dwayne
Johnson, *The Lost World* for Jeff Goldblum. Meanwhile 13% of window slots are
held by films with under 50 votes, mostly new and upcoming releases.

### 9. Cost of a deal

Over the 82 replayed Dailies the original made a median of **120 TMDb calls per
deal, up to 795**. v2 makes a median of 13, up to 33 (40 deals, each from a
cold start).

### 10. Smaller things

- **Phones.** A grid cell is about 70px wide at 375px, so the answer box shows
  eight characters and suggestions wrap one word per line. The 14px input font
  also makes iOS Safari zoom the page on every tap. (Seen in an emulated
  phone viewport, not on a real device.)
- **Suggestion list.** Replies aren't sequenced, so a slow reply can overwrite a
  newer one, and one arriving after Enter reopens the list over the result.
  There is no keyboard navigation.
- **No whole-grid check.** A film can be used once per grid, but cells are only
  checked one at a time. Nothing guarantees nine *different* answers exist.
- **Sandbox** lets a row actor also be the co-star category; the resulting
  share link is then rejected as broken.
- **A tab left open past midnight** keeps playing yesterday's Daily with no
  notice.
- **Peeking.** Sandbox, or a share link to today's grid with the date removed,
  shows See All for the Daily's exact cells without locking the Daily. This is
  unavoidable without a server, and v2 doesn't change it.

### One thing that turned out fine

The README's "one catch" is that two players' Dailies could differ if TMDb
answers a check differently. I replayed all 82 Dailies on Nov 13 and again on
Nov 15 with fresh TMDb data: **all 82 came out identical**. The risk is real in
principle but small in practice.

---

## Part 2. The scoring

### What the original score measures

`50 + rarity`, where rarity runs 1–50 on a log curve of the film's raw TMDb
vote count (about 4 votes → 50, about 20,000 → 1). Five problems:

1. **The top of the scale is junk.** Points rise all the way down to 4 votes,
   where the entries are making-ofs, TV specials and shorts. 30% of all valid
   credits score 91–100.
2. **It's biased by release year.** TMDb's voters are recent-film heavy. The
   50th most-voted film of 1990 has 691 votes; the 50th of 2015 has 5,261. So
   films equally famous for their year score very differently:

   | Films ranked 30th–60th in their year | 1970s | 1980s | 1990s | 2000s | 2010s | 2020s |
   |---|---|---|---|---|---|---|
   | Original, median points | 76 | 71 | 66 | 61 | 58 | 63 |
   | v2, median points | 72 | 70 | 68 | 66 | 65 | 68 |

   The 2020s row shows the second half of the bias: recent films haven't
   collected their votes yet.
3. **It ignores the actor.** Samuel L. Jackson in *GoodFellas* (billed 51st)
   and Ray Liotta in *GoodFellas* score the same. So do Emma Thompson's two
   minutes in *I Am Legend* and Will Smith's lead.
4. **Realistic answers are squeezed into a quarter of the range.** The curve
   gives 13.6 points per tenfold change in votes. Films people actually name
   (500 to 30,000 votes) span about 51–73.
5. **See All and Submit can disagree**, because one reads votes from the
   actor's credit list and the other from the film's own page, and they apply
   different junk rules.

### What v2 measures instead

One number per actor + film, **link strength**: how readily people connect
this actor with this film.

```
link strength = film's votes, adjusted for its release year
                × billing weight   (× 0.6 if it's a voice role)

points = 50 + deep-cut bonus (0–50)
         bonus = 0 at link ≥ 20,000, 50 at link ≤ 150, log scale between
```

This is "votes × billing weight", candidate 1 in billing-research.md, with the
year question from the same file folded in.

**Year adjustment.** Each film is ranked among its own year's releases, using a
table of vote counts at fixed ranks (1st, 3rd, 5th … 1000th) for every year
from 1915. It is then given the votes a film of that rank has in 2010–2017,
when TMDb voting peaked. A setting, `eraCorrection`, blends that with the raw
count: 0 keeps raw votes, 1 treats the 40th film of 1995 exactly like the 40th
of 2015. It is set to **0.75**. That is a judgment call, made like this:

- TMDb's own popularity numbers say its audience pays less attention to older
  films, but not nearly as much less as the vote counts say: at equal rank, a
  1990 film has 1.7× less current popularity than a 2015 film, against 7.6×
  fewer votes. Worked through, that puts TMDb's own audience at roughly
  0.2–0.3.
- Reading equal-rank films side by side says more than that for people who
  grew up with 80s and 90s films. The 1990 films around rank 50 are *Presumed
  Innocent*, *Hard to Kill*, *Air America*. The 2015 films with the same raw
  votes are *Ricki and the Flash*, *Miss You Already*, *A Little Chaos*. The
  2015 films at the same rank are *Southpaw*, *Crimson Peak*, *Joy*. The 1990
  films read closer to the second group than the first.

**Billing weight.** Billed 1st or 2nd counts in full, 5th about 0.6, 10th
about 0.3, 20th about 0.12, 50th about 0.04. As billing-research.md found,
position as a percentage of the cast list doesn't work, so this uses the
absolute position on a smooth curve rather than a cutoff. Voice roles count a
further 0.6: Emma Thompson is 2nd-billed in *Brave*, and few people would name
it for her.

**Which credits count.** A role in a released feature. Documentary and special
appearances as themself, archive footage, unreleased films and shorts are out.
Narrating a documentary counts (Morgan Freeman, *March of the Penguins*), and
so does playing yourself in a fiction film (Margot Robbie, *The Big Short*).
Shorts are found with one extra call per actor and confirmed against the
film's page, because TMDb's runtime filter returns some features too (*The
Simpsons Movie* comes back as "under 45 minutes").

### Old points and new points

| Actor | Film | Votes | Rank in year | Billed | Original | v2 |
|---|---|---|---|---|---|---|
| Tom Hanks | Forrest Gump (1994) | 30,896 | 3 | 1st | 51 | 50 |
| | Big (1988) | 4,254 | 11 | 1st | 60 | 56 |
| | The 'Burbs (1989) | 1,455 | 30 | 1st | 66 | 64 |
| | Nothing in Common (1986) | 144 | 142 | 1st | 80 | 83 |
| | The Simpsons Movie (2007) | 8,830 | 13 | 19th, voice | 56 | 81 |
| | Ithaca (2015) | 111 | 778 | 6th | 82 | 100 |
| Samuel L. Jackson | Pulp Fiction (1994) | 31,337 | 2 | 2nd | 51 | 50 |
| | Jurassic Park (1993) | 18,614 | 1 | 10th | 51 | 59 |
| | GoodFellas (1990) | 15,035 | 1 | 51st | 53 | 81 |
| | Iron Man (2008) | 29,190 | 2 | 64th | 51 | 83 |
| Emma Thompson | Love Actually (2003) | 7,683 | 13 | 3rd | 57 | 57 |
| | I Am Legend (2007) | 17,565 | 3 | 7th | 52 | 58 |
| | Sense and Sensibility (1995) | 1,939 | 38 | 1st | 65 | 65 |
| | Harry Potter: Deathly Hallows 2 (2011) | 22,743 | 3 | 67th | 51 | 86 |
| Brad Pitt | Thelma & Louise (1991) | 4,081 | 7 | 7th | 60 | 64 |
| | Deadpool 2 (2018) | 19,930 | 3 | 21st | 51 | 71 |
| | Being John Malkovich (1999) | 5,048 | 17 | 62nd | 59 | 94 |

For mid-range lead roles the two scores land close together. The differences
are at the ends: the junk is gone from the top, small parts in big films now
earn a bonus, and the bonus stops growing at "almost nobody has seen it"
instead of at "four votes". Well-known pairings score 50–69 (median 62) and
deep cuts 70–100. Reproduce with `python3 v2/research/compare_scoring.py`, or
browse any actor in the Scoring lab.

### The same number runs the dealer

A film counts as **well known for an actor** at link strength 3,000 or more.
That replaces the 5,000-vote rule, and it does what billing-research.md asked
for: Emma Thompson gets *Sense and Sensibility*, *The Remains of the Day* and
*Saving Mr. Banks* back, and Kathleen Turner goes from one well-known film to
eight. The median actor goes from 9 well-known films to 13. As a check, 97% of
the films TMDb lists as an actor's `known_for` clear the threshold.

### The open questions in TODO.md and billing-research.md

- **Votes, popularity, or a blend (TODO.md item 1)?** Not popularity. It
  measures what's trending today, and 13% of an actor's 50 most "popular"
  films have under 50 votes. v2 doesn't use it anywhere. Year-adjusted votes
  give the stability of votes without the era bias.
- **Does the 5,000 cutoff need to scale with year?** Yes, and rank within the
  year works, as you guessed. v2 uses it for scoring and for the dealer.
- **Run the billing table for more actors.** Done pool-wide. The lab shows it
  for any actor.
- **Percent position or fixed count?** Neither: absolute position on a smooth
  curve.

### What the model still gets wrong

- **Billing isn't screen time.** *I Am Legend* still counts as well known for
  Emma Thompson (billed 7th, link 9,100). Nothing in TMDb's data can tell a
  two-minute part billed 7th from a real supporting role billed 7th.
- **TMDb's billing order is entered by volunteers** and is sometimes
  alphabetical or arbitrary. It lists Marion Cotillard 1st in *Contagion*.
- **Franchise roles.** Once you know Emma Thompson is Trelawney, every Harry
  Potter film she's in is an equally easy guess, but *Deathly Hallows 2*
  (billed 67th) scores 86 and *Azkaban* (billed 11th) scores 60.
- **Three numbers are judgment calls:** the era correction (0.75), the voice
  weight (0.6) and the shape of the billing curve. All three have sliders in
  the lab.
- **The year table is a snapshot.** A film released this month keeps gaining
  votes, so it will look more famous than it is until the table is rebuilt.
  That errs in a harmless direction (new releases are fresh in memory), but
  the table wants rebuilding every month or two.
- **It's still a proxy.** The real measure of a deep cut is how few *players*
  pick it, as the sports grids do. That needs a server collecting answers.

---

## Part 3. What else v2 changes

**Dealing.** The dealer now decides the shape of the grid first: usually one
"connection" column (director, franchise or co-star), sometimes none or two,
and the rest from genre, time and title, never two from the same family. It
starts from one actor drawn evenly from the pool, picks a connection that
includes them, and draws the other two actors from that connection's list.
Over 400 simulated deals:

| | Original (82 Dailies) | v2 (400 deals) |
|---|---|---|
| Genre | 42% | 22% |
| Decade / year range | 35% | 22% |
| Title starts with / contains | 19% | 24% |
| Co-star | 3% | 15% |
| Director | 1% | 10% |
| Franchise | 0% | 7% |
| Deals that succeeded | 82 of 82 | 400 of 400 |
| Different actors seen | | all 216 dealable |

**Whole-grid check.** A grid is only dealt if nine *different* well-known
films can fill it. About one planned grid in five failed this. The case that
prompted it: "Directed by Christopher Nolan" next to "Co-starred with Elliot
Page", where *Inception* is the well-known answer to most of both columns and
whoever uses it first leaves the other cells to deep cuts.

**Dealable actors.** 216 of the 236 actors have four or more well-known films
and can anchor a row. The other 20 stay available in Sandbox and as co-stars:
Amy Poehler, Aziz Ansari, Constance Wu, David Oyelowo, Eric Roberts, Evan
Peters, Finn Wolfhard, Gaten Matarazzo, Janelle Monáe, Kumail Nanjiani,
Letitia Wright, Lorraine Bracco, Mindy Kaling, Noah Schnapp, Priyanka Chopra,
Rinko Kikuchi, Sandra Oh, Sofía Vergara, Sophie Turner, Terrence Howard.

**The Daily.** v2 has its own seed and its own save slot, so it's a different
grid from the original's and never touches your progress there. The next 60
(Nov 16 to Jan 14) are dealt ahead and stored in the page, so every player
gets the same grid whatever TMDb says that day. After that it falls back to
live dealing. Dealing the same 60 dates twice gave the same 60 grids. For 60 later dates that would be dealt live, raising every
vote count by 0.1% (about a week of drift for a well-known older film) changed
none of the grids, 1% changed one, and 5% changed seven.

**Also:** a Scoring lab, a guess counter (shown and shared, never scored), a
points breakdown that explains the film, the role and the link strength, a
Billed column in See All, a wider typing box and a full-width message bar on
phones, arrow keys in the suggestion list, a notice when a new Daily is out,
and a retry when TMDb rate-limits.

## How this was checked

- The page's scoring and the Python model give identical points for all 948
  films of five test actors (`research/crosscheck.py`).
- Played through in the page: typed and picked answers, wrong answers, See
  All, the breakdown, the lab, Sandbox, share links (including links in the
  original's spelling), a phone-sized viewport.
- The four broken actors, the dead categories and the Genre crash were each
  reproduced in the original and confirmed fixed in v2.

**Not checked:**

- **v2 with a pasted key.** I ran it through the local proxy, which adds the
  key server-side, and confirmed the key box appears when there's no proxy. I
  did not paste your key into the page, so the direct browser-to-TMDb path in
  v2 is untested. It uses the same request code as the original plus three
  endpoints the original doesn't call (`/discover/movie`, `/collection`,
  `/person/{id}`).
- A real phone. The phone layout was checked in an emulated viewport only.
- Opening `index.html` straight from disk (`file://`).

## If you keep the original

[`patches/v1-hotfix.patch`](patches/v1-hotfix.patch) fixes the four actors and
the Genre crash in three small changes, without changing what gets dealt, so
Dailies, saved games and share links are unaffected. I tested it at
`/v1-hotfix/` on the dev server: all four actors and the co-star case are
accepted, and See All works on Genre after a reload. The original now lives at
`v1/index.html`, so to apply it there:

```bash
git apply --directory=v1 v2/patches/v1-hotfix.patch
```

It does not fix the wrong-film lookups, the dead categories or anything in
Part 2.

## Decisions that are yours

1. **Apply the hotfix to the original?** Since v2 became the live game, this
   only matters to anyone still using `/v1/` (its Dailies on Nov 28 and Nov 30
   are the two affected).
2. **Franchise boundaries.** I made X-Men include the Wolverine and Deadpool
   films, Rocky include Creed, Star Wars include Rogue One, Solo and The Clone
   Wars, and John Wick include Ballerina. The Lord of the Rings does not
   include The Hobbit. These are in `FRANCHISES` in `research/build_data.py`.
3. **The pool.** Keanu Reeves would bring The Matrix and John Wick to life.
   Twenty actors can't currently carry a row.
4. **The three judgment-call settings**, after trying a few actors in the lab.
5. **"Title contains F, V, W or Y"** is still the most common single category
   in v2 (about 1 grid in 4), because it has only one value. More letter sets,
   or a lower weight in `DEAL.familyTypes`, would thin it out.
