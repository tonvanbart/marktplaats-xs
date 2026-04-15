# Tasks

## 1. Repository scaffolding
- [x] 1.1 Create `.gitignore` (ignore `site/`, `__pycache__/`, `.venv/`)
- [x] 1.2 Create `requirements.txt` with `httpx`, `jinja2`, `pyyaml`
- [x] 1.3 Create `queries.yml` with one example query
      (`Yamaha XS650` → `https://www.marktplaats.nl/l/motoren/motoren-yamaha/q/xs650/`)
- [x] 1.4 Create empty `site/` directory placeholder (or let fetch.py create it)

## 2. Fetch pipeline (`fetch.py`)
- [x] 2.1 Load `queries.yml` into a list of `{name, url}` dicts
- [x] 2.2 For each query, GET the URL with a realistic `User-Agent` header
- [x] 2.3 Extract `<script id="__NEXT_DATA__" type="application/json">…</script>`
      via a single regex; `json.loads()` the body
- [x] 2.4 Navigate to `props.pageProps.searchRequestAndResponse.listings`
- [x] 2.5 Normalise each listing into a render-friendly dict:
      `id`, `title`, `url` (absolute), `lat`, `lon`, `city`, `thumbUrl`,
      `priceDisplay`, `date`, `sellerName`, `reserved`
- [x] 2.6 Implement price rendering for `FIXED`, `MIN_BID`, `FAST_BID`,
      `RESERVED`, and unknown types
- [x] 2.7 Wrap each query in try/except; collect a per-query error
      structure on failure so the template can render a notice
- [x] 2.8 Render `templates/index.html.j2` with the collected query
      results and write to `site/index.html`

## 3. Template (`templates/index.html.j2`)
- [x] 3.1 HTML skeleton with Leaflet CSS/JS and `leaflet.markercluster`
      CSS/JS loaded from a public CDN
- [x] 3.2 Full-viewport `<div id="map">` with basic CSS
- [x] 3.3 Initialise a Leaflet map centred roughly on the Netherlands
      (e.g. `[52.2, 5.3]`, zoom 7) with an OpenStreetMap tile layer
- [x] 3.4 For each query, create a `L.markerClusterGroup()` as its own
      layer; add markers from the inlined data array
- [x] 3.5 Bind a popup to each marker containing:
      thumbnail, title, price, city, "reserved" badge if applicable,
      and a link to the marktplaats.nl listing
- [x] 3.6 Add an `L.control.layers` (overlays) so the user can toggle
      each query on/off
- [x] 3.7 Render a small "last updated" footer with the build timestamp
- [x] 3.8 Render a visible warning banner if any query returned an error

## 4. GitHub Actions workflow (`.github/workflows/update.yml`)
- [x] 4.1 Triggers: `schedule: cron "0 6 * * *"` and `workflow_dispatch`
- [x] 4.2 `permissions: contents: read, pages: write, id-token: write`
- [x] 4.3 `environment: name: github-pages`
- [x] 4.4 Steps: checkout → setup-python 3.12 → pip install -r requirements.txt
      → `python fetch.py` → `actions/configure-pages` →
      `actions/upload-pages-artifact` with `path: ./site` →
      `actions/deploy-pages`
- [ ] 4.5 Verify the workflow runs green on manual dispatch from a test branch

## 5. GitHub Pages configuration
- [ ] 5.1 In repo settings, set Pages source to "GitHub Actions"
- [ ] 5.2 Confirm first deploy publishes `index.html` at the Pages URL

## 6. Smoke test
- [ ] 6.1 Trigger the workflow manually
- [ ] 6.2 Open the deployed page and verify markers appear on the map
- [ ] 6.3 Click a marker and verify the popup shows thumbnail, title, price,
      and a working link to the listing
- [ ] 6.4 Toggle a layer on/off via the layers control
- [ ] 6.5 Confirm "last updated" footer reflects the latest run
