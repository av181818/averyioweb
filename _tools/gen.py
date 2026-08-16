#!/usr/bin/env python3
"""Generate averyio app pages + site chrome. Emits plain static HTML."""
import os, re, json, html

# Repo root, derived from this file's location so the scripts work on any
# machine and no local path is baked into the repo.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _css_version():
    """Short content hash of site.css.

    GitHub Pages serves assets with cache-control: max-age=600 and the
    stylesheet URL never changed, so a browser could hold an old site.css
    while loading new HTML — which silently unstyles anything whose markup
    changed. Versioning the URL keeps the two in lockstep: change the CSS,
    get a new URL, fetch immediately. Unchanged CSS keeps its URL and stays
    cached."""
    import hashlib
    css = open(os.path.join(ROOT, "assets", "site.css"), "rb").read()
    return hashlib.sha256(css).hexdigest()[:8]

CSS_V = _css_version()
SITE = "https://averyio.net"

# ── shared chrome ────────────────────────────────────────────────────────
def head(title, desc, canonical, og_image="/assets/og-image.png", extra=""):
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta name="description" content="{desc}" />
  <link rel="canonical" href="{canonical}" />
  <meta property="og:type" content="website" />
  <meta property="og:site_name" content="averyio" />
  <meta property="og:locale" content="en_GB" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:image" content="{SITE}{og_image}" />
  <meta property="og:url" content="{canonical}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:site" content="@averyio18" />
  <meta name="twitter:image" content="{SITE}{og_image}" />
  <link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png" />
  <link rel="icon" type="image/png" sizes="16x16" href="/assets/favicon-16.png" />
  <link rel="apple-touch-icon" href="/assets/apple-touch-icon.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="/assets/site.css?v={CSS_V}" />
{extra}</head>
<body>
"""

HOME_SVG = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5 12 3l9 7.5"/>'
            '<path d="M5 9.5V20a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V9.5"/></svg>')

APPLE_SVG = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17.05 12.53c-.02-2.2 1.8-3.26 1.88-3.31'
             '-1.02-1.5-2.62-1.7-3.19-1.72-1.36-.14-2.65.8-3.34.8-.69 0-1.75-.78-2.87-.76-1.48.02-2.84.86-3.6 2.18'
             '-1.53 2.66-.39 6.6 1.1 8.76.73 1.06 1.6 2.25 2.74 2.21 1.1-.04 1.52-.71 2.85-.71 1.33 0 1.71.71 2.87.69'
             '1.18-.02 1.93-1.08 2.65-2.14.84-1.23 1.18-2.42 1.2-2.48-.03-.01-2.3-.88-2.32-3.5zM14.88 5.9'
             'c.6-.73 1.01-1.75.9-2.76-.87.04-1.93.58-2.55 1.31-.56.65-1.05 1.69-.92 2.68.97.08 1.96-.49 2.57-1.23z"/></svg>')

X_SVG = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17'
         'l-4.714-6.231-5.401 6.231H2.747l7.73-8.835L1.254 2.25H8.08l4.259 5.63 5.905-5.63Zm-1.161 17.52h1.833'
         'L7.084 4.126H5.117z"/></svg>')

def nav(active=""):
    def cls(k, base=""):
        c = (base + (" active" if active == k else "")).strip()
        return f' class="{c}"' if c else ""
    return f"""  <nav>
    <div class="wrap nav-inner">
      <a class="nav-logo" href="/"><img src="/assets/logo-64.png" alt="" width="26" height="26" decoding="async" />averyio<span>.net</span></a>
      <div class="nav-links">
        <a href="/" aria-label="Home" class="nav-home{' active' if active=='home' else ''}">{HOME_SVG}</a>
        <a href="/apps.html"{cls('apps')}>Apps</a>
        <a href="/finance.html"{cls('finance')}>Finance</a>
        <a href="/privacy.html"{cls('privacy')}>Privacy</a>
        <a class="nav-cta{' active' if active=='contact' else ''}" href="/contact.html">Contact</a>
      </div>
    </div>
  </nav>
  <main>
"""

def footer(apps):
    links = "\n".join(
        [f'          <a href="{s["url"]}">{s["name"]}</a>' for s in SITE_APPS] +
        [f'          <a href="/apps/{a["slug"]}/">{a["name"]}</a>' for a in apps])
    return f"""  </main>
  <footer>
    <div class="wrap footer-inner">
      <div class="footer-cols">
        <div class="footer-col">
          <p class="footer-col-head">averyioApps</p>
{links}
        </div>
        <div class="footer-col">
          <p class="footer-col-head">averyio</p>
          <a href="/">Home</a>
          <a href="/apps.html">All apps</a>
          <a href="/finance.html">averyioFinance</a>
          <a href="/contact.html">Contact</a>
          <a href="/privacy.html">Privacy</a>
        </div>
      </div>
      <span>&copy; 2026 averyio</span>
    </div>
  </footer>

