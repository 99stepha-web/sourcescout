from pathlib import Path

from google_search_console import filter_new_urls

SITE = Path.home() / "product-finds-website"
PRODUCTS = SITE / "products"

BASE_URLS = [
    "https://sourcescout.store/",
    "https://sourcescout.store/products.html",
]


def all_product_urls():
    return [
        f"https://sourcescout.store/products/{p.name}"
        for p in sorted(PRODUCTS.glob("*.html"))
    ]


def main():
    urls = BASE_URLS + all_product_urls()
    new_urls = filter_new_urls(urls)

    print(f"Found {len(urls)} total published URLs.")
    print(f"{len(new_urls)} never inspected.")

    for url in new_urls:
        print(url)

    if new_urls:
        print("\nRun inspection with:")
        print("python google_search_console.py " + " ".join(new_urls))


if __name__ == "__main__":
    main()
