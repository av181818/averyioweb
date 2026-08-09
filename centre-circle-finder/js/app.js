/* ============================================================
   Centre Circle Finder — app logic
   Map engine: MapLibre GL + OpenFreeMap vector tiles (free at
   any scale, no key, commercial use allowed).
   The light/dark "duotone" basemaps are generated at runtime by
   recolouring OpenFreeMap's Positron style against our brand
   ramp, so the data dots stay the only saturated colour.
   Geocoding: Nominatim (OpenStreetMap), GB-only, on demand.
   ============================================================ */
(async function () {
  "use strict";

  const DATA = window.FOOTBALL_DATA;
  const LEAGUES = DATA.leagues;
  const TEAMS = DATA.teams;

  const LEAGUE_ORDER = [
    "PL", "CH", "L1", "L2", "NL", "NLN", "NLS",
    "NPLP", "SLPC", "SLPS", "ISTP",
    "NPL1E", "NPL1M", "NPL1W", "SL1C", "SL1S", "IST1N", "IST1SC", "IST1SE",
    "SP", "SC", "SL1", "SL2", "HL", "LLE", "LLW",
    "CP", "CN", "CS",
    "NI", "NIC"
  ];
  const COUNTRY_ORDER = ["England", "Scotland", "Wales", "Northern Ireland"];
  // Every ground gets the same marker size — no league is visually privileged
  // over another. Icons are authored at 24px (BALL_PX 72 @ pixelRatio 3), so
  // MARKER_PX 24 lines up with icon-size 1.0 at full zoom.
  const MARKER_PX = 24;

  // MapLibre is lng,lat ordered
  const UK_BOUNDS = [[-8.65, 49.85], [1.80, 58.72]];

  // Roomy on purpose: maxBounds clamps the WHOLE viewport, not just the centre,
  // so a snug value silently crops the default view (a tight value once pushed
  // northern Scotland off the top). Still tight enough to keep panning near the UK.
  const MAX_BOUNDS = [[-22, 42], [14, 64]];

  const SIDEBAR_W = 372;
  const isMobile = () => matchMedia("(max-width: 900px)").matches;
  // Fit the UK into the space the chrome actually leaves free, measured rather
  // than guessed. Fixed constants were wrong on real phones: safe-area insets
  // push the top controls down, and the attribution bar is taller than it looks
  // once it wraps to two lines — so on a short viewport (a phone with browser
  // toolbars showing, where height rather than width becomes the binding
  // constraint) the south coast ended up clipped behind it after a reset.
  const CHROME_GAP = 14;
  function rectOf(sel) {
    const n = document.querySelector(sel);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return (r.width && r.height) ? r : null;   // null when hidden or empty
  }
  // Nothing spans the top of the map any more — the zoom buttons and the Reset
  // pill are small corner controls the map can pass under (it is open sea
  // there). Reserving a full-width band for those once cost so much height
  // that the fit needed a zoom below minZoom, got clamped, and overflowed.
  function chromeTop() {
    return 24;
  }
  // The attribution genuinely does span the width on a phone, .map-bar is
  // bottom-centred on desktop, and #sidebar is the peeking sheet — all three
  // must be cleared. The half-screen filter means the sheet only counts while
  // it is minimised; raised, it covers too much to fit the map around.
  function chromeBottom() {
    const half = innerHeight / 2;
    const ts = ["#sidebar", ".map-bar", ".maplibregl-ctrl-bottom-right", ".maplibregl-ctrl-attrib"]
      .map(rectOf).filter(Boolean).map((r) => r.top).filter((t) => t > half);
    return ts.length ? Math.round(innerHeight - Math.min(...ts)) + CHROME_GAP : 46;
  }
  const ukPad = () => isMobile()
    ? { top: chromeTop(), bottom: chromeBottom(), left: 14, right: 14 }
    : { top: chromeTop(), bottom: chromeBottom(), left: SIDEBAR_W + 34, right: 26 };
  // On mobile the panel is a bottom sheet covering ~72% of the screen that
  // never fully hides: minimised it still shows the brand bar and the
  // search field. Mirrors --peek in css/styles.css (used only as the fallback
  // for drag travel, which is otherwise measured).
  const PEEK_PX = 158;
  const sheetOpen = () => document.body.classList.contains("side-open");
  const setSheet = (open) => {
    document.body.classList.toggle("side-open", open);
    const head = $("#side-head");
    if (head) head.setAttribute("aria-expanded", String(open));
  };
  const openSheet = () => setSheet(true);
  const closeSheet = () => setSheet(false);
  const closeSheetOnMobile = () => { if (isMobile()) closeSheet(); };

  // Pad the bottom for whatever the sheet is currently covering, so a flown-to
  // ground always lands in the visible strip above it.
  const flyPad = () => isMobile()
    ? { top: sheetOpen() ? 76 : Math.round(innerHeight * 0.52),
        bottom: sheetOpen() ? Math.round(innerHeight * 0.72) + 16 : 36,
        left: 18, right: 18 }
    : { top: 80, bottom: 30, left: SIDEBAR_W + 42, right: 30 };

  const $ = (sel) => document.querySelector(sel);

  // ---------- helpers ----------

  function esc(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));
  }

  function norm(s) {
    try {
      return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
    } catch {
      return s.toLowerCase();
    }
  }

  function haversineKm(lat1, lng1, lat2, lng2) {
    const R = 6371, rad = Math.PI / 180;
    const dLat = (lat2 - lat1) * rad, dLng = (lng2 - lng1) * rad;
    const a = Math.sin(dLat / 2) ** 2 +
      Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(dLng / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(a));
  }

  const fmtMiles = (km) => (km * 0.621371).toFixed(1) + " mi";
  const fmtCap = (n) => n == null ? null : n.toLocaleString("en-GB");

  function initials(name) {
    const w = name.replace(/^(AFC|FC|The)\s+/i, "").trim().split(/\s+/)
      .filter((x) => !/^(of|the|and|&)$/i.test(x));
    // Always two characters so the badge reads like a kit number: one-word
    // clubs (Aberdeen, Arsenal) fall back to their first two letters.
    const a = w[0] || "?";
    return (w[1] ? a[0] + w[1][0] : a.slice(0, 2)).toUpperCase();
  }

  // ---------- groundhopper: which grounds you've been to ----------
  // Keyed on a slug of the club name, NOT the array index: ids are positional
  // and would silently re-point at different clubs the moment a season update
  // adds or removes one. All 597 names slug uniquely (checked).
  const VISIT_KEY = "ccf-visited";
  // One-time read-through to keys used before the app was renamed, purely so an
  // existing tally isn't lost. Nothing is ever written to these.
  const LEGACY_VISIT_KEYS = ["footballmap-visited", "awaydays-visited"];
  const slugOf = (name) => norm(name).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  let visited = new Set();
  try {
    const stored = localStorage.getItem(VISIT_KEY) ||
      LEGACY_VISIT_KEYS.map((k) => localStorage.getItem(k)).find(Boolean) || "[]";
    const raw = JSON.parse(stored);
    if (Array.isArray(raw)) visited = new Set(raw);
  } catch { /* corrupt or unavailable storage just means an empty tally */ }
  const saveVisits = () => {
    try { localStorage.setItem(VISIT_KEY, JSON.stringify([...visited])); } catch {}
  };
  const isVisited = (t) => visited.has(t.slug);
  // "all" | "todo" | "done" — a view filter, never a data change
  let visitFilter = "all";

  // Coordinates carry `exact` when verified against OpenStreetMap / Wikidata.
  // Unverified professional grounds (levels 1–4) came from stadium infoboxes and
  // are reliable, so only flag unverified non-league pins as approximate.
  const approxPin = (t, lg) => !t.exact && lg.tier >= 5;

  const townOnly = (town) => town.replace(/\s*\(.*\)$/, "");
  function outLink(tpl, t) {
    return tpl
      .replace("{q}", encodeURIComponent(townOnly(t.town)))
      .replace("{lat}", t.lat)
      .replace("{lng}", t.lng);
  }
  const links = window.CCF_LINKS || {};

  // ---------- theme ----------

  const themeBtn = $("#theme-toggle");
  let theme = localStorage.getItem("ccf-theme") || localStorage.getItem("ukfm-theme") ||
    (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");

  function applyThemeChrome() {
    document.body.classList.toggle("dark", theme === "dark");
    themeBtn.textContent = theme === "dark" ? "☀️" : "🌙";
  }
  applyThemeChrome();

  // ---------- duotone style generation ----------
  // Fetch OpenFreeMap's Positron style once, then remap every colour onto a
  // two-colour brand ramp by luminance: light = ink-blue on paper, dark =
  // pale slate on near-black navy.

  // Kept low-saturation on purpose: the basemap sets a pitch-side mood while
  // the green club markers stay the only saturated thing on screen.
  const RAMPS = {
    light: { lo: [92, 116, 104], hi: [247, 250, 246] },   // green-grey ink → warm paper
    dark: { lo: [156, 178, 164], hi: [11, 18, 15] }       // pale sage → night-pitch black
  };

  function parseColor(str) {
    if (typeof str !== "string") return null;
    const s = str.trim();
    let m;
    if ((m = s.match(/^#([0-9a-f]{3})$/i))) {
      const h = m[1];
      return [parseInt(h[0] + h[0], 16), parseInt(h[1] + h[1], 16), parseInt(h[2] + h[2], 16), 1];
    }
    if ((m = s.match(/^#([0-9a-f]{6})([0-9a-f]{2})?$/i))) {
      const h = m[1];
      const a = m[2] ? parseInt(m[2], 16) / 255 : 1;
      return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16), a];
    }
    if ((m = s.match(/^rgba?\(([^)]+)\)$/i))) {
      const p = m[1].split(",").map((x) => parseFloat(x));
      if (p.length >= 3) return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
    }
    if ((m = s.match(/^hsla?\(([^)]+)\)$/i))) {
      const p = m[1].split(",").map((x) => parseFloat(x));
      if (p.length >= 3) {
        const [h, sPct, lPct] = p;
        const a = p.length > 3 ? p[3] : 1;
        const sN = sPct / 100, lN = lPct / 100;
        const c = (1 - Math.abs(2 * lN - 1)) * sN;
        const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
        const mm = lN - c / 2;
        let r = 0, g = 0, b = 0;
        if (h < 60) { r = c; g = x; } else if (h < 120) { r = x; g = c; }
        else if (h < 180) { g = c; b = x; } else if (h < 240) { g = x; b = c; }
        else if (h < 300) { r = x; b = c; } else { r = c; b = x; }
        return [(r + mm) * 255, (g + mm) * 255, (b + mm) * 255, a];
      }
    }
    if (s === "white") return [255, 255, 255, 1];
    if (s === "black") return [0, 0, 0, 1];
    return null;
  }

  function duotone(str, ramp) {
    const c = parseColor(str);
    if (!c) return str;
    const lum = (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255;
    const r = Math.round(ramp.lo[0] + (ramp.hi[0] - ramp.lo[0]) * lum);
    const g = Math.round(ramp.lo[1] + (ramp.hi[1] - ramp.lo[1]) * lum);
    const b = Math.round(ramp.lo[2] + (ramp.hi[2] - ramp.lo[2]) * lum);
    return `rgba(${r},${g},${b},${+c[3].toFixed(3)})`;
  }

  function recolorValue(v, ramp) {
    if (typeof v === "string") return duotone(v, ramp);
    if (Array.isArray(v)) return v.map((x) => recolorValue(x, ramp));
    if (v && typeof v === "object") {
      const out = {};
      for (const k of Object.keys(v)) out[k] = recolorValue(v[k], ramp);
      return out;
    }
    return v;
  }

  function recolorStyle(base, ramp) {
    const st = JSON.parse(JSON.stringify(base));
    // Drop raster sources (Natural Earth shaded relief): invisible under the
    // duotone treatment, and their tile loading can stall style readiness.
    Object.entries(st.sources).forEach(([id, src]) => {
      if (src.type === "raster") delete st.sources[id];
    });
    st.layers = st.layers.filter((l) => !l.source || st.sources[l.source]);
    st.layers.forEach((layer) => {
      ["paint", "layout"].forEach((section) => {
        const props = layer[section];
        if (!props) return;
        Object.keys(props).forEach((key) => {
          if (/color$/.test(key)) props[key] = recolorValue(props[key], ramp);
        });
      });
    });
    return st;
  }

  // The generated styles are handed to MapLibre as blob URLs rather than
  // objects: maplibre-gl 5.24 stalls silently on style objects, but loads
  // identical JSON through its URL path without issue.
  const styleUrl = (st) => URL.createObjectURL(new Blob([JSON.stringify(st)], { type: "application/json" }));
  let styles;
  try {
    const res = await fetch("https://tiles.openfreemap.org/styles/positron");
    const base = await res.json();
    styles = {
      light: styleUrl(recolorStyle(base, RAMPS.light)),
      dark: styleUrl(recolorStyle(base, RAMPS.dark))
    };
  } catch (err) {
    console.warn("Centre Circle Finder: basemap style failed to load, using flat fallback:", err);
    // offline / blocked: plain background so the dots still work
    const flat = (bg) => ({ version: 8, sources: {}, layers: [{ id: "bg", type: "background", paint: { "background-color": bg } }] });
    styles = { light: styleUrl(flat("#eef2f6")), dark: styleUrl(flat("#101318")) };
  }

  // ---------- map ----------

  const map = new maplibregl.Map({
    container: "map",
    style: styles[theme],
    center: [-3.4, 54.4],
    zoom: 5,
    // Low enough that fitting UK_BOUNDS is never clamped: on a phone, chrome
    // padding plus safe-area insets can demand ~4.2, and a clamped fit crops
    // the country. maxBounds still stops anyone panning off to sea.
    minZoom: 3.8,
    maxZoom: 17.5,
    maxBounds: MAX_BOUNDS,
    attributionControl: false
  });
  // Bottom-right, diagonally opposite Reset. MapLibre PREPENDS controls in the
  // bottom corners, so the last one added sits highest — attribution first puts
  // the zoom buttons above it, with the credit line closest to the edge.
  map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
  map.on("error", (e) => console.warn("Centre Circle Finder: map error:", e && e.error && e.error.message));
  window._map = map;

  // Some embedded previews report the page as hidden, which suspends
  // requestAnimationFrame and freezes WebGL maps. Watchdog: keep a RAF
  // heartbeat; whenever it goes stale, drive the render loop manually.
  // In normal visible browser tabs the heartbeat stays fresh and the
  // pump never fires.
  let lastRaf = performance.now();
  (function rafBeat() {
    lastRaf = performance.now();
    requestAnimationFrame(rafBeat);
  })();
  setInterval(() => {
    // wait for the style JSON to be parsed, then keep rendering: tile loads
    // and style completion both depend on render frames running
    if (!(map.style && map.style._loaded)) return;
    if (performance.now() - lastRaf > 600) {
      try { map._render(performance.now()); } catch (e) { /* mid style swap */ }
    }
  }, 150);
  map.touchZoomRotate.disableRotation();
  map.dragRotate.disable();

  // True while the camera is still framing the whole UK. Mobile browsers resize
  // the viewport every time their toolbars slide in or out, and the map used to
  // be fitted exactly once — so a fit computed against one height left the UK
  // cropped at the next. We refit on every resize, but only while the user
  // hasn't navigated somewhere themselves.
  let atDefaultView = true;

  function fitUK(animate) {
    atDefaultView = true;
    // Cancel any camera animation still in flight first. A resize landing
    // mid-flyTo (a phone toolbar sliding away during the Reset animation)
    // otherwise leaves the running ease fighting the new fit, and the map
    // settles somewhere between the two.
    map.stop();
    // Wipe the padding the last flyTo left on the transform. It PERSISTS, and
    // fitBounds computes relative to it — so after visiting a ground (whose
    // flyPad reserves ~52% of the screen at the top) Reset was fitting the UK
    // into what was left, landing zoomed out and low. First load only looked
    // right because the transform padding is still zero at that point.
    map.setPadding({ top: 0, right: 0, bottom: 0, left: 0 });
    map.fitBounds(UK_BOUNDS, {
      padding: ukPad(),
      duration: animate ? 800 : 0,
      linear: true   // ease straight there rather than flyTo's zoom-out arc
    });
  }
  // originalEvent is present only for user gestures — programmatic camera moves
  // (this fit, and the flyTo animations) don't set it
  map.on("movestart", (e) => { if (e && e.originalEvent) atDefaultView = false; });

  // ---------- club data as a clustered GeoJSON source ----------

  TEAMS.forEach((t, i) => { t.id = i; t.slug = slugOf(t.name); });

  function teamFeature(t) {
    const lg = LEAGUES[t.league];
    return {
      type: "Feature",
      id: t.id,
      geometry: { type: "Point", coordinates: [t.lng, t.lat] },
      properties: {
        id: t.id, league: t.league, tier: lg.tier,
        // drives the icon only; the record itself is untouched
        visited: isVisited(t)
      }
    };
  }

  // ---------- football icons, drawn on a canvas for the GPU layer ----------

  const BALL_PX = 72;          // drawn at 3x, displayed at 24px when icon-size = 1
  const PENTA = [50, 27, 71.9, 42.9, 63.5, 68.6, 36.5, 68.6, 28.1, 42.9];
  const RIM = [[77.6, 12], [94.7, 64.5], [50, 97], [5.3, 64.5], [22.4, 12]];
  const SEAMS = [[50, 27, 50, -2], [71.9, 42.9, 99, 34], [63.5, 68.6, 79.9, 91],
    [36.5, 68.6, 20.1, 91], [28.1, 42.9, 1, 34]];

  function pentaPath(g, cx, cy, r, S) {
    g.beginPath();
    for (let i = 0; i < 5; i++) {
      const a = (-90 + i * 72) * Math.PI / 180;
      const x = (cx + r * Math.cos(a)) * S, y = (cy + r * Math.sin(a)) * S;
      i ? g.lineTo(x, y) : g.moveTo(x, y);
    }
    g.closePath();
  }

  function makeBall(fill, ring) {
    const px = BALL_PX, S = px / 100, r = px / 2;
    const c = document.createElement("canvas");
    c.width = c.height = px;
    const g = c.getContext("2d");
    const rad = r - px * 0.075;

    g.beginPath(); g.arc(r, r, rad, 0, Math.PI * 2);
    g.fillStyle = fill; g.fill();

    g.save();
    g.beginPath(); g.arc(r, r, rad, 0, Math.PI * 2); g.clip();
    // panels
    g.fillStyle = "rgba(0,0,0,0.34)";
    g.beginPath();
    for (let i = 0; i < PENTA.length; i += 2) {
      const x = PENTA[i] * S, y = PENTA[i + 1] * S;
      i ? g.lineTo(x, y) : g.moveTo(x, y);
    }
    g.closePath(); g.fill();
    RIM.forEach(([cx, cy]) => { pentaPath(g, cx, cy, 14, S); g.fill(); });
    // seams
    g.strokeStyle = "rgba(0,0,0,0.28)";
    g.lineWidth = 5 * S; g.lineCap = "round";
    SEAMS.forEach(([x1, y1, x2, y2]) => {
      g.beginPath(); g.moveTo(x1 * S, y1 * S); g.lineTo(x2 * S, y2 * S); g.stroke();
    });
    // highlight
    const gr = g.createRadialGradient(px * 0.32, px * 0.26, 0, px * 0.32, px * 0.26, px * 0.48);
    gr.addColorStop(0, "rgba(255,255,255,0.55)");
    gr.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = gr; g.fillRect(0, 0, px, px);
    g.restore();

    // ring
    g.beginPath(); g.arc(r, r, rad, 0, Math.PI * 2);
    g.lineWidth = px * 0.085; g.strokeStyle = ring; g.stroke();

    return g.getImageData(0, 0, px, px);
  }

  // one ball for every club — no per-level colouring
  function loadBallImages() {
    const cs = getComputedStyle(document.body);
    const ring = (cs.getPropertyValue("--marker-ring") || "#fff").trim();
    const fill = (cs.getPropertyValue("--club") || "#ee4d2e").trim();
    const img = makeBall(fill, ring);
    if (map.hasImage("ball")) map.updateImage("ball", img);
    else map.addImage("ball", img, { pixelRatio: 3 });
    // visited grounds differ by colour alone on the map; the ground list keeps
    // its ✓, so there is still a non-colour cue somewhere in the UI
    const seen = (cs.getPropertyValue("--visited") || fill).trim();
    const done = makeBall(seen, ring);
    if (map.hasImage("ball-done")) map.updateImage("ball-done", done);
    else map.addImage("ball-done", done, { pixelRatio: 3 });
  }

  const featureCollection = (teams) => ({ type: "FeatureCollection", features: teams.map(teamFeature) });

  // Every ground is drawn, at every zoom — no clustering. A GPU symbol layer
  // handles all 597 at once, scaled down when zoomed out so the UK view reads
  // as a dot-density map of the football pyramid.
  // setStyle() (the theme switch) drops the source, the layer AND the image
  // independently, so each is restored on its own terms rather than behind a
  // single `if (getSource) return` guard — that guard could see a surviving
  // source and skip re-adding the image, leaving 597 icons pointing at a
  // sprite that no longer exists, i.e. a map with no grounds on it.
  function addClubSource() {
    if (!map.getSource("clubs")) {
      map.addSource("clubs", { type: "geojson", data: featureCollection(visibleTeams()) });
    }
    loadBallImages();   // always — this is also what re-tints the ball per theme
    if (!map.getLayer("grounds")) {
      map.addLayer({
        id: "grounds",
        type: "symbol",
        source: "clubs",
        layout: {
          "icon-image": ["case", ["get", "visited"], "ball-done", "ball"],
          // uniform for every club, growing as you zoom in (24px × the factor)
          "icon-size": ["interpolate", ["linear"], ["zoom"],
            5, 0.36, 7, 0.50, 9, 0.68, 12, 0.95, 15, 1.10
          ],
          "icon-allow-overlap": true,
          "icon-ignore-placement": true
        },
        paint: { "icon-opacity": 1 }
      });
    }
  }

  // ---------- DOM markers synced to the clustered source ----------

  let currentPopup = null;
  let selectedMarker = null;   // lone DOM marker used for the selected ground's pulse
  let selectedId = null;

  const tip = document.createElement("div");
  tip.className = "club-tip hidden";
  document.body.appendChild(tip);
  const hideTip = () => tip.classList.add("hidden");

  function showTipAt(px, py, html) {
    tip.innerHTML = html;
    tip.classList.remove("hidden");
    const rect = map.getContainer().getBoundingClientRect();
    tip.style.left = (rect.left + px) + "px";
    tip.style.top = (rect.top + py - 14) + "px";
  }

  function bindLayerInteractions() {
    if (map.__boundGrounds) return;
    map.__boundGrounds = true;

    map.on("mousemove", "grounds", (e) => {
      const f = e.features && e.features[0];
      if (!f) return;
      map.getCanvas().style.cursor = "pointer";
      const t = TEAMS[f.properties.id];
      const lg = LEAGUES[t.league];
      showTipAt(e.point.x, e.point.y,
        `${esc(t.name)} <span class="tip-league">${esc(lg.short)}</span>`);
    });
    map.on("mouseleave", "grounds", () => {
      map.getCanvas().style.cursor = "";
      hideTip();
    });
    map.on("click", "grounds", (e) => {
      const f = e.features && e.features[0];
      if (!f) return;
      hideTip();
      openClubPopup(TEAMS[f.properties.id], false);
    });
  }

  // ---------- popup / selection ----------

  // Behind the ⓘ next to "Mark as visited". Deliberately the same words as the
  // .tally-note paragraph in index.html — the warning matters most at the moment
  // someone starts a collection, which is here, not in a panel they may never
  // open. **If you edit one, edit the other.**
  const VISIT_NOTE =
    'Open any ground and tap <b>Mark as visited</b> to tick it off. ' +
    "Your list is saved <b>in this browser only</b> — there's no account, so " +
    'clearing your browsing data, or switching browser or device, starts you ' +
    'from scratch. Use <b>Export</b> to save a backup file, and <b>Import</b> ' +
    'to merge it back in.';

  function popupHtml(t) {
    const lg = LEAGUES[t.league];
    const cap = fmtCap(t.capacity);
    const gmaps = `https://www.google.com/maps/search/?api=1&query=${t.lat}%2C${t.lng}`;
    return `
      <div class="pp">
        <div class="pp-head">
          <div class="pp-mono">${initials(t.name)}</div>
          <div>
            <div class="pp-name">${esc(t.name)}</div>
            <div class="pp-league"><span class="dot"></span>${esc(lg.name)}</div>
          </div>
        </div>
        <div class="pp-stats">
          <div class="pp-stat wide"><div class="k">Stadium${approxPin(t, lg) ? ' <span class="k-approx" title="Not yet verified against OpenStreetMap — may be a town-level position, so check the address before travelling">· approx. location</span>' : ""}</div><div class="v">${t.stadium ? esc(t.stadium) : "—"}</div></div>
          <div class="pp-stat"><div class="k">Town</div><div class="v">${esc(t.town)}</div></div>
          <div class="pp-stat"><div class="k">Capacity</div><div class="v num">${cap || "—"}</div></div>
          <div class="pp-stat wide"><div class="k">Status</div><div class="v">${esc(lg.status)} <span class="lvl-pill">Level ${lg.tier} · ${esc(lg.country)}</span></div></div>
        </div>
        <div class="pp-visit-row">
          <button class="pp-visit${isVisited(t) ? " is-on" : ""}" onclick="window._ukfmVisit(${t.id})">
            <span class="pv-box" aria-hidden="true">${isVisited(t) ? "✓" : ""}</span>
            ${isVisited(t) ? "Been here" : "Mark as visited"}
          </button>
          <button class="pp-info" type="button" aria-expanded="false"
                  aria-label="How your ticked-off list is stored"
                  onclick="window._ukfmVisitInfo(this)">i</button>
        </div>
        <p class="pp-note" hidden>${VISIT_NOTE}</p>
        <div class="pp-actions">
          <a class="pp-btn primary" href="${gmaps}" target="_blank" rel="noopener">Directions</a>
          <button class="pp-btn" onclick="window._ukfmNearby(${t.id})">Nearby</button>
        </div>
        ${links.hotels || links.transit ? `<div class="pp-actions secondary">
          ${links.hotels ? `<a class="pp-btn mini" href="${outLink(links.hotels, t)}" target="_blank" rel="noopener sponsored">🏨 Hotels nearby</a>` : ""}
          ${links.transit ? `<a class="pp-btn mini" href="${outLink(links.transit, t)}" target="_blank" rel="noopener">🚆 Get there</a>` : ""}
        </div>` : ""}
      </div>`;
  }

  // The selected ground is lifted out of the GPU layer and re-drawn as a single
  // DOM marker, so it can carry the CSS pulse without animating 597 icons.
  function stopPulse() {
    if (selectedMarker) { selectedMarker.remove(); selectedMarker = null; }
    selectedId = null;
    if (map.getLayer("grounds")) map.setFilter("grounds", null);
    markLiveState();
  }

  function pulseAt(t) {
    stopPulse();
    selectedId = t.id;
    if (map.getLayer("grounds")) map.setFilter("grounds", ["!=", ["get", "id"], t.id]);
    const lg = LEAGUES[t.league];
    const el = document.createElement("div");
    el.className = "club-marker sel";
    el.style.width = MARKER_PX + "px";
    el.style.height = MARKER_PX + "px";
    el.innerHTML = `<div class="cdot"></div>`;
    selectedMarker = new maplibregl.Marker({ element: el, anchor: "center" })
      .setLngLat([t.lng, t.lat]).addTo(map);
    markLiveState();
  }

  function openClubPopup(t, recenter) {
    if (currentPopup) currentPopup.remove();
    stopPulse();
    // drop the sheet back to peek so the card isn't opening behind it
    closeSheetOnMobile();
    const lg = LEAGUES[t.league];
    currentPopup = new maplibregl.Popup({
      offset: MARKER_PX / 2 + 10,
      maxWidth: "310px",
      closeButton: true
    })
      .setLngLat([t.lng, t.lat])
      .setHTML(popupHtml(t))
      .addTo(map);
    currentPopup.on("close", () => { stopPulse(); document.body.classList.remove("card-open"); });
    document.body.classList.add("card-open");
    pulseAt(t);

    if (recenter) {
      map.easeTo({ center: [t.lng, t.lat], padding: flyPad(), duration: 500 });
    }
  }

  function selectTeam(t) {
    if (!map.isStyleLoaded()) { whenMapReady(() => selectTeam(t)); return; }
    if (!active.has(t.league)) {
      active.add(t.league);
      syncCheckboxes();
      syncFilterChips();
      refresh();
    }
    closeSheetOnMobile();
    atDefaultView = false;
    const targetZoom = Math.max(map.getZoom(), 12.6);
    map.flyTo({ center: [t.lng, t.lat], zoom: targetZoom, padding: flyPad(), duration: 950, essential: true });
    map.once("moveend", () => openClubPopup(t, false));
  }

  // ---------- state ----------

  const active = new Set(LEAGUE_ORDER);
  let listQuery = "";
  let sortMode = "name";
  let placePin = null;

  const leagueCounts = {};
  TEAMS.forEach((t) => { leagueCounts[t.league] = (leagueCounts[t.league] || 0) + 1; });

  function visibleTeams() {
    return TEAMS.filter((t) =>
      active.has(t.league) &&
      (visitFilter === "all" ||
       (visitFilter === "done" ? isVisited(t) : !isVisited(t))));
  }

  function refresh() {
    const src = map.getSource("clubs");
    if (src) src.setData(featureCollection(visibleTeams()));
    renderList();
  }

  // markLiveState() counts the visit filter as "something to undo", but never
  // the visits themselves — Reset must not wipe someone's collection.
  const visitFiltered = () => visitFilter !== "all";

  // ---------- filters UI ----------

  function buildFilters() {
    const wrap = $("#filter-groups");
    wrap.innerHTML = "";
    COUNTRY_ORDER.forEach((country) => {
      const codes = LEAGUE_ORDER.filter((c) => LEAGUES[c].country === country);
      if (!codes.length) return;

      const det = document.createElement("details");
      det.className = "f-group";
      det.open = true;
      const total = codes.reduce((s, c) => s + (leagueCounts[c] || 0), 0);
      const sum = document.createElement("summary");
      sum.className = "f-country";
      sum.innerHTML = `<span class="fc-name">${esc(country)} <span class="fc-total">${total}</span></span>
        <span class="fc-links"><button data-grp="${country}" data-on="1">all</button>·<button data-grp="${country}" data-on="0">none</button></span>`;
      det.appendChild(sum);

      codes.forEach((code) => {
        const lg = LEAGUES[code];
        const row = document.createElement("button");
        row.className = "f-row";
        row.type = "button";
        row.dataset.league = code;
        row.setAttribute("aria-pressed", String(active.has(code)));
        row.innerHTML = `<span class="dot"></span>
          <span class="f-name">${esc(lg.name)}</span>
          <span class="f-count">${leagueCounts[code] || 0}</span>`;
        det.appendChild(row);
      });
      wrap.appendChild(det);
    });

    // click a league to toggle it; several can be on at once
    wrap.addEventListener("click", (e) => {
      const row = e.target.closest(".f-row[data-league]");
      if (!row) return;
      const code = row.dataset.league;
      active.has(code) ? active.delete(code) : active.add(code);
      if (!active.size) LEAGUE_ORDER.forEach((c) => active.add(c));
      syncCheckboxes();
      syncFilterChips();
      refresh();
    });

    wrap.addEventListener("click", (e) => {
      const grp = e.target.getAttribute("data-grp");
      if (grp == null) return;
      e.preventDefault(); // keep the <details> group from toggling
      const on = e.target.getAttribute("data-on") === "1";
      LEAGUE_ORDER.filter((c) => LEAGUES[c].country === grp)
        .forEach((c) => { on ? active.add(c) : active.delete(c); });
      syncCheckboxes();
      syncFilterChips();
      refresh();
    });
  }

  function syncCheckboxes() {
    document.querySelectorAll("#filter-groups .f-row[data-league]").forEach((row) => {
      const on = active.has(row.dataset.league);
      row.classList.toggle("is-on", on);
      row.setAttribute("aria-pressed", String(on));
    });
  }

  // ---------- club list ----------

  function listMatches() {
    const q = norm(listQuery.trim());
    let arr = visibleTeams();
    if (q) {
      arr = arr.filter((t) =>
        norm(t.name).includes(q) || norm(t.town).includes(q) || norm(t.stadium || "").includes(q));
    }
    const byTier = (t) => LEAGUES[t.league].tier;
    if (sortMode === "name") {
      arr.sort((a, b) => a.name.localeCompare(b.name));
    } else if (sortMode === "league") {
      arr.sort((a, b) => byTier(a) - byTier(b) ||
        LEAGUE_ORDER.indexOf(a.league) - LEAGUE_ORDER.indexOf(b.league) ||
        a.name.localeCompare(b.name));
    } else {
      arr.sort((a, b) => (b.capacity || 0) - (a.capacity || 0) || a.name.localeCompare(b.name));
    }
    return arr;
  }

  function renderList() {
    const arr = listMatches();
    const ul = $("#club-list");
    ul.innerHTML = "";
    $("#visible-count").textContent = arr.length;

    if (!arr.length) {
      ul.innerHTML = `<div class="list-empty">No grounds match — adjust the league filters or search.</div>`;
      return;
    }
    const frag = document.createDocumentFragment();
    arr.forEach((t) => {
      const lg = LEAGUES[t.league];
      const li = document.createElement("li");
      if (isVisited(t)) li.className = "is-done";
      li.innerHTML = `<span class="dot"></span>
        <span class="cl-text">
          <span class="cl-name">${esc(t.name)}</span>
          <span class="cl-meta"><span class="lg-chip">${esc(lg.short)}</span> ${esc(t.town)}</span>
        </span>
        ${t.capacity ? `<span class="cl-cap">${fmtCap(t.capacity)}</span>` : ""}`;
      li.addEventListener("click", () => selectTeam(t));
      frag.appendChild(li);
    });
    ul.appendChild(frag);
  }

  // ---------- tabs ----------

  function showTab(name) {
    document.querySelectorAll(".tab").forEach((t) => {
      const on = t.dataset.tab === name;
      t.classList.toggle("is-active", on);
      t.setAttribute("aria-selected", String(on));
    });
    document.querySelectorAll(".panel-tab").forEach((p) => {
      p.classList.toggle("is-active", p.id === "panel-" + name);
    });
    $(".side-scroll").scrollTop = 0;
  }
  document.querySelectorAll(".tab").forEach((t) => {
    t.addEventListener("click", () => showTab(t.dataset.tab));
  });

  // ---------- omnibox: clubs, grounds, towns and places in one field ----------

  const omni = $("#omni");
  const omniResults = $("#omni-results");
  let omniItems = [];
  let omniCursor = -1;

  function closeOmni() {
    omniResults.classList.add("hidden");
    omni.setAttribute("aria-expanded", "false");
    omniItems = [];
    omniCursor = -1;
  }

  function runOmni() {
    const raw = omni.value.trim();
    if (!raw) { closeOmni(); return; }
    const q = norm(raw);
    const hits = TEAMS
      .filter((t) => norm(t.name).includes(q) || norm(t.town).includes(q) || norm(t.stadium || "").includes(q))
      .sort((a, b) => {
        // clubs whose name starts with the query rank first, then bigger grounds
        const as = norm(a.name).startsWith(q) ? 0 : 1;
        const bs = norm(b.name).startsWith(q) ? 0 : 1;
        return as - bs || (b.capacity || 0) - (a.capacity || 0) || a.name.localeCompare(b.name);
      })
      .slice(0, 6);

    omniResults.innerHTML = "";
    omniItems = [];

    if (hits.length) {
      const sec = document.createElement("div");
      sec.className = "omni-sec";
      sec.textContent = "Clubs & grounds";
      omniResults.appendChild(sec);
      hits.forEach((t) => {
        const lg = LEAGUES[t.league];
        const b = document.createElement("button");
        b.className = "omni-row";
        b.innerHTML = `<span class="dot"></span>
          <span class="or-text">
            <span class="or-name">${esc(t.name)}</span>
            <span class="or-meta"><span class="lg-chip">${esc(lg.short)}</span> ${esc(t.stadium || t.town)}</span>
          </span>`;
        b.addEventListener("click", () => { closeOmni(); selectTeam(t); });
        omniResults.appendChild(b);
        omniItems.push(b);
      });
    }

    const secP = document.createElement("div");
    secP.className = "omni-sec";
    secP.textContent = "Places";
    omniResults.appendChild(secP);
    const pb = document.createElement("button");
    pb.className = "omni-row";
    pb.innerHTML = `<span class="ab-icon" aria-hidden="true">📍</span>
      <span class="or-text">
        <span class="or-name">Grounds near “${esc(raw)}”</span>
        <span class="or-meta">Search this town, city or postcode</span>
      </span>
      <span class="or-go">↵</span>`;
    pb.addEventListener("click", () => { closeOmni(); showTab("explore"); geocode(raw); });
    omniResults.appendChild(pb);
    omniItems.push(pb);

    omniResults.classList.remove("hidden");
    omni.setAttribute("aria-expanded", "true");
    omniCursor = -1;
  }

  function moveOmni(step) {
    if (!omniItems.length) return;
    if (omniCursor >= 0) omniItems[omniCursor].classList.remove("is-cursor");
    omniCursor = (omniCursor + step + omniItems.length) % omniItems.length;
    omniItems[omniCursor].classList.add("is-cursor");
    omniItems[omniCursor].scrollIntoView({ block: "nearest" });
  }

  omni.addEventListener("input", () => { runOmni(); markLiveState(); });
  omni.addEventListener("focus", () => { if (omni.value.trim()) runOmni(); });
  omni.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); moveOmni(1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); moveOmni(-1); }
    else if (e.key === "Escape") { closeOmni(); omni.blur(); }
    else if (e.key === "Enter") {
      e.preventDefault();
      if (omniCursor >= 0) omniItems[omniCursor].click();
      else if (omniItems.length) omniItems[0].click();
    }
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".omni-wrap")) closeOmni();
  });

  // ---------- grounds list filter ----------

  const groundFilter = $("#ground-filter");
  groundFilter.addEventListener("input", () => {
    listQuery = groundFilter.value;
    renderList();
    markLiveState();
  });

  // ---------- place search / near me ----------

  const placeResults = $("#place-results");
  const exploreEmpty = $("#explore-empty");

  function prMessage(html, busy) {
    showTab("explore");
    placeResults.classList.remove("hidden");
    exploreEmpty.classList.add("hidden");
    placeResults.innerHTML = `<div class="pr-empty">${busy ? '<span class="spin-ball" aria-hidden="true"></span>' : ""}${html}</div>`;
  }

  function clearPlace() {
    if (placePin) { placePin.remove(); placePin = null; }
    placeResults.classList.add("hidden");
    placeResults.innerHTML = "";
    exploreEmpty.classList.remove("hidden");
    markLiveState();
  }

  // Wait until the style is usable, then run fn. Polls rather than listening:
  // map.once("load") never fires after boot, and "idle"/"styledata" are not
  // dependable while the render loop is being pumped manually — both would
  // silently drop the user's action. Runs anyway after ~6s rather than never.
  function whenMapReady(fn) {
    if (map.isStyleLoaded()) { fn(); return; }
    let tries = 0;
    const iv = setInterval(() => {
      if (map.isStyleLoaded() || ++tries > 60) { clearInterval(iv); fn(); }
    }, 100);
  }

  function showPlace(lat, lng, label) {
    if (placePin) placePin.remove();
    const pinEl = document.createElement("div");
    pinEl.className = "place-pin";
    pinEl.style.width = "31px";
    pinEl.style.height = "40px";
    pinEl.innerHTML = `<div class="pin"></div><div class="pulse"></div>`;
    placePin = new maplibregl.Marker({ element: pinEl, anchor: "bottom" })
      .setLngLat([lng, lat])
      .addTo(map);

    atDefaultView = false;
    // the map is the focus now — drop the sheet so the user can see where they
    // have landed; the ranked board is waiting when they raise it again
    closeSheetOnMobile();
    map.flyTo({ center: [lng, lat], zoom: 9.6, padding: flyPad(), duration: 950, essential: true });

    const dists = visibleTeams()
      .map((t) => ({ t, km: haversineKm(lat, lng, t.lat, t.lng) }))
      .sort((a, b) => a.km - b.km);
    const near = dists.slice(0, 12);
    const within25 = dists.filter((d) => d.km <= 40.2).length;

    showTab("explore");
    placeResults.classList.remove("hidden");
    exploreEmpty.classList.add("hidden");
    placeResults.innerHTML = `
      <div class="pr-head"><span>Grounds near <strong>${esc(label)}</strong></span>
      <button class="link-btn" id="place-clear">clear ×</button></div>
      <div class="pr-sub">${within25} ground${within25 === 1 ? "" : "s"} within 25 miles — pick your match</div>`;

    near.forEach(({ t, km }) => {
      const lg = LEAGUES[t.league];
      const b = document.createElement("button");
      b.className = "pr-row";
      b.innerHTML = `<span class="dot"></span>
        <span class="pr-name">${esc(t.name)} <span class="lg-chip">${esc(lg.short)}</span></span>
        <span class="pr-dist">${fmtMiles(km)}</span>`;
      b.addEventListener("click", () => selectTeam(t));
      placeResults.appendChild(b);
    });
    $("#place-clear").addEventListener("click", clearPlace);
    markLiveState();
  }

  window._ukfmVisit = (id) => {
    const t = TEAMS[id];
    if (!t) return;
    if (visited.has(t.slug)) visited.delete(t.slug); else visited.add(t.slug);
    saveVisits();
    refresh();                                   // re-icons the layer + list
    renderTally();
    if (currentPopup) currentPopup.setHTML(popupHtml(t));
    markLiveState();
  };

  // The ⓘ beside "Mark as visited". A native title= tooltip would be invisible
  // on a touch screen, which is most of this app's use, so it toggles a note.
  window._ukfmVisitInfo = (btn) => {
    const note = btn.closest(".pp").querySelector(".pp-note");
    if (!note) return;
    const opening = note.hidden;
    note.hidden = !opening;
    btn.setAttribute("aria-expanded", opening ? "true" : "false");
    btn.classList.toggle("is-on", opening);
    if (!currentPopup) return;
    // The card just grew by the height of the note. maplibre picks which side of
    // the pin to hang a popup when it places it and never re-checks, so re-set
    // the same coordinate to re-run that choice against the new height.
    currentPopup.setLngLat(currentPopup.getLngLat());
    // Re-anchoring only helps when one side has room. On a short window neither
    // does, and the card would keep Directions and Nearby below the fold — so
    // pan the map by however much is hanging off. Measured next frame, once the
    // note has actually been laid out.
    if (!opening) return;
    // Measured straight away, not in a rAF: reading a rect forces layout, so the
    // note's height is already accounted for, and a frame callback is throttled
    // in a background tab — which is exactly when this silently did nothing.
    const card = btn.closest(".pp");
    if (!card) return;
    const c = card.getBoundingClientRect();
    const m = map.getContainer().getBoundingClientRect();
    const below = c.bottom - m.bottom + 12;
    const above = m.top - c.top + 12;
    if (below > 0) map.panBy([0, below], { duration: 240 });
    else if (above > 0) map.panBy([0, -above], { duration: 240 });
  };

  // "Nearby" button inside popups — re-centre the nearby search on that ground
  window._ukfmNearby = (id) => {
    const t = TEAMS[id];
    if (!t) return;
    if (currentPopup) currentPopup.remove();
    showPlace(t.lat, t.lng, t.name);
    // the exception: Nearby is asked for precisely to read the list
    if (isMobile()) openSheet();
  };

  async function geocode(q) {
    prMessage("Searching…", true);
    try {
      const url = "https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&countrycodes=gb&q=" +
        encodeURIComponent(q);
      const res = await fetch(url, { headers: { "Accept": "application/json" } });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const js = await res.json();
      if (!js.length) { prMessage(`No UK place found for “${esc(q)}”.`); return; }
      const hit = js[0];
      const label = (hit.display_name || q).split(",").slice(0, 2).join(",");
      showPlace(parseFloat(hit.lat), parseFloat(hit.lon), label);
    } catch (err) {
      prMessage("Place search unavailable (network error). Try again in a moment.");
    }
  }

  $("#near-me").addEventListener("click", () => {
    if (!navigator.geolocation) { prMessage("Geolocation is not supported by this browser."); return; }
    prMessage("Locating…", true);
    navigator.geolocation.getCurrentPosition(
      (pos) => showPlace(pos.coords.latitude, pos.coords.longitude, "your location"),
      () => prMessage("Couldn't get your location — check browser permissions."),
      { enableHighAccuracy: false, timeout: 8000 }
    );
  });

  // ---------- place helpers ----------

  const CITIES = [
    ["London", 51.507, -0.128], ["Manchester", 53.480, -2.243],
    ["Liverpool", 53.408, -2.992], ["Birmingham", 52.480, -1.899],
    ["Leeds", 53.800, -1.549], ["Sheffield", 53.381, -1.470],
    ["Newcastle", 54.978, -1.618], ["Glasgow", 55.861, -4.250],
    ["Edinburgh", 55.953, -3.188], ["Cardiff", 51.482, -3.179],
    ["Belfast", 54.597, -5.930], ["Bristol", 51.454, -2.588]
  ];
  function renderCityChips(container) {
    if (!container) return;
    CITIES.forEach(([name, lat, lng]) => {
      const n = TEAMS.filter((t) => haversineKm(lat, lng, t.lat, t.lng) <= 40.2).length;
      const b = document.createElement("button");
      b.className = "city-chip";
      b.innerHTML = `${esc(name)} <span class="cc-n">${n}</span>`;
      b.title = `${n} grounds within 25 miles of ${name}`;
      b.addEventListener("click", () => showPlace(lat, lng, name));
      container.appendChild(b);
    });
  }
  renderCityChips($("#city-chips"));

  // The brand mark over the map is a logo, not a control — no handler here on
  // purpose. Getting back to the UK view is Reset's job.

  $("#surprise-me").addEventListener("click", () => {
    const pool = visibleTeams();
    if (pool.length) selectTeam(pool[Math.floor(Math.random() * pool.length)]);
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) {
      e.preventDefault();
      if (isMobile()) openSheet();
      omni.focus();
    }
  });

  // ---------- filter chips (nation + tier) ----------
  // `active` (the set of selected league codes) stays the single source of
  // truth. Chips toggle whole facets on/off and reflect back three states:
  // on = every league in that facet selected, partial = some, off = none.

  const NATIONS = [
    ["England", "England"], ["Scotland", "Scotland"],
    ["Wales", "Wales"], ["Northern Ireland", "N. Ireland"]
  ];
  const TIERS = [
    ["pro", "Professional", (lg) => lg.tier <= 4],
    ["non", "Non-league", (lg) => lg.tier >= 5]
  ];

  const facetCodes = {};
  NATIONS.forEach(([key]) => {
    facetCodes["nation:" + key] = LEAGUE_ORDER.filter((c) => LEAGUES[c].country === key);
  });
  TIERS.forEach(([key, , test]) => {
    facetCodes["tier:" + key] = LEAGUE_ORDER.filter((c) => test(LEAGUES[c]));
  });
  const countTeams = (codes) => TEAMS.filter((t) => codes.includes(t.league)).length;

  function makeChip(id, label, codes) {
    const b = document.createElement("button");
    b.className = "f-chip";
    b.dataset.facet = id;
    b.innerHTML = `${esc(label)} <span class="fc-n">${countTeams(codes)}</span>`;
    b.title = `${label} — ${countTeams(codes)} grounds`;
    b.addEventListener("click", () => {
      const allOn = codes.every((c) => active.has(c));
      codes.forEach((c) => { allOn ? active.delete(c) : active.add(c); });
      // never leave the map empty — an empty selection reads as "broken"
      if (!active.size) LEAGUE_ORDER.forEach((c) => active.add(c));
      syncCheckboxes();
      syncFilterChips();
      refresh();
    });
    return b;
  }

  const nationWrap = $("#nation-chips");
  NATIONS.forEach(([key, label]) => nationWrap.appendChild(makeChip("nation:" + key, label, facetCodes["nation:" + key])));
  const tierWrap = $("#tier-chips");
  TIERS.forEach(([key, label]) => tierWrap.appendChild(makeChip("tier:" + key, label, facetCodes["tier:" + key])));

  function syncFilterChips() {
    document.querySelectorAll(".f-chip[data-facet]").forEach((chip) => {
      const codes = facetCodes[chip.dataset.facet] || [];
      const on = codes.filter((c) => active.has(c)).length;
      chip.classList.toggle("on", on === codes.length && on > 0);
      chip.classList.toggle("partial", on > 0 && on < codes.length);
    });
    syncVisitChips();          // every state change routes through here
    const shown = visibleTeams().length;
    $("#filter-count").textContent = shown;
    const nSel = LEAGUE_ORDER.filter((c) => active.has(c)).length;
    const filtered = nSel !== LEAGUE_ORDER.length;
    $("#league-sum").textContent = filtered
      ? `${nSel} of ${LEAGUE_ORDER.length}` : `all ${LEAGUE_ORDER.length}`;
    // a dot on the Leagues tab so an active filter is visible from any tab
    $("#filter-dot").hidden = !filtered;
    markLiveState();
  }

  // The reset button highlights whenever there is something to undo, so the
  // map never silently hides grounds without an obvious way back.
  function markLiveState() {
    const filtered = LEAGUE_ORDER.some((c) => !active.has(c));
    const live = filtered || visitFiltered() || !!placePin || selectedId != null ||
      !!(omni && omni.value.trim()) || !!(groundFilter && groundFilter.value.trim());
    $("#reset-all").classList.toggle("is-live", live);
  }

  // ---------- groundhopper tally + filter chips ----------

  function renderTally() {
    const n = TEAMS.filter(isVisited).length;
    $("#tally-n").textContent = n;
    $("#tally-of").textContent = "of " + TEAMS.length;
    $("#tally-fill").style.width = (n / TEAMS.length * 100).toFixed(2) + "%";
    // disabled, not hidden — see the comment on these buttons in index.html
    $("#tally-clear").disabled = n === 0;
    $("#tally-export").disabled = n === 0;
    syncVisitChips();
  }

  const VISIT_FACETS = [
    ["all", "All"], ["todo", "To visit"], ["done", "Visited"]
  ];
  function buildVisitChips() {
    const wrap = $("#visit-chips");
    if (!wrap) return;
    wrap.innerHTML = "";
    VISIT_FACETS.forEach(([key, label]) => {
      const b = document.createElement("button");
      b.className = "f-chip";
      b.dataset.visit = key;
      b.innerHTML = `${label} <span class="fc-n"></span>`;
      b.addEventListener("click", () => {
        visitFilter = key;
        refresh();
        syncFilterChips();       // repaints these chips too
        markLiveState();
      });
      wrap.appendChild(b);
    });
    syncVisitChips();
  }
  function syncVisitChips() {
    const done = TEAMS.filter(isVisited).length;
    const counts = { all: TEAMS.length, todo: TEAMS.length - done, done };
    document.querySelectorAll("#visit-chips .f-chip").forEach((chip) => {
      chip.classList.toggle("on", chip.dataset.visit === visitFilter);
      chip.querySelector(".fc-n").textContent = counts[chip.dataset.visit];
    });
  }

  // Export/import: localStorage is per-browser and one "clear site data" from
  // wiping a collection someone spent years building, so it has to be portable.
  const VISIT_FILE = { app: "centre-circle-finder", kind: "visited-grounds", version: 1 };

  const tallyExport = $("#tally-export");
  if (tallyExport) tallyExport.addEventListener("click", () => {
    const body = JSON.stringify(
      { ...VISIT_FILE, exported: new Date().toISOString(), visited: [...visited] }, null, 2);
    const url = URL.createObjectURL(new Blob([body], { type: "application/json" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `centre-circle-finder-visited-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  });

  const tallyFile = $("#tally-file");
  const tallyImport = $("#tally-import");
  if (tallyImport && tallyFile) {
    tallyImport.addEventListener("click", () => tallyFile.click());
    tallyFile.addEventListener("change", async (e) => {
      const file = e.target.files && e.target.files[0];
      e.target.value = "";                       // so re-picking the same file fires
      if (!file) return;
      try {
        const data = JSON.parse(await file.text());
        // accept our own export, or a bare array of slugs
        const list = Array.isArray(data) ? data : data && data.visited;
        if (!Array.isArray(list)) throw new Error("not a visited list");
        // Only accept slugs that match a club we actually carry, so a stale or
        // hand-edited file can't quietly seed junk into the tally.
        const known = new Set(TEAMS.map((t) => t.slug));
        const before = visited.size;
        let skipped = 0;
        list.forEach((slug) => {
          if (typeof slug !== "string") return;
          if (known.has(slug)) visited.add(slug); else skipped++;
        });
        saveVisits();
        refresh();
        renderTally();
        // merge, never replace — importing should not be able to lose grounds
        alert(`Imported ${visited.size - before} new ground(s). You're now on ${visited.size}.` +
          (skipped
            ? `\n\n${skipped} entr${skipped === 1 ? "y" : "ies"} didn't match a club in this season's data and ${skipped === 1 ? "was" : "were"} skipped.`
            : ""));
      } catch {
        alert("That doesn't look like a Centre Circle Finder export. Expected a .json file with a \"visited\" list.");
      }
    });
  }

  const tallyClear = $("#tally-clear");
  if (tallyClear) tallyClear.addEventListener("click", () => {
    if (!visited.size) return;
    if (!confirm(`Clear all ${visited.size} ticked-off grounds? This can't be undone.`)) return;
    visited.clear();
    saveVisits();
    refresh();
    renderTally();
  });

  // spotlight: hovering a league filter row or legend level row highlights
  // just those dots on the map, dimming everything else
  // spotlight now dims the GPU layer via a paint expression
  function spotlight(match) {
    if (!map.getLayer("grounds")) return;
    map.setPaintProperty("grounds", "icon-opacity",
      match ? ["case", match, 1, 0.13] : 1);
  }
  const byLeague = (code) => ["==", ["get", "league"], code];
  const filterWrap = $("#filter-groups");
  filterWrap.addEventListener("mouseover", (e) => {
    const row = e.target.closest(".f-row");
    if (!row) return;
    if (row.dataset.league) spotlight(byLeague(row.dataset.league));
  });
  filterWrap.addEventListener("mouseout", (e) => {
    if (e.target.closest(".f-row")) spotlight(null);
  });

  // ---------- misc UI ----------

  $("#sort-clubs").addEventListener("change", (e) => {
    sortMode = e.target.value;
    renderList();
  });

  // One reset for everything: filters, both searches, the selected ground and
  // the camera. Reachable from the map at all times and from the Leagues panel.
  function resetAll() {
    LEAGUE_ORDER.forEach((c) => active.add(c));
    visitFilter = "all";          // the view resets; the collection does not
    syncCheckboxes();
    listQuery = "";
    groundFilter.value = "";
    omni.value = "";
    closeOmni();
    clearPlace();
    if (currentPopup) currentPopup.remove();
    document.body.classList.remove("card-open");
    stopPulse();
    spotlight(null);
    refresh();
    syncFilterChips();
    showTab("explore");
    fitUK(true);
  }
  $("#filters-reset").addEventListener("click", resetAll);
  $("#reset-all").addEventListener("click", resetAll);

  function setTheme(next, save) {
    theme = next;
    applyThemeChrome();
    if (save) localStorage.setItem("ccf-theme", theme);
    const keep = selectedId;
    stopPulse();
    map.setStyle(styles[theme]);
    // The first "styledata" fires while the swap is still in flight — the old
    // source can still be present at that moment, so rebuilding there raced
    // the teardown and the grounds vanished. Poll for a genuinely loaded style
    // instead, the same way every other deferred action in here does.
    whenMapReady(() => {
      // setStyle drops sources/layers/images — rebuild, with balls re-tinted
      addClubSource();
      bindLayerInteractions();
      refresh();
      if (keep != null) pulseAt(TEAMS[keep]);
    });
  }
  themeBtn.addEventListener("click", () => setTheme(theme === "dark" ? "light" : "dark", true));

  // ---------- bottom sheet ----------

  const sheetEl = $("#sidebar");
  const sheetGrip = $("#sheet-grip");

  // Tapping the search field is the primary way in: it expands the sheet and
  // focuses the input in one go, so the visible peek strip is also the control.
  omni.addEventListener("focus", () => { if (isMobile()) openSheet(); });

  // The masthead is the handle. Tapping it raises the sheet, tapping it again
  // minimises it — so the brand bar is both the branding and the control,
  // and there is no hamburger to explain.
  const sideHead = $("#side-head");
  if (sideHead) sideHead.addEventListener("click", () => {
    if (isMobile()) setSheet(!sheetOpen());
  });

  if (sheetGrip) {
    // Drag the handle either way between minimised and raised.
    let startY = 0, dy = 0, dragging = false, wasOpen = false, justDragged = false;
    // Measured from the resting position rather than derived from --peek,
    // which carries an env(safe-area-inset-bottom) that JS can't resolve.
    let collapsedY = null;
    const currentY = () =>
      Math.round(sheetEl.getBoundingClientRect().top - (innerHeight - sheetEl.offsetHeight));
    const travel = () =>
      Math.max(1, collapsedY != null ? collapsedY : sheetEl.offsetHeight - PEEK_PX);

    // pointerup is followed by click, so a completed drag must swallow the
    // click it generates or the sheet would snap and then toggle straight back
    sheetGrip.addEventListener("click", () => {
      if (justDragged) { justDragged = false; return; }   // consume it here…
      setSheet(!sheetOpen());
    });

    sheetGrip.addEventListener("pointerdown", (e) => {
      if (!isMobile()) return;
      dragging = true; dy = 0;
      // …and again here, because a drag that ends without a following click
      // (released off the element, gesture cancelled) would otherwise leave
      // the flag set and swallow the next genuine tap
      justDragged = false;
      startY = e.clientY;
      wasOpen = sheetOpen();
      if (!wasOpen) collapsedY = currentY();
      document.body.classList.add("sheet-dragging");
      sheetGrip.setPointerCapture(e.pointerId);
    });

    sheetGrip.addEventListener("pointermove", (e) => {
      if (!dragging) return;
      dy = e.clientY - startY;
      // clamp to the two snap points, so it can't be dragged off either end
      const base = wasOpen ? 0 : travel();
      const y = Math.min(travel(), Math.max(0, base + dy));
      sheetEl.style.transform = `translateY(${y}px)`;
    });

    const endDrag = (e) => {
      if (!dragging) return;
      dragging = false;
      document.body.classList.remove("sheet-dragging");
      sheetEl.style.transform = "";
      if (e && e.pointerId != null && sheetGrip.hasPointerCapture(e.pointerId)) {
        sheetGrip.releasePointerCapture(e.pointerId);
      }
      // a short drag is a tap — leave it to the click handler to toggle
      if (Math.abs(dy) < 24) return;
      justDragged = true;
      setSheet(dy < 0);
    };
    sheetGrip.addEventListener("pointerup", endDrag);
    sheetGrip.addEventListener("pointercancel", endDrag);
    // Belt and braces: if the gesture is interrupted (the OS takes over, the
    // tab is backgrounded) neither pointerup nor pointercancel is guaranteed,
    // and the sheet would be stranded mid-drag with its transition disabled.
    // Losing capture is the one signal that always arrives.
    sheetGrip.addEventListener("lostpointercapture", endDrag);
  }

  map.on("click", closeSheetOnMobile);

  // ---------- boot ----------

  $("#club-total").textContent = TEAMS.length;
  const lgTotal = $("#league-total");
  if (lgTotal) lgTotal.textContent = Object.keys(LEAGUES).length;
  buildFilters();
  buildVisitChips();
  renderTally();
  syncCheckboxes();   // paint the initial on/off state of the league rows
  renderList();


  // A static ground page links in as /centre-circle-finder/?club=<slug> to open
  // the map on one stadium. Resolved before the load handlers so the opening UK
  // fit can be skipped — left in, it fires after the flyTo and pulls the view
  // straight back out. The slug rule must match _tools/grounds.py exactly, or
  // the link silently lands on the default view.
  const focusClub = (() => {
    const want = new URLSearchParams(location.search).get("club");
    if (!want) return null;
    const slugify = (s) => s.toLowerCase().replace(/&/g, " and ").replace(/'/g, "")
      .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    return TEAMS.find((t) => slugify(t.name) === want) || null;
  })();

  map.on("load", () => {
    addClubSource();
    bindLayerInteractions();
    if (focusClub) selectTeam(focusClub);
    else fitUK(false);
  });

  // container can be zero-sized or mid-layout in embedded panes
  const mapEl = document.getElementById("map");
  let needsFit = !focusClub;
  function tryFit() {
    if (needsFit && mapEl.clientWidth > 50 && mapEl.clientHeight > 50) {
      map.resize();
      fitUK(false);
      needsFit = false;
    }
  }
  map.on("load", () => { needsFit = !focusClub; tryFit(); });

  // Re-frame the UK whenever the container changes size — a phone's toolbars
  // sliding in and out, or a rotation. Debounced because iOS fires a burst of
  // resizes during that animation, and skipped once the user has navigated
  // somewhere, so we never yank them back to the UK view.
  let refitTimer = null;
  function refitOnResize() {
    clearTimeout(refitTimer);
    refitTimer = setTimeout(() => {
      if (atDefaultView && !needsFit) fitUK(false);
    }, 160);
  }
  new ResizeObserver(() => {
    map.resize();
    tryFit();
    refitOnResize();
  }).observe(mapEl);
  addEventListener("orientationchange", refitOnResize);
})();
