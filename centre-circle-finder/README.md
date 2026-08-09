# Centre Circle Finder — UK Football Ground Explorer

An interactive ground finder and trip planner covering every professional and
semi-professional football ground in the United Kingdom — **597 clubs across
31 leagues** for the **2026–27 season**, from the Premier League down to step 4
of the English National League System, the Scottish Highland & Lowland
Leagues, Cymru North/South and the NIFL Championship. Pick a city, see every
ground you could reach, choose your match.

## Design: "matchday programme"

The interface deliberately doesn't look like a SaaS dashboard. It borrows
football's own print culture instead:

- **Condensed uppercase type** (Barlow Condensed) for every heading, label and
  numeral — programme covers, kit numbers and stadium signage — with Inter
  carrying the body text.
- **Sharp geometry.** Corner radii are 2–9px, not 12–20px: programmes, kits and
  pitch markings are rectilinear. Rounding is reserved for the ball itself.
- **Ink on warm paper** (`#0e1512` on `#fbfaf7`) by day, floodlit black by
  night, with a newsprint grain over the panel and one decisive green accent.
  Large soft gradients were removed — they were what made it feel generic.
- **Numbered sections** (`01 / 02 / 03`) rendered from a CSS counter, like a
  contents page.
- **A masthead** in solid black with faint kit stripes, a floodlight bloom and a
  green touchline rule beneath it; stats sit under a hairline as a fixture strip.
- **Club cards as team sheets** — a jersey-number badge, the club name in big
  condensed caps on a black band, and a stat grid whose rules are 1px gaps
  showing the background through, so lines appear only between real neighbours.
- **Structural motifs**: mown stripes, pitch lines and a centre-circle arc on the
  "Kick off here" card, a corner-flag place marker, and every ground drawn as a
  football.
- **Small print sits under the masthead**, not in a footer — a two-line strip
  above the search box. It is sized to wrap to exactly two lines (10px, with
  `hyphens: auto`, because the text packs to ~1.9 lines and a ragged right edge
  otherwise tips it onto a third), which costs 41px instead of the old footer's
  ~60px and frees the bottom of the panel entirely.