</body>
</html>
"""

def crumb(trail):
    parts = []
    for i, (label, href) in enumerate(trail):
        if href:
            parts.append(f'<a href="{href}">{label}</a>')
        else:
            parts.append(f'<span aria-current="page">{label}</span>')
        if i < len(trail) - 1:
            parts.append('<span class="sep">/</span>')
    return ('  <div class="wrap crumb">\n    ' + "\n    ".join(parts) + "\n  </div>\n")

def ld(obj):
    return ('  <script type="application/ld+json">\n'
            + json.dumps(obj, indent=2) + "\n  </script>\n")

# ── icons for feature blocks ─────────────────────────────────────────────
ICO = {
 "bolt":   '<path d="M13 2 4.5 13.5H11l-1 8.5 8.5-11.5H12l1-8.5Z"/>',
 "clock":  '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
 "shield": '<path d="M12 3 5 6v5.5c0 4.3 3 8.2 7 9.5 4-1.3 7-5.2 7-9.5V6l-7-3Z"/>',
 "chart":  '<path d="M3 17l5-5 4 3 7-8"/><path d="M16 4h5v5"/>',
 "book":   '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H19v15H6.5A2.5 2.5 0 0 0 4 20.5V5.5Z"/><path d="M19 18v3H6.5"/>',
 "check":  '<path d="M20 6 9 17l-5-5"/>',
 "star":   '<path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6-5.4-2.8-5.4 2.8 1-6L3.2 9.4l6.1-.9L12 3Z"/>',
 "phone":  '<rect x="6" y="2" width="12" height="20" rx="2.5"/><path d="M11 18.5h2"/>',
 "target": '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r="1"/>',
 "flame":  '<path d="M12 3c3 3.5 5.5 5.8 5.5 9.5A5.5 5.5 0 0 1 6.5 13C6.5 9 9 8 12 3Z"/>',
 "cloud":  '<path d="M7 18h10a3.5 3.5 0 0 0 .3-7A5.5 5.5 0 0 0 6.6 10 3.9 3.9 0 0 0 7 18Z"/>',
 "grid":   '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
 "eye":    '<path d="M2 12s3.5-6.5 10-6.5S22 12 22 12s-3.5 6.5-10 6.5S2 12 2 12Z"/><circle cx="12" cy="12" r="2.5"/>',
 "sun":    '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4"/>',
 "trophy": '<path d="M7 4h10v5a5 5 0 0 1-10 0V4Z"/><path d="M7 6H4v1a3 3 0 0 0 3 3M17 6h3v1a3 3 0 0 1-3 3M9 20h6M12 14v6"/>',
 "coin":   '<circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9.8c0-1.1 1.1-1.8 2.5-1.8s2.5.7 2.5 1.8-1.1 1.6-2.5 1.9-2.5.8-2.5 1.9 1.1 1.8 2.5 1.8 2.5-.7 2.5-1.8"/>',
}
def ico(k):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICO[k]}</svg>')

# ── app data ─────────────────────────────────────────────────────────────
APPS = [
{
 "slug":"investfast", "size":"1.7", "footprint":"Every one of the 144 lessons, the whole course, your progress and your stats — in about 1.7 MB. No ad library, no tracking SDK, nothing taking up room that is not the course itself.", "ios":"18.6", "asset":"investfast", "name":"InvestFast",
 "store_name":"Invest Fast: Stocks & Money",
 "tagline":"Learn to invest in 24 hours.",
 "title":"InvestFast — Learn to Invest in 24 Hours, for Beginners",
 "desc":"Learn to invest in 24 hours. 144 plain-English lessons on stocks, ETFs, index funds and tax. Pay once — no subscription, no ads, no in-app purchases.",
 "lead":"The complete, plain-English investing course for absolute beginners, built into an iPhone and iPad app. Twenty-four modules and 144 ten-minute lessons take you from “what is a stock?” to a personal plan you can run for 40 years — mindset, money, markets, tax and everything in between. Real examples, zero jargon.",
 "appid":"6762561241",
 "store_url":"https://apps.apple.com/gb/app/invest-fast-stocks-money/id6762561241",
 "privacy":"/privacy-investfast.html",
 "category":"EducationalApplication", "genre":"Education",
 "meta":["One-time purchase","iPhone &amp; iPad","iOS 18.6+","~1.7 MB download","Education &amp; Finance","No subscription"],
 "tags":["iOS","Finance"],
 "shots":[
   ("investfast-1","InvestFast lesson screen — go from beginner to confident investor"),
   ("investfast-2","InvestFast curriculum — 24 modules and 144 investing lessons"),
   ("investfast-3","An InvestFast lesson explaining investing in plain English"),
   ("investfast-4","InvestFast progress streaks keeping you on track"),
   ("investfast-5","The InvestFast learning path from zero to your own plan"),
   ("investfast-6","InvestFast lifetime access, no subscription"),
 ],
 "features":[
   ("book","24 modules, 144 lessons","Ten-minute lessons, module by module, from first principles to graduation — a clear path from zero to confident."),
   ("clock","About 24 hours, end to end","Spread it over a week, a weekend, or one determined day. Every lesson ends in an action, not a cliffhanger for the next one."),
   ("chart","Stocks, ETFs and index funds","How stocks, bonds and index funds actually work — plus ETFs, diversification and the maths of compounding."),
   ("eye","Fundamental and technical analysis","How to read a company before you buy it, what charts genuinely tell you, and where they mislead."),
   ("coin","Money first, investing second","Debt, emergency fund and budgeting that sticks, before a penny goes into the market."),
   # Replaces the pricing card removed 2026-08-10. Wording mirrors the App Store
   # listing ("Track your streak, your lessons mastered, and your milestones",
   # "including the 24-Hour Club") per the claim-only-what-the-listing-says rule,
   # and restores the six-card grid every other app page has.
   ("trophy","Learning that sticks","Streaks, daily goals and 16 achievements — including the 24-Hour Club — and every lesson you master is tracked, right through to graduation."),
 ],
 "faq":[
   ("Do I need any investing experience?","None. InvestFast is built for complete beginners — nurses, engineers, freelancers, anyone who found finance intimidating or condescending. It starts at zero and explains every term in plain English."),
   ("How long does it really take?","Roughly 24 hours of focused reading from the first lesson to the last. Most people spread that across a week or two. Your progress is saved, so you can dip in and out."),
   ("Does InvestFast tell me what to buy?","No. It teaches you the mechanics so you can make your own decisions. There are no stock tips, no signals and no “secrets” — and nothing in the app is financial advice."),
   ("Is there a subscription or in-app purchases?","No. InvestFast is a one-time purchase — pay once and all 24 modules, all 144 lessons and every future update are included, forever. No subscriptions, no in-app purchases, no ads."),
   ("Does it track me or sell my data?","No. Your progress never leaves your device — no account, no sign-up, and it works fully offline. Apple's privacy label reads Data Not Collected; see the <a href=\"/privacy-investfast.html\">InvestFast privacy policy</a> for the full detail."),
   ("What devices does it run on?","iPhone and iPad running iOS 18.6 or later. One purchase covers both."),
 ],
},
{
 "slug":"surge", "size":"0.7", "footprint":"The entire timer is under a megabyte — smaller than one photo on your phone. No ads, no account and no data collection, so nothing ships that is not the timer.", "ios":"18.6", "asset":"surge", "name":"Surge",
 "store_name":"Surge: Interval Timer & HIIT",
 "tagline":"An interval timer built for the way you actually train.",
 "title":"Surge — Interval Timer & HIIT App for iPhone & iPad",
 "desc":"A HIIT and interval timer for iPhone and iPad with Tabata, Boxing and EMOM presets built in. Audio cues, haptics, no ads — pay once, yours for life.",
 "lead":"Surge is an interval timer for HIIT, Tabata, boxing rounds, EMOM and any circuit-style workout — at home, in the gym or ringside. Set your work and rest, pick your rounds and press play — Surge calls every phase with beeps and haptics, so you train bell to bell without watching the clock.",
 "appid":"6762224044",
 "store_url":"https://apps.apple.com/gb/app/surge-interval-timer-hiit/id6762224044",
 "privacy":"/privacy-surge.html",
 "category":"HealthApplication", "genre":"Health &amp; Fitness",
 "meta":["One-time purchase","iPhone &amp; iPad","iOS 18.6+","~0.7 MB download","Health &amp; Fitness","No subscription"],
 "tags":["iOS","Fitness"],
 "shots":[
   ("surge-1","Surge interval timer running a timed round with a progress ring"),
   ("surge-2","Surge preset list — Tabata, HIIT, Boxing, EMOM and Circuit, ready in one tap"),
   ("surge-3","A completed workout in Surge — pay once, every feature included"),
   ("surge-4","Customising work time, rest time and rounds in Surge"),
   ("surge-5","Surge running hands-free with a large glanceable countdown"),
   ("surge-6","Surge audio cues and haptic feedback settings"),
 ],
 "features":[
   ("bolt","Rounds ready to go","Tabata 20/10 × 8, HIIT 40/20 × 10, Boxing 3:00/1:00 × 6, EMOM 60s × 10 and Stretch 30/10 × 12 — all built in, and every one editable to match your training."),
   ("clock","Your workout, your rules","Work from 5 seconds to 10 minutes, rest up to 5 minutes, 1–50 rounds with an optional preparation countdown — and save up to 20 presets with custom names and icons."),
   ("phone","Built to be glanceable","A dark interface with a large, glanceable countdown display and an animated progress ring."),
   ("check","Cues you don’t have to look for","Audio countdown beeps and haptic feedback on every phase change, so you can keep your eyes off the screen."),
   ("sun","The screen stays awake","Skip a phase mid-workout, and the screen stays lit to the final bell — no lock-outs halfway through a round."),
   ("shield","Nothing to sign up for","No account, no ads, no data collection. Your presets stay on your device."),
 ],
 "faq":[
   ("What workouts does it suit?","Anything on a clock — HIIT, Tabata, CrossFit-style WODs, boxing and MMA rounds, EMOM, circuit training, jump rope intervals, strength work with timed rest, and yoga or stretching flows."),
     ("Does the screen stay on?","Yes. The screen stays awake during workouts, so you never lose the count mid-round."),
   ("Is there a subscription or in-app purchases?","No. Surge is a one-time purchase — pay once and every preset and feature is included, forever. No subscriptions, no in-app purchases, no ads."),
   ("Does Surge collect my data?","No. There is no account, no tracking and no ads, and your presets never leave your device. The full detail is in the <a href=\"/privacy-surge.html\">Surge privacy policy</a>."),
   ("Does it work on iPad?","Yes — Surge is universal. One app, one purchase, iPhone and iPad."),
 ],
},
{
 "slug":"big-time-clock", "size":"0.4", "footprint":"It is a clock. It should be tiny, and it is — about 0.4 MB, one of the smallest things we have shipped. Small enough to leave on a decade-old iPhone you have repurposed as a bedside display without a second thought.", "ios":"18.6", "asset":"bigtimeclock", "name":"Big Time Clock",
 "store_name":"Big Time Clock: Full Screen",
 "tagline":"Turn any iPhone or iPad into a full-screen clock.",
 "title":"Big Time Clock — Full Screen Clock for iPhone & iPad",
 "desc":"Turn an iPhone or iPad into a full-screen digital or analog clock. 12/24-hour, the screen stays awake, no ads — pay once, yours for life.",
 "lead":"A clean black canvas, crisp numerals, and nothing else competing for your attention — ideal for a bedside table, a desk, the kitchen counter or a studio wall. It is the perfect second life for an older iPhone or iPad.",
 "appid":"6763140176",
 "store_url":"https://apps.apple.com/gb/app/big-time-clock-full-screen/id6763140176",
 "privacy":"/privacy-bigtimeclock.html",
 "category":"UtilitiesApplication", "genre":"Utilities",
 "meta":["One-time purchase","iPhone &amp; iPad","iOS 18.6+","~0.4 MB download","Utilities","No subscription"],
 "tags":["iOS","Utilities"],
 "shots":[
   ("bigtimeclock-1","Big Time Clock showing the time full screen in large white numerals"),
   ("bigtimeclock-2","The Big Time Clock analog face with a sweeping red second hand"),
   ("bigtimeclock-3","Light and bold typography options in Big Time Clock"),
   ("bigtimeclock-4","Big Time Clock settings revealed with a single tap"),
   ("bigtimeclock-5","Big Time Clock in 24-hour format at full size"),
   ("bigtimeclock-6","Big Time Clock keeping the screen awake overnight on a bedside table"),
 ],
 "features":[
   ("clock","Digital or analog","A full-screen digital clock with massive numerals, or an elegant analog face with a smoothly sweeping red second hand."),
   ("phone","Portrait and landscape","Rotate the device and the layout adapts — upright in a dock, on its side in a stand."),
   ("sun","Made for night","A deep-black background that sits right on OLED displays and cuts glare in a dark bedroom."),
   ("grid","Your format, your type","12-hour or 24-hour time with seconds, light or bold typography, and a day and date display you can switch off."),
   ("eye","Auto-hiding controls","One tap reveals the controls, another hides them. No menus, no settings pages, no account."),
   ("shield","No tracking, ever","No ads, no accounts, no data collection — it never even touches the network. Just a clock that does its job."),
 ],
 "faq":[
   ("Will the screen turn off while I am using it?","No. Big Time Clock keeps the display awake for as long as the clock is on screen, so it works as a proper bedside or desk clock."),
   ("Can I use an old iPhone or iPad as a dedicated clock?","That is one of the best uses for it. Plug an older device into a charger, put it in a stand, and it becomes a permanent nightstand, kitchen or studio clock."),
   ("Does it support 24-hour time?","Yes — switch between 12-hour and 24-hour format, and toggle the day and date display on or off."),
   ("Is there an analog clock as well?","Yes, both faces are built in. Like the digital clock, the analog face works in portrait and landscape."),
   ("Is there a subscription or in-app purchases?","No. Big Time Clock is a one-time purchase — pay once and both clock faces and every feature are included, forever. No subscriptions, no in-app purchases, no advertising."),
   ("Does it collect any data?","No tracking, no ads, no data collection. Read the <a href=\"/privacy-bigtimeclock.html\">Big Time Clock privacy policy</a> for the full statement."),
 ],
},
{
 "slug":"lume", "size":"1.6", "footprint":"A full task manager, 12 ranks of progression, a stats dashboard and a 180-day heatmap, all inside about 1.6 MB. No analytics SDK, no ad library and no account system — so none of that weight ever ships to your phone.", "ios":"17.0", "asset":"lume", "name":"Lume",
 "store_name":"Lume: Simple Task & To Do List",
 "tagline":"A to-do list you actually want to open.",
 "title":"Lume — Gamified To-Do List & Task Manager for iPhone",
 "desc":"A gamified to-do list for iPhone and iPad. Earn points, climb 12 ranks, keep a streak alive. iCloud sync, no ads, no account — pay once, yours for life.",
 "lead":"Every task you finish earns points, beating a due date earns a bonus, and a daily streak keeps the momentum going. It is a real task manager first and a game second — fast to capture, sorted by what is actually due next.",
 "appid":"6770331131",
 "store_url":"https://apps.apple.com/gb/app/lume-simple-task-to-do-list/id6770331131",
 "privacy":"/privacy-lume.html",
 "category":"BusinessApplication", "genre":"Productivity",
 "meta":["One-time purchase","iPhone &amp; iPad","iOS 17+","~1.6 MB download","Productivity","iCloud sync included"],
 "tags":["iOS","Productivity"],
 "shots":[
   ("lume-1","Lume task list showing points earned for every completed task"),
   ("lume-2","Lume rank progression from Spark to Cosmos"),
   ("lume-3","Lume categories — pay once, no subscriptions, no ads"),
   ("lume-4","The Lume stats dashboard with a 180-day activity heatmap"),
   ("lume-5","How points work in Lume — early, on-time and late finishes all scored"),
   ("lume-6","Earning bonus points in Lume for beating a due date"),
 ],
 "features":[
   ("star","Points for finishing real work","Points come only from completing genuine tasks on time. Nothing you can set yourself changes your score, so it cannot be gamed."),
   ("trophy","12 ranks, 5 stars each","Climb a long-term ladder from Spark all the way to Cosmos, so the work you deliver adds up to something visible."),
   ("flame","Streaks that respect you","Keep a daily streak alive with a built-in grace day for the one you miss — and no guilt-trip notifications, ever."),
   ("check","A proper task manager","A title and a due date is all a task needs. Low and high priority, optional categories, an Overdue / Today / Coming up view sorted by due date, and an optional morning brief of what is due."),
   ("chart","A real stats dashboard","Completion quality, personal records and a 180-day activity heatmap that shows the shape of your habits — every bit of it included."),
   ("cloud","iCloud sync, always on","Your tasks stay in step across iPhone and iPad with no setup and no account to create. It is your iCloud, not our server — we cannot see any of it."),
 ],
 "faq":[
   ("What makes Lume different from other to-do apps?","The scoring. Your score reflects work you actually finished on time, so it is progress you can trust rather than a number you can inflate. Finish early and you are rewarded; finish late and you still score, just for less."),
   ("Do I need an account?","No. There is no sign-up. iCloud sync uses your own iCloud account automatically, so your tasks follow you across devices with nothing to configure."),
   ("What happens if I miss a day?","One missed day is forgiven by the built-in grace day, so a single bad day does not wipe out a long streak. Lume also never sends guilt-inducing notifications."),
   ("Is there a subscription or in-app purchases?","No. Lume is a one-time purchase — pay once and everything is included, forever: unlimited tasks and categories, iCloud sync and every future update. No subscriptions, no in-app purchases, no ads."),
   ("Does Lume collect my data?","No. Lume collects nothing — no analytics, no tracking, no ads and no account. Syncing happens inside your own iCloud, which we have no ability to read. See the <a href=\"/privacy-lume.html\">Lume privacy policy</a>."),
   ("Does it work on iPad?","Yes. Lume is designed for iPhone and iPad and stays in step across both through iCloud."),
 ],
},
{
 "slug":"tap-dot-tap", "size":"1.2", "footprint":"The whole game, every neon skin and the leaderboard come to about 1.2 MB. Nothing ships that is not the game itself.", "ios":"17.0", "asset":"tapdottap", "name":"Tap Dot Tap",
 "store_name":"Tap Dot Tap: Neon Speed Test",
 "tagline":"A dot appears. Tap it before it vanishes.",
 "title":"Tap Dot Tap — Reaction Time & Reflex Game for iPhone",
 "desc":"A one-tap reflex and reaction time game for iPhone. Tap the dot before it vanishes — one miss ends the run. Pay once — every skin included, offline, no ads.",
 "lead":"A one-tap reflex game that puts your reaction time on trial. Miss a single one and the run is over. Simple to learn and ruthless to master, because the targets keep shrinking and speeding up the longer you last.",
 "appid":"6778353191",
 "store_url":"https://apps.apple.com/gb/app/tap-dot-tap-neon-speed-test/id6778353191",
 "privacy":"/privacy-tapdottap.html",
 "category":"GameApplication", "genre":"Games",
 "meta":["One-time purchase","iPhone","iOS 17+","~1.2 MB download","Games · Casual","Plays offline"],
 "tags":["iOS","Game"],
 "shots":[
   ("tapdottap-1","Tap Dot Tap gameplay — tap the neon dot before it vanishes"),
   ("tapdottap-2","The Tap Dot Tap menu — pay once, play forever, no ads"),
   ("tapdottap-3","Dots getting smaller and faster as a Tap Dot Tap run climbs"),
   ("tapdottap-4","Game over in Tap Dot Tap — one miss ends the run"),
   ("tapdottap-5","The Tap Dot Tap global leaderboard powered by Game Center"),
   ("tapdottap-6","The five neon dot skins in Tap Dot Tap, every one included"),
 ],
 "features":[
   ("target","One tap to learn","Controls anyone can pick up in seconds, and a difficulty curve that climbs in waves — relentless, but always fair."),
   ("bolt","Under a second to react","Dots shrink, accelerate and land further apart the longer you last, until every single tap counts."),
   ("trophy","Global Game Center leaderboards","Today, this week and all-time boards. See your world rank, take on friends, and chase down your personal best."),
   ("star","Five neon skins","Aqua, Magma, Emerald, Sunset and Gold — all included from your first run. Nothing to unlock, nothing extra to buy."),
   ("phone","Plays offline","No connection needed. The leaderboard is opt-in, and nothing is shared until you say so."),
   ("shield","No ads, no sign-up","No advertising, no account and no tracking — your score stays on your device unless you opt in to the leaderboard. Just satisfying haptics and buttery-smooth neon visuals."),
 ],
 "faq":[
   ("How does the game work?","One target at a time, and under a second to reach it. Survive and the difficulty climbs in waves; miss once and that is the run over."),
   ("Are there leaderboards?","Yes, powered by Game Center, and entirely opt-in — you can play forever without ever appearing on one."),
   ("Can I play without an internet connection?","Yes. Tap Dot Tap plays fully offline; only the optional leaderboard needs a connection."),
   ("Is it suitable for children?","Yes, it is rated 4+. There are no ads, no chat and no sign-up."),
   ("Is there a subscription or in-app purchases?","No. Tap Dot Tap is a one-time purchase — pay once and every feature and every skin is included, forever. No subscriptions, no in-app purchases, no ads."),
   ("Does it collect any data?","No account, no sign-up and no tracking. Nothing is shared unless you opt into the leaderboard. See the <a href=\"/privacy-tapdottap.html\">Tap Dot Tap privacy policy</a>."),
 ],
},
]

# ── apps hosted on averyio.net but outside the /apps/<slug>/ system ──────
# These ship as their own self-contained page (own CSS, own JS, own visual
# identity) rather than as an App Store listing with a generated marketing
# page. They still need a tile on apps.html, a footer link and a sitemap
# entry — declare them HERE rather than hand-editing the generated HTML,
# which the generators overwrite. That is exactly how the Centre Circle
# Finder card was silently lost once already.
#
# Do not restyle these pages to the site theme: they keep their own identity
# on purpose (owner directive 2026-08-09), the same way each App Store app
# keeps its own.
SITE_APPS = [
{
 "name": "Centre Circle Finder",
 "url": "/centre-circle-finder/",
 "asset": "centre-circle-finder",
 # 5:4 crop of the poster, centred on the wordmark and the stats. The full
 # poster puts its content in the lower half, so the stage's top-crop showed
 # nothing but pitch texture — see `tile` in gen_site.py's stage_html().
 "tile": ("centre-circle-finder-tile",
          "Centre Circle Finder — 597 UK football grounds across 31 leagues"),
 "desc": ("Every professional and semi-professional football ground in the UK "
          "&mdash; 597 grounds across 31 leagues, on one map."),
 "tags": ["Web", "Football"],
  "priority": "0.8",
},
{
 # Moved out of APPS on 2026-08-09. It had a generated /apps/btc-prix/
 # marketing page, so the tile led to a description page and only then to
 # the app — a middle layer the owner asked to remove. The tile now goes
 # straight to the app. The old URL still resolves via REDIRECTS below.
 "name": "BTCPRIX",
 "url": "/btc-prix/",
 "asset": None,          # no App Store icon — falls back to the ₿ monogram
 "mono": "₿",
 "tile": ("btcprix-tile", "BTCPRIX — the live Bitcoin price on the web"),
 "desc": "Real-time Bitcoin price tracking on the web.",
 "tags": ["Web", "Crypto"],
  "priority": "0.7",
},
]

# ── retired URLs ─────────────────────────────────────────────────────────
# GitHub Pages cannot issue a 301, so a page that moves leaves a meta-refresh
# stub behind: the old URL keeps working for anyone who has it, and the
# canonical consolidates its ranking onto the destination. Deleting the file
# outright would 404 a URL that is indexed and linked from the sitemap.
REDIRECTS = [("apps/btc-prix/index.html", "/btc-prix/", "BTCPRIX")]

ETHOS = [
 ("No bloat","Megabytes, not gigabytes. No frameworks bolted on, no ad libraries, no analytics SDK phoning home — nothing ships that has not earned its place."),
 ("No subscriptions","One upfront price where an app charges at all — no monthly fee, no in-app purchases, nothing that quietly renews. What you buy is yours to keep."),
 ("No ads, ever","Not a banner, not an interstitial, not a “watch this to continue”. You are the customer, never the product."),
 ("Private by design","No analytics, nothing sold. Your data lives on your device — and where an app syncs or backs up, it goes through your own private iCloud account, never a server of ours or anyone else's."),
]

def ethos_section(heading):
    """The four rules. Rendered identically wherever it appears, on the
    tinted ground so it separates the sections either side of it."""
    items = "\n".join(
        f"""        <div class="ethos-item">
          <span class="ethos-num">{i:02d}</span>
          <h3>{t}</h3>
          <p>{d}</p>
        </div>""" for i, (t, d) in enumerate(ETHOS, 1))
    return f"""
  <section class="sec sec-tint">
    <div class="wrap">
      <div class="sec-head">
        <p class="eyebrow">The promise</p>
        <h2>{heading}</h2>
      </div>
      <div class="ethos-grid">
{items}
      </div>
    </div>
  </section>
