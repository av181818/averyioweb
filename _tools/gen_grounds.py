#!/usr/bin/env python3
"""Generate the static ground pages for Centre Circle Finder.

    python3 _tools/gen_grounds.py

Three page types plus an index, all derived from teams.js via grounds.py:

    /centre-circle-finder/grounds/                 the hub — every club A–Z
    /centre-circle-finder/club/<club>/             one per club (597)
    /centre-circle-finder/city/<city>/             towns with 2+ clubs (59)
    /centre-circle-finder/league/<league>/         one per league (31)

The map app itself stays at /centre-circle-finder/ and is not touched here
beyond the link into the hub.
"""
import html, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# reuse gen.py's helpers + app data without triggering its write block
_src = open(os.path.join(os.path.dirname(__file__), "gen.py"), encoding="utf-8").read()
exec(_src.split("# ── write app pages")[0], globals())
from grounds import CLUBS, CITIES, LEAGUE_PAGES, SEASON

APP = "/centre-circle-finder/"
HUB = "/centre-circle-finder/grounds/"
e = lambda s: html.escape(str(s), quote=True)

# A city page exists only for towns with 2+ clubs, so a club in a one-club town
# has nothing to link to. Map club -> its city page, where there is one.
CITY_FOR = {}
for city in CITIES:
    for c in city["clubs"]:
        CITY_FOR[c["slug"]] = city
LEAGUE_FOR = {l["key"]: l for l in LEAGUE_PAGES}


def W(rel, s):
    p = os.path.join(ROOT, rel.strip("/"), "index.html")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)


def fit(parts, limit):
    """Assemble a description from clauses, keeping only what fits.

    Truncating a sentence with an ellipsis reads like a broken page in a search
    result, so clauses are dropped whole instead. Measured after escaping, since
    an ampersand costs five characters in the attribute — the two clubs with a
    "&" in the name were the ones that overran."""
    out = ""
    for p in parts:
        cand = (out + " " + p).strip()
        if len(e(cand)) <= limit:
            out = cand
    return out


def title_of(*options):
    """First title that fits Google's ~60-char display width."""
    for t in options:
        if len(t) <= 60:
            return t
    return options[-1][:57].rstrip(" ,—-") + "…"


def crumbs(trail):
    """Breadcrumb markup + the matching JSON-LD, from one definition."""
    items = [{"@type": "ListItem", "position": i + 1, "name": name,
              "item": SITE + href}
             for i, (name, href) in enumerate(trail)]
    nav_trail = [(name, href if i < len(trail) - 1 else None)
                 for i, (name, href) in enumerate(trail)]
    return crumb(nav_trail), {"@context": "https://schema.org",
                              "@type": "BreadcrumbList", "itemListElement": items}


def tier_label(c):
    return f"Tier {c['tier']} · {c['country']}"


def club_line(c, dist=None):
    """One club in a list, used on every page type."""
    meta = f"{e(c['stadium'])} · {e(c['town'])}"
    d = f'<span class="gp-dist">{dist} mi</span>' if dist is not None else ""
    return (f'      <a class="gp-item" href="{c["url"]}">\n'
            f'        <span class="gp-item-name">{e(c["name"])}{d}</span>\n'
            f'        <span class="gp-item-meta">{meta}</span>\n'
            f'        <span class="gp-item-league">{e(c["league_name"])}</span>\n'
            f'      </a>\n')


