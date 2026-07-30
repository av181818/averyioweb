#!/usr/bin/env python3
"""Generate the averyio site chrome pages (home, apps index, finance,
contact, privacy index, 404) plus sitemap.xml and robots.txt."""
import os

# reuse gen.py's helpers + app data without triggering its write block
_src = open(os.path.join(os.path.dirname(__file__), "gen.py"), encoding="utf-8").read()
exec(_src.split("# ── write app pages")[0], globals())

TODAY = "2026-07-28"

CARD_DESC = {
 "investfast":     "Learn to invest in 24 hours — 144 plain-English lessons on stocks, ETFs and tax.",
 "surge":          "An interval and HIIT timer with Tabata, Boxing and EMOM built in.",
 "big-time-clock": "Turn an iPhone or iPad into a beautiful full-screen clock.",
 "lume":           "A gamified to-do list that makes getting things done genuinely rewarding.",
 "tap-dot-tap":    "A one-tap reflex game. Tap the dot before it vanishes.",
 "btc-prix":       "Real-time Bitcoin price tracking, free on the web.",
}

def app_card(a):
    icon = f"/assets/apps/{a['asset']}-icon.webp" if a["asset"] else "/assets/logo-256.png"
    icon2 = f"/assets/apps/{a['asset']}-icon@2x.webp" if a["asset"] else "/assets/logo-256.png"
    tags = "".join(f'<span class="tag">{t}</span>' for t in a["tags"])
    tile = (f'<img class="app-icon" src="{icon}" srcset="{icon} 1x, {icon2} 2x" alt="" width="54" height="54" loading="lazy" decoding="async" />'
            if a["asset"] else
            f'<div class="mono-tile" aria-hidden="true">{a["mono"]}</div>')
    return f"""        <a href="/apps/{a['slug']}/" class="card">
          <div class="card-top">
            {tile}
            <span class="card-arrow">&rarr;</span>
          </div>
          <div>
            <p class="card-title">{a['name']}</p>
            <p class="card-desc">{CARD_DESC[a['slug']]}</p>
          </div>
          <div class="card-footer">{tags}</div>
        </a>"""

SEE_ALL_CARD = f"""        <a href="/apps.html" class="card card-more">
          <div class="card-top">
            <div class="feature-ico">{ico('grid')}</div>
            <span class="card-arrow">&rarr;</span>
          </div>
          <div>
            <p class="card-title">See all apps</p>
            <p class="card-desc">The full line-up &mdash; what each one does, how it works and what it costs.</p>
          </div>
        </a>"""

ethos_html = "\n".join(
    f"""        <div class="ethos-item">
          <h3>{t}</h3>
          <p>{d}</p>
        </div>""" for t, d in ETHOS)

W = lambda rel, s: (os.makedirs(os.path.dirname(os.path.join(ROOT, rel)) or ROOT, exist_ok=True),
                    open(os.path.join(ROOT, rel), "w", encoding="utf-8").write(s),
                    print(f"  {rel:26s} {len(s.encode())//1024}KB"))


PRICE_SHORT = {
 "investfast":"Free + unlock", "surge":"Free + unlock", "big-time-clock":"\u00a30.99",
 "lume":"Free + unlock", "tap-dot-tap":"Free + unlock", "btc-prix":"Free",
}

