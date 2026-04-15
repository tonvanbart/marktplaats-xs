# map-site Spec Delta

## ADDED Requirements

### Requirement: Single static page
The site SHALL be a single `index.html` file. All marker data SHALL be
inlined into the page at build time; the browser SHALL NOT make any
runtime fetches to Marktplaats or to any backend.

#### Scenario: Browser loads the page offline after initial CDN load
- **WHEN** the user opens the deployed page and network access to
  marktplaats.nl is blocked
- **THEN** the map, marker positions, and popup text SHALL still render
  (thumbnail images MAY fail to load since they are hotlinked)

### Requirement: Map with clustered markers
The page SHALL display a Leaflet map centred on the Netherlands using
OpenStreetMap tiles. Listings SHALL be rendered as markers grouped by
`leaflet.markercluster` to prevent overlap when multiple listings share
a location.

#### Scenario: Multiple listings in the same city
- **WHEN** two or more listings share the same latitude/longitude
- **THEN** they SHALL be grouped into a single cluster marker
- **AND** clicking the cluster SHALL expand it to reveal individual markers

### Requirement: Per-listing popup
Each marker SHALL bind a popup containing: a thumbnail image hotlinked
from the Marktplaats CDN, the listing title, a formatted price, the
city name, and a hyperlink to the full listing on `www.marktplaats.nl`.

#### Scenario: Listing with FIXED price
- **WHEN** a listing has `priceType: FIXED` and `priceCents: 125000`
- **THEN** the popup SHALL show the price as `€ 1.250,-` (or equivalent
  localised format)

#### Scenario: Listing with non-numeric price type
- **WHEN** a listing has `priceType: FAST_BID` and `priceCents: 0`
- **THEN** the popup SHALL show the price as `Bieden` (not `€ 0,00`)

#### Scenario: Reserved listing
- **WHEN** a listing has `reserved: true` or `priceType: RESERVED`
- **THEN** the popup SHALL display a `Gereserveerd` badge

### Requirement: Toggleable layers per saved search
When multiple queries are configured, each query's markers SHALL form
their own Leaflet layer, and the page SHALL render an
`L.control.layers` control so the user can toggle each query on or off
independently.

#### Scenario: User hides one query
- **GIVEN** two queries are configured and both have markers on the map
- **WHEN** the user unchecks one query in the layers control
- **THEN** only markers from the other query SHALL remain visible

### Requirement: Last-updated footer
The page SHALL display a "last updated" timestamp reflecting when the
current build was generated.

#### Scenario: Footer reflects build time
- **WHEN** a build runs at 2026-04-15T06:00:00Z
- **THEN** the deployed page SHALL display that timestamp in a footer

### Requirement: Visible warning on fetch errors
If the build completed with one or more failed queries, the page SHALL
render a visible banner listing which queries failed, so a human visitor
knows the displayed data is incomplete.

#### Scenario: One query fails, one succeeds
- **GIVEN** two queries are configured
- **WHEN** the fetch for query A fails but query B succeeds
- **THEN** the page SHALL render markers for query B
- **AND** SHALL display a banner stating that query A could not be
  fetched in the current build
