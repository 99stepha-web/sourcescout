from pathlib import Path
from html import unescape
from datetime import datetime, timezone
from urllib.parse import quote
import json
import re

SITE_ROOT = Path.home() / "product-finds-website"
PRODUCTS_DIR = SITE_ROOT / "products"
BASE_URL = "https://sourcescout.store"

START = "<!-- SOURCESCOUT_SEO_START -->"
END = "<!-- SOURCESCOUT_SEO_END -->"


def clean_text(value):
    value = unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def get_title(html, filename):
    patterns = [
        r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']',
        r'<h1[^>]*>(.*?)</h1>',
        r'<title[^>]*>(.*?)</title>',
    ]

    for pattern in patterns:
        m = re.search(pattern, html, re.I | re.S)
        if m:
            title = clean_text(m.group(1))
            if title:
                return title

    return Path(filename).stem.replace("-", " ").title()


def get_description(html, title):
    patterns = [
        r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
        r'<p[^>]*>(.*?)</p>',
    ]

    for pattern in patterns:
        m = re.search(pattern, html, re.I | re.S)
        if m:
            text = clean_text(m.group(1))
            if text and text.lower() != title.lower():
                return text[:157].rstrip() + "..."

    return (
        f"Independent product research and buying guide for "
        f"{title}."
    )


def get_image(html):
    patterns = [
        r'<meta\s+property=["\']og:image["\']\s+content=["\'](.*?)["\']',
        r'<img[^>]+src=["\'](.*?)["\']',
    ]

    for pattern in patterns:
        m = re.search(pattern, html, re.I | re.S)
        if m:
            image = m.group(1).strip()
            if image:
                if image.startswith("//"):
                    return "https:" + image
                if image.startswith("/"):
                    return BASE_URL + image
                return image

    return ""


def make_metadata(filename, html):
    title = get_title(html, filename)
    description = get_description(html, title)

    relative = f"/products/{quote(filename)}"
    canonical = BASE_URL + relative

    image = get_image(html)

    today = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d"
    )

    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "dateModified": today,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": canonical,
        },
        "publisher": {
            "@type": "Organization",
            "name": "SourceScout",
            "url": BASE_URL,
        },
    }

    if image:
        article["image"] = [image]

    json_ld = json.dumps(
        article,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    image_tags = ""

    if image:
        image_tags = f"""
<meta property="og:image" content="{image}">
<meta property="og:image:alt" content="{title}">
<meta name="twitter:image" content="{image}">
"""

    return f"""
{START}
<meta name="description" content="{description}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{canonical}">

<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="SourceScout">
{image_tags}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{description}">
<meta name="twitter:url" content="{canonical}">

<script type="application/ld+json">
{json_ld}
</script>
{END}
"""


LEGACY_PATTERNS = [
    r'\s*<meta\s+name=["\']robots["\']\s+content=["\']index,follow["\']>',
    r'\s*<link\s+rel=["\']canonical["\']\s+href=["\']https://sourcescout\.store/["\']>',
    r'\s*<meta\s+property=["\']og:type["\']\s+content=["\']article["\']>',
]


def strip_legacy_tags(html):
    for pattern in LEGACY_PATTERNS:
        html = re.sub(pattern, "", html, flags=re.I)
    return html


def inject(html, metadata):
    html = re.sub(
        r"\n?" + re.escape(START) + r".*?" + re.escape(END) + r"\n?",
        "",
        html,
        flags=re.S,
    )

    html = strip_legacy_tags(html)

    match = re.search(
        r"<head\b[^>]*>",
        html,
        flags=re.I,
    )

    if not match:
        raise RuntimeError("No <head> found")

    position = match.end()

    return (
        html[:position]
        + metadata
        + html[position:]
    )


def enhance_all():
    if not PRODUCTS_DIR.exists():
        raise SystemExit(
            f"❌ Missing products directory: {PRODUCTS_DIR}"
        )

    files = sorted(
        PRODUCTS_DIR.glob("*.html")
    )

    changed = 0

    for file in files:
        html = file.read_text(
            encoding="utf-8"
        )

        # Strip any previously-injected block first so metadata is
        # always derived from the source content, never from our
        # own prior output (avoids compounding truncation on reruns).
        html = re.sub(
            r"\n?" + re.escape(START) + r".*?" + re.escape(END) + r"\n?",
            "",
            html,
            flags=re.S,
        )
        html = strip_legacy_tags(html)

        metadata = make_metadata(
            file.name,
            html,
        )

        updated = inject(
            html,
            metadata,
        )

        if updated != html:
            file.write_text(
                updated,
                encoding="utf-8",
            )
            changed += 1

    print(
        f"✅ SEO metadata installed on "
        f"{changed}/{len(files)} product articles."
    )


if __name__ == "__main__":
    enhance_all()