def cmp_table():
    """One row per app, A-Z. This is the apps page's main content, so it
    carries everything the old tiles did — icon, name, link and description —
    plus the data the tiles could not show."""
    rows = sorted(APPS, key=lambda a: a["name"].lower())
    out = []
    for a in rows:
        icon = (f'<img src="/assets/apps/{a["asset"]}-icon.webp" srcset="/assets/apps/{a["asset"]}-icon.webp 1x, /assets/apps/{a["asset"]}-icon@2x.webp 2x" alt="" width="32" height="32" loading="lazy" decoding="async" />'
                if a["asset"] else f'<span class="mono-tile" aria-hidden="true">{a["mono"]}</span>')
        platform = "iPhone &amp; iPad" if a["ios"] else "Web"
        size = f'<span class="size">~{a["size"]} MB</span>' if a["size"] else '<span class="size">\u2014</span>'
        out.append(f"""          <tr>
            <td><a class="app-cell" href="/apps/{a['slug']}/">{icon}{a['name']} <span class="a">&rarr;</span></a></td>
            <td class="what">{CARD_DESC[a['slug']]}</td>
            <td>{platform}</td>
            <td>{a['genre']}</td>
            <td>{size}</td>
            <td>{PRICE_SHORT[a['slug']]}</td>
          </tr>""")
    body = "\n".join(out)
    return f"""
  <section class="cmp" id="apps">
    <div class="wrap">
      <div class="sec-head">
        <p class="eyebrow">Take your pick</p>
        <h2>Find the one you need</h2>
        <p>Tap any name for the full story \u2014 what it does, how it works, the screenshots, and the honest download size.</p>
      </div>
      <div class="cmp-wrap">
        <table>
          <thead>
            <tr>
              <th scope="col">App</th>
              <th scope="col">What it does</th>
              <th scope="col">Platform</th>
              <th scope="col">Category</th>
              <th scope="col">Download</th>
              <th scope="col">Price</th>
            </tr>
          </thead>
          <tbody>
{body}
          </tbody>
        </table>
      </div>
    </div>
  </section>
"""

# ── index.html ───────────────────────────────────────────────────────────
org = {
  "@context":"https://schema.org","@type":"Organization","name":"averyio",
  "url":SITE+"/","logo":f"{SITE}/assets/logo-512.png",
  "description":"averyio builds small, fast apps for iPhone, iPad and the web, alongside averyioFinance — no subscriptions, no ads, no tracking and no bloat.",
  "sameAs":["https://x.com/averyio18"],
  # sub-brands: the six apps plus the finance arm
  "brand":[{"@type":"Brand","name":a["name"],"url":f"{SITE}/apps/{a['slug']}/"} for a in APPS]
          + [{"@type":"Brand","name":"averyioApps","url":SITE+"/apps.html"},
              {"@type":"Brand","name":"averyioFinance","url":SITE+"/finance.html"}],
}
website = {"@context":"https://schema.org","@type":"WebSite","name":"averyio",
           "url":SITE+"/","publisher":{"@type":"Organization","name":"averyio"}}
itemlist = {
  "@context":"https://schema.org","@type":"ItemList","name":"Apps by averyio",
  "itemListElement":[{"@type":"ListItem","position":i,"name":a["name"],
                      "url":f"{SITE}/apps/{a['slug']}/"} for i, a in enumerate(APPS, 1)]}

home = head("averyio — Fast, Lightweight Apps for iPhone, iPad & the Web. No Bloat.",
  "Small, fast apps for iPhone, iPad and the web — megabytes, not gigabytes. Plus averyioFinance. No subscriptions, no ads, no tracking, no bloat.",
  SITE+"/", extra=ld(org)+ld(website)+ld(itemlist))