"""

# ── app page renderer ────────────────────────────────────────────────────
def store_btn(app, dark=True):
    if app["appid"]:
        return (f'<a class="btn {"btn-dark" if dark else "btn-ghost"} btn-store" href="{app["store_url"]}" '
                f'target="_blank" rel="noopener">{APPLE_SVG}'
                f'<span class="store-copy"><span class="store-sm">Download on the</span>'
                f'<span class="store-lg">App Store</span></span></a>')
    # A hosted app lives on this domain now, so it opens in the same tab —
    # target="_blank" is for leaving the site, and this no longer does.
    href = app.get("hosted") or app["store_url"]
    ext = "" if app.get("hosted") else ' target="_blank" rel="noopener"'
    return (f'<a class="btn {"btn-dark" if dark else "btn-ghost"}" href="{href}"{ext}>'
            f'Open {app["name"]} <span class="a">&rarr;</span></a>')

def app_page(app, apps):
    url = f"{SITE}/apps/{app['slug']}/"
    icon = f"/assets/apps/{app['asset']}-icon.webp" if app["asset"] else "/assets/logo-256.png"
    icon2x = f"/assets/apps/{app['asset']}-icon@2x.webp" if app["asset"] else "/assets/logo-256.png"
    # Every APPS entry has an App Store icon. The monogram fallback went with
    # BTCPRIX when it moved to SITE_APPS, and its `.mono-tile-lg` rule was
    # deleted as dead CSS — so an assetless app here would render unstyled.
    if not app["asset"]:
        raise SystemExit(f"{app['name']}: /apps/<slug>/ pages need an 'asset' icon.")
    hero_icon = (f'<img class="app-icon-lg" src="{icon2x}" '
                 f'alt="{app["name"]} app icon" width="92" height="92" />')

    sw = {
      "@context":"https://schema.org", "@type":"SoftwareApplication",
      "name": app["store_name"], "alternateName": app["name"],
      "applicationCategory": app["category"],
      "operatingSystem": f"iOS {app['ios']} or later" if app["ios"] else "Any web browser",
      "description": html.unescape(app["desc"]),
      "url": url,
      "installUrl": (SITE + app["hosted"]) if app.get("hosted") else app["store_url"],
      "image": f"{SITE}{icon2x}",
      "publisher": {"@type":"Organization","name":"averyio","url":SITE+"/"},
    }
    bc = {
      "@context":"https://schema.org","@type":"BreadcrumbList",
      "itemListElement":[
        {"@type":"ListItem","position":1,"name":"Home","item":SITE+"/"},
        {"@type":"ListItem","position":2,"name":"averyioApps","item":SITE+"/apps.html"},
        {"@type":"ListItem","position":3,"name":app["name"],"item":url},
      ]}
    faq = {
      "@context":"https://schema.org","@type":"FAQPage",
      "mainEntity":[{"@type":"Question","name":html.unescape(q),
                     "acceptedAnswer":{"@type":"Answer",
                     "text":html.unescape(re.sub(r"<[^>]+>", "", a))}}
                    for q,a in app["faq"]]}

    out = head(app["title"], app["desc"], url,
               og_image=f"/assets/apps/{app['asset']}-1.webp" if app["asset"] else "/assets/og-image.png",
               extra=ld(sw)+ld(bc)+ld(faq))
    out += nav("apps")
    out += crumb([("Home","/"),("averyioApps","/apps.html"),(app["name"],None)])

    # hero
    out += f"""
  <header class="app-hero">
    <div class="wrap">
      {hero_icon}
      <h1>{app['name']}<span class="accent">.</span></h1>
      <p class="app-tagline">{app['tagline']}</p>
      <p class="app-lead">{app['lead']}</p>
      <div class="app-meta">
        {"".join(f"<span>{m}</span>" for m in app['meta'])}
      </div>
      <div class="btn-row">
        {store_btn(app)}
      </div>
      {f'<p class="app-note"><a href="{app["privacy"]}">Privacy policy</a></p>' if app['privacy'] else ''}
    </div>
  </header>
