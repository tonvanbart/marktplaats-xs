# Add Marktplaats Map Site

## Why

For fun and personal interest, track one or more Marktplaats saved searches
and visualise the results as markers on a map. Each daily rebuild shows where
in the Netherlands the currently-listed items are, with a thumbnail and basic
details available on click/hover. No real-time needs, no notifications, no
state — just a daily snapshot deployed to GitHub Pages.

## What Changes

- **NEW capability: `map-site`** — a statically-generated single-page site
  that renders Marktplaats search results as clustered markers on a Leaflet
  map, with a popup per marker containing a thumbnail, title, price, city,
  and a link to the listing.
- **NEW capability: `fetch-pipeline`** — a Python script that reads a YAML
  list of Marktplaats search URLs, fetches each page, extracts the
  `__NEXT_DATA__` JSON blob, normalises the listings, and renders the site
  via a Jinja2 template.
- **NEW capability: `deploy-workflow`** — a GitHub Actions workflow that runs
  the fetch pipeline on a daily cron and on manual dispatch, then publishes
  the generated `site/` directory via `actions/deploy-pages`.

No existing capabilities are modified (this is a greenfield repository).

## Impact

- **Affected specs:** new capabilities `map-site`, `fetch-pipeline`,
  `deploy-workflow` (all ADDED).
- **Affected code:** new files only — `fetch.py`, `templates/index.html.j2`,
  `queries.yml`, `.github/workflows/update.yml`, `.gitignore`,
  `requirements.txt`.
- **External dependencies:** Marktplaats serves listing data inside a
  `<script id="__NEXT_DATA__">` tag on its category/search pages. If that
  embedding changes or GitHub Actions runner IPs get bot-gated, the fetch
  will break. Accepted as a "fun project" risk; mitigated only by
  per-query error handling so one broken query does not kill the build.
- **Cost:** zero (GitHub Pages + Actions free tier, OpenStreetMap tiles,
  no API keys).
