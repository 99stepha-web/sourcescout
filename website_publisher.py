from homepage_seo import main as generate_homepage_seo
from seo_metadata import enhance_all as enhance_seo_metadata
from seo_generator import generate as generate_seo_files
from catalog_enhancer import enhance, enhance_seo as enhance_catalog_seo
import html
import json
import re
import sqlite3
import subprocess
from affiliate.utils.url_utils import clean_affiliate_url
from pathlib import Path


DB_PATH = Path("data/scout.db")
SITE = Path.home() / "product-finds-website"
PRODUCTS_DIR = SITE / "products"


def clean_affiliate_url(value):
    """
    Return ONLY the real Taobao affiliate URL.

    Accepts:
        https://m.tb.cn/h.xxxxx

    Also accepts:
        [https://m.tb.cn/h.xxxxx](https://m.tb.cn/h.xxxxx)
    """

    value = str(value or "").strip()

    # First extract the URL from anywhere inside the value.
    match = re.search(
        r"https://(?:m\.tb\.cn|s\.click\.taobao\.com)/[A-Za-z0-9._~:/?#\[\]@!$&'*+,;=%-]+",
        value,
    )

    if not match:
        raise ValueError(
            f"Invalid Taobao affiliate URL: {value}"
        )

    url = match.group(0)

    # Remove any trailing Markdown characters.
    url = url.rstrip(")]}>,\"'")

    return url


def get_ready_products():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT
            id,
            title,
            slug,
            article_title,
            article_content,
            affiliate_url,
            image_url,
            price,
            platform
        FROM products
        WHERE article_content IS NOT NULL
          AND article_content != ''
          AND slug IS NOT NULL
          AND slug != ''
          AND affiliate_url IS NOT NULL
          AND affiliate_url != ''
        ORDER BY id ASC
        """
    ).fetchall()

    conn.close()

    return rows


def build_article_html(product):

    article = json.loads(
        product["article_content"]
    )

    title = html.escape(
        article.get(
            "article_title",
            product["title"],
        )
    )

    excerpt = html.escape(
        article.get("excerpt", "")
    )

    introduction = html.escape(
        article.get("introduction", "")
    )

    why_it_stands_out = html.escape(
        article.get(
            "why_it_stands_out",
            "",
        )
    ).replace(
        "\n\n",
        "</p><p>",
    )

    who_its_for = html.escape(
        article.get(
            "who_its_for",
            "",
        )
    )

    things_to_consider = html.escape(
        article.get(
            "things_to_consider",
            "",
        )
    )

    verdict = html.escape(
        article.get("verdict", "")
    )

    # CRITICAL:
    # Always clean the URL immediately before writing HTML.
    raw_affiliate_url = product["affiliate_url"]

    affiliate_url = clean_affiliate_url(
        raw_affiliate_url
    )

    affiliate_url = html.escape(
        affiliate_url,
        quote=True,
    )

    product_title = html.escape(
        product["title"]
    )

    image_url = html.escape(
        product["image_url"] or "",
        quote=True,
    )

    price = html.escape(
        str(product["price"] or "")
    )

    image_html = ""

    if image_url:

        image_html = f"""
        <img
            src="{image_url}"
            alt="{product_title}"
            class="product-image"
            loading="lazy"
        >
        """

    return f"""<!DOCTYPE html>
<html lang="en">

<head>

    <meta name="author" content="SourceScout">



<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>{title} | SourceScout</title>

<style>

body {{
    margin: 0;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Arial,
        sans-serif;
    background: #f7f7f7;
    color: #222;
    line-height: 1.7;
}}

.container {{
    max-width: 850px;
    margin: 0 auto;
    padding: 40px 20px;
}}

.article {{
    background: white;
    padding: 40px;
    border-radius: 14px;
    box-shadow: 0 4px 20px rgba(0,0,0,.06);
}}

h1 {{
    font-size: 36px;
    line-height: 1.2;
}}

h2 {{
    margin-top: 35px;
}}

.excerpt {{
    color: #666;
    font-size: 18px;
    margin-bottom: 30px;
}}