"""
    # screenshots
    if app["shots"]:
        imgs = "\n".join(
            f'        <img src="/assets/apps/{n}.webp" srcset="/assets/apps/{n}-sm.webp 320w, /assets/apps/{n}.webp 640w" '
            f'sizes="(max-width: 640px) 60vw, 244px" alt="{alt}" width="640" height="1387" loading="lazy" decoding="async" />'
            for n, alt in app["shots"])
        out += f"""
  <section class="shots" aria-label="{app['name']} screenshots">
    <div class="wrap">
      <div class="shots-scroll">
{imgs}
      </div>
    </div>
  </section>
"""
    # footprint — the "no bloat" stat, straight from the App Store size
    stat = (f'<div class="footprint-num"><span class="approx">~</span>{app["size"]}<span class="unit">MB</span></div>'
            f'<p class="footprint-label">Download size</p>') if app["size"] else (
            '<div class="footprint-num">0<span class="unit">KB</span></div>'
            '<p class="footprint-label">To install</p>')
    out += f"""
  <section class="sec sec-white" id="footprint">
    <div class="wrap">
      <div class="footprint-inner">
        <div>
          {stat}
        </div>
        <div class="footprint-copy">
          <h2>No bloat, and we mean it literally</h2>
          <p>{app['footprint']}</p>
        </div>
      </div>
    </div>
  </section>
