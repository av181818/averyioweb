#!/usr/bin/env python3
"""Generate the averyio site chrome pages (home, apps index, finance,
contact, privacy index, 404) plus sitemap.xml and robots.txt."""
import os

# reuse gen.py's helpers + app data without triggering its write block
_src = open(os.path.join(os.path.dirname(__file__), "gen.py"), encoding="utf-8").read()
exec(_src.split("# ── write app pages")[0], globals())

TODAY = "2026-08-09"

CARD_DESC = {
 "investfast":     "Learn to invest in 24 hours — 144 plain-English lessons on stocks, ETFs and tax.",
 "surge":          "An interval and HIIT timer with Tabata, Boxing and EMOM built in.",
 "big-time-clock": "Turn an iPhone or iPad into a beautiful full-screen clock.",
 "lume":           "A gamified to-do list that makes getting things done genuinely rewarding.",
 "tap-dot-tap":    "A one-tap reflex game. Tap the dot before it vanishes.",
}

# ── the tile's artwork ───────────────────────────────────────────────────
# The stage is 5:4 and crops with `object-position: 50% 0`, i.e. it shows the
# TOP of whatever image it is given. App Store screenshots suit that — their
# headline is at the top. Artwork that centres its content does not: Centre
# Circle Finder's poster showed nothing but pitch texture, and BTCPRIX had no
# screenshot at all and fell back to a bare monogram. Both now supply a `tile`:
# a purpose-made 640x512 crop that fills the stage exactly.
def stage_html(a):
    t = a.get("tile")
    if t:
        n, alt = t
        return (f'<div class="show-stage"><img src="/assets/apps/{n}.webp" '
                f'srcset="/assets/apps/{n}-sm.webp 320w, /assets/apps/{n}.webp 640w" '
                f'sizes="(max-width: 640px) 92vw, (max-width: 1000px) 46vw, 31vw" '
                f'alt="{alt}" width="640" height="512" loading="lazy" decoding="async" /></div>')
    if a.get("shots"):
        n, alt = a["shots"][0]
        return (f'<div class="show-stage"><img src="/assets/apps/{n}.webp" '
                f'srcset="/assets/apps/{n}-sm.webp 320w, /assets/apps/{n}.webp 638w" '
                f'sizes="(max-width: 640px) 92vw, (max-width: 1000px) 46vw, 31vw" '
                f'alt="{alt}" width="638" height="1387" loading="lazy" decoding="async" /></div>')
    # Every product now supplies artwork. The old monogram-on-ink fallback was
    # removed with its `.show-blank` rule once BTCPRIX got a real tile — a
    # dead CSS rule fails check.py. Fail loudly here rather than shipping a
    # tile with an empty stage.
    raise SystemExit(
        f"{a['name']}: no artwork. Add a 'tile' (a 640x512 crop) or 'shots' "
        f"entry — see stage_html() in gen_site.py.")

# ── app showcase tile ────────────────────────────────────────────────────
# The tile's icon. Products with no App Store icon (BTCPRIX) fall back to
# the monogram, so both card renderers share this.
def icon_html(a):
    if a.get("asset"):
        return (f'<img class="app-icon" src="/assets/apps/{a["asset"]}-icon.webp" '
                f'srcset="/assets/apps/{a["asset"]}-icon.webp 1x, /assets/apps/{a["asset"]}-icon@2x.webp 2x" '
                f'alt="" width="46" height="46" loading="lazy" decoding="async" />')
    return f'<div class="mono-tile" aria-hidden="true">{a["mono"]}</div>'

def show_card(a):
    icon = icon_html(a)
    stage = stage_html(a)

    # The real download size rides along on the tile. It used to live in the
    # apps.html spec table, which was removed 2026-08-06 — and "no bloat" is
    # the whole pitch, so the number should not vanish from the browse pages.
    tags = "".join(f'<span class="tag">{t}</span>' for t in a["tags"])
    if a["size"]:
        tags += f'<span class="tag neutral">~{a["size"]} MB</span>'
    return f"""        <a href="/apps/{a['slug']}/" class="show">
          {stage}
          <div class="show-body">
            <div class="show-head">
              {icon}
              <p class="show-name">{a['name']}</p>
              <span class="show-go">&rarr;</span>
            </div>
            <p class="show-tag">{CARD_DESC[a['slug']]}</p>
            <div class="show-tags">{tags}</div>
          </div>
        </a>"""

