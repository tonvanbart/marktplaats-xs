# fetch-pipeline Spec Delta

## ADDED Requirements

### Requirement: Query configuration via YAML
The pipeline SHALL read its list of saved searches from a committed
`queries.yml` file at the repository root. Each entry SHALL specify a
`name` (used as the layer label) and a `url` (the human-facing
marktplaats.nl search URL as pasted from a browser address bar).

#### Scenario: Adding a new search
- **WHEN** a user adds a new `{name, url}` entry to `queries.yml` and
  the next build runs
- **THEN** the pipeline SHALL fetch, parse, and render that query as a
  new layer on the map without any other code changes

### Requirement: Fetch via same URL a browser uses
The pipeline SHALL fetch each configured URL with an HTTP GET and a
realistic `User-Agent` header. It SHALL NOT call any reverse-engineered
internal API endpoint.

#### Scenario: Configured URL is the one copied from the browser
- **GIVEN** a `queries.yml` entry with
  `url: https://www.marktplaats.nl/l/motoren/motoren-yamaha/q/xs650/`
- **WHEN** the pipeline runs
- **THEN** it SHALL GET that exact URL (no query parameter rewriting)

### Requirement: Extract listings from `__NEXT_DATA__`
The pipeline SHALL locate the `<script id="__NEXT_DATA__"
type="application/json">…</script>` element in the response body,
`json.loads()` its contents, and read listings from
`props.pageProps.searchRequestAndResponse.listings`.

#### Scenario: Page missing `__NEXT_DATA__`
- **WHEN** a fetched page does not contain a `__NEXT_DATA__` script tag
- **THEN** the pipeline SHALL record an error for that query
- **AND** SHALL NOT abort the overall build

### Requirement: Normalise listings for rendering
For each listing, the pipeline SHALL produce a render-friendly record
containing at minimum: stable `id` (`itemId`), `title`, absolute `url`
(`https://www.marktplaats.nl` + `vipUrl`), `lat`, `lon`, `city`
(`location.cityName`), `thumbUrl` (`pictures[0].mediumUrl`, or `null`
if absent), `priceDisplay`, `date`, `sellerName`, and `reserved`.

#### Scenario: Listing without pictures
- **WHEN** a listing has an empty `pictures` array
- **THEN** `thumbUrl` SHALL be `null`
- **AND** the popup SHALL render without an `<img>` tag

### Requirement: Price display handles all known `priceType` values
The pipeline SHALL produce a human-readable `priceDisplay` string
according to this mapping: `FIXED` → `€ X,YY`; `MIN_BID` →
`€ X,YY (vanaf)`; `FAST_BID` → `Bieden`; `RESERVED` → `Gereserveerd`;
any unknown value → `—`.

#### Scenario: Unknown price type
- **WHEN** a listing has `priceType: "SOME_NEW_VALUE"` not in the
  known set
- **THEN** `priceDisplay` SHALL be the literal string `—`
- **AND** no exception SHALL be raised

### Requirement: Per-query error isolation
The pipeline SHALL wrap each query's fetch-and-parse step in its own
error boundary. A failure in one query SHALL NOT prevent other queries
from being processed, and SHALL NOT cause the build to exit non-zero.

#### Scenario: First query fails
- **GIVEN** two queries A and B are configured
- **WHEN** fetching query A raises an exception
- **THEN** the pipeline SHALL still fetch and render query B
- **AND** SHALL exit 0
- **AND** SHALL include an error record for query A in the render
  context so the template can display a warning banner

### Requirement: Output location
The pipeline SHALL write the rendered page to `site/index.html` and
SHALL create the `site/` directory if it does not exist.

#### Scenario: Fresh checkout with no `site/` directory
- **GIVEN** the `site/` directory does not exist
- **WHEN** the pipeline runs to completion
- **THEN** the `site/` directory SHALL be created
- **AND** `site/index.html` SHALL contain the rendered page