.product-image {{
    display: block;
    max-width: 100%;
    max-height: 500px;
    margin: 25px auto;
    object-fit: contain;
    border-radius: 10px;
}}

.buy-box {{
    margin: 35px 0;
    padding: 25px;
    background: #f3f7ff;
    border-radius: 12px;
    text-align: center;
}}

.price {{
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 15px;
}}

.buy-button {{
    display: inline-block;
    padding: 14px 28px;
    background: #111;
    color: white;
    text-decoration: none;
    border-radius: 8px;
    font-weight: 600;
}}

.disclosure {{
    margin-top: 35px;
    padding-top: 20px;
    border-top: 1px solid #ddd;
    color: #777;
    font-size: 13px;
}}

</style>

</head>

<body>

<div class="container">

<article class="article">

<h1>{title}</h1>

<div class="excerpt">
{excerpt}
</div>

{image_html}

<p>
{introduction}
</p>

<div class="buy-box">

<div class="price">
{price} CNY
</div>

<a
    class="buy-button"
    href="{affiliate_url}"
    target="_blank"
    rel="nofollow sponsored noopener"
>
View Product
</a>

</div>

<h2>Why It Stands Out</h2>

<p>
{why_it_stands_out}
</p>

<h2>Who It's For</h2>

<p>
{who_its_for}
</p>

<h2>Things to Consider</h2>

<p>
{things_to_consider}
</p>

<h2>Our Verdict</h2>

<p>
{verdict}
</p>

<div class="disclosure">
SourceScout may earn a commission if you purchase
through links on this page. This does not affect
the editorial evaluation.
</div>

</article>

</div>