home += nav("home")
home += f"""
  <header class="hero">
    <div class="wrap">
      <img class="hero-avatar" src="/assets/logo-256.png" alt="averyio" width="128" height="128" />
      <h1>averyio<span class="accent">.</span></h1>
      <p class="hero-lead">Small, fast apps for iPhone, iPad and the web. No subscriptions, no ads, no tracking and none of the bloat. <a href="/finance.html" style="color:var(--red);text-decoration:none;font-weight:600;">averyioFinance</a> covers the markets — recaps, dips and the long game.</p>
      <div class="btn-row" style="margin-top:1.7rem;">
        <a class="btn btn-dark" href="/apps.html">See the apps <span class="a">&rarr;</span></a>
        <a class="btn btn-ghost" href="https://x.com/averyio18" target="_blank" rel="noopener">{X_SVG} Follow on X</a>
      </div>
    </div>
  </header>

  <section class="features" id="apps">
    <div class="wrap">
      <div class="sec-head">
        <p class="eyebrow">For iPhone, iPad &amp; the web</p>
        <h2>averyio<span class="accent">Apps</span></h2>
        <p>Each one does a single job properly, without the bloat. Most are free to try, and none of them will ever ask you for a monthly fee.</p>
      </div>
      <div class="grid">
{chr(10).join(app_card(a) for a in APPS[:5])}
{SEE_ALL_CARD}
      </div>
    </div>
  </section>

  <section class="footprint" id="footprint">
    <div class="wrap">
      <div class="footprint-inner dark">
        <div class="footprint-stat">
          <div class="footprint-num word">Megabytes.</div>
          <p class="footprint-label">Not gigabytes</p>
        </div>
        <div class="footprint-copy">
          <h2>Where the size actually goes</h2>
          <p>Where an app of ours is bigger, it is because of what it actually does — not what came along for the ride. Every app page lists its exact size, and the comparison table puts them side by side. We are not hiding from the number.</p>
        </div>
      </div>
    </div>
  </section>

  <section class="ethos">
    <div class="wrap">
      <div class="sec-head">
        <p class="eyebrow">The promise</p>
        <h2>The same four rules, every time</h2>
      </div>
      <div class="ethos-grid">
{ethos_html}
      </div>
    </div>
  </section>

  <section class="division" id="finance">
    <div class="wrap">
      <div class="division-inner">
        <div>
          <p class="eyebrow">The finance arm</p>
          <p class="division-name">averyio<span class="accent">Finance</span></p>
          <p class="division-desc">The other half of what we do. A long-term, low-cost, anti-hype way of looking at markets \u2014 written down as evergreen thinking, backed by the tools we build. Educational only, and never advice.</p>
          <div class="btn-row">
            <a class="btn btn-dark" href="/finance.html">Explore averyioFinance <span class="a">&rarr;</span></a>
            <a class="btn btn-ghost" href="https://x.com/averyio18" target="_blank" rel="noopener">{X_SVG} @averyio18</a>
          </div>
        </div>
        <ul class="division-points">
          <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg><span><b>Buy the dip.</b> Red months are the discount, not the emergency.</span></li>
          <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg><span><b>Stay boring.</b> Broad and dull compounds; clever and concentrated usually does not.</span></li>
          <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg><span><b>Keep costs low.</b> Fees are the one input you control completely.</span></li>
          <li><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg><span><b>Only risk what you can lose.</b> Especially in crypto.</span></li>
        </ul>
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

ap = head("averyioApps — iPhone, iPad & Web Apps With No Ads, No Subscriptions",
  "Every app by averyio for iPhone, iPad and the web. Each one tiny, fast and focused on a single job — with no subscriptions, no ads and no tracking.",
  SITE+"/apps.html", extra=ld(apps_list)+ld(apps_bc))
ap += nav("apps")
ap += crumb([("Home","/"),("averyioApps",None)])
ap += f"""
  <header class="hero" style="padding-top:clamp(30px,6vw,52px);">
    <div class="wrap">
      <p class="eyebrow">For iPhone, iPad &amp; the web</p>
      <h1 class="long">averyio<span class="accent">Apps.</span></h1>
      <p class="app-tagline">One job each. Done properly.</p>
      <p class="hero-lead">Small, focused apps with nothing bolted on. No ads, no tracking, and never a subscription.</p>
    </div>
  </header>

{cmp_table()}
  <section class="ethos">
    <div class="wrap">
      <div class="sec-head">
        <p class="eyebrow">The promise</p>
        <h2>What every averyio app has in common</h2>
      </div>
      <div class="ethos-grid">
{ethos_html}
      </div>
    </div>
  </section>

  <section class="cta-band">
    <div class="wrap">
      <div class="cta-inner">
        <h2>Something you&rsquo;d like us to build?</h2>
        <p>We&rsquo;re a small operation and we take ideas seriously. The fastest way to reach us is on X.</p>
        <div class="btn-row">
          <a class="btn btn-ghost" href="https://x.com/averyio18" target="_blank" rel="noopener">{X_SVG} @averyio18</a>
          <a class="btn btn-ghost" href="/contact.html">Contact <span class="a">&rarr;</span></a>
        </div>
      </div>
    </div>
  </section>
"""
ap += """
  <script>
    /* Whole-row click for the app table. A <tr> cannot be wrapped in an
       anchor, and a stretched-link overlay is not reliable: Safari does not
       treat position:relative on a <tr> as a containing block, so every
       row's overlay resolves against a larger ancestor, they stack, and
       only the last row painted stays clickable. This sends a row click to
       that row's own link. With JS off, the app name is still a link. */
    document.querySelectorAll('.cmp tbody tr').forEach(function (row) {
      var link = row.querySelector('a.app-cell');
      if (!link) return;
      row.addEventListener('click', function (e) {
        if (e.target.closest('a')) return;                  // real link wins
        if (window.getSelection().toString()) return;       // allow selection
        window.location = link.href;
      });
    });
  </script>
