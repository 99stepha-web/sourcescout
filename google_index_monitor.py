from pathlib import Path
import subprocess
import sys

SITE = Path.home() / "product-finds-website"
PRODUCTS = SITE / "products"

urls = [
    "https://sourcescout.store/",
    "https://sourcescout.store/products.html",
]

urls.extend(
    f"https://sourcescout.store/products/{p.name}"
    for p in sorted(PRODUCTS.glob("*.html"))
)

print(
    f"Found {len(urls)} URLs for Search Console inspection."
)

for url in urls:
    print(url)

print(
    "\nRun inspection with:"
)
print(
    "python google_search_console.py "
    + " ".join(urls[:2])
)