# Same tile, for an app that lives outside the /apps/<slug>/ system (see
# SITE_APPS in gen.py). Identical markup to show_card so the grid stays
# uniform; it just links straight to the app's own page.
def site_app_card(s):
    tags = "".join(f'<span class="tag">{t}</span>' for t in s["tags"])
    if s.get("note"):
        tags += f'<span class="tag neutral">{s["note"]}</span>'
    return f"""        <a href="{s['url']}" class="show">
          {stage_html(s)}
          <div class="show-body">
            <div class="show-head">
              {icon_html(s)}
              <p class="show-name">{s['name']}</p>
              <span class="show-go">&rarr;</span>
            </div>
            <p class="show-tag">{s['desc']}</p>
            <div class="show-tags">{tags}</div>
          </div>
        </a>"""

# Terminal tile on the home grid. The home page shows the first three apps
# and then this; the full line-up lives on apps.html. Adding a fourth app
# therefore never changes the home page.
#
# Its stage is a cluster of the real app icons rather than a generic glyph —
# it shows what is behind the link, and gives the tile something to look at
# next to three pieces of App Store artwork. Capped at six so the 3x2 grid
# never ends on a ragged row.
_ALL_ICONS = "\n              ".join(
    (f'<img src="/assets/apps/{a["asset"]}-icon.webp" '
     f'srcset="/assets/apps/{a["asset"]}-icon.webp 1x, /assets/apps/{a["asset"]}-icon@2x.webp 2x" '
     f'alt="" width="46" height="46" loading="lazy" decoding="async" />')
    if a.get("asset") else
    f'<span class="show-all-mono" aria-hidden="true">{a["mono"]}</span>'
    # every product, not just APPS — BTCPRIX moved to SITE_APPS and would
    # otherwise vanish from the cluster, leaving 5 icons in a 3-wide grid
    for a in (SITE_APPS + APPS)[:6])

SHOW_MORE = f"""        <a href="/apps.html" class="show show-more">
          <div class="show-stage">
            <div class="show-all-grid">
              {_ALL_ICONS}
            </div>
          </div>
          <div class="show-body">
            <div class="show-head">
              <p class="show-name">See all apps</p>
            </div>
            <p class="show-tag">What each one does and how it works.</p>
            <span class="show-more-cta">The full line-up <span class="a">&rarr;</span></span>
          </div>
        </a>"""

W = lambda rel, s: (os.makedirs(os.path.dirname(os.path.join(ROOT, rel)) or ROOT, exist_ok=True),
                    open(os.path.join(ROOT, rel), "w", encoding="utf-8").write(s),
                    print(f"  {rel:26s} {len(s.encode())//1024}KB"))

# ── index.html ───────────────────────────────────────────────────────────
# The home page is the apps page. averyioFinance has its own section of the
# site and is deliberately not promoted here — the nav and footer carry the
# only links to it (owner directive 2026-08-06).
org = {
  "@context":"https://schema.org","@type":"Organization","name":"averyio",
  "url":SITE+"/","logo":f"{SITE}/assets/logo-512.png",
  "description":"averyio builds small, fast apps for iPhone, iPad and the web — one-time purchases, never subscriptions. No ads, no tracking, no bloat.",
  "sameAs":["https://x.com/averyio18"],
  # sub-brands: the apps plus the two divisions
  "brand":[{"@type":"Brand","name":a["name"],"url":f"{SITE}/apps/{a['slug']}/"} for a in APPS]
          + [{"@type":"Brand","name":"averyioApps","url":SITE+"/apps.html"},
              {"@type":"Brand","name":"averyioFinance","url":SITE+"/finance.html"}],
}
website = {"@context":"https://schema.org","@type":"WebSite","name":"averyio",
           "url":SITE+"/","publisher":{"@type":"Organization","name":"averyio"}}