</body>
</html>
"""


def sanitize_published_html(content):
    """
    Final safety layer.

    Converts accidental Markdown-wrapped affiliate URLs
    inside generated HTML into real href URLs.

    Example:

    href="[https://m.tb.cn/h.123](https://m.tb.cn/h.123)"

    becomes:

    href="https://m.tb.cn/h.123"
    """

    from affiliate.utils.url_utils import clean_affiliate_url

    # ---------------------------------------------------------
    # Fix href attributes containing Markdown links
    # ---------------------------------------------------------

    def fix_href(match):
        raw = match.group(1)

        cleaned = clean_affiliate_url(raw)

        if cleaned:
            return f'href="{cleaned}"'

        return match.group(0)

    content = re.sub(
        r'href="([^"]+)"',
        fix_href,
        content,
        flags=re.IGNORECASE,
    )

    # ---------------------------------------------------------
    # Final protection:
    # if a Markdown affiliate URL somehow survived,
    # convert the whole Markdown expression.
    # ---------------------------------------------------------

    def fix_markdown(match):
        raw = match.group(0)

        cleaned = clean_affiliate_url(raw)

        return cleaned if cleaned else raw

    content = re.sub(
        r'\[https://(?:m\.tb\.cn|s\.click\.taobao\.com)/[^\]]+\]\(https://(?:m\.tb\.cn|s\.click\.taobao\.com)/[^)]+\)',
        fix_markdown,
        content,
        flags=re.IGNORECASE,
    )

    # ---------------------------------------------------------
    # HARD VALIDATION
    # ---------------------------------------------------------

    bad = re.findall(
        r'href="\[https://(?:m\.tb\.cn|s\.click\.taobao\.com)/',
        content,
        flags=re.IGNORECASE,
    )

    if bad:
        raise ValueError(
            "❌ Published HTML still contains a Markdown-wrapped "
            "affiliate URL."
        )

    return content


BAD_CONTENT_MARKERS = ("[object Object]", "undefined", "None", "null")


def validate_article(product, content):
    errors = []

    if not (product["title"] or "").strip():
        errors.append("missing title")

    if not content or len(content) < 500:
        errors.append("missing article content")

    if not (product["slug"] or "").strip():
        errors.append("missing slug")

    if not clean_affiliate_url(product["affiliate_url"] or ""):
        errors.append("missing affiliate link")

    if not (product["image_url"] or "").strip():
        errors.append("missing product image")

    if 'class="buy-button"' not in content:
        errors.append("missing CTA")

    if "```" in content:
        errors.append("markdown code fence in HTML")

    for marker in BAD_CONTENT_MARKERS:
        if marker in content:
            errors.append(f"raw '{marker}' in content")

    return errors


def publish():

    PRODUCTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    products = get_ready_products()

    if not products:
        print("\n❌ No products ready for publishing.")
        return []

    published = []

    for product in products:

        try:
            content = build_article_html(product)
            content = sanitize_published_html(content)
        except Exception as e:
            print("\n❌ Article failed validation:")
            print(f"   Product ID: {product['id']}")
            print(f"   Title: {product['title']}")
            print(f"   Failed stage: build/sanitize")
            print(f"   Error: {e}")
            continue

        errors = validate_article(product, content)

        if errors:
            print("\n❌ Article failed validation:")
            print(f"   Product ID: {product['id']}")
            print(f"   Title: {product['title']}")
            print(f"   Failed stage: validation")
            print(f"   Error: {'; '.join(errors)}")
            continue

        clean_url = clean_affiliate_url(
            product["affiliate_url"]
        )

        filename = (
            PRODUCTS_DIR
            / f"{product['slug']}.html"
        )

        filename.write_text(
            content,
            encoding="utf-8",
        )

        _mark_published(product["id"])

        print("\n✅ Published article:")
        print(f"   Product ID: {product['id']}")
        print(f"   Title: {product['title']}")
        print(f"   Affiliate: {clean_url}")
        print(f"   File: {filename}")

        published.append(
            str(filename)
        )

    return published


def _mark_published(product_id):
    """
    Record the first time a product was actually written to disk.
    Only fills published_at if it isn't already set, so republishing
    an unchanged article doesn't reset its original publish date.
    """

    conn = sqlite3.connect(DB_PATH)

    conn.execute(
        """
        UPDATE products
        SET published_at = COALESCE(published_at, CURRENT_TIMESTAMP)
        WHERE id = ?
        """,
        (product_id,),
    )

    conn.commit()
    conn.close()



def generate_products_index():
    """
    Automatically rebuild products.html from every published
    product article in the website repository.
    """

    site_path = Path(SITE)
    products_dir = site_path / "products"
    index_path = site_path / "products.html"

    if not products_dir.exists():
        print("⚠️ Products directory does not exist.")
        return

    articles = sorted(
        products_dir.glob("*.html"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    cards = []

    for article in articles:

        try:
            html = article.read_text(encoding="utf-8")

            title_match = re.search(
                r"<title>(.*?)</title>",
                html,
                re.IGNORECASE | re.DOTALL,
            )

            title = (
                re.sub(r"\s+", " ", title_match.group(1)).strip()
                if title_match
                else article.stem.replace("-", " ").title()
            )

            # Try to extract the first meaningful image.
            image_match = re.search(
                r'<img[^>]+src="([^"]+)"',
                html,
                re.IGNORECASE,
            )

            image = (
                image_match.group(1)
                if image_match
                else ""
            )

            # Extract the article description/excerpt when available.
            description_match = re.search(
                r'<meta[^>]+name="description"[^>]+content="([^"]*)"',
                html,
                re.IGNORECASE,
            )

            description = (
                description_match.group(1).strip()
                if description_match
                else "Independent product research and buying guide from SourceScout."
            )

            url = f"products/{article.name}"

            image_html = (
                f'<img src="{image}" alt="{title}" loading="lazy">'
                if image
                else '<div class="product-placeholder">SourceScout</div>'
            )

            cards.append(
                f"""
                <article class="product-card">
                    <a href="{url}" class="product-image">
                        {image_html}
                    </a>

                    <div class="product-content">
                        <h2>
                            <a href="{url}">{title}</a>
                        </h2>

                        <p>{description}</p>

                        <a href="{url}" class="view-product">
                            View Product →
                        </a>
                    </div>
                </article>
                """
            )

        except Exception as e:
            print(
                f"⚠️ Could not index {article.name}: {e}"
            )

    if not cards:
        cards_html = """
        <div class="empty-state">
            <h2>No products published yet</h2>
            <p>SourceScout is researching new products.</p>
        </div>
        """
    else:
        cards_html = "\n".join(cards)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Products | SourceScout</title>

    <meta
        name="description"
        content="Discover independently researched products, buying guides, and recommendations from SourceScout."
    >

    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Roboto,
                Arial,
                sans-serif;
            background: #f7f8fa;
            color: #171717;
        }}

        header {{
            background: #ffffff;
            border-bottom: 1px solid #e5e7eb;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        .nav {{
            max-width: 1180px;
            margin: auto;
            padding: 18px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .brand {{
            font-size: 22px;
            font-weight: 800;
            text-decoration: none;
            color: #111827;
        }}

        nav a {{
            margin-left: 24px;
            color: #4b5563;
            text-decoration: none;
            font-size: 15px;
        }}

        nav a:hover {{
            color: #111827;
        }}

        .hero {{
            max-width: 1180px;
            margin: auto;
            padding: 60px 24px 30px;
        }}

        .hero h1 {{
            margin: 0 0 12px;
            font-size: clamp(34px, 5vw, 52px);
            line-height: 1.05;
        }}

        .hero p {{
            max-width: 700px;
            color: #6b7280;
            font-size: 18px;
            line-height: 1.7;
            margin: 0;
        }}

        .catalog {{
            max-width: 1180px;
            margin: auto;
            padding: 20px 24px 70px;
        }}

        .product-grid {{
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
        }}

        .product-card {{
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            overflow: hidden;
            transition:
                transform .18s ease,
                box-shadow .18s ease;
        }}

        .product-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 30px rgba(0,0,0,.08);
        }}

        .product-image {{
            display: block;
            height: 230px;
            background: #f3f4f6;
            overflow: hidden;
        }}

        .product-image img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}

        .product-placeholder {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #9ca3af;
            font-weight: 700;
        }}

        .product-content {{
            padding: 22px;
        }}

        .product-content h2 {{
            margin: 0 0 12px;
            font-size: 20px;
            line-height: 1.35;
        }}

        .product-content h2 a {{
            color: #111827;
            text-decoration: none;
        }}

        .product-content p {{
            margin: 0 0 20px;
            color: #6b7280;
            line-height: 1.6;
            font-size: 14px;
        }}

        .view-product {{
            display: inline-block;
            color: #111827;
            font-weight: 700;
            text-decoration: none;
        }}

        .view-product:hover {{
            text-decoration: underline;
        }}

        .empty-state {{
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 60px 30px;
            text-align: center;
        }}

        footer {{
            border-top: 1px solid #e5e7eb;
            background: #ffffff;
            padding: 30px 24px;
            text-align: center;
            color: #6b7280;
            font-size: 14px;
        }}

        @media (max-width: 650px) {{
            .nav {{
                padding: 16px;
            }}

            nav a {{
                margin-left: 12px;
            }}

            .hero,
            .catalog {{
                padding-left: 16px;
                padding-right: 16px;
            }}
        }}
    </style>
</head>

<body>

<header>
    <div class="nav">
        <a href="/" class="brand">SourceScout</a>

        <nav>
            <a href="/">Home</a>
            <a href="/products.html">Products</a>
            <a href="/guides.html">Guides</a>
            <a href="/about.html">About</a>
        </nav>
    </div>
</header>

<main>

    <section class="hero">
        <h1>Product Research</h1>

        <p>
            Explore products researched and evaluated by SourceScout.
            Each product includes independent analysis, important
            considerations, and a direct route to the original listing.
        </p>
    </section>

    <section class="catalog">
        <div class="product-grid">
            {cards_html}
        </div>
    </section>

</main>

<footer>
    © 2026 SourceScout. Product research and affiliate disclosure apply.
</footer>

</body>
</html>
"""

    index_path.write_text(
        page,
        encoding="utf-8",
    )

    print(
        f"✅ Product index generated: "
        f"{len(cards)} published products"
    )



