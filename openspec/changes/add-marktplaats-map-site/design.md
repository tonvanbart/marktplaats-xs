# Design

## Context

Personal project. Goal: given one or more Marktplaats search URLs, produce a
static website showing the results as markers on a map of the Netherlands.
Rebuilt once per day by GitHub Actions and published via GitHub Pages. No
state, no history, no notifications — each run is a full snapshot that
replaces the previous one.

Constraints:

- Zero hosting cost.
- No API keys, no secrets, no billing accounts.
- Tolerant of upstream breakage (one query failing must not kill the build).
- Small and boring: one script, one template, one workflow.

## Goals / Non-Goals

**Goals**

- Render a single Leaflet map with clustered markers for all listings.
- Popup per marker: thumbnail, title, price (handling non-numeric price
  types), city, and a link to the full listing on marktplaats.nl.
- Support multiple saved searches configured in one YAML file, each becoming
  a toggleable map layer.
- Rebuild daily via cron and on manual workflow dispatch.
- Deploy as a GitHub Pages artifact — no commits to any branch.

**Non-Goals**

- No RSS, no KML, no notifications, no "what's new since last time".
- No persistent state of any kind (no `state.json`, no database, no cache).
- No client-side fetches — the browser loads one static HTML file and the
  marker data is inlined.
- No image downloading or resizing — thumbnails are hotlinked from
  Marktplaats' CDN at their existing `mediumUrl` size.
- No authentication, no rate-limit backoff beyond a simple retry.
- No real-time freshness; "best effort, daily-ish" matches GitHub Actions'
  scheduled-workflow guarantees.

## Decisions

### Data source: `__NEXT_DATA__` from the human-facing URL

Marktplaats category/search pages embed the full listing data as a JSON blob
inside `<script id="__NEXT_DATA__" type="application/json">…</script>`.
Confirmed during exploration: `props.pageProps.searchRequestAndResponse.listings`
contains an array where each entry has `title`, `vipUrl`, `priceInfo`,
`location.latitude`, `location.longitude`, `location.cityName`, `pictures[]`,
`date`, and more.

**Why not the internal `/lrp/api/search` endpoint?** Using the same URL a
browser uses is less fragile and less "scraping-ish": no reverse-engineered
parameters, no headers to spoof beyond a plausible `User-Agent`, and it
matches exactly what the user sees when they copy a URL from the address
bar.

**Alternative considered:** parsing rendered HTML with BeautifulSoup.
Rejected — the JSON blob is already structured, so a single regex to extract
it plus `json.loads()` is simpler and more robust than DOM traversal.

### Map stack: Leaflet + `leaflet.markercluster` + OpenStreetMap tiles

Leaflet is free, keyless, has a tiny footprint, and loads from a CDN with
two `<script>` tags. Marker clustering is essential because multiple
listings from the same city will pile up on the same coordinates.
OpenStreetMap tiles via the standard `tile.openstreetmap.org` URL template
are fine for a low-traffic personal site.

**Alternative considered:** Google Maps JS API. Rejected — requires an API
key exposed in static HTML, a Google Cloud billing account even on the free
tier, and adds referrer-restriction plumbing. Leaflet removes all of that.

### No image processing

Marktplaats pictures come with several pre-sized variants:
`extraSmallUrl`, `mediumUrl`, `largeUrl`, `extraExtraLargeUrl`. `mediumUrl`
(~82px) is the right size for a popup thumbnail. Hotlinking it directly
means **no Pillow dependency**, no image downloads, no artifact bloat, and
the template just embeds the Marktplaats CDN URL as an `<img src="…">`.

**Risk:** Marktplaats could block hotlinking or rotate image URLs between
daily rebuilds. Acceptable — the next daily build fetches fresh URLs.

### Price rendering is polymorphic

`priceInfo.priceType` varies:

| priceType  | Render as                          |
| ---------- | ---------------------------------- |
| `FIXED`    | `€ {priceCents/100}`               |
| `MIN_BID`  | `€ {priceCents/100} (vanaf)`       |
| `FAST_BID` | `Bieden`                           |
| `RESERVED` | `Gereserveerd`                     |
| other      | `—`                                |

Handled by a small Jinja filter. `priceCents: 0` combined with
`FAST_BID`/`RESERVED` is expected and must not show `€ 0,00`.

### Configuration: `queries.yml`

A plain YAML file with a list of `{name, url}` entries, committed to the
repo. Editing this file is the only way to change what the site tracks.
Example:

```yaml
queries:
  - name: "Yamaha XS650"
    url:  "https://www.marktplaats.nl/l/motoren/motoren-yamaha/q/xs650/"
```

Each query becomes a **toggleable Leaflet layer** controlled via
`L.control.layers`. A user can hide/show individual searches on the map.

### Deploy: `actions/deploy-pages` (artifact upload, no commits)

The workflow uploads `./site/` as a Pages artifact and GitHub serves it
directly. No `gh-pages` branch, no `/docs` in `main`, no commits per cron
tick. Stateless builds fit this deployment shape perfectly.

Requires in the workflow:

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
environment:
  name: github-pages
```

### Schedule: daily cron + manual dispatch

```yaml
on:
  schedule:
    - cron: "0 6 * * *"   # 06:00 UTC, once per day
  workflow_dispatch:
```

GitHub cron is best-effort; 24-hour cadence makes delays invisible.

### Error handling: per-query graceful degradation

`fetch.py` loops over queries in a try/except. A failed query logs the
error and is replaced on the page by a visible "couldn't fetch X today"
note. The build exits 0 as long as at least the template renders. One
broken query never takes down the whole site.

### Output layout

```
site/
└── index.html    # single self-contained page, all marker data inlined
```

That is the entire deployed artifact. One file. CSS/JS for Leaflet comes
from CDN `<link>`/`<script>` tags.

## Risks / Trade-offs

- **Upstream fragility.** If Marktplaats removes `__NEXT_DATA__`, changes
  its shape, or gates GitHub Actions runner IPs, the fetch breaks silently
  between daily builds. Mitigation: graceful per-query errors, accept that
  this is a fun project that may rot.
- **Coordinate precision is fuzzed.** Lat/lon appears to be neighbourhood-
  level, not street-level. Fine for a map overview; not fine if you
  expected house-level pins. Documented, no mitigation needed.
- **No deduplication.** A listing that appears in two different saved
  searches will produce two markers at the same point. Acceptable — cluster
  expansion shows both, and each is from a different "layer" anyway.
- **Hotlinked images could disappear.** See "no image processing" — the
  next daily rebuild replaces stale URLs.

## Migration Plan

Not applicable — greenfield repository, no existing data or users.

## Open Questions

- None blocking. Reasonable defaults can be chosen for cosmetic choices
  (map centre/zoom, colour per layer, popup styling) during implementation.
