#!/usr/bin/env python3
"""Parse the Centre Circle Finder club dataset into Python.

`centre-circle-finder/data/teams.js` is the single source of truth for the
map app and, through this module, for the static ground pages too. It stays
a .js file because the app loads it directly with a <script> tag — so this
reads the `T(...)` constructor calls rather than importing JSON.

Nothing here is written by hand: change teams.js for a new season and every
generated page follows.
"""
import math, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "centre-circle-finder", "data", "teams.js")

# ── parsing ──────────────────────────────────────────────────────────────
def _args(s):
    """Split one T(...) argument list on top-level commas.

    Naive splitting breaks on the many stadium names that contain a comma or
    brackets — "Vitality Stadium (Dean Court)", "Belfast (East)" — so track
    quoting and depth."""
    out, buf, depth, quote = [], "", 0, None
    for ch in s:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote, buf = ch, buf + ch
        elif ch in "([":
            depth, buf = depth + 1, buf + ch
        elif ch in ")]":
            depth, buf = depth - 1, buf + ch
        elif ch == "," and depth == 0:
            out.append(buf.strip())
            buf = ""
        else:
            buf += ch
    if buf.strip():
        out.append(buf.strip())
    return out


def _val(tok):
    tok = tok.strip()
    if tok in ("null", "undefined", ""):
        return None
    if tok[0] in "\"'":
        return tok[1:-1]
    return float(tok) if "." in tok else int(tok)


def _load():
    src = open(SRC, encoding="utf-8").read()

    leagues = {}
    for m in re.finditer(r'(\w+):\s*\{([^}]*)\}', src):
        body = m.group(2)
        if "tier:" not in body:
            continue
        f = {}
        for km in re.finditer(r'(\w+):\s*("(?:[^"\\]|\\.)*"|[\w.-]+)', body):
            f[km.group(1)] = _val(km.group(2))
        leagues[m.group(1)] = f

    teams = []
    # The leading quote is what distinguishes a call — T("PL", ...) — from the
    # `function T(league, name, ...)` definition a few lines above them.
    for m in re.finditer(r'\bT\(\s*("[^;]*?)\)\s*,?\s*(?=\n)', src):
        a = [_val(x) for x in _args(m.group(1))]
        if len(a) < 7:
            continue
        teams.append({
            "league": a[0], "name": a[1], "stadium": a[2], "town": a[3],
            "capacity": a[4], "lat": a[5], "lng": a[6],
            "exact": len(a) > 7 and a[7] == 1,
        })

    season = (re.search(r'season:\s*"([^"]+)"', src) or [None, ""])[1]
    return season, leagues, teams


# ── helpers ──────────────────────────────────────────────────────────────
def slug(s):
    s = s.lower().replace("&", " and ").replace("'", "")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def base_town(t):
    """"London (Holloway)" -> "London". The bracket is a district, not a
    different place, so it groups under the city."""
    return re.sub(r"\s*\(.*\)\s*$", "", t).strip()


def haversine(a, b):
    """Great-circle distance in miles between two club records."""
    R = 3958.8
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dp = p2 - p1
    dl = math.radians(b["lng"] - a["lng"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


# ── build the model ──────────────────────────────────────────────────────
SEASON, LEAGUES, CLUBS = _load()

for c in CLUBS:
    lg = LEAGUES[c["league"]]
    c["slug"] = slug(c["name"])
    c["url"] = f"/centre-circle-finder/club/{c['slug']}/"
    c["city"] = base_town(c["town"])
    c["country"] = lg["country"]
    c["league_name"] = lg["name"]
    c["tier"] = lg["tier"]
    c["status"] = lg["status"]

CLUBS.sort(key=lambda c: c["name"])

# Nearest other grounds, precomputed. This is the section that makes each club
# page genuinely different from every other one — and it is the away-day
# question the app gets used for.
for c in CLUBS:
    near = sorted(((haversine(c, o), o) for o in CLUBS if o is not c),
                  key=lambda p: p[0])[:6]
    c["near"] = [(round(d, 1), o) for d, o in near]

def _clusters(clubs, miles=10):
    """Split clubs sharing a town name into actual places.

    Different towns share a name: Ashford in Surrey and Ashford in Kent are
    62 miles apart, the two Bangors 117. Grouping on the name alone would put
    them on one page and state something false. Single-linkage keeps a big
    city whole — London's 42 grounds chain together through near neighbours
    even though its extremes are 29 miles apart — while breaking apart names
    that genuinely belong to two places."""
    groups = [[c] for c in clubs]
    merged = True
    while merged:
        merged = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                if any(haversine(a, b) <= miles for a in groups[i] for b in groups[j]):
                    groups[i] += groups[j]
                    del groups[j]
                    merged = True
                    break
            if merged:
                break
    return groups


# Towns are only worth a page where there is more than one club. With a single
# club the page could say nothing the club's own page does not already say —
# that is the textbook definition of a doorway page, and Google treats a mass
# of them as a sitewide quality problem rather than 400 harmless pages.
_by_city = {}
for c in CLUBS:
    _by_city.setdefault(c["city"], []).append(c)

CITIES = []
for name, cl in sorted(_by_city.items()):
    groups = _clusters(cl)
    for g in groups:
        if len(g) < 2:
            continue
        countries = sorted({c["country"] for c in g})
        # Only a name that splits into two real places needs qualifying. Cardiff
        # spans two countries' league systems but is one city, so it stays plain.
        label = name
        if len(groups) > 1 and len(countries) == 1:
            label = f"{name}, {countries[0]}"
        CITIES.append({
            "name": name, "label": label, "slug": slug(label),
            "url": f"/centre-circle-finder/city/{slug(label)}/",
            "clubs": sorted(g, key=lambda c: (c["tier"], c["name"])),
            "countries": countries,
            "country": countries[0] if len(countries) == 1 else None,
        })
CITIES.sort(key=lambda c: c["label"])

LEAGUE_PAGES = []
for key, lg in LEAGUES.items():
    cl = [c for c in CLUBS if c["league"] == key]
    if not cl:
        continue
    LEAGUE_PAGES.append({
        "key": key, "name": lg["name"], "slug": slug(lg["name"]),
        "url": f"/centre-circle-finder/league/{slug(lg['name'])}/",
        "country": lg["country"], "tier": lg["tier"], "status": lg["status"],
        "clubs": sorted(cl, key=lambda c: c["name"]),
    })
LEAGUE_PAGES.sort(key=lambda l: (l["country"], l["tier"], l["name"]))

CITY_OF = {c["slug"]: c for c in CITIES}
LEAGUE_OF = {l["key"]: l for l in LEAGUE_PAGES}


if __name__ == "__main__":
    print(f"season {SEASON}: {len(CLUBS)} clubs, {len(LEAGUE_PAGES)} leagues, "
          f"{len(CITIES)} multi-club cities")
    dup = len(CLUBS) - len({c['slug'] for c in CLUBS})
    print(f"slug collisions: clubs {dup}, cities "
          f"{len(CITIES) - len({c['slug'] for c in CITIES})}, leagues "
          f"{len(LEAGUE_PAGES) - len({l['slug'] for l in LEAGUE_PAGES})}")
    print(f"exact coords: {sum(1 for c in CLUBS if c['exact'])}/{len(CLUBS)}")
    print(f"capacity known: {sum(1 for c in CLUBS if c['capacity'])}/{len(CLUBS)}")
    mixed = [c for c in CITIES if c["country"] is None]
    print(f"cities spanning >1 country: {[(c['name'], c['countries']) for c in mixed]}")