"""
ap += footer(APPS)
W("apps.html", ap)

# ── finance.html — the averyioFinance sub-brand ──────────────────────────
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

fin = head("averyioFinance — Daily Market Recaps, Dip Buying & Long-Term Investing",
  "Daily market recaps, dip-buying vibes and a long-term take on investing that refuses to get excited. Educational only — never financial advice.",
  SITE+"/finance.html", extra=ld(fin_brand)+ld(fin_bc))
fin += nav("finance")
fin += crumb([("Home","/"),("averyioFinance",None)])
fin += f"""
  <header class="hero" style="padding-top:clamp(30px,6vw,52px);">
    <div class="wrap">
      <p class="eyebrow">Markets &amp; investing</p>
      <h1 class="long">averyio<span class="accent">Finance.</span></h1>
      <p class="app-tagline">Buying dips.</p>
      <p class="hero-lead">Daily market recaps, dip-buying vibes and a running commentary on whatever the market has decided to do to us today. The thinking lives here. The chaos lives on X.</p>
      <p class="notice">{WARN_SVG}<span><strong>This is not financial advice.</strong> We are not financial advisers and nothing here is a recommendation to buy or sell anything. It is how we think, written down \u2014 for education, not instruction.</span></p>
      <div class="btn-row" style="margin-top:1.6rem;">
        <a class="btn btn-dark" href="https://x.com/averyio18" target="_blank" rel="noopener">{X_SVG} Follow @averyio18 on X</a>
      </div>
    </div>
  </header>

  <section class="features" id="principles">
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

  <section class="features" id="tools">
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

        <a href="/apps/btc-prix/" class="card">
          <div class="card-top">
            <div class="mono-tile" aria-hidden="true">&#8383;</div>
            <span class="card-arrow">&rarr;</span>
          </div>
          <div>
            <p class="card-title">BTC Prix</p>
            <p class="card-desc">The live Bitcoin price, in a page that loads before you have finished blinking. Free, no account.</p>
          </div>
          <div class="card-footer"><span class="tag">Web</span><span class="tag">Crypto</span></div>
        </a>

        <a href="/apps/investfast/" class="card">
          <div class="card-top">
            <img class="app-icon" src="/assets/apps/investfast-icon.webp" srcset="/assets/apps/investfast-icon.webp 1x, /assets/apps/investfast-icon@2x.webp 2x" alt="" width="54" height="54" loading="lazy" decoding="async" />
            <span class="card-arrow">&rarr;</span>
          </div>
          <div>
            <p class="card-title">InvestFast</p>
            <p class="card-desc">Everything above, taught properly and without the jargon. 144 lessons, module 1 free.</p>
          </div>
          <div class="card-footer"><span class="tag">iOS</span><span class="tag">Finance</span></div>
        </a>

      </div>
      <p class="cmp-note">The TradingView link is an affiliate link \u2014 if you sign up through it we get a small cut, at no extra cost to you. We use it every day ourselves, which is the only reason it is on this page.</p>
    </div>
  </section>

  <section class="cta-band">
    <div class="wrap">
      <div class="cta-inner">
        <h2>The good stuff is on X</h2>
        <p>Recaps every session, takes that have not been through a compliance department, and a running tally of whatever oil is doing to us this week.</p>
        <div class="btn-row">
          <a class="btn btn-store btn-ghost" href="https://x.com/averyio18" target="_blank" rel="noopener" style="padding:0.9rem 1.5rem;">{X_SVG} Follow @averyio18</a>
          <a class="btn btn-ghost" href="/apps/investfast/">Learn the basics <span class="a">&rarr;</span></a>
        </div>
      </div>
    </div>
  </section>

  <div class="wrap disclaimer">
    Nothing on this page is financial advice. averyio is not a financial adviser and none of this is a recommendation to buy or sell any investment. Markets carry risk and you can lose money \u2014 crypto especially. Past performance tells you nothing reliable about future returns. Only ever risk what you can afford to lose, and if you want advice, speak to someone qualified and regulated to give it.
  </div>
