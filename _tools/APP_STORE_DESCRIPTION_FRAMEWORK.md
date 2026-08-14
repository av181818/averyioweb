# App Store description framework

The reusable skeleton for every averyio app description, so the ethos reads
identically across the line-up: **pay once, no subscriptions, no ads, no
tracking, small and fast, nothing bolted on**.

Built 2026-08-14 from the audit of the five live listings: the structure below
is what the strongest ones (Tap Dot Tap, Surge) already do, made uniform.
Plain text only — the App Store renders no formatting. `•` for bullets, CAPS
for section headers, hard limit 4,000 characters.

---

## The skeleton

```
[HOOK — one sentence: what the app is and who it is for.]

Pay once and it's yours forever. No subscriptions, no in-app purchases, no ads — every feature included.

[BODY LEAD — one or two sentences on how it works or why it is different.]

[SECTION 1 — CAPS HEADER, the app's core capability]
• [feature]
• [feature]
• [feature]

[SECTION 2 — CAPS HEADER, second capability or "MAKE IT YOURS" etc.]
• [feature]
• [feature]

BUILT RIGHT
• Pay once, own it for life — the price you see is everything
• No subscriptions, no in-app purchases, no upsells
• No ads, ever
• Megabytes, not gigabytes — no ad libraries, no analytics SDKs, nothing that isn't the app itself
• [PRIVACY LINE — pick the matching variant below]
• Designed for iPhone and iPad

[CLOSE — one line: Download {App} and {the payoff}.]
```

## Privacy-line variants

The one line that must differ per app, because the truth differs:

| App | Line |
|---|---|
| Default (Surge, Big Time Clock) | `No account, no sign-up, no tracking, no data collection` |
| InvestFast | `No account, no tracking — Apple's privacy label reads Data Not Collected` |
| Lume | `No tracking, no account — Apple's privacy label reads Data Not Collected. Sync runs through your own private iCloud, never our servers` |
| Tap Dot Tap | `No account, no tracking — the leaderboard is opt-in, and nothing is shared until you say so` |

**Why Lume's "Data Not Collected" is honest despite iCloud sync** (verified on the live store
2026-08-14 — all five apps carry that label): Apple defines "collect" as transmitting data off
the device *in a way the developer can access*. Lume's sync uses the user's private iCloud
database, which averyio cannot read, so nothing is collected. The label breaks the moment sync
moves to any developer-accessible backend, or any analytics/crash SDK ships — redeclare it and
rewrite this line before either of those ever happens.

## The rules

1. **Lines that are verbatim across every app, never reworded:** the pay-once
   line (line 2) and the whole BUILT RIGHT block apart from the privacy line.
   Consistency across listings is the point of the framework.
2. **Position is the message.** The hook + pay-once line must both sit in the
   first three lines — that is all the store shows before "more". This was the
   audit's main finding: Lume buried the model at 80% depth, Big Time Clock
   omitted it entirely.
3. **Never a price amount or currency symbol.** Descriptions are worldwide;
   £1.99 is wrong in every other storefront. "Pay once" carries the model
   without the number.
4. **Size claims are qualitative** — "megabytes, not gigabytes" — never
   "under X MB", which goes stale with a release. One tolerated exception:
   Surge may keep "the whole timer is under a megabyte" while it has headroom
   (0.7 MB as of v1.2.0).
5. **Counts of the app's own content are fine** (144 lessons, 12 ranks, five
   skins); counts across the portfolio are not (same rule as the site).
6. **"Every future update" is a commitment, not filler.** InvestFast and Lume
   currently promise it. Keep it only while a paid major-version upgrade is
   genuinely off the table; adding it to the shared block would make that
   promise for every app at once, so it stays per-app and deliberate.
7. **The site mirrors the listing** (owner directive 2026-07-29), so a
   description edit is a site-copy trigger: after a new listing goes live,
   re-check the app's page copy against it.

## Filled example — Big Time Clock

The app that currently has no model language at all; this is the full rework:

```
Big Time Clock turns your iPhone or iPad into a gorgeous full-screen clock — for your bedside table, desk, kitchen or studio.

Pay once and it's yours forever. No subscriptions, no in-app purchases, no ads — every feature included.

A clean black canvas. Crisp white numerals. No clutter, no distractions — just the time, readable from across the room.

FEATURES
• Full-screen digital clock with massive, easy-to-read numerals
• Elegant analog clock with smoothly sweeping red second hand
• Works beautifully in portrait and landscape — just rotate
• 12-hour or 24-hour format
• Light or bold typography
• Day and date display, on or off
• Screen stays awake so you never miss the time
• Auto-hiding controls — one tap to reveal, another to hide

PERFECT FOR
• Bedside nightstand clock
• Desk and home-office display
• Kitchen, studio, gym or classroom
• An old iPhone or iPad repurposed as a dedicated clock
• Hotel rooms and travel

BUILT RIGHT
• Pay once, own it for life — the price you see is everything
• No subscriptions, no in-app purchases, no upsells
• No ads, ever
• Megabytes, not gigabytes — no ad libraries, no analytics SDKs, nothing that isn't the app itself
• No account, no sign-up, no tracking, no data collection
• Designed for iPhone and iPad

Download Big Time Clock and give the time the screen it deserves.
```

## Submission checklist (per app, when applying)

- [ ] Hook + pay-once line inside the first three lines
- [ ] BUILT RIGHT block present and verbatim, correct privacy variant
- [ ] No currency amounts anywhere
- [ ] "iPad" mentioned (InvestFast and Tap Dot Tap were missing it)
- [ ] Subtitle checked against the ethos while in App Store Connect
- [ ] After the listing is live: re-run the site mirror check