# ── club pages ───────────────────────────────────────────────────────────
def club_page(c):
    lg = LEAGUE_FOR[c["league"]]
    city = CITY_FOR.get(c["slug"])
    url = SITE + c["url"]
    cap = f"{c['capacity']:,}" if c["capacity"] else "Not recorded"

    title = title_of(f"{c['name']} — {c['stadium']}",
                     f"{c['name']} — {c['stadium'].split(' (')[0]}",
                     f"{c['name']} football ground")
    desc = fit([f"{c['stadium']} is the home of {c['name']}, {c['league_name']}.",
                f"Located in {c['town']},",
                f"capacity {cap}," if c["capacity"] else "",
                "with a map and the nearest other grounds."], 160)

    facts = [("League", f'<a href="{lg["url"]}">{e(lg["name"])}</a>'),
             ("Level", e(tier_label(c))),
             ("Ground", e(c["stadium"])),
             ("Town", (f'<a href="{city["url"]}">{e(c["town"])}</a>'
                       if city else e(c["town"]))),
             ("Capacity", e(cap)),
             ("Season", e(SEASON))]
    facts_html = "".join(
        f'      <div class="gp-fact"><span class="gp-fact-k">{k}</span>'
        f'<span class="gp-fact-v">{v}</span></div>\n' for k, v in facts)

    near = "".join(club_line(o, d) for d, o in c["near"])
    same_city = ""
    if city:
        others = [o for o in city["clubs"] if o is not c]
        same_city = (
            f'    <h2>Other clubs in {e(city["name"])}</h2>\n'
            f'    <div class="gp-list">\n{"".join(club_line(o) for o in others)}    </div>\n')

    # Coordinates are only published as structured data when they were verified
    # against OpenStreetMap. Emitting a town-centre guess as a precise geo would
    # be telling Google something we do not actually know.
    place = {"@context": "https://schema.org", "@type": "StadiumOrArena",
             "name": c["stadium"], "url": url,
             "address": {"@type": "PostalAddress", "addressLocality": c["town"],
                         "addressCountry": c["country"]},
             "containedInPlace": {"@type": "City", "name": c["city"]}}
    if c["exact"]:
        place["geo"] = {"@type": "GeoCoordinates",
                        "latitude": c["lat"], "longitude": c["lng"]}
    if c["capacity"]:
        place["maximumAttendeeCapacity"] = c["capacity"]

    bc_html, bc_ld = crumbs([("Home", "/"), ("Centre Circle Finder", APP),
                             ("Grounds", HUB), (c["name"], c["url"])])

    approx = "" if c["exact"] else (
        '    <p class="gp-note">The pin for this ground is a town-level '
        'approximation, not a verified stadium position — check the address '
        'before travelling.</p>\n')

    return (head(e(title), e(desc), url)
            + nav() + bc_html
            + '  <section class="wrap gp-hero">\n'
            + f'    <h1>{e(c["name"])}<span class="gp-ground">{e(c["stadium"])}</span></h1>\n'
            + f'    <p class="gp-sub">{e(c["league_name"])} · {e(c["town"])}</p>\n'
            + f'    <div class="gp-facts">\n{facts_html}    </div>\n'
            + approx
            + f'    <a class="gp-cta" href="{APP}?club={c["slug"]}">Open on the map</a>\n'
            + '  </section>\n'
            + '  <section class="wrap gp-sec">\n'
            + '    <h2>Nearest grounds</h2>\n'
            + f'    <div class="gp-list">\n{near}    </div>\n'
            + same_city
            + f'    <p class="gp-more"><a href="{lg["url"]}">All {e(lg["name"])} grounds</a>'
            + f' · <a href="{HUB}">Every UK ground</a></p>\n'
            + '  </section>\n'
            + ld(place) + ld(bc_ld) + footer(APPS))


# ── city pages ───────────────────────────────────────────────────────────
def city_page(city):
    url = SITE + city["url"]
    n = len(city["clubs"])
    leagues = sorted({c["league_name"] for c in city["clubs"]})
    title = title_of(f"Football grounds in {city['label']}",
                     f"{city['label']} football grounds")
    desc = fit([f"All {n} senior football grounds in {city['label']},",
                f"across {len(leagues)} leagues." if len(leagues) > 1
                else f"in the {leagues[0]}.",
                "Clubs, stadiums, capacities and a map of every ground."], 160)

    items = "".join(club_line(c) for c in city["clubs"])
    ld_list = {"@context": "https://schema.org", "@type": "ItemList",
               "name": f"Football grounds in {city['label']}",
               "numberOfItems": n,
               "itemListElement": [
                   {"@type": "ListItem", "position": i + 1, "name": c["stadium"],
                    "url": SITE + c["url"]}
                   for i, c in enumerate(city["clubs"])]}
    bc_html, bc_ld = crumbs([("Home", "/"), ("Centre Circle Finder", APP),
                             ("Grounds", HUB), (city["label"], city["url"])])

    return (head(e(title), e(desc), url)
            + nav() + bc_html
            + '  <section class="wrap gp-hero">\n'
            + f'    <h1>Football grounds in {e(city["label"])}</h1>\n'
            + f'    <p class="gp-sub">{n} clubs across {len(leagues)} '
            + f'{"leagues" if len(leagues) > 1 else "league"} · {e(SEASON)}</p>\n'
            + f'    <a class="gp-cta" href="{APP}">Open the map</a>\n'
            + '  </section>\n'
            + '  <section class="wrap gp-sec">\n'
            + f'    <div class="gp-list">\n{items}    </div>\n'
            + f'    <p class="gp-more"><a href="{HUB}">Every UK ground</a></p>\n'
            + '  </section>\n'
            + ld(ld_list) + ld(bc_ld) + footer(APPS))


