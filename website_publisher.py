import html
import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote

from database import SessionLocal
from models import Product


# ==================================================
# CONFIGURATION
# ==================================================

WEBSITE_ROOT = Path("/Users/pro/product-finds-website")
PRODUCTS_DIR = WEBSITE_ROOT / "products"

PRODUCTS_PAGE = WEBSITE_ROOT / "products.html"
SITEMAP_FILE = WEBSITE_ROOT / "sitemap.xml"

SITE_URL = "https://sourcescout.store"

PRODUCTS_START_MARKER = "<!-- AUTO-PRODUCTS-START -->"
PRODUCTS_END_MARKER = "<!-- AUTO-PRODUCTS-END -->"


# ==================================================
# BASIC HELPERS
# ==================================================

def escape(value):
    """Safely escape text for HTML."""

    if value is None:
        return ""

    return html.escape(
        str(value),
        quote=True,
    )


def format_price(value):
    """Format price safely."""

    if value is None:
        return "N/A"

    try:
        return f"${float(value):,.2f}"

    except (TypeError, ValueError):
        return escape(value)


def humanize_key(key):
    """Convert JSON field names into headings."""

    return (
        str(key)
        .replace("_", " ")
        .strip()
        .title()
    )


def clean_text(value):
    """Normalize text for summaries and metadata."""

    if not value:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()


def truncate(value, length=180):
    """Safely shorten text."""

    value = clean_text(value)

    if len(value) <= length:
        return value

    return (
        value[:length]
        .rsplit(" ", 1)[0]
        + "..."
    )


# ==================================================
# ARTICLE CONTENT PARSING
# ==================================================

def strip_json_fences(content):
    """Remove accidental ```json code fences."""

    if not content:
        return ""

    content = str(content).strip()

    if content.startswith("```"):

        content = re.sub(
            r"^```(?:json)?\s*",
            "",
            content,
            flags=re.IGNORECASE,
        )

        content = re.sub(
            r"\s*```$",
            "",
            content,
        )

    return content.strip()


def parse_article_json(content):
    """
    Attempt to parse stored article content as JSON.

    Returns dictionary or None.
    """

    if not content:
        return None

    content = strip_json_fences(
        content
    )

    try:

        parsed = json.loads(
            content
        )

        if isinstance(parsed, dict):
            return parsed

    except (
        json.JSONDecodeError,
        TypeError,
    ):

        pass

    return None


# ==================================================
# MARKDOWN / TEXT TO HTML
# ==================================================

def markdown_to_html(content):
    """
    Convert basic generated Markdown/plain text
    into safe HTML.
    """

    if not content:
        return ""

    lines = str(content).splitlines()

    output = []
    paragraph = []
    in_list = False


    def close_list():

        nonlocal in_list

        if in_list:

            output.append(
                "</ul>"
            )

            in_list = False


    def flush_paragraph():

        nonlocal paragraph

        if not paragraph:
            return

        text = " ".join(
            line.strip()
            for line in paragraph
            if line.strip()
        )

        if text:

            output.append(
                f"<p>{escape(text)}</p>"
            )

        paragraph = []


    for raw_line in lines:

        line = raw_line.strip()

        if not line:

            flush_paragraph()
            close_list()

            continue


        if line.startswith("### "):

            flush_paragraph()
            close_list()

            output.append(
                f"<h3>{escape(line[4:])}</h3>"
            )


        elif line.startswith("## "):

            flush_paragraph()
            close_list()

            output.append(
                f"<h2>{escape(line[3:])}</h2>"
            )


        elif line.startswith("# "):

            flush_paragraph()
            close_list()

            output.append(
                f"<h2>{escape(line[2:])}</h2>"
            )


        elif line.startswith("- "):

            flush_paragraph()

            if not in_list:

                output.append(
                    "<ul>"
                )

                in_list = True

            output.append(
                f"<li>{escape(line[2:])}</li>"
            )


        else:

            paragraph.append(
                line
            )


    flush_paragraph()
    close_list()

    return "\n".join(
        output
    )


# ==================================================
# JSON ARTICLE RENDERING
# ==================================================

SKIPPED_ARTICLE_KEYS = {
    "article_title",
    "title",
    "slug",
}