"""

    # features
    feats = "\n".join(
        f"""        <div class="feature">
          <div class="feature-ico">{ico(k)}</div>
          <h3>{t}</h3>
          <p>{d}</p>
        </div>""" for k, t, d in app["features"])
    out += f"""
  <section class="sec">
    <div class="wrap">
      <div class="sec-head">
        <p class="eyebrow">Features</p>
        <h2>What {app['name']} does</h2>
      </div>
      <div class="feature-grid">
{feats}
      </div>
    </div>
  </section>
"""
    out += ethos_section("How every averyio app works")

    # faq
    qs = "\n".join(
        f"""        <div class="faq-item">
          <h3>{q}</h3>
          <p>{a}</p>
        </div>""" for q, a in app["faq"])
    out += f"""
  <section class="sec">
    <div class="wrap">
      <div class="sec-head">
        <p class="eyebrow">FAQ</p>
        <h2>{app['name']} questions, answered</h2>
      </div>
      <div class="faq-list">
{qs}
      </div>
    </div>
  </section>
"""
    # closing cta
    out += f"""
  <section class="cta-band">
    <div class="wrap">
      <div class="cta-inner">
        <h2>Get {app['name']}</h2>
        <p>Pay once and it&rsquo;s yours — no ads, no subscriptions. The same promise behind every averyio app.</p>
        <div class="btn-row">
          {store_btn(app, dark=False)}
          <a class="btn btn-ghost" href="/apps.html">All averyio apps <span class="a">&rarr;</span></a>
        </div>
      </div>
    </div>
  </section>
"""
    out += footer(apps)
    return out

# ── write app pages ──────────────────────────────────────────────────────
written = []
for a in APPS:
    d = os.path.join(ROOT, "apps", a["slug"])
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "index.html")
    open(p, "w", encoding="utf-8").write(app_page(a, APPS))
    written.append((f"apps/{a['slug']}/index.html", os.path.getsize(p)))

for path, size in written:
    print(f"  {path:34s} {size//1024}KB")
print(f"\n{len(written)} app pages written")
json.dump([{k: v for k, v in a.items() if k in
            ("slug","name","store_name","tagline","desc","asset","tags","store_url","genre")}
           for a in APPS], open("apps-data.json","w"), indent=1)