# Every product, in the order the apps page lists them. SITE_APPS must be in
# here too — an ItemList that omits a product tells Google the line-up is
# smaller than it is.
_all_products = [(s["name"], SITE + s["url"]) for s in SITE_APPS] + \
                [(a["name"], f"{SITE}/apps/{a['slug']}/") for a in APPS]
itemlist = {
  "@context":"https://schema.org","@type":"ItemList","name":"Apps by averyio",
  "itemListElement":[{"@type":"ListItem","position":i,"name":n,"url":u}
                     for i,(n,u) in enumerate(_all_products, 1)]}

# The hero trio, in DOM order: left (rotated back), centre (forward), right.
HERO_SHOTS = [("surge-1","Surge, the interval timer, running on iPhone"),
              ("investfast-1","InvestFast, the investing course, running on iPhone"),
              ("lume-1","Lume, the gamified to-do list, running on iPhone")]
hero_fan = "\n".join(
    f'          <img src="/assets/apps/{n}.webp" srcset="/assets/apps/{n}-sm.webp 320w, /assets/apps/{n}.webp 638w" '
    f'sizes="220px" alt="{alt}" width="638" height="1387" decoding="async" />'
    for n, alt in HERO_SHOTS)

home = head("averyio — Small, Fast Apps for iPhone, iPad & the Web",
  "Small, fast apps for iPhone, iPad and the web — megabytes, not gigabytes. Pay once, own it forever. No subscriptions, no ads, no tracking, no bloat.",
  SITE+"/", extra=ld(org)+ld(website)+ld(itemlist))
home += nav("home")
home += f"""
  <header class="hero">
    <div class="wrap">
      <div class="hero-split">
        <div>
          <img class="hero-avatar" src="/assets/logo-256.png" alt="averyio" width="128" height="128" />
          <h1>averyio<span class="accent">.</span></h1>
          <p class="hero-lead">Small, fast apps for iPhone, iPad and the web. Pay once or not at all — no subscriptions, no ads, no tracking, and nothing bolted on that you never asked for.</p>
          <div class="btn-row">
            <a class="btn btn-dark" href="/apps.html">See the apps <span class="a">&rarr;</span></a>
          </div>
        </div>
        <div class="fan">
{hero_fan}
        </div>
      </div>
    </div>
  </header>

  <section class="sec sec-white" id="apps">
    <div class="wrap">
      <div class="sec-head">
        <p class="eyebrow">For iPhone, iPad &amp; the web</p>
        <h2>averyio<span class="accent">Apps</span></h2>
        <p>Every one built to do a single job properly and then get out of the way. One upfront price where there is a price at all — never a monthly fee, and no in-app purchases waiting inside.</p>
      </div>
      <div class="show-grid quad">
{chr(10).join(show_card(a) for a in APPS[:3])}
{SHOW_MORE}
      </div>
    </div>
  </section>

  <section class="band" id="footprint">
    <div class="wrap">
      <div class="band-inner">
        <div>
          <div class="band-num">Megabytes.</div>
          <p class="band-label">Not gigabytes</p>
        </div>
        <div class="band-copy">
          <h2>Where the size actually goes</h2>
          <p>Where an app of ours is bigger, it is because of what it actually does — not what came along for the ride. Every app carries its real download size, right on the tile and again on its own page. We are not hiding from the number.</p>
        </div>
      </div>
    </div>
  </section>
"""
home += ethos_section("The same four rules, every time")
home += f"""
  <section class="cta-band">
    <div class="wrap">
      <div class="cta-inner">
        <h2>Have a proper look around</h2>
        <p>Every app has a page of its own: real screenshots, what it does and the honest download size. No signup wall to get past first.</p>
        <div class="btn-row">
          <a class="btn btn-light" href="/apps.html">Browse averyioApps <span class="a">&rarr;</span></a>
          <a class="btn btn-ghost" href="/contact.html">Contact <span class="a">&rarr;</span></a>
        </div>
      </div>
    </div>
  </section>
"""
home += footer(APPS)
W("index.html", home)