def render_json_value(key, value):
    """Render one JSON field into HTML."""

    if value is None:
        return ""


    # ----------------------------------------------
    # LIST
    # ----------------------------------------------

    if isinstance(value, list):

        if not value:
            return ""

        output = [
            f"<h2>{escape(humanize_key(key))}</h2>",
            "<ul>",
        ]

        for item in value:

            if isinstance(item, dict):

                item_text = " — ".join(
                    f"{humanize_key(k)}: {v}"
                    for k, v in item.items()
                    if v is not None
                )

                output.append(
                    f"<li>{escape(item_text)}</li>"
                )

            else:

                output.append(
                    f"<li>{escape(item)}</li>"
                )

        output.append(
            "</ul>"
        )

        return "\n".join(
            output
        )


    # ----------------------------------------------
    # DICTIONARY
    # ----------------------------------------------

    if isinstance(value, dict):

        output = [
            f"<h2>{escape(humanize_key(key))}</h2>"
        ]

        for sub_key, sub_value in value.items():

            if sub_value is None:
                continue

            output.append(
                f"<h3>{escape(humanize_key(sub_key))}</h3>"
            )

            if isinstance(
                sub_value,
                list,
            ):

                output.append(
                    "<ul>"
                )

                for item in sub_value:

                    output.append(
                        f"<li>{escape(item)}</li>"
                    )

                output.append(
                    "</ul>"
                )

            else:

                output.append(
                    markdown_to_html(
                        str(sub_value)
                    )
                )

        return "\n".join(
            output
        )


    # ----------------------------------------------
    # TEXT
    # ----------------------------------------------

    text = str(
        value
    ).strip()

    if not text:
        return ""


    if key == "excerpt":

        return f"""
        <p class="article-excerpt">
            {escape(text)}
        </p>
        """


    if key == "introduction":

        return markdown_to_html(
            text
        )


    return (
        f"<h2>{escape(humanize_key(key))}</h2>\n"
        + markdown_to_html(text)
    )


def json_article_to_html(data):
    """Convert structured article JSON to HTML."""

    output = []

    for key, value in data.items():

        if key in SKIPPED_ARTICLE_KEYS:
            continue

        rendered = render_json_value(
            key,
            value,
        )

        if rendered:

            output.append(
                rendered
            )

    return "\n".join(
        output
    )


def article_to_html(content):
    """
    Detect JSON or normal text automatically.
    """

    if not content:
        return ""

    parsed = parse_article_json(
        content
    )

    if parsed:

        return json_article_to_html(
            parsed
        )

    return markdown_to_html(
        content
    )


# ==================================================
# ARTICLE METADATA
# ==================================================

def get_article_data(product):
    """Extract article title and excerpt."""

    title = (
        product.article_title
        or product.title
    )

    excerpt = ""

    parsed = parse_article_json(
        product.article_content
    )

    if parsed:

        title = (
            parsed.get(
                "article_title"
            )
            or parsed.get(
                "title"
            )
            or title
        )

        excerpt = (
            parsed.get(
                "excerpt"
            )
            or parsed.get(
                "summary"
            )
            or ""
        )

    return (
        title,
        excerpt,
    )


# ==================================================
# PRODUCT FACTS
# ==================================================

def build_product_facts(product):

    facts = []

    if product.platform:

        facts.append(
            (
                "Marketplace",
                product.platform,
            )
        )


    if product.price is not None:

        facts.append(
            (
                "Price",
                format_price(
                    product.price
                ),
            )
        )


    if product.orders:

        facts.append(
            (
                "Orders",
                f"{product.orders:,}",
            )
        )


    if product.rating:

        facts.append(
            (
                "Rating",
                f"{product.rating}/5",
            )
        )


    if not facts:

        return ""


    cards = ""


    for label, value in facts:

        cards += f"""
        <div class="fact-item">

            <span class="fact-label">
                {escape(label)}
            </span>

            <strong>
                {escape(value)}
            </strong>

        </div>
        """


    return f"""
    <div class="product-facts">

        {cards}

    </div>
    """


# ==================================================
# BUILD ARTICLE PAGE
# ==================================================

