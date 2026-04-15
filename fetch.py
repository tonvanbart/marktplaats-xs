from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
QUERIES_FILE = ROOT / "queries.yml"
TEMPLATES_DIR = ROOT / "templates"
SITE_DIR = ROOT / "site"
OUTPUT_FILE = SITE_DIR / "index.html"

MARKTPLAATS_BASE = "https://www.marktplaats.nl"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(.*?)</script>',
    re.DOTALL,
)


def load_queries() -> list[dict]:
    with QUERIES_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return list(data.get("queries") or [])


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
    }
    with httpx.Client(headers=headers, follow_redirects=True, timeout=30.0) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.text


def extract_next_data(html: str) -> dict:
    match = NEXT_DATA_RE.search(html)
    if not match:
        raise ValueError("__NEXT_DATA__ script tag not found in response")
    return json.loads(match.group(1))


def extract_listings(next_data: dict) -> list[dict]:
    try:
        return (
            next_data["props"]["pageProps"]["searchRequestAndResponse"]["listings"]
            or []
        )
    except (KeyError, TypeError) as exc:
        raise ValueError(f"listings path missing in __NEXT_DATA__: {exc}") from exc


def format_price(price_info: dict | None) -> str:
    if not price_info:
        return "—"
    ptype = price_info.get("priceType")
    cents = price_info.get("priceCents", 0) or 0

    def euros(c: int) -> str:
        whole, frac = divmod(c, 100)
        whole_str = f"{whole:,}".replace(",", ".")
        if frac == 0 and price_info.get("suppressZeroCents", False):
            return f"€ {whole_str},-"
        return f"€ {whole_str},{frac:02d}"

    if ptype == "FIXED":
        return euros(cents)
    if ptype == "MIN_BID":
        return f"{euros(cents)} (vanaf)"
    if ptype == "FAST_BID":
        return "Bieden"
    if ptype == "RESERVED":
        return "Gereserveerd"
    return "—"


def normalise_listing(raw: dict) -> dict | None:
    location = raw.get("location") or {}
    lat = location.get("latitude")
    lon = location.get("longitude")
    if lat is None or lon is None:
        return None

    pictures = raw.get("pictures") or []
    thumb_url = None
    if pictures:
        thumb_url = pictures[0].get("mediumUrl")

    vip_url = raw.get("vipUrl") or ""
    if vip_url.startswith("/"):
        absolute_url = MARKTPLAATS_BASE + vip_url
    else:
        absolute_url = vip_url

    return {
        "id": raw.get("itemId"),
        "title": raw.get("title") or "",
        "url": absolute_url,
        "lat": lat,
        "lon": lon,
        "city": location.get("cityName") or "",
        "thumbUrl": thumb_url,
        "priceDisplay": format_price(raw.get("priceInfo")),
        "date": raw.get("date") or "",
        "sellerName": (raw.get("sellerInformation") or {}).get("sellerName") or "",
        "reserved": bool(raw.get("reserved")),
    }


def process_query(query: dict) -> dict:
    name = query.get("name") or "(unnamed)"
    url = query.get("url")
    if not url:
        return {"name": name, "url": None, "listings": [], "error": "missing url"}

    try:
        html = fetch_html(url)
        next_data = extract_next_data(html)
        raw_listings = extract_listings(next_data)
        listings = [n for n in (normalise_listing(r) for r in raw_listings) if n]
        print(f"[ok] {name}: {len(listings)} listings", file=sys.stderr)
        return {"name": name, "url": url, "listings": listings, "error": None}
    except Exception as exc:
        print(f"[error] {name}: {exc}", file=sys.stderr)
        return {"name": name, "url": url, "listings": [], "error": str(exc)}


def render(results: list[dict]) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml", "j2"]),
    )
    template = env.get_template("index.html.j2")
    return template.render(
        results=results,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        has_errors=any(r["error"] for r in results),
    )


def main() -> int:
    queries = load_queries()
    if not queries:
        print("No queries configured in queries.yml", file=sys.stderr)

    results = [process_query(q) for q in queries]
    html = render(results)

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