# ── apps.html ────────────────────────────────────────────────────────────
apps_bc = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
  {"@type":"ListItem","position":1,"name":"Home","item":SITE+"/"},
  {"@type":"ListItem","position":2,"name":"averyioApps","item":SITE+"/apps.html"}]}
apps_list = dict(itemlist); apps_list["name"] = "All apps by averyio"

ap = head("averyioApps — iPhone & iPad Apps, No Ads, No Subscriptions",
  "Every app by averyio for iPhone, iPad and the web. Tiny, fast and focused on a single job — one-time purchases with no subscriptions, no ads and no tracking.",
  SITE+"/apps.html", extra=ld(apps_list)+ld(apps_bc))
ap += nav("apps")
ap += crumb([("Home","/"),("averyioApps",None)])
ap += f"""
  <header class="hero">
    <div class="wrap">
      <p class="eyebrow">For iPhone, iPad &amp; the web</p>
      <h1 class="long">averyio<span class="accent">Apps.</span></h1>
      <p class="app-tagline">One job each. Done properly.</p>
      <p class="hero-lead">Small, focused apps with nothing bolted on. Pay once and it&rsquo;s yours — no ads, no tracking, and never a subscription.</p>
    </div>
  </header>

  <section class="sec" id="apps">
    <div class="wrap">
      <div class="sec-head">
        <p class="eyebrow">The line-up</p>
        <h2>Everything we have shipped</h2>
      </div>
      <div class="show-grid">
{chr(10).join(site_app_card(s) for s in SITE_APPS)}
{chr(10).join(show_card(a) for a in APPS)}
      </div>
    </div>
  </section>
"""
ap += ethos_section("What every averyio app has in common")
ap += f"""
  <section class="cta-band">
    <div class="wrap">
      <div class="cta-inner">
        <h2>Something you&rsquo;d like us to build?</h2>
        <p>We&rsquo;re a small operation and we take ideas seriously. The fastest way to reach us is on X.</p>
        <div class="btn-row">
          <a class="btn btn-light" href="https://x.com/averyio18" target="_blank" rel="noopener">{X_SVG} @averyio18</a>
          <a class="btn btn-ghost" href="/contact.html">Contact <span class="a">&rarr;</span></a>
        </div>
      </div>
    </div>
  </section>
"""
ap += footer(APPS)
W("apps.html", ap)

# ── finance.html — the averyioFinance division ───────────────────────────
# Voice calibrated to the @averyio18 X account (bio: "Buying dips by day |
# Coding bugs by night | Daily market recaps, dip buying vibes & overall
# chaos"): witty and irreverent, but written as a website — no emoji walls,
# no ALL-CAPS blocks. The not-advice disclaimer stays prominent regardless.
PRINCIPLES = [
 ("Buy the dip","Red days are a sale nobody queues up for. Everyone insists they want to buy low, right up until things are actually low, at which point they discover an urgent need to sell. We treat a red month as the discount, not the emergency."),
 ("Time in the market","The people who do well are almost always the ones who did nothing, for an extremely long time. Selling the top and buying the bottom is a trick everyone can do in hindsight and nobody can do twice."),
 ("Boring is undefeated","Everyone wants the 10x. The people who actually got there owned a dull index fund and forgot the password for twenty years. Broad and boring beats clever and concentrated far more often than anyone selling clever will admit."),
 ("Keep costs low","Fees are the one number you control completely, and they compound against you with exactly the same enthusiasm your returns compound for you. A percent shaved off costs beats a hot tip, every time."),
 ("Zoom out","Every chart is chaos on a one-day view and a line going up on a thirty-year one. If you are investing for decades and panicking over an afternoon, one of those two timeframes is wrong."),
 ("Only risk what you can lose","A position you can sleep through is a position you will still own when it matters. If a red candle is ruining your evening, the size is the problem, not the candle. That goes double for crypto."),
]

TRADINGVIEW_AFF = "https://www.tradingview.com/?aff_id=160229"