def generate_homepage_products():
    """
    Inject the latest published product cards into index.html.
    """

    site_path = Path(SITE)
    products_dir = site_path / "products"
    homepage = site_path / "index.html"

    if not homepage.exists():
        print("⚠️ index.html not found.")
        return

    articles = sorted(
        products_dir.glob("*.html"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    cards = []

    for article in articles[:6]:

        try:
            html = article.read_text(
                encoding="utf-8"
            )

            title_match = re.search(
                r"<title>(.*?)</title>",
                html,
                re.IGNORECASE | re.DOTALL,
            )

            title = (
                re.sub(
                    r"\s+",
                    " ",
                    title_match.group(1),
                ).strip()
                if title_match
                else article.stem.replace(
                    "-",
                    " ",
                ).title()
            )

            image_match = re.search(
                r'<img[^>]+src="([^"]+)"',
                html,
                re.IGNORECASE,
            )

            image = (
                image_match.group(1)
                if image_match
                else ""
            )

            description_match = re.search(
                r'<meta[^>]+name="description"[^>]+content="([^"]*)"',
                html,
                re.IGNORECASE,
            )

            description = (
                description_match.group(1).strip()
                if description_match
                else "Independent product research from SourceScout."
            )

            url = f"products/{article.name}"

            image_html = (
                f'<img src="{image}" alt="{title}" loading="lazy">'
                if image
                else '<div class="product-placeholder">SourceScout</div>'
            )

            cards.append(
                f"""
                <article class="scout-product-card">
                    <a href="{url}" class="scout-product-image">
                        {image_html}
                    </a>

                    <div class="scout-product-body">
                        <h3>
                            <a href="{url}">{title}</a>
                        </h3>

                        <p>{description}</p>

                        <a href="{url}" class="scout-product-link">
                            Read Research →
                        </a>
                    </div>
                </article>
                """
            )

        except Exception as e:
            print(
                f"⚠️ Homepage product error "
                f"{article.name}: {e}"
            )

    if not cards:
        print("⚠️ No published products for homepage.")
        return

    cards_html = "\n".join(cards)

    homepage_text = homepage.read_text(
        encoding="utf-8"
    )

    start_marker = (
        '<!-- SOURCESCOUT_PRODUCTS_START -->'
    )

    end_marker = (
        '<!-- SOURCESCOUT_PRODUCTS_END -->'
    )

    block = f"""
{start_marker}
<section class="scout-products-section">

    <div class="scout-products-heading">
        <div>
            <span class="scout-eyebrow">
                LATEST RESEARCH
            </span>

            <h2>Featured Products</h2>

            <p>
                Explore our latest independently researched
                product picks.
            </p>
        </div>

        <a href="/products.html" class="scout-view-all">
            View All Products →
        </a>
    </div>

    <div class="scout-product-grid">
        {cards_html}
    </div>

</section>
{end_marker}
"""

    css = """
<style id="sourcescout-product-home-css">
.scout-products-section {
    max-width: 1180px;
    margin: 0 auto;
    padding: 70px 24px;
}

.scout-products-heading {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 30px;
    margin-bottom: 30px;
}

.scout-eyebrow {
    font-size: 12px;
    font-weight: 800;
    letter-spacing: .12em;
    color: #6b7280;
}

.scout-products-heading h2 {
    margin: 8px 0;
    font-size: clamp(30px, 4vw, 42px);
    line-height: 1.1;
}

.scout-products-heading p {
    margin: 0;
    color: #6b7280;
}

.scout-view-all {
    white-space: nowrap;
    color: #111827;
    text-decoration: none;
    font-weight: 700;
}

.scout-product-grid {
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(280px, 1fr));
    gap: 24px;
}

.scout-product-card {
    overflow: hidden;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    transition:
        transform .18s ease,
        box-shadow .18s ease;
}

.scout-product-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 30px rgba(0,0,0,.08);
}

.scout-product-image {
    display: block;
    height: 220px;
    overflow: hidden;
    background: #f3f4f6;
}

.scout-product-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
}

.scout-product-body {
    padding: 20px;
}

.scout-product-body h3 {
    margin: 0 0 10px;
    font-size: 19px;
    line-height: 1.35;
}

.scout-product-body h3 a {
    color: #111827;
    text-decoration: none;
}

.scout-product-body p {
    margin: 0 0 18px;
    color: #6b7280;
    font-size: 14px;
    line-height: 1.6;
}

.scout-product-link {
    color: #111827;
    text-decoration: none;
    font-weight: 700;
}

.scout-product-link:hover {
    text-decoration: underline;
}

.scout-product-body .product-placeholder {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #9ca3af;
    font-weight: 700;
}

@media (max-width: 700px) {
    .scout-products-section {
        padding: 50px 16px;
    }

    .scout-products-heading {
        align-items: flex-start;
        flex-direction: column;
    }
}
</style>
"""

    if start_marker in homepage_text:
        pattern = re.compile(
            re.escape(start_marker)
            + r".*?"
            + re.escape(end_marker),
            re.DOTALL,
        )

        homepage_text = pattern.sub(
            block.strip(),
            homepage_text,
        )

    else:
        body_match = re.search(
            r"</body>",
            homepage_text,
            re.IGNORECASE,
        )

        if not body_match:
            print(
                "⚠️ </body> not found. "
                "Homepage unchanged."
            )
            return

        homepage_text = (
            homepage_text[:body_match.start()]
            + block
            + "\n"
            + homepage_text[body_match.start():]
        )

    if "sourcescout-product-home-css" not in homepage_text:
        head_match = re.search(
            r"</head>",
            homepage_text,
            re.IGNORECASE,
        )

        if head_match:
            homepage_text = (
                homepage_text[:head_match.start()]
                + css
                + "\n"
                + homepage_text[head_match.start():]
            )

    homepage.write_text(
        homepage_text,
        encoding="utf-8",
    )

    print(
        f"✅ Homepage updated with "
        f"{len(cards)} featured products."
    )


def deploy():
    print("\n========== PUBLISH ARTICLES ==========")

    published = publish()

    if not published:
        return

    print("\n========== PRODUCT INDEX ==========")
    generate_products_index()

    print("\n========== HOMEPAGE ==========")
    generate_homepage_products()

    print("\n========== CATALOG FILTERS ==========")
    enhance()
    enhance_catalog_seo()

    print("\n========== SITEMAP + ROBOTS.TXT ==========")
    generate_seo_files()

    print("\n========== SEO METADATA ==========")
    enhance_seo_metadata()

    print("\n========== HOMEPAGE SEO ==========")
    generate_homepage_seo()

    print("\n========== GIT DEPLOY ==========")

    subprocess.run(
        ["git", "add", "."],
        cwd=SITE,
        check=True,
    )

    result = subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "Publish new products and refresh SEO/catalog",
        ],
        cwd=SITE,
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:

        print(result.stdout)

        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=SITE,
            check=True,
        )

        print(
            "\n✅ Website deployed successfully."
        )

    elif "nothing to commit" in (
        result.stdout + result.stderr
    ).lower():

        print(
            "\nℹ️ Nothing new to commit."
        )

    else:

        print(result.stdout)
        print(result.stderr)

        raise RuntimeError(
            "Git commit failed."
        )

    # Google Search Console automation.
    # Never allowed to fail a successful website deployment.
    print("\n========== GOOGLE SEARCH CONSOLE ==========")

    try:
        from google_search_console import build_service, submit_sitemap, inspect_new_urls

        gsc = build_service()
        submit_sitemap(gsc)

        new_urls = [
            "https://sourcescout.store/" + str(Path(p).relative_to(SITE)).replace("\\", "/")
            for p in published
        ]

        inspect_new_urls(gsc, new_urls)

    except (Exception, SystemExit) as e:
        print(f"ℹ️ Google Search Console automation skipped: {e}")


if __name__ == "__main__":
    deploy()