def build_article_page(product):

    article_title, excerpt = (
        get_article_data(
            product
        )
    )


    article_content = article_to_html(
        product.article_content
    )


    product_title = escape(
        product.title
    )


    page_title = escape(
        article_title
    )


    description = (
        excerpt
        or (
            "Independent SourceScout product research "
            f"and buying insights for {product.title}."
        )
    )


    description = truncate(
        description,
        155,
    )


    # ----------------------------------------------
    # PRODUCT IMAGE
    # ----------------------------------------------

    image_html = ""


    if product.image_url:

        image_html = f"""
        <div class="article-image">

            <img
                src="{escape(product.image_url)}"
                alt="{product_title}"
                loading="lazy"
            >

        </div>
        """


    # ----------------------------------------------
    # PRODUCT FACTS
    # ----------------------------------------------

    product_facts = (
        build_product_facts(
            product
        )
    )


    # ----------------------------------------------
    # AFFILIATE BUTTON
    # ----------------------------------------------

    affiliate_button = ""


    if product.affiliate_url:

        affiliate_button = f"""
        <section class="product-cta">

            <h2>
                Interested in this product?
            </h2>

            <p>
                Check the current listing,
                availability and pricing
                on the marketplace.
            </p>

            <a
                href="{escape(product.affiliate_url)}"
                target="_blank"
                rel="nofollow sponsored noopener"
                class="cta-button"
            >
                Check Product
            </a>

            <p class="affiliate-note">

                This may be an affiliate link.
                SourceScout may earn a commission
                at no additional cost to you.

            </p>

        </section>
        """


    return f"""<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>
        {page_title} | SourceScout
    </title>

    <meta
        name="description"
        content="{escape(description)}"
    >

    <link
        rel="canonical"
        href="{SITE_URL}/products/{escape(product.slug)}.html"
    >

    <link
        rel="stylesheet"
        href="../css/style.css"
    >

    <style>

        .article-container {{
            max-width: 820px;
            margin: 0 auto;
            padding: 80px 24px;
        }}

        .article-header {{
            margin-bottom: 48px;
        }}

        .article-category {{
            color: #ff5733;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}

        .article-header h1 {{
            font-size: clamp(
                38px,
                6vw,
                64px
            );

            line-height: 1.05;

            margin:
                18px
                0;
        }}

        .article-meta {{
            color: #777;
            font-size: 14px;
        }}

        .article-image {{
            margin: 40px 0;
        }}

        .article-image img {{
            display: block;
            width: 100%;
            max-height: 620px;
            object-fit: contain;
            border-radius: 8px;
        }}

        .product-facts {{

            display: grid;

            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(
                        130px,
                        1fr
                    )
                );

            gap: 1px;

            background: #ddd;

            margin:
                40px
                0;

            border:
                1px
                solid
                #ddd;
        }}

        .fact-item {{
            background: #f7f7f4;
            padding: 22px;
        }}

        .fact-label {{
            display: block;
            color: #777;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 7px;
        }}

        .fact-item strong {{
            font-size: 18px;
        }}

        .article-content {{
            font-size: 18px;
            line-height: 1.8;
        }}

        .article-excerpt {{
            font-size: 22px;
            line-height: 1.6;
            color: #555;
            margin-bottom: 40px;
        }}

        .article-content h2 {{
            margin-top: 52px;
            margin-bottom: 16px;
            font-size: 30px;
            line-height: 1.25;
        }}

        .article-content h3 {{
            margin-top: 36px;
            margin-bottom: 12px;
            font-size: 23px;
        }}

        .article-content p {{
            margin-top: 0;
            margin-bottom: 22px;
        }}

        .article-content ul {{
            margin: 20px 0 30px;
            padding-left: 25px;
        }}

        .article-content li {{
            margin-bottom: 10px;
        }}

        .product-cta {{
            margin: 60px 0;
            padding: 40px;
            background: #f5f5f2;
            text-align: center;
        }}

        .product-cta h2 {{
            margin-top: 0;
        }}

        .cta-button {{
            display: inline-block;
            margin-top: 12px;
            padding: 16px 28px;
            background: #111;
            color: white;
            text-decoration: none;
            font-weight: 700;
            border-radius: 4px;
        }}

        .affiliate-note {{
            margin-top: 16px;
            color: #777;
            font-size: 12px;
        }}

        .article-disclosure {{
            margin-top: 60px;
            padding-top: 24px;
            border-top: 1px solid #ddd;
            color: #777;
            font-size: 13px;
            line-height: 1.6;
        }}

    </style>

</head>


<body>


<header>

    <div class="container nav">

        <a
            href="../index.html"
            class="logo"
        >
            Source<span>Scout</span>
        </a>


        <nav>

            <a href="../index.html">
                Home
            </a>

            <a href="../products.html">
                Product Finds
            </a>

            <a href="../guides.html">
                Buying Guides
            </a>

            <a href="../about.html">
                About
            </a>

        </nav>

    </div>

</header>


<main>

    <article class="article-container">


        <div class="article-header">

            <div class="article-category">
                Product Find
            </div>

            <h1>
                {page_title}
            </h1>

            <div class="article-meta">
                SourceScout Editorial
            </div>

        </div>


        {image_html}


        {product_facts}


        <div class="article-content">

            {article_content}

        </div>


        {affiliate_button}


        <div class="article-disclosure">

            SourceScout independently researches
            products and marketplace opportunities.

            Some links on this page may be affiliate
            links, which means we may earn a commission
            if you make a purchase through them.

        </div>


    </article>

</main>


<footer>

    <div class="container">

        <p>
            © {datetime.now().year}
            SourceScout.
            All rights reserved.
        </p>

    </div>

</footer>


</body>

</html>
"""


