#!/usr/bin/env python3
"""Pre-flight checks for averyio.net.

    cd _tools && python3 check.py           # check the local files
    cd _tools && python3 check.py --live    # also diff every file against averyio.net

Every check here exists because it caught a real bug at least once. Run it
before ./upload.sh, and again with --live afterwards.
"""
import glob, hashlib, json, os, re, subprocess, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://averyio.net"
os.chdir(ROOT)

PAGES = ["index.html", "apps.html", "finance.html", "contact.html",
         "privacy.html", "404.html"] + sorted(glob.glob("apps/*/index.html"))
FROZEN = ["privacy-investfast.html", "privacy-surge.html", "privacy-bigtimeclock.html",
          "privacy-lume.html", "privacy-tapdottap.html", "privacy-zenith.html"]
LIVE_MAP = {"index.html": "/", "apps.html": "/apps.html", "finance.html": "/finance.html",
            "privacy.html": "/privacy.html", "contact.html": "/contact.html",
            "404.html": "/404.html", "sitemap.xml": "/sitemap.xml", "robots.txt": "/robots.txt",
            **{f"apps/{s}/index.html": f"/apps/{s}/" for s in
               ["investfast", "surge", "big-time-clock", "lume", "tap-dot-tap", "btc-prix"]},
            **{f: "/" + f for f in FROZEN}}

fails = []
def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{'' if ok else '  — ' + detail}")
    if not ok:
        fails.append(name)

def text_of(path):
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"<(script|style).*?</\1>", "", s, flags=re.S)
    s = re.sub(r"<nav>.*?</nav>|<footer>.*?</footer>", "", s, flags=re.S)
    return s

print("\nSTYLESHEET")
css = re.sub(r"/\*.*?\*/", "", open("assets/site.css", encoding="utf-8").read(), flags=re.S)
defined = set(re.findall(r"\.([A-Za-z][\w-]*)", css))
used = set()
for p in PAGES:
    for m in re.finditer(r'class="([^"]+)"', re.sub(r"<(script|style).*?</\1>", "", open(p, encoding="utf-8").read(), flags=re.S)):
        used.update(m.group(1).split())
orphans = sorted(used - defined)
# this is the check that would have caught the .cmp-note deletion
check("every class in the markup has styling", not orphans, ", ".join(orphans))
IGNORE = {"html","body","a","p","h1","h2","h3","td","th","tr","table","thead","tbody",
          "tfoot","ul","li","svg","img","span","div","section","nav","footer","header","script","main"}
dead = sorted(c for c in defined if c not in used and c not in IGNORE)
check("no dead CSS rules", not dead, ", ".join(dead))

print("\nLINKS")
broken, checked = [], 0
for p in PAGES + FROZEN:
    src = open(p, encoding="utf-8").read()
    refs = re.findall(r'(?:href|src)="([^"]+)"', src)
    refs += [x.strip().split()[0] for s in re.findall(r'srcset="([^"]+)"', src) for x in s.split(",")]
    for r in refs:
        if r.startswith(("http", "mailto:", "#", "data:")):
            continue
        checked += 1
        path = r.split("#")[0].split("?")[0]
        if not path:
            continue
        t = os.path.join(ROOT, path.lstrip("/")) if path.startswith("/") else \
            os.path.normpath(os.path.join(os.path.dirname(p), path))
        if os.path.isdir(t):
            t = os.path.join(t, "index.html")
        if not os.path.exists(t):
            broken.append(f"{p} -> {r}")
check(f"all {checked} internal links resolve", not broken, "; ".join(broken[:4]))

print("\nSEO / MARKUP")
long_desc, bad_h1, bad_ld = [], [], []
for p in PAGES:
    s = open(p, encoding="utf-8").read()
    d = re.search(r'<meta name="description" content="(.*?)"', s, re.S)
    if d and len(d.group(1)) > 160:
        long_desc.append(f"{p} ({len(d.group(1))})")
    if len(re.findall(r"<h1[ >]", s)) != 1:
        bad_h1.append(p)
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            json.loads(b)
        except Exception:
            bad_ld.append(p)
check("meta descriptions within 160 chars", not long_desc, ", ".join(long_desc))
check("exactly one <h1> per page", not bad_h1, ", ".join(bad_h1))
check("all JSON-LD parses", not bad_ld, ", ".join(bad_ld))

print("\nCOPY")
dupes = []
for p in PAGES:
    blocks = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(2))).strip()
              for m in re.finditer(r"<(h1|h2|h3|p|li)[^>]*>(.*?)</\1>", text_of(p), re.S)]
    words = re.sub(r"[^a-z ]", " ", " ".join(b for b in blocks if len(b.split()) >= 4).lower()).split()
    grams = Counter(" ".join(words[i:i + 5]) for i in range(len(words) - 4))
    rep = {g: c for g, c in grams.items() if c > 1}
    rep = {g: c for g, c in rep.items() if not any(g != o and g in o for o in rep)}
    # price labels are restated at the CTA on purpose
    rep = {g: c for g, c in rep.items()
           if not re.search(r"one time|single one|free \+|module free|optional one", g)}
    if rep:
        dupes.append(f"{p}: {list(rep)[:2]}")
check("no accidental repeated phrasing", not dupes, "; ".join(dupes))

banned = []
for p in PAGES:
    t = text_of(p).lower()
    for phrase in ["six apps", "five iphone apps", "pay once", "buy once and own",
                   "under 2 mb", "parent brand", "sub-brand"]:
        if phrase in t:
            banned.append(f"{p}: '{phrase}'")
check("no banned claims (counts, size promises, brand-architecture jargon)", not banned, "; ".join(banned))

print("\nFROZEN FILES")
dirty = subprocess.run(["git", "status", "--porcelain"] + FROZEN,
                       capture_output=True, text=True).stdout.strip()
check(f"the {len(FROZEN)} App Store privacy pages are unmodified", not dirty, dirty.replace("\n", "; "))

if "--live" in sys.argv:
    print("\nLIVE (averyio.net)")
    v = re.search(r"site\.css\?v=([a-f0-9]+)", open("apps.html", encoding="utf-8").read())
    m = dict(LIVE_MAP)
    m["assets/site.css"] = f"/assets/site.css?v={v.group(1)}" if v else "/assets/site.css"
    def fetch(path):
        """curl, not urllib — some Python installs have no CA bundle and every
        request fails cert verification, which looks like a site outage."""
        r = subprocess.run(["curl", "-sS", "--fail", f"{SITE}{path}"], capture_output=True)
        return r.stdout if r.returncode == 0 else None

    diffs = []
    for local, path in m.items():
        got = fetch(path)
        if got is None:
            diffs.append(f"{local}: not served")
            continue
        if hashlib.sha256(got).hexdigest() != hashlib.sha256(open(local, "rb").read()).hexdigest():
            diffs.append(f"{local}: differs")
    check(f"all {len(m)} files identical to live", not diffs, "; ".join(diffs[:4]))
    published = [u for u in ["/_tools/gen.py", "/_tools/gen_site.py", "/_tools/check.py"]
                 if fetch(u) is not None]   # a 404 is the expected, correct outcome
    check("generators are not published", not published, ", ".join(published))

print("\n" + ("ALL CHECKS PASSED" if not fails else f"{len(fails)} FAILED: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
