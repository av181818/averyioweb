# Page generators

These two scripts produce most of the HTML in this repo. **The generated pages are committed** —
the site is plain static HTML and needs no build step to serve. These exist so a change to shared
chrome or app data is one edit instead of twelve.

```bash
cd _tools && python3 gen.py && python3 gen_site.py
```

| Script | Writes |
|---|---|
| `gen.py` | `apps/<slug>/index.html` × 6. Also holds the shared chrome (`head`, `nav`, `footer`, `crumb`), the `APPS` data table and the `ETHOS` block used across the site. |
| `gen_site.py` | `index.html`, `apps.html`, `finance.html`, `contact.html`, `privacy.html`, `404.html`, `sitemap.xml`, `robots.txt`. Imports everything above from `gen.py`. |

Run `gen.py` first — `gen_site.py` reads its helpers and data.

## Read before editing

**Re-running these overwrites hand edits to any generated page.** If you tweak `index.html`
directly and later run the scripts, the tweak is gone. Change the generator instead. The two are
in sync as of the last commit: running both produces a zero diff.

**Not generated — edit these directly:**

- `assets/site.css` — the shared stylesheet. **Re-run the generators after changing it**, because
  the HTML references it with a content hash (`site.css?v=…`) computed by `_css_version()` in
  `gen.py`. Skipping that step lets browsers serve stale CSS against new markup.
- `privacy-*.html` — the five App Store policy pages. **Frozen.** Apple links to these URLs from
  the live listings; never move, rename or restyle them.

## Why the leading underscore

GitHub Pages runs Jekyll, which excludes `_`-prefixed directories from the published output. So
these scripts are version-controlled but are not served from averyio.net.

See `.claude/HANDOFF.md` for the full picture — constraints, gotchas and outstanding work.