# ==================================================
# PRODUCT CARD FOR products.html
# ==================================================

def build_product_card(product):

    article_title, excerpt = (
        get_article_data(
            product
        )
    )


    article_url = (
        f"products/"
        f"{product.slug}.html"
    )


    image_html = ""


    if product.image_url:

        image_html = f"""
            <img
                src="{escape(product.image_url)}"
                alt="{escape(product.title)}"
                loading="lazy"
                style="
                    width:100%;
                    height:220px;
                    object-fit:cover;
                    margin-bottom:20px;
                "
            >
        """


    return f"""
        <article
            class="product-card"
            data-product-id="{product.id}"
        >

            {image_html}

            <div class="product-card-content">

                <span class="product-platform">
                    {escape(product.platform)}
                </span>

                <h2>
                    <a href="{escape(article_url)}">
                        {escape(article_title)}
                    </a>
                </h2>

                <p>
                    {escape(truncate(excerpt, 180))}
                </p>

                <div class="product-card-meta">

                    <span>
                        {escape(format_price(product.price))}
                    </span>

                    <span>
                        {escape(product.rating)}/5
                    </span>

                </div>

                <a
                    href="{escape(article_url)}"
                    class="read-more"
                >
                    Read Product Research →
                </a>

            </div>

        </article>
    """


# ==================================================
# PRODUCTS PAGE MANAGEMENT
# ==================================================

def ensure_products_markers():
    """
    Add automatic publishing markers to products.html.

    The first time this runs, markers are inserted
    immediately before </main>.
    """

    if not PRODUCTS_PAGE.exists():

        raise FileNotFoundError(
            f"products.html not found: "
            f"{PRODUCTS_PAGE}"
        )


    content = PRODUCTS_PAGE.read_text(
        encoding="utf-8"
    )


    if (
        PRODUCTS_START_MARKER in content
        and PRODUCTS_END_MARKER in content
    ):

        return


    marker_block = f"""

<section class="auto-products-section">

    <div class="container">

        <div class="auto-products-grid">

{PRODUCTS_START_MARKER}

{PRODUCTS_END_MARKER}

        </div>

    </div>

</section>

"""


    if "</main>" not in content:

        raise ValueError(
            "Could not find </main> "
            "inside products.html."
        )


    content = content.replace(
        "</main>",
        marker_block + "\n</main>",
        1,
    )


    PRODUCTS_PAGE.write_text(
        content,
        encoding="utf-8",
    )