fin_bc = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
  {"@type":"ListItem","position":1,"name":"Home","item":SITE+"/"},
  {"@type":"ListItem","position":2,"name":"averyioFinance","item":SITE+"/finance.html"}]}
fin_brand = {
  "@context":"https://schema.org","@type":"Brand","name":"averyioFinance",
  "url":SITE+"/finance.html",
  "description":"Daily market recaps, dip-buying vibes and a long-term take on investing. Educational only, never financial advice.",
  "parentOrganization":{"@type":"Organization","name":"averyio","url":SITE+"/"},
}

WARN_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            '<circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16.2v.1"/></svg>')

principle_cards = "\n".join(
    f"""        <div class="feature">
          <div class="feature-ico num">{i:02d}</div>
          <h3>{t}</h3>
          <p>{d}</p>
        </div>""" for i, (t, d) in enumerate(PRINCIPLES, 1))

fin = head("averyioFinance — Market Recaps & Long-Term Investing",
  "Daily market recaps, dip-buying vibes and a long-term take on investing that refuses to get excited. Educational only — never financial advice.",
  SITE+"/finance.html", extra=ld(fin_brand)+ld(fin_bc))
fin += nav("finance")
fin += crumb([("Home","/"),("averyioFinance",None)])
fin += f"""
  <header class="hero">
    <div class="wrap">
      <p class="eyebrow">Markets &amp; investing</p>
      <h1 class="long">averyio<span class="accent">Finance.</span></h1>
      <p class="app-tagline">Buying dips.</p>
      <p class="hero-lead">Daily market recaps, dip-buying vibes and a running commentary on whatever the market has decided to do to us today. The thinking lives here. The chaos lives on X.</p>
      <p class="notice">{WARN_SVG}<span><strong>This is not financial advice.</strong> We are not financial advisers and nothing here is a recommendation to buy or sell anything. It is how we think, written down — for education, not instruction.</span></p>
      <div class="btn-row">
        <a class="btn btn-dark" href="https://x.com/averyio18" target="_blank" rel="noopener">{X_SVG} Follow @averyio18 on X</a>
      </div>
    </div>
  </header>

  <section class="sec sec-white" id="principles">
    <div class="wrap">
      <div class="sec-head">
        <p class="eyebrow">How we think</p>
        <h2>Six ideas that do the heavy lifting</h2>
        <p>None of this is clever, and that is rather the point. Clever is how people lose money interestingly. These are the ideas we keep coming back to once the noise dies down.</p>
      </div>
      <div class="feature-grid">
{principle_cards}
      </div>
    </div>
  </section>

  <section class="sec" id="tools">
    <div class="wrap">
      <div class="sec-head">
        <p class="eyebrow">The kit</p>
        <h2>Useful tools</h2>
      </div>
      <div class="grid">

        <a href="{TRADINGVIEW_AFF}" target="_blank" rel="noopener sponsored" class="card">
          <div class="card-top">
            <div class="feature-ico" style="margin-bottom:0;">{ico('chart')}</div>
            <span class="card-arrow">&#8599;</span>
          </div>
          <div>
            <p class="card-title">TradingView</p>
            <p class="card-desc">The platform we chart on, every single day. Sign up through us and you get $15 off.</p>
          </div>
          <div class="card-footer"><span class="tag">$15 off</span><span class="tag neutral">Affiliate</span></div>
        </a>

        <a href="/btc-prix/" class="card">
          <div class="card-top">
            <div class="mono-tile" aria-hidden="true">&#8383;</div>
            <span class="card-arrow">&rarr;</span>
          </div>
          <div>
            <p class="card-title">BTCPRIX</p>
            <p class="card-desc">The live Bitcoin price, in a page that loads before you have finished blinking. No account.</p>
          </div>
          <div class="card-footer"><span class="tag">Web</span><span class="tag">Crypto</span></div>
        </a>

        <a href="/apps/investfast/" class="card">
          <div class="card-top">
            <img class="app-icon" src="/assets/apps/investfast-icon.webp" srcset="/assets/apps/investfast-icon.webp 1x, /assets/apps/investfast-icon@2x.webp 2x" alt="" width="46" height="46" loading="lazy" decoding="async" />
            <span class="card-arrow">&rarr;</span>
          </div>
          <div>
            <p class="card-title">InvestFast</p>
            <p class="card-desc">Everything above, taught properly and without the jargon. 144 lessons.</p>
          </div>
          <div class="card-footer"><span class="tag">iOS</span><span class="tag">Finance</span></div>
        </a>

      </div>
      <p class="cmp-note">The TradingView link is an affiliate link — if you sign up through it we get a small cut, at no extra cost to you. We use it every day ourselves, which is the only reason it is on this page.</p>
    </div>
  </section>

  <section class="cta-band">
    <div class="wrap">
      <div class="cta-inner">
        <h2>The good stuff is on X</h2>
        <p>Recaps every session, takes that have not been through a compliance department, and a running tally of whatever oil is doing to us this week.</p>
        <div class="btn-row">
          <a class="btn btn-light" href="https://x.com/averyio18" target="_blank" rel="noopener">{X_SVG} Follow @averyio18</a>
          <a class="btn btn-ghost" href="/apps/investfast/">Learn the basics <span class="a">&rarr;</span></a>
        </div>
      </div>
    </div>
  </section>

  <div class="wrap disclaimer">
    Nothing on this page is financial advice. averyio is not a financial adviser and none of this is a recommendation to buy or sell any investment. Markets carry risk and you can lose money — crypto especially. Past performance tells you nothing reliable about future returns. Only ever risk what you can afford to lose, and if you want advice, speak to someone qualified and regulated to give it.
  </div>
"""
fin += footer(APPS)
W("finance.html", fin)