"""
fin += footer(APPS)
W("finance.html", fin)

# ── contact.html ─────────────────────────────────────────────────────────
con_bc = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
  {"@type":"ListItem","position":1,"name":"Home","item":SITE+"/"},
  {"@type":"ListItem","position":2,"name":"Contact","item":SITE+"/contact.html"}]}
con = head("Contact averyio",
  "Get in touch with averyio. The fastest way to reach us is on X, @averyio18.",
  SITE+"/contact.html", extra=ld(con_bc))
con += nav("contact")
con += crumb([("Home","/"),("Contact",None)])
con += f"""
  <header class="hero" style="padding-top:clamp(30px,6vw,52px);">
    <div class="wrap">
      <h1>Let&rsquo;s talk<span class="accent">.</span></h1>
    </div>
  </header>

  <section class="cta-band" style="padding-top:clamp(20px,4vw,32px);">
    <div class="wrap">
      <div class="cta-inner">
        <h2>Questions, bugs and ideas all welcome</h2>
        <p>Got a question, found a bug, or thought of an app you wish existed? Tell us what happened and which app it was, and we&rsquo;ll get on it. Small operation, fast fixes — and we read everything.</p>
        <div class="btn-row">
          <a class="btn btn-light" href="https://x.com/averyio18" target="_blank" rel="noopener">{X_SVG} @averyio18 on X</a>
          <a class="btn btn-ghost" href="/privacy.html">Privacy policies <span class="a">&rarr;</span></a>
        </div>
      </div>
    </div>
  </section>
"""
con += footer(APPS)
W("contact.html", con)

# ── privacy.html — hrefs to privacy-*.html MUST stay exactly as they are ──
PRIV = [("InvestFast","/privacy-investfast.html"),("Surge","/privacy-surge.html"),
        ("Big Time Clock","/privacy-bigtimeclock.html"),("Lume","/privacy-lume.html"),
        ("Tap Dot Tap","/privacy-tapdottap.html")]
priv_bc = {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
  {"@type":"ListItem","position":1,"name":"Home","item":SITE+"/"},
  {"@type":"ListItem","position":2,"name":"Privacy","item":SITE+"/privacy.html"}]}
pv = head("Privacy Policies — averyio Apps",
  "Privacy policies for every averyio app: InvestFast, Surge, Big Time Clock, Lume and Tap Dot Tap. No ads, no tracking, no data sold.",
  SITE+"/privacy.html", extra=ld(priv_bc))
pv += nav("privacy")
pv += crumb([("Home","/"),("Privacy",None)])
pv += f"""
  <header class="hero" style="padding-top:clamp(30px,6vw,52px);">
    <div class="wrap">
      <h1>Privacy<span class="accent">.</span></h1>
      <p class="hero-lead">The short version: our apps do not track you, do not show ads, and do not sell your data. Where an app syncs or backs up, it uses your own private iCloud account \u2014 never a server owned by us or by anyone else. The full policy for each app is below.</p>
    </div>
  </header>

  <section class="features">
    <div class="wrap">
      <div class="sec-head">
        <p class="eyebrow">Legal</p>
        <h2>App privacy policies</h2>
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
      <div class="btn-row" style="margin-top:1.7rem;">
        <a class="btn btn-dark" href="/apps.html">See the apps <span class="a">&rarr;</span></a>
        <a class="btn btn-ghost" href="/">Home <span class="a">&rarr;</span></a>
      </div>
    </div>
  </header>
"""
nf += footer(APPS)
W("404.html", nf)

# ── sitemap.xml + robots.txt ─────────────────────────────────────────────
urls = [(SITE+"/", "1.0"), (SITE+"/apps.html", "0.9"), (SITE+"/finance.html", "0.7"),
        (SITE+"/privacy.html", "0.3"), (SITE+"/contact.html", "0.5")]
urls += [(f"{SITE}/apps/{a['slug']}/", "0.8") for a in APPS]
urls += [(SITE+p, "0.2") for _, p in PRIV]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u, pr in urls:
    sm += f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <priority>{pr}</priority>\n  </url>\n"
sm += "</urlset>\n"
W("sitemap.xml", sm)
W("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
print(f"\nsitemap: {len(urls)} URLs")