def update_products_page(
    db,
    include_product_id=None,
):
    """
    Rebuild the automatic product cards section
    using all products marked as published.
    """

    ensure_products_markers()


    products = (
        db.query(Product)
        .filter(
            (Product.publish_status == "published")
            | (Product.id == include_product_id)
        )
        .order_by(
            Product.published_at.desc()
        )
        .all()
    )


    cards = []


    for product in products:

        if not product.slug:
            continue

        cards.append(
            build_product_card(
                product
            )
        )


    cards_html = "\n".join(
        cards
    )


    content = PRODUCTS_PAGE.read_text(
        encoding="utf-8"
    )


    pattern = (
        re.escape(
            PRODUCTS_START_MARKER
        )
        + r".*?"
        + re.escape(
            PRODUCTS_END_MARKER
        )
    )


    replacement = (
        PRODUCTS_START_MARKER
        + "\n"
        + cards_html
        + "\n"
        + PRODUCTS_END_MARKER
    )


    updated_content = re.sub(
        pattern,
        replacement,
        content,
        flags=re.DOTALL,
    )


    PRODUCTS_PAGE.write_text(
        updated_content,
        encoding="utf-8",
    )


    print(
        f"✅ products.html updated "
        f"with {len(cards)} published product(s)."
    )


# ==================================================
# SITEMAP MANAGEMENT
# ==================================================

def update_sitemap(
    db,
    include_product_id=None,
):
    """
    Add all published product article URLs
    to sitemap.xml.
    """

    products = (
        db.query(Product)
        .filter(
            (Product.publish_status == "published")
            | (Product.id == include_product_id)
        )
        .all()
    )


    product_entries = []


    for product in products:

        if not product.slug:
            continue


        if product.published_at:

            try:

                lastmod = (
                    product.published_at
                    .strftime(
                        "%Y-%m-%d"
                    )
                )

            except AttributeError:

                lastmod = (
                    datetime.now(
                        timezone.utc
                    )
                    .strftime(
                        "%Y-%m-%d"
                    )
                )

        else:

            lastmod = (
                datetime.now(
                    timezone.utc
                )
                .strftime(
                    "%Y-%m-%d"
                )
            )


        product_entries.append(
            f"""
    <url>

        <loc>
            {SITE_URL}/products/{escape(product.slug)}.html
        </loc>

        <lastmod>
            {lastmod}
        </lastmod>

        <changefreq>
            weekly
        </changefreq>

        <priority>
            0.8
        </priority>

    </url>
"""
        )


    product_xml = "\n".join(
        product_entries
    )


    if SITEMAP_FILE.exists():

        sitemap = (
            SITEMAP_FILE.read_text(
                encoding="utf-8"
            )
        )

    else:

        sitemap = """<?xml version="1.0" encoding="UTF-8"?>

<urlset
    xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
>

</urlset>
"""


    start_marker = (
        "<!-- AUTO-PRODUCT-SITEMAP-START -->"
    )

    end_marker = (
        "<!-- AUTO-PRODUCT-SITEMAP-END -->"
    )


    automatic_block = f"""
{start_marker}

{product_xml}

{end_marker}
"""


    if (
        start_marker in sitemap
        and end_marker in sitemap
    ):

        pattern = (
            re.escape(
                start_marker
            )
            + r".*?"
            + re.escape(
                end_marker
            )
        )


        sitemap = re.sub(
            pattern,
            automatic_block.strip(),
            sitemap,
            flags=re.DOTALL,
        )


    else:

        if "</urlset>" not in sitemap:

            raise ValueError(
                "Invalid sitemap.xml: "
                "</urlset> was not found."
            )


        sitemap = sitemap.replace(
            "</urlset>",
            automatic_block
            + "\n</urlset>",
            1,
        )


    SITEMAP_FILE.write_text(
        sitemap,
        encoding="utf-8",
    )


    print(
        f"✅ sitemap.xml updated "
        f"with {len(product_entries)} "
        f"product URL(s)."
    )


# ==================================================
# GIT AUTOMATIC DEPLOYMENT
# ==================================================

def run_git_command(command):
    """Run a Git command inside website repository."""

    result = subprocess.run(
        command,
        cwd=WEBSITE_ROOT,
        capture_output=True,
        text=True,
    )


    if result.returncode != 0:

        raise RuntimeError(
            "\n"
            f"Git command failed:\n"
            f"{' '.join(command)}\n\n"
            f"{result.stderr}"
        )


    return result.stdout.strip()


