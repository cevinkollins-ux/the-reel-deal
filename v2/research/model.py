"""The v2 scoring model in Python, for research and for build_data.py.

This mirrors the JavaScript in v2/index.html (search for "Link strength").
The page is the source of truth for play; this copy exists so the model can be
run over the whole actor pool offline. If you change a constant in one place,
change it in the other.
"""
import math
import re
import unicodedata

RANKS = [1, 3, 5, 10, 20, 30, 50, 100, 200, 500, 1000]
REF_YEARS = range(2010, 2018)   # the years TMDB's vote counts peak; the "reference era"
ERA_CORRECTION = 0.75           # 0 = raw votes (v1), 1 = same rank in any year counts the same
KNOWN_LINK = 3000               # link strength at which an actor-film pair counts as well known
BONUS_ZERO_AT = 20000           # link strength that earns no deep-cut bonus
BONUS_FULL_AT = 150             # link strength that earns the full bonus
BONUS_MAX = 50

NON_FEATURE = re.compile(
    r"\b(behind[\s-]the[\s-]scenes|making[\s-]of|gag reel|bloopers|deleted scenes|"
    r"bonus (features?|footage|clip)|featurette|extended (trailer|preview)|"
    r"red[\s-]band trailer|teaser trailer|first look|table read)\b", re.I)
SELF_RE = re.compile(r"\b(self|himself|herself|themself|themselves)\b", re.I)
ARCHIVE_RE = re.compile(r"\barchive\b", re.I)
GENRE_DOCUMENTARY, GENRE_MUSIC, GENRE_TV_MOVIE = 99, 10402, 10770


def clean_row(row):
    """Repair glitches (a 0 between real values) and force a non-increasing row."""
    row = list(row)
    for i, v in enumerate(row):
        if v <= 0:
            prev = row[i - 1] if i else 1
            nxt = next((x for x in row[i + 1:] if x > 0), max(1, prev // 4))
            row[i] = max(1, int(round(math.sqrt(max(prev, 1) * max(nxt, 1)))))
    for i in range(1, len(row)):
        row[i] = min(row[i], row[i - 1])
    return [max(1, v) for v in row]


class YearTable:
    def __init__(self, years):
        """years: {year: [votes at each of RANKS]}"""
        self.years = {int(y): clean_row(r) for y, r in years.items()}
        self.first, self.last = min(self.years), max(self.years)
        self.ref = [math.exp(sum(math.log(self.years[y][i]) for y in REF_YEARS) / len(REF_YEARS))
                    for i in range(len(RANKS))]

    def rank(self, votes, year):
        row = self.years[min(max(year, self.first), self.last)]
        v = max(votes, 1)
        if v >= row[0]:
            return 1.0
        for i in range(1, len(row)):
            if v >= row[i]:
                hi, lo = row[i - 1], row[i]
                if hi == lo:
                    return float(RANKS[i - 1])
                t = (math.log(hi) - math.log(v)) / (math.log(hi) - math.log(lo))
                return math.exp(math.log(RANKS[i - 1]) + t * (math.log(RANKS[i]) - math.log(RANKS[i - 1])))
        return RANKS[-1] * (row[-1] / v)

    def ref_votes(self, rank):
        row = self.ref
        if rank <= 1:
            return row[0]
        for i in range(1, len(RANKS)):
            if rank <= RANKS[i]:
                t = (math.log(rank) - math.log(RANKS[i - 1])) / (math.log(RANKS[i]) - math.log(RANKS[i - 1]))
                return math.exp(math.log(row[i - 1]) + t * (math.log(row[i]) - math.log(row[i - 1])))
        return row[-1] * RANKS[-1] / rank

    def adjusted_votes(self, votes, year, alpha=ERA_CORRECTION):
        v = max(votes, 1)
        if year is None:
            return float(v)
        full = self.ref_votes(self.rank(v, year))
        return math.exp((1 - alpha) * math.log(v) + alpha * math.log(max(full, 1)))


def year_of(credit):
    try:
        return int((credit.get("release_date") or "")[:4])
    except ValueError:
        return None


def billing_weight(order):
    if order is None:
        return 0.3
    if order <= 1:
        return 1.0
    return 1.0 / (1.0 + ((order - 1) / 4.0) ** 1.3)


def link_strength(table, credit, alpha=ERA_CORRECTION):
    return table.adjusted_votes(credit.get("vote_count") or 0, year_of(credit), alpha) * billing_weight(credit.get("order"))


def deep_cut_bonus(link):
    span = math.log10(BONUS_ZERO_AT) - math.log10(BONUS_FULL_AT)
    t = (math.log10(BONUS_ZERO_AT) - math.log10(max(link, 1))) / span
    return int(round(BONUS_MAX * max(0.0, min(1.0, t))))


def rarity_v1(votes):
    lg = math.log10(max(votes, 0) + 1)
    return max(1, min(50, int(round(50 - ((lg - 0.7) / (4.3 - 0.7)) * 49))))


def fold(text):
    return "".join(c for c in unicodedata.normalize("NFD", text or "") if not unicodedata.combining(c)).lower()


def real_v1(m):
    """v1's isRealFeatureCredit(), minus the runtime check (credits carry no runtime)."""
    title = m.get("title") or ""
    return bool((m.get("vote_count") or 0) >= 1 and title and not m.get("video")
                and "|" not in title and not NON_FEATURE.search(title))


def ineligible_reason(actor_name, m, today):
    """None if the credit counts as an answer in v2, else a short reason."""
    if not real_v1(m):
        return "junk"
    date = m.get("release_date") or ""
    if not date or date > today:
        return "unreleased"
    character = m.get("character") or ""
    genres = m.get("genre_ids") or []
    if ARCHIVE_RE.search(character):
        return "archive"
    is_self = bool(SELF_RE.search(character))
    if GENRE_DOCUMENTARY in genres and (is_self or not character.strip()):
        return "documentary"
    if is_self and (GENRE_MUSIC in genres or GENRE_TV_MOVIE in genres):
        return "self"
    if is_self and fold(actor_name) in fold(m.get("title")):
        return "self"
    return None


def eligible_credits(actor_name, cast, today):
    """Eligible credits, one per film (the best-billed one if a film is listed twice)."""
    best = {}
    for m in cast:
        if ineligible_reason(actor_name, m, today):
            continue
        if m["id"] not in best or (m.get("order") or 0) < (best[m["id"]].get("order") or 0):
            best[m["id"]] = m
    return list(best.values())