# ── contact.html ─────────────────────────────────────────────────────────
con_bc = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
  {"@type":"ListItem","position":1,"name":"Home","item":SITE+"/"},
  {"@type":"ListItem","position":2,"name":"Contact","item":SITE+"/contact.html"}]}
con = head("Contact averyio — Questions, Bugs & App Ideas",
  "Get in touch with averyio. The fastest way to reach us is on X, @averyio18.",
  SITE+"/contact.html", extra=ld(con_bc))
con += nav("contact")
con += crumb([("Home","/"),("Contact",None)])
# Deliberately no `.cta-band` here. Every other page closes on the ink
# panel, but this page IS the call to action — a second dark shout added
# nothing and read as heavy. It closes on the light `.contact-panel`.
CONTACT_REASONS = [
 ("bolt", "Something is broken",
  "Tell us what happened and which app you were using. We are a small operation, which is the whole reason fixes go out quickly."),
 ("star", "An app you wish existed",
  "We take suggestions seriously. If there is a small, sharp tool you would reach for every day, we would like to hear about it."),
 ("shield", "A question about your data",
  "Every policy we have is published in full and in plain English. If any of it is unclear, ask and we will explain it properly."),
]
reason_cards = "\n".join(
    f"""        <div class="feature">
          <div class="feature-ico">{ico(k)}</div>
          <h3>{t}</h3>
          <p>{d}</p>
        </div>""" for k, t, d in CONTACT_REASONS)

con += f"""
  <header class="hero">
    <div class="wrap">
      <p class="eyebrow">Get in touch</p>
      <h1>Let&rsquo;s talk<span class="accent">.</span></h1>
      <p class="app-tagline">A human answers.</p>
      <p class="hero-lead">No contact form, no ticket number, no support bot with a cheerful name. Just us, and we read everything that comes in.</p>
    </div>
  </header>

  <section class="sec sec-white">
    <div class="wrap">
      <div class="sec-head">
        <p class="eyebrow">What to send</p>
        <h2>Worth getting in touch about</h2>
      </div>
      <div class="feature-grid">
{reason_cards}
      </div>
    </div>
  </section>

  <section class="sec">
    <div class="wrap">
      <div class="contact-panel">
        <div class="contact-mark">{X_SVG}</div>
        <div>
          <p class="eyebrow">The fastest way</p>
          <p class="contact-handle">@averyio18</p>
          <p class="contact-note">A message or a mention on X reaches us directly, and it is where we are most days anyway. Expect a reply from a person who worked on the thing you are asking about.</p>
        </div>
        <div class="btn-row contact-actions">
          <a class="btn btn-dark" href="https://x.com/averyio18" target="_blank" rel="noopener">{X_SVG} Message us on X</a>
          <a class="btn btn-ghost" href="/privacy.html">Privacy policies <span class="a">&rarr;</span></a>
        </div>
      </div>
    </div>
  </section>
"""
con += footer(APPS)
W("contact.html", con)