def deploy_to_cloudflare(product):
    """
    Commit and push website changes.

    Cloudflare Pages then deploys automatically
    from the GitHub main branch.
    """

    print()
    print(
        "🚀 Preparing automatic deployment..."
    )


    run_git_command(
        [
            "git",
            "add",
            ".",
        ]
    )


    status = run_git_command(
        [
            "git",
            "status",
            "--porcelain",
        ]
    )


    if not status:

        print(
            "ℹ️ No website changes to commit."
        )

        return


    commit_message = (
        "Publish SourceScout product: "
        f"{product.title}"
    )


    run_git_command(
        [
            "git",
            "commit",
            "-m",
            commit_message,
        ]
    )


    run_git_command(
        [
            "git",
            "push",
        ]
    )


    print(
        "✅ Changes pushed to GitHub."
    )

    print(
        "☁️ Cloudflare Pages deployment triggered."
    )


# ==================================================
# PUBLISH PRODUCT
# ==================================================

def publish_product(
    product_id,
    auto_deploy=True,
):

    db = SessionLocal()


    try:

        product = (
            db.query(Product)
            .filter(
                Product.id
                == product_id
            )
            .first()
        )


        if not product:

            raise ValueError(
                f"Product {product_id} "
                "was not found."
            )


        if not product.slug:

            raise ValueError(
                "Product does not have a slug."
            )


        if not product.article_content:

            raise ValueError(
                "Product does not have "
                "generated article content."
            )


        # ------------------------------------------
        # REQUIRE AFFILIATE LINK
        # ------------------------------------------

        # Production deployment requires a real
        # affiliate tracking URL.
        #
        # Preview mode (auto_deploy=False) is allowed
        # without an affiliate URL.

        if (
            auto_deploy
            and not str(
                product.affiliate_url or ""
            ).strip()
        ):

            raise ValueError(
                "Product does not have an affiliate URL. "
                "Add the affiliate tracking link before publishing."
            )


        # ------------------------------------------
        # CREATE ARTICLE FILE
        # ------------------------------------------

        # Preview files are kept separate from
        # production website article files.

        if auto_deploy:

            output_directory = (
                PRODUCTS_DIR
            )

        else:

            output_directory = (
                WEBSITE_ROOT
                / "previews"
            )


        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )


        output_path = (
            output_directory
            / f"{product.slug}.html"
        )


        page = build_article_page(
            product
        )


        output_path.write_text(
            page,
            encoding="utf-8",
        )


        print()
        print(
            "✅ Article generated:"
        )

        print(
            output_path
        )


        # ------------------------------------------
        # PREVIEW MODE — STOP HERE
        # ------------------------------------------

        if not auto_deploy:

            print()
            print(
                "👁️ Preview generated successfully."
            )

            print(
                "No database publishing status changed."
            )

            print(
                "products.html was not updated."
            )

            print(
                "sitemap.xml was not updated."
            )

            print(
                "No GitHub or Cloudflare deployment occurred."
            )

            return output_path


        # ------------------------------------------
        # UPDATE WEBSITE INDEX FILES
        # ------------------------------------------

        update_products_page(
            db,
            include_product_id=product.id,
        )


        update_sitemap(
            db,
            include_product_id=product.id,
        )


        # ------------------------------------------
        # DEPLOY FIRST
        #
        # Do not mark the product as published until
        # deployment completes successfully.
        # ------------------------------------------

        deploy_to_cloudflare(
            product
        )


        # ------------------------------------------
        # MARK AS PUBLISHED AFTER SUCCESSFUL DEPLOY
        # ------------------------------------------

        product.publish_status = (
            "published"
        )


        if not product.published_at:

            product.published_at = (
                datetime.utcnow()
            )


        db.commit()


        public_url = (
            f"{SITE_URL}/products/"
            f"{product.slug}.html"
        )


        print()
        print(
            "🎉 Publishing pipeline completed."
        )

        print()
        print(
            "🌐 Public URL:"
        )

        print(
            public_url
        )


        return output_path


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()


# ==================================================
# COMMAND LINE
# ==================================================

if __name__ == "__main__":

    if len(sys.argv) > 1:

        product_id = int(
            sys.argv[1]
        )

    else:

        product_id = 5


    preview_mode = (
        len(sys.argv) > 2
        and sys.argv[2].strip().lower()
        == "preview"
    )


    if preview_mode:

        print()
        print(
            "👁️ PREVIEW MODE"
        )

        print(
            "Article will be generated locally "
            "without deployment."
        )


    publish_product(
        product_id,
        auto_deploy=not preview_mode,
    )