# ── league pages ─────────────────────────────────────────────────────────
def league_page(lg):
    url = SITE + lg["url"]
    cl = lg["clubs"]
    title = title_of(f"{lg['name']} grounds {SEASON}",
                     f"{lg['name']} grounds", f"{lg['name']}")
    desc = fit([f"Every {lg['name']} ground for {SEASON}:",
                f"all {len(cl)} clubs,", "with stadiums, towns, capacities",
                "and a map of the whole division."], 160)

    rows = "".join(
        f'          <tr><td><a href="{c["url"]}">{e(c["name"])}</a></td>'
        f'<td>{e(c["stadium"])}</td><td>{e(c["town"])}</td>'
        f'<td class="gp-num">{c["capacity"]:,}</td></tr>\n' if c["capacity"] else
        f'          <tr><td><a href="{c["url"]}">{e(c["name"])}</a></td>'
        f'<td>{e(c["stadium"])}</td><td>{e(c["town"])}</td>'
        f'<td class="gp-num">—</td></tr>\n' for c in cl)

    ld_list = {"@context": "https://schema.org", "@type": "ItemList",
               "name": f"{lg['name']} grounds {SEASON}", "numberOfItems": len(cl),
               "itemListElement": [
                   {"@type": "ListItem", "position": i + 1, "name": c["stadium"],
                    "url": SITE + c["url"]} for i, c in enumerate(cl)]}
    bc_html, bc_ld = crumbs([("Home", "/"), ("Centre Circle Finder", APP),
                             ("Grounds", HUB), (lg["name"], lg["url"])])

    return (head(e(title), e(desc), url)
            + nav() + bc_html
            + '  <section class="wrap gp-hero">\n'
            + f'    <h1>{e(lg["name"])} grounds</h1>\n'
            + f'    <p class="gp-sub">{len(cl)} clubs · Tier {lg["tier"]} · '
            + f'{e(lg["country"])} · {e(lg["status"])} · {e(SEASON)}</p>\n'
            + f'    <a class="gp-cta" href="{APP}">Open the map</a>\n'
            + '  </section>\n'
            + '  <section class="wrap gp-sec">\n'
            + '    <div class="gp-tw">\n      <table class="gp-table">\n'
            + '        <thead><tr><th>Club</th><th>Ground</th><th>Town</th>'
            + '<th class="gp-num">Capacity</th></tr></thead>\n'
            + f'        <tbody>\n{rows}        </tbody>\n'
            + '      </table>\n    </div>\n'
            + f'    <p class="gp-more"><a href="{HUB}">Every UK ground</a></p>\n'
            + '  </section>\n'
            + ld(ld_list) + ld(bc_ld) + footer(APPS))


# ── hub ──────────────────────────────────────────────────────────────────
def hub_page():
    url = SITE + HUB
    by_country = {}
    for lg in LEAGUE_PAGES:
        by_country.setdefault(lg["country"], []).append(lg)
    league_html = ""
    for country, ls in by_country.items():
        links = "".join(f'        <a href="{l["url"]}">{e(l["name"])}'
                        f'<span>{len(l["clubs"])}</span></a>\n' for l in ls)
        league_html += (f'      <div class="gp-col">\n        <h3>{e(country)}</h3>\n'
                        f'{links}      </div>\n')

    city_html = "".join(f'      <a href="{c["url"]}">{e(c["label"])}'
                        f'<span>{len(c["clubs"])}</span></a>\n' for c in CITIES)

    az = {}
    for c in CLUBS:
        az.setdefault(c["name"][0].upper(), []).append(c)
    az_html = ""
    for letter in sorted(az):
        links = "".join(f'        <a href="{c["url"]}">{e(c["name"])}</a>\n'
                        for c in az[letter])
        az_html += (f'      <div class="gp-az">\n        <h3>{e(letter)}</h3>\n'
                    f'        <div class="gp-az-links">\n{links}        </div>\n      </div>\n')

    title = title_of(f"UK football grounds — all {len(CLUBS)} clubs")
    desc = fit([f"Every one of the {len(CLUBS)} senior football grounds in England,",
                "Scotland, Wales and Northern Ireland —",
                f"{len(LEAGUE_PAGES)} leagues, with locations and capacities."], 160)
    bc_html, bc_ld = crumbs([("Home", "/"), ("Centre Circle Finder", APP),
                             ("Grounds", HUB)])

    return (head(e(title), e(desc), url)
            + nav() + bc_html
            + '  <section class="wrap gp-hero">\n'
            + '    <h1>Every UK football ground</h1>\n'
            + f'    <p class="gp-sub">{len(CLUBS)} clubs · {len(LEAGUE_PAGES)} leagues · '
            + f'England, Scotland, Wales and Northern Ireland · {e(SEASON)}</p>\n'
            + f'    <a class="gp-cta" href="{APP}">Open the map</a>\n'
            + '  </section>\n'
            + '  <section class="wrap gp-sec">\n    <h2>By league</h2>\n'
            + f'    <div class="gp-cols">\n{league_html}    </div>\n'
            + '    <h2>By city</h2>\n'
            + f'    <div class="gp-cities">\n{city_html}    </div>\n'
            + '    <h2>Every club A–Z</h2>\n'
            + f'{az_html}'
            + '  </section>\n'
            + ld(bc_ld) + footer(APPS))


# ── run ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    W(HUB, hub_page())
    for c in CLUBS:
        W(c["url"], club_page(c))
    for c in CITIES:
        W(c["url"], city_page(c))
    for l in LEAGUE_PAGES:
        W(l["url"], league_page(l))
    print(f"grounds: 1 hub + {len(CLUBS)} clubs + {len(CITIES)} cities + "
          f"{len(LEAGUE_PAGES)} leagues = {1+len(CLUBS)+len(CITIES)+len(LEAGUE_PAGES)} pages")