# ── privacy.html ─────────────────────────────────────────────────────────
# The hrefs to privacy-*.html MUST stay exactly as they are: Apple links to
# those URLs from the live App Store listings. This page is the cover-all
# for the whole business, so app policies sit in their own section and
# future business areas get sections of their own.
PRIV = [("InvestFast","/privacy-investfast.html"),("Surge","/privacy-surge.html"),
        ("Big Time Clock","/privacy-bigtimeclock.html"),("Lume","/privacy-lume.html"),
        ("Tap Dot Tap","/privacy-tapdottap.html"),("Zenith","/privacy-zenith.html")]
priv_bc = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
  {"@type":"ListItem","position":1,"name":"Home","item":SITE+"/"},
  {"@type":"ListItem","position":2,"name":"Privacy","item":SITE+"/privacy.html"}]}
pv = head("Privacy — No Tracking, No Ads, No Data Sold | averyio",
  "Privacy policies for every averyio app. No tracking, no ads and no data sold — read the full policy for each app in plain English.",
  SITE+"/privacy.html", extra=ld(priv_bc))
pv += nav("privacy")
pv += crumb([("Home","/"),("Privacy",None)])
pv += f"""
  <header class="hero">
    <div class="wrap">
      <p class="eyebrow">Across averyio</p>
      <h1>Privacy<span class="accent">.</span></h1>
      <p class="app-tagline">Your data is yours.</p>
      <p class="hero-lead">One rule across everything we do: no tracking, no data sold, no surprises. Every policy we have lives on this page, starting with the apps.</p>
    </div>
  </header>

  <section class="sec sec-white">
    <div class="wrap">
      <div class="sec-head">
        <p class="eyebrow">Legal</p>
        <h2>App privacy policies</h2>
        <p>The short version: our apps do not track you, do not show ads, and do not sell your data. Where an app syncs or backs up, it uses your own private iCloud account — never a server owned by us or by anyone else. The full policy for each app is below.</p>
      </div>
      <div class="grid">
{chr(10).join(f'''        <a href="{href}" class="card">
          <div class="card-top">
            <p class="card-title" style="margin:0;">{name}</p>
            <span class="card-arrow">&rarr;</span>
          </div>
        </a>''' for name, href in PRIV)}
      </div>
    </div>
  </section>
"""
pv += footer(APPS)
W("privacy.html", pv)

# ── 404.html ─────────────────────────────────────────────────────────────
nf = head("Page not found — averyio", "That page does not exist. Browse the apps by averyio instead.",
          SITE+"/404.html", extra='  <meta name="robots" content="noindex" />\n')
nf += nav()
nf += f"""
  <header class="hero">
    <div class="wrap">
      <h1>404<span class="accent">.</span></h1>
      <p class="hero-lead">That page does not exist — it may have moved. The apps are all still here.</p>
      <div class="btn-row">
        <a class="btn btn-dark" href="/apps.html">See the apps <span class="a">&rarr;</span></a>
        <a class="btn btn-ghost" href="/">Home <span class="a">&rarr;</span></a>
      </div>
    </div>
  </header>
"""
nf += footer(APPS)
W("404.html", nf)

