"""
Lightweight local audit for the published website.

Scans index.html, products.html, and products/*.html for:
  - broken internal links (hrefs pointing at local files that don't exist)
  - missing local images
  - invalid/missing canonical URLs
  - missing metadata (title, description, canonical, OG tags)
  - duplicate canonical URLs across pages

No network access — everything is checked against the local filesystem.
"""

import re
from pathlib import Path
from urllib.parse import urlsplit, unquote

SITE = Path.home() / "product-finds-website"
BASE_URL = "https://sourcescout.store"

REQUIRED_META = [
    (r'<title>.*?</title>', "title"),
    (r'<meta\s+name=["\']description["\']', "meta description"),
    (r'<link\s+rel=["\']canonical["\']', "canonical link"),
    (r'<meta\s+property=["\']og:title["\']', "og:title"),
    (r'<meta\s+property=["\']og:description["\']', "og:description"),
    (r'<meta\s+property=["\']og:image["\']', "og:image"),
]


def local_target_exists(href, source_dir):
    if href.startswith(("http://", "https://", "mailto:", "tel:", "#", "javascript:")):
        return True

    path = unquote(urlsplit(href).path)
    if not path:
        return True

    if path.startswith("/"):
        return (SITE / path.lstrip("/")).exists()

    return (source_dir / path).resolve().exists()


def audit_file(path):
    errors = []
    html = path.read_text(encoding="utf-8")

    for pattern, label in REQUIRED_META:
        if not re.search(pattern, html, re.I | re.S):
            errors.append(f"missing {label}")

    canonical_match = re.search(
        r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']',
        html,
        re.I,
    )
    canonical = canonical_match.group(1) if canonical_match else None

    if canonical and not canonical.startswith(BASE_URL):
        errors.append(f"canonical does not start with {BASE_URL}: {canonical}")

    for href in re.findall(r'href=["\']([^"\']+)["\']', html):
        if href.startswith(BASE_URL):
            href = href[len(BASE_URL):] or "/"
        if not local_target_exists(href, path.parent):
            errors.append(f"broken internal link: {href}")

    for src in re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html):
        if src.startswith(("http://", "https://", "data:")):
            continue
        if not local_target_exists(src, path.parent):
            errors.append(f"missing local image: {src}")

    ids = re.findall(r'\sid=["\']([^"\']+)["\']', html)
    seen = set()
    for id_value in ids:
        if id_value in seen:
            errors.append(f"duplicate id: {id_value}")
        seen.add(id_value)

    if path.parent.name == "products":
        buy_tags = re.findall(r"<a\b[^>]*?>", html, re.S)
        affiliate_hrefs = []

        for tag in buy_tags:
            if "buy-button" not in tag:
                continue
            href_match = re.search(r'href=["\']([^"\']+)["\']', tag, re.S)
            if href_match:
                affiliate_hrefs.append(href_match.group(1))

        if not affiliate_hrefs:
            errors.append("missing CTA (no buy-button link)")
        elif not any(
            "m.tb.cn/" in h or "s.click.taobao.com/" in h
            for h in affiliate_hrefs
        ):
            errors.append(f"invalid affiliate URL: {affiliate_hrefs[0]}")

    return errors, canonical


def main():
    targets = [SITE / "index.html", SITE / "products.html"]
    targets += sorted((SITE / "products").glob("*.html"))

    canonicals = {}
    total_errors = 0

    for path in targets:
        if not path.exists():
            print(f"❌ {path.relative_to(SITE)}: file missing")
            total_errors += 1
            continue

        errors, canonical = audit_file(path)

        if canonical:
            canonicals.setdefault(canonical, []).append(path.name)

        if errors:
            total_errors += len(errors)
            print(f"❌ {path.relative_to(SITE)}")
            for e in errors:
                print(f"   - {e}")

    dupes = {url: files for url, files in canonicals.items() if len(files) > 1}

    if dupes:
        print("\n❌ Duplicate canonical URLs:")
        for url, files in dupes.items():
            print(f"   {url}: {files}")
        total_errors += len(dupes)

    print(f"\n{'✅ No issues found.' if total_errors == 0 else f'⚠️ {total_errors} issue(s) found.'}")

    return total_errors


if __name__ == "__main__":
    main()
