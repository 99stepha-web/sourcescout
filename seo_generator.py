from pathlib import Path
from xml.sax.saxutils import escape
from datetime import datetime, timezone
import re

SITE_ROOT = Path.home() / "product-finds-website"
BASE = "https://sourcescout.store"


def product_title(html):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S | re.I)
    if not m:
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    if not m:
        return "SourceScout Product"
    return re.sub(r"<[^>]+>", "", m.group(1)).strip()


def lastmod(path):
    return datetime.fromtimestamp(
        path.stat().st_mtime, tz=timezone.utc
    ).strftime("%Y-%m-%d")


def generate():

    products_dir = SITE_ROOT / "products"
    files = sorted(products_dir.glob("*.html"))

    urls = [
        (f"{BASE}/", lastmod(SITE_ROOT / "index.html")),
        (f"{BASE}/products.html", lastmod(SITE_ROOT / "products.html")),
    ]

    for file in files:
        urls.append(
            (f"{BASE}/products/{file.name}", lastmod(file))
        )

    entries = []

    for url, mod in urls:
        entries.append(
            f"""  <url>
    <loc>{escape(url)}</loc>
    <lastmod>{mod}</lastmod>
  </url>"""
        )

    sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
%s
</urlset>
""" % "\n".join(entries)

    (SITE_ROOT / "sitemap.xml").write_text(
        sitemap,
        encoding="utf-8",
    )

    robots = f"""User-agent: *
Allow: /

Sitemap: {BASE}/sitemap.xml
"""

    (SITE_ROOT / "robots.txt").write_text(
        robots,
        encoding="utf-8",
    )

    print(
        f"✅ sitemap.xml generated: {len(urls)} URLs"
    )
    print("✅ robots.txt generated")


if __name__ == "__main__":
    generate()