Built as a dependency-free static site: plain HTML/CSS/JS with
[MapLibre GL](https://maplibre.org) rendering
[OpenFreeMap](https://openfreemap.org) vector tiles — free at any scale, no
key, commercial use allowed — and geocoding by Nominatim. The branded light
and dark "duotone" basemaps are generated at runtime by recolouring
OpenFreeMap's Positron style, so the club dots stay the only saturated colour
on screen. No build step, no API keys.

Brand greens follow **FotMob's palette**, read straight off their site's CSS
variables: `#00985f` (`--color-fotMobGreen`), `#33c771` (`--color-ufoGreen`)
and `#61df6e` (`--color-accentGreen`).

They're applied with contrast measured rather than assumed. `#00985f` is
3.7:1 on white — right for a marker, too light for small text, so text-weight
green is `#00744a` (5.6:1 on the panel) and dark mode takes FotMob's own accent
`#61df6e` (10.7:1). Markers are the brand green by day (3.5:1 on the basemap)
and `#33c771` at night (8.1:1).

Text sitting *on* a green fill flips with the theme, via `--on-green`: white on
the dark light-mode green is 5.8:1, but white on dark mode's bright `#33c771`
is only **2.2:1**, so there the same buttons take near-black text (8.7:1).
Greys are measured too — `--muted` is `#68716b` (4.8:1) in light and `#8b968f`
(6.0:1) in dark.

## Run it

Open `index.html` directly in a browser, or serve the folder (nicer URLs, no
quirks):

```bash
python3 serve.py
```

then visit <http://localhost:8123> — or `http://<your-LAN-ip>:8123` from a
phone on the same Wi-Fi.

Use `serve.py` rather than `python3 -m http.server`. The built-in server sends
no cache headers, and because the `?v=N` cache-buster on the CSS and JS lives
*inside* `index.html`, a browser holding a stale index keeps requesting stale
assets — you end up looking at a build from several edits ago. `serve.py` is
the same static server with `Cache-Control: no-store` on every response.

## Deploying

This lives inside the **averyio.net** site repo (`av181818/averyioweb`) as a
top-level folder, and publishes with the rest of the site via GitHub Pages:

```bash
git add centre-circle-finder && git commit -m "..." && git push
```

Live at `https://averyio.net/centre-circle-finder/` a minute or so later.

It sits in the site repo rather than a repo of its own for one reason: a
GitHub Pages custom domain attaches to a single repository, so anything hosted
separately would publish to `<user>.github.io/...` and inherit none of
averyio.net's search authority. Being a folder on the main domain is what makes
the SEO work.

To work on it without touching the rest of the site, open an editor or a Claude
Code session **scoped to this folder** — it is entirely self-contained, with no
shared CSS, JS or build step. `python3 serve.py` runs it locally on :8123.
Commit with an explicit path (`git add centre-circle-finder`) so unrelated
changes elsewhere in the site can't ride along.

Two things worth knowing:

- **Every internal path is relative** (`css/…`, `js/…`, `data/…`), so the app
  works at any depth with no changes. It does rely on the URL keeping its
  **trailing slash**; Pages redirects to add it.
- **HTTPS is required for "Near me."** `navigator.geolocation` only runs in a
  secure context, which is why it works on `localhost` but not over a
  plain-HTTP LAN address.

Note there is deliberately **no `.nojekyll`** here. It would only take effect at
the site root anyway, and adding one there would publish `_tools/`, which
Jekyll's underscore rule currently keeps private. Nothing in this folder starts
with an underscore, so Jekyll leaves it alone.

## Features## Features

- **One search box for everything** — the omnibox matches clubs, stadium names
  and towns as you type (press `/` to focus, arrow keys to move, Enter to go),
  and always offers "Grounds near *your text*" underneath, which geocodes any
  town, city or **UK postcode**. A hint line under the field spells out what
  you can type, so the postcode option isn't hidden.
- **Two-tab sidebar** — **Explore** holds the whole planning flow in four
  labelled sections (start here → results → popular cities → filter
  grounds → individual leagues), and **Grounds** is the full sortable list.
- **Plan a trip** — tap a **popular-city chip** (each showing its ground
  count), use **Near me**, or roll **Surprise me** for a random ground. You get
  a straight distance-ranked "grounds near X" board with league chips and a
  within-25-miles count. It renders **directly beneath those buttons**, above
  the city chips — so the status line ("Locating…", a permissions error) and
  the results appear where you just tapped, not further down the panel.
- **Club cards** — a team-sheet card: click any dot for stadium, town, capacity
  and status (with the pyramid level inline), plus
  **Directions** (Google Maps) and **Nearby** — which
  re-centres the nearby search on that ground for hopping between matches.
- **League spotlight** — hover any league in the filter list and only those
  grounds stay lit on the map; everything else dims. Pointer-only, so the
  instruction for it is hidden on touch layouts rather than promising something
  a finger can't do; the rows themselves still toggle on tap.
- **Every ground, always visible** — no clustering. All 597 are drawn by a
  single GPU symbol layer, scaled down when you zoom out, so the UK view reads
  as a dot-density map of the football pyramid rather than a handful of
  bubbles. Hovering a league in the sidebar spotlights just those grounds and
  dims the rest, which makes each league's geographic footprint obvious.
- **Compact filters** — two chip rows (nation, tier) with live counts cover
  most queries; all 31 leagues sit behind one disclosure. See *Filters* below.
- **Groundhopper mode** — tick grounds off as you visit them. The **Grounds**
  tab carries a running tally (`9 of 597`), visited grounds are drawn **red**
  against the green ones still to do, and a **Ticked off** filter narrows the
  map to *To visit* or *Visited*. Those filter chips carry colour
  swatches, so they double as the map's key and no legend has to sit over the
  map. **Export / Import** write and read a small versioned `.json` file;
  import *merges* and silently drops any slug that doesn't match a current club.
  The panel states the limitation in plain words rather than burying it —
  saved in this browser only, no account, lost if you clear browsing data or
  switch device, back it up with Export. That warning is deliberately always
  visible rather than behind a disclosure: a data-loss warning nobody opens is
  no warning at all. It is stored under `ccf-visited`
  — no account, no backend — and **Reset never touches it** (it clears the
  filter, not the collection).
  The store is keyed on a slug of the club name rather than the array index,
  because ids are positional and would silently re-point at different clubs the
  moment a season update adds or removes one. All 597 names slug uniquely.
- **Sortable ground list** (A–Z, by league, by capacity) that doubles as the
  accessible table view of the map.
- **Light & dark themes** (auto-detects, toggleable, persisted) — two bespoke
  duotone vector basemaps (ink-on-paper by day, slate-on-navy by night); UI
  and markers switch together.
- **Built for phones** — the panel is a **peeking bottom sheet** with no
  hamburger. At rest it shows the *Centre Circle Finder* bar, the small print and the
  search field; the map keeps everything above. **Tap the bar to raise it, tap
  again to minimise** — it is both the branding and the control, so there is no
  icon to explain. Anything that moves the camera — choosing a search result, a
  ground, a city, Near me — **retracts it automatically**, so the map becomes
  the focus and you see where you have landed; the ranked board is waiting when
  you raise it again. (*Nearby*, inside a club card, is the one exception: it
  exists to produce that list, so it re-raises.) The handle also drags either
  way, and tapping the map minimises it. The sheet counts toward the map's
  bottom padding while minimised, so the UK is never fitted underneath it.
- **Gestures belong to the map.** `body` is `touch-action: pan-x pan-y`, which
  withholds the *browser's* pinch and double-tap zoom while leaving panning
  intact; the map itself is `touch-action: none` so MapLibre handles every
  gesture inside it. Without this, a pinch starting on any chrome over the map
  zoomed the page instead — and pinching to undo it just zoomed the map, so you
  ended up stuck at the wrong scale. (Trade-off: no browser zoom on mobile. The
  map has its own, and body text stays at its designed size.) Inputs are 16px
  so iOS doesn't zoom on focus, every control clears a ~44px touch target,
  tappable elements are `touch-action: manipulation` to drop the 300ms
  double-tap delay, club cards are compacted to fit a phone screen, and
  `env(safe-area-inset-*)` keeps things off the notch and home indicator.

## Leagues covered

| Nation | Leagues | Clubs |
|---|---|---|
| England (levels 1–8) | Premier League, EFL Championship / League One / League Two, National League, NL North, NL South, NPL Premier + Div One East/Midlands/West, Southern Premier Central/South + Div One Central/South, Isthmian Premier + North/South Central/South East | 428 |
| Scotland (levels 1–5) | Scottish Premiership, Championship, League One, League Two, Highland League, Lowland League East & West | 93 |
| Wales (levels 1–2) | Cymru Premier, Cymru North, Cymru South | 48 |
| Northern Ireland (levels 1–2) | NIFL Premiership, NIFL Championship | 28 |

Below these levels the pyramid is amateur (county and regional leagues,
thousands of clubs), which is where this map draws the line. Notable 2026–27
structural quirks reflected in the data: the Scottish Lowland League split into
East and West divisions, the NIFL Championship expanded to 16 clubs, and the
Cymru Premier grew to 16. Jersey Bulls (Isthmian South Central) sit outside the
initial map view — search for them or pan south past the Channel.

## Map encoding

**Markers carry three states**, all measured rather than eyeballed: green (to
visit), **crimson** (visited), **amber** (currently selected).

One red serves both themes (`#f43f5e`). Earlier attempts went dark on the
theory that lightness carries the separation — but a dark maroon (`#8f0f28`,
hue 24°) reads as *purple* on paper once the icon's pentagons darken it, which
is the opposite of useful. This brighter tone sits at 3.5:1 on the basemap,
the same as the green markers. Known trade-off: it is only ΔE 16 from the
selected amber under simulated colour blindness (ΔE 33 from the green, which is
what matters most) — that affects one marker at a time, and the amber's pulse
ring distinguishes it without colour. Light reds and pinks are the real trap:
`#ff8fa3` and `#ff6b8a` collapse toward the green at ΔE 10–16.

On the map the state is carried by colour alone; the
ground list keeps a ✓, so there is still a non-colour cue in the UI.

The selected amber pair was measured the same way — yellow-vs-green is
the classic colour-blind confusion, so `--sel` was checked against `--club`
under simulated protanopia, deuteranopia and tritanopia (worst-case ΔE 45 in
light, 38 in dark; ~20 is enough to read as a different colour). It carries a
dark ring, unlike the green markers' pale one, because amber on the pale
basemap is only 2:1 and needs the definition.

**One dot per club — every ground identical.** There is no colour or size
hierarchy between leagues: the map answers "where is football played?", not
"which clubs matter?". Markers are drawn as footballs in a single
green (`--club` in `css/styles.css`) that reads clearly against both the pale
and the navy duotone basemaps, at a uniform size set by `MARKER_PX` in
`js/app.js`. The league is named wherever a club appears — hover tooltip, club
card, sidebar list — rather than being encoded in the marker.

## Filters

Two chip rows cover almost every real query, with a live count underneath:

- **Nation** — England (428) · Scotland (93) · Wales (48) · N. Ireland (28)
- **Tier** — Professional (210) · Non-league (387)

Chips are toggles over the selected-league set, and show three states: **on**
(every league in that facet selected), **partial** (some — shown as an outline
plus a dot), **off**. So selecting *Professional* leaves England and Scotland
partial, because only their top four divisions are in play — the UI never
misreports what is on the map. Selecting nothing is impossible; emptying the
last facet restores everything rather than leaving a blank map.

Filters sit in the lower half of the **Explore** tab, below the the trip-planning tools
and separated by a heavier rule — so choosing a city and narrowing the map
happen on the same page, in the order you actually do them. They stay grouped
because they interact: you need nation, tier and the resulting count in one
glance. An active filter is also announced outside that section — the
**Explore tab shows a dot** whenever the selection isn't "all", the `n of 597
grounds shown` line updates live, and the **Reset** button over the map lights
up green. The map never silently hides grounds without an obvious way back.

**Reset** sits top-right on every device, always present and **always green** —
it is the way back to the opening view, so it reads as the primary control
rather than something that lights up conditionally. `.is-live` adds a soft ring
when there is actually a filter or selection to clear. The zoom buttons sit
**bottom-right, diagonally opposite**, so they can't be mistaken for part of it.
(Kept rather than dropped: pinch and scroll-wheel cover most people, but `+`/`−`
is the only zoom control that is keyboard-reachable and needs no gesture.)
Reset returns the whole app to its default view in one click: every league re-enabled, both search boxes
cleared, any place pin and selected ground dropped, the popup closed, the
Explore tab restored and the camera flown back to the full UK. The *Reset* link
inside the Leagues panel does exactly the same thing.

Below that, a collapsed **"Pick individual leagues"** disclosure holds all 31
leagues grouped by nation with per-nation all/none links, for when someone
wants exactly the National League North — expanded by default so the option is
obvious. These are **click-to-toggle rows, not checkboxes** — any number can be on at once; a selected league is tinted with a
full-colour ball, a deselected one is dimmed and greyscale. Hovering any league
spotlights it on the map.

## Data

- `data/teams.js` is the entire dataset — one line per club with league,
  stadium, town, capacity and lat/lng. Edit that file to update; nothing else
  needs to change (counts and filters are derived at runtime).
- Club lists, stadiums and capacities were taken from the Wikipedia 2026–27
  season articles for each league (fetched August 2026).
- **Coordinates**: 443 of the 597 grounds carry an `exact: true` flag, meaning
  the coordinate was verified against **OpenStreetMap** and/or **Wikidata** in
  August 2026 (typically landing within 5–20 m of the stadium footprint). The
  remaining 154 are unverified: the 39 at levels 1–4 came from stadium
  infoboxes and are reliable, while the 115 non-league ones may be town-level
  and are labelled **"approx. location"** in the club card.
- The verification was deliberately conservative — OSM matches were accepted up
  to 5 km, but Wikidata matches only when the ground *name* also agreed and the
  move was under 3 km, because Wikidata's "home venue" property is often a
  ground the club has since left. That gate caught stale groundshares for
  Kettering Town, Kingstonian, Cray Wanderers, Boston United, Hayes & Yeading
  and Pontypridd United, plus a plainly wrong Darlington coordinate.
- Clubs that genuinely share a ground (Chesham/Aylesbury, Falkirk/East
  Stirlingshire, Hamilton/Clyde, Connah's Quay/Flint) are offset by ~70 m so
  both markers stay clickable.
- `capacity: null` means "not reliably known" and the popup simply omits the row.

### Updating for a new season

Promotion/relegation only moves clubs between leagues — their coordinates don't
change. For each affected club in `data/teams.js`, change its league code
(first argument of `T(...)`), add lines for newly promoted clubs, remove or
re-code relegated ones, and update the `season` string at the bottom.

### Ideas for extending

- Women's pyramid (WSL, Championship) — same `T()` format, new league codes.
- English step 5–6 (regional feeder leagues below level 8).
- NIFL Premier Intermediate League / Scottish tier 6.

## Running costs: £0

Every service in the stack is free, keyless and CDN/public-hosted — there is
nothing to sign up for and no bill to receive:

| Piece | Provider | Licence / terms | Notes at scale |
|---|---|---|---|
| Map engine | [MapLibre GL JS](https://maplibre.org) 4.7.1 | BSD-3 | Free forever; served from unpkg (or vendor locally). |
| Basemap tiles | [OpenFreeMap](https://openfreemap.org) vector tiles (Positron style, recoloured at runtime) | **Free at any scale, no key, commercial use allowed** | This is the end-state provider — no swap needed as traffic grows. Self-hosting ([Protomaps](https://protomaps.com)) remains an option for full independence. |
| Geocoding | [Nominatim](https://operations.osmfoundation.org/policies/nominatim/) | Free public service, ~1 req/s fair use | Only called when a user hits Go; city chips use built-in coordinates (no network). Swap for LocationIQ's free tier if volume grows. |
| Fonts | Google Fonts (Barlow Condensed, Inter) | OFL | Can be self-hosted for privacy. |
| Club data | Wikipedia / FAW / NI Football League | CC BY-SA facts, embedded at build time | Static file — zero runtime cost. |
| Hosting | any static host | — | GitHub Pages / Cloudflare Pages / Netlify free tiers all work: it's a folder of static files. |

## Monetisation (affiliate-ready)

Every club card carries **🏨 Hotels nearby** and **🚆 Get there** buttons whose
URLs are built from templates in [`js/config.js`](js/config.js) — append your
affiliate/partner parameters there (e.g. Booking.com `&aid=YOUR_ID`) and every
card on the site updates. Outbound hotel links already carry
`rel="sponsored"`, the correct markup for affiliate links. `{q}` is the town,
`{lat}`/`{lng}` the ground coordinates, so the templates work with most travel
partners.

## Attribution

Basemap: [OpenFreeMap](https://openfreemap.org) ©
[OpenMapTiles](https://www.openmaptiles.org/), data from
[OpenStreetMap](https://www.openstreetmap.org/copyright) contributors. Place
search uses the public
[Nominatim](https://operations.osmfoundation.org/policies/nominatim/)
service — rate-limited, for light interactive use.
