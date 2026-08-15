from pathlib import Path
import re

import category_taxonomy

SITE = Path.home() / "product-finds-website"
INDEX = SITE / "products.html"
BASE_URL = "https://sourcescout.store"

START = "<!-- SOURCESCOUT_CATALOG_START -->"
END = "<!-- SOURCESCOUT_CATALOG_END -->"

SEO_START = "<!-- SOURCESCOUT_CATALOG_SEO_START -->"
SEO_END = "<!-- SOURCESCOUT_CATALOG_SEO_END -->"


def enhance_seo():
    if not INDEX.exists():
        raise SystemExit(f"❌ Missing: {INDEX}")

    html = INDEX.read_text(encoding="utf-8")

    html = re.sub(
        r"\n?" + re.escape(SEO_START) + r".*?" + re.escape(SEO_END) + r"\n?",
        "",
        html,
        flags=re.S,
    )

    canonical = f"{BASE_URL}/products.html"

    metadata = f"""
{SEO_START}
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{canonical}">
<link rel="icon" type="image/png" href="/favicon.png">
<link rel="apple-touch-icon" href="/favicon.png">
<meta property="og:type" content="website">
<meta property="og:title" content="Products | SourceScout">
<meta property="og:description" content="Discover independently researched products, buying guides, and recommendations from SourceScout.">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE_URL}/social-share.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Products | SourceScout">
<meta name="twitter:description" content="Discover independently researched products, buying guides, and recommendations from SourceScout.">
<meta name="twitter:image" content="{BASE_URL}/social-share.png">
{SEO_END}
"""

    match = re.search(r"<head\b[^>]*>", html, re.I)

    if not match:
        raise SystemExit("❌ <head> not found in products.html")

    html = html[:match.end()] + metadata + html[match.end():]

    INDEX.write_text(html, encoding="utf-8")

    print("✅ products.html SEO metadata installed.")

def category(title):
    return category_taxonomy.category_for(title) or "Other"


def enhance():
    if not INDEX.exists():
        raise SystemExit(f"❌ Missing: {INDEX}")

    html = INDEX.read_text(encoding="utf-8")

    if START in html:
        html = re.sub(
            r"\n?" + re.escape(START) + r".*?" + re.escape(END) + r"\n?",
            "",
            html,
            flags=re.S,
        )

    grid = re.search(
        r'<div\s+class=["\']product-grid["\']>',
        html,
        re.I,
    )

    if not grid:
        raise SystemExit("❌ product-grid not found in products.html")

    controls = f"""
{START}
<style>
.catalog-tools {{
    display:flex;
    gap:12px;
    margin:0 0 28px;
    flex-wrap:wrap;
}}
#scout-filter-input {{
    flex:1;
    min-width:240px;
    padding:13px 16px;
    border:1px solid #d1d5db;
    border-radius:10px;
    font-size:15px;
}}
#scout-category,#scout-sort {{
    padding:13px 16px;
    border:1px solid #d1d5db;
    border-radius:10px;
    background:#fff;
    font-size:15px;
}}
.scout-category {{
    display:inline-block;
    margin-bottom:8px;
    padding:5px 9px;
    border-radius:999px;
    background:#f3f4f6;
    font-size:11px;
    font-weight:700;
    text-transform:uppercase;
}}
#scout-no-results {{
    display:none;
    text-align:center;
    padding:50px 20px;
}}
</style>

<div class="catalog-tools">
<input id="scout-filter-input"
       type="search"
       placeholder="Search products..."
       aria-label="Search products">

<select id="scout-category">
<option value="all">All Categories</option>
<option value="Coffee & Espresso">Coffee & Espresso</option>
<option value="Home & Kitchen">Home & Kitchen</option>
<option value="Beauty">Beauty</option>
<option value="Fashion">Fashion</option>
<option value="Electronics">Electronics</option>
<option value="Outdoor & Travel">Outdoor & Travel</option>
<option value="Other">Other</option>
</select>

<select id="scout-sort">
<option value="latest">Latest</option>
<option value="az">A–Z</option>
<option value="za">Z–A</option>
</select>
</div>

<p id="scout-no-results">No products match your search.</p>

<script>
(function () {{
    const input = document.getElementById("scout-filter-input");
    const categorySelect = document.getElementById("scout-category");
    const sort = document.getElementById("scout-sort");
    const grid = document.querySelector(".product-grid");
    const empty = document.getElementById("scout-no-results");

    if (!input || !grid) return;

    const cards = Array.from(
        grid.querySelectorAll(".product-card")
    );

    cards.forEach(function(card) {{
        const text = card.textContent || "";
        let c = "Other";

        if (/coffee|espresso|咖啡/i.test(text))
            c = "Coffee & Espresso";
        else if (/beauty|skincare|makeup|美容|护肤/i.test(text))
            c = "Beauty";
        else if (/jacket|shirt|dress|bag|shoes|fashion|服装|外套|鞋|包/i.test(text))
            c = "Fashion";
        else if (/phone|laptop|tablet|camera|headphone|电子|手机|电脑|耳机/i.test(text))
            c = "Electronics";
        else if (/travel|camping|outdoor|portable|旅行|户外|便携/i.test(text))
            c = "Outdoor & Travel";
        else if (/kitchen|cooking|home|厨房|家用/i.test(text))
            c = "Home & Kitchen";

        card.dataset.category = c;

        if (!card.querySelector(".scout-category")) {{
            const label = document.createElement("span");
            label.className = "scout-category";
            label.textContent = c;

            const content =
                card.querySelector(".product-content");

            if (content)
                content.prepend(label);
        }}
    }});

    function update() {{
        const q = input.value.trim().toLowerCase();
        const selected = categorySelect.value;

        cards.forEach(function(card) {{
            const text =
                card.textContent.toLowerCase();

            const matchSearch =
                !q || text.includes(q);

            const matchCategory =
                selected === "all" ||
                card.dataset.category === selected;

            card.style.display =
                matchSearch && matchCategory
                    ? ""
                    : "none";
        }});

        const visible = cards.filter(function(card) {{
            return card.style.display !== "none";
        }});

        empty.style.display =
            visible.length ? "none" : "block";

        const ordered = [...cards];

        if (sort.value === "az") {{
            ordered.sort((a,b) =>
                a.textContent.trim()
                .localeCompare(b.textContent.trim())
            );
        }}

        if (sort.value === "za") {{
            ordered.sort((a,b) =>
                b.textContent.trim()
                .localeCompare(a.textContent.trim())
            );
        }}

        ordered.forEach(card => grid.appendChild(card));
    }}

    input.addEventListener("input", update);
    categorySelect.addEventListener("change", update);
    sort.addEventListener("change", update);
}})();
</script>
{END}
"""

    html = (
        html[:grid.start()]
        + controls
        + html[grid.start():]
    )

    INDEX.write_text(html, encoding="utf-8")

    print("✅ products.html enhanced successfully.")
    print(f"   File: {INDEX}")


if __name__ == "__main__":
    enhance()