# ── retired URLs ─────────────────────────────────────────────────────────
# A meta-refresh stub, not a deletion: the old URL stays resolvable for anyone
# who has it, and the canonical points Google at the destination. It is
# deliberately noindex so the two do not compete.
for path, dest, name in REDIRECTS:
    W(path, f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8" />
  <title>{name} has moved</title>
  <link rel="canonical" href="{SITE}{dest}" />
  <meta name="robots" content="noindex, follow" />
  <meta http-equiv="refresh" content="0; url={dest}" />
</head>
<body>
  <p>{name} has moved to <a href="{dest}">{SITE}{dest}</a>.</p>
</body>
</html>
""")

# ── sitemap.xml + robots.txt ─────────────────────────────────────────────
# lastmod is per-URL, taken from the file's own last commit date. Stamping
# every URL with today's date (which this used to do) makes lastmod worthless:
# Google learns the dates do not track real changes and starts ignoring them.
import subprocess
def _lastmod(path):
    d = subprocess.run(["git", "log", "-1", "--format=%cs", "--", path],
                       cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return d or TODAY

urls = [(SITE+"/", "1.0", "index.html"),
        (SITE+"/apps.html", "0.9", "apps.html"),
        (SITE+"/finance.html", "0.7", "finance.html"),
        (SITE+"/privacy.html", "0.3", "privacy.html"),
        (SITE+"/contact.html", "0.5", "contact.html")]
urls += [(f"{SITE}/apps/{a['slug']}/", "0.8", f"apps/{a['slug']}/index.html") for a in APPS]
urls += [(SITE + s["url"], s["priority"], s["url"].strip("/") + "/index.html") for s in SITE_APPS]
# Apps hosted on this domain that also keep a /apps/<slug>/ marketing page.
# They already have a tile via APPS, so they need only a sitemap entry.
urls += [(SITE + a["hosted"], "0.7", a["hosted"].strip("/") + "/index.html")
         for a in APPS if a.get("hosted")]
urls += [(SITE+p, "0.2", p.lstrip("/")) for _, p in PRIV]

# Centre Circle Finder's static ground pages. The 688 club/city/league pages
# all derive from one data file, so they share its commit date — asking git for
# 688 individual lastmods would add a minute to every build for an identical
# answer. The hub is different: it is one templated page whose markup can move
# for reasons the data never sees (it did on 2026-08-10 for a CSS change while
# teams.js sat at 08-09), so it gets its own date like every other page.
from grounds import CLUBS, CITIES, LEAGUE_PAGES
_gm = _lastmod("centre-circle-finder/data/teams.js")
urls += [(SITE + "/centre-circle-finder/grounds/", "0.6", "centre-circle-finder/grounds/index.html")]
urls += [(SITE + l["url"], "0.5", None) for l in LEAGUE_PAGES]
urls += [(SITE + c["url"], "0.5", None) for c in CITIES]
urls += [(SITE + c["url"], "0.4", None) for c in CLUBS]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u, pr, src in urls:
    sm += (f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{_lastmod(src) if src else _gm}</lastmod>\n"
           f"    <priority>{pr}</priority>\n  </url>\n")
sm += "</urlset>\n"
W("sitemap.xml", sm)
# Jekyll only hides `_`- and `.`-prefixed paths, so an app folder's working
# files (notes, dev server) are served publicly alongside the app itself. They
# hold nothing sensitive — the repo is public — but they should not be indexed.
#
# Found by looking, not by listing: the previous version named README.md and
# serve.py for every SITE_APP and a third set keyed off APPS' "hosted" flag.
# BTCPRIX lost that flag when it moved into SITE_APPS, so its two SEO markdown
# files went unlisted and stayed crawlable, while robots disallowed a README and
# a serve.py that do not exist in its folder. Globbing keeps the file and the
# rule in step no matter which app grows or loses one.
import glob as _glob
NOINDEX = sorted(
    s["url"] + os.path.basename(p)
    for s in SITE_APPS
    for pattern in ("*.md", "*.py")
    for p in _glob.glob(os.path.join(ROOT, s["url"].strip("/"), pattern)))
W("robots.txt",
  "User-agent: *\nAllow: /\n"
  + "".join(f"Disallow: {p}\n" for p in NOINDEX)
  + f"\nSitemap: {SITE}/sitemap.xml\n")
print(f"\nsitemap: {len(urls)} URLs")
