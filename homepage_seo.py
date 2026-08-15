from pathlib import Path
import re
import json

SITE = Path.home() / "product-finds-website"
INDEX = SITE / "index.html"

BASE = "https://sourcescout.store"
START = "<!-- SOURCESCOUT_HOME_SEO_START -->"
END = "<!-- SOURCESCOUT_HOME_SEO_END -->"

def main():
    if not INDEX.exists():
        raise SystemExit(f"❌ Missing {INDEX}")

    html = INDEX.read_text(encoding="utf-8")

    html = re.sub(
        r"\n?" + re.escape(START) + r".*?" + re.escape(END) + r"\n?",
        "",
        html,
        flags=re.S,
    )

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": f"{BASE}/#organization",
                "name": "SourceScout",
                "url": BASE,
                "logo": {
                    "@type": "ImageObject",
                    "url": f"{BASE}/favicon.png",
                },
            },
            {
                "@type": "WebSite",
                "@id": f"{BASE}/#website",
                "url": BASE,
                "name": "SourceScout",
                "publisher": {
                    "@id": f"{BASE}/#organization"
                },
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": {
                        "@type": "EntryPoint",
                        "urlTemplate":
                            f"{BASE}/products.html?search={{search_term_string}}",
                    },
                    "query-input":
                        "required name=search_term_string",
                },
            },
        ],
    }

    metadata = f"""
{START}
<meta name="description" content="SourceScout discovers, researches, and evaluates interesting products with AI-powered analysis and practical buying guides.">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{BASE}/">
<link rel="icon" type="image/png" href="/favicon.png">
<link rel="apple-touch-icon" href="/favicon.png">

<meta property="og:type" content="website">
<meta property="og:title" content="SourceScout — AI-Powered Product Research & Buying Guides">
<meta property="og:description" content="Discover interesting products, compare options, and make smarter buying decisions with SourceScout.">
<meta property="og:url" content="{BASE}/">
<meta property="og:site_name" content="SourceScout">
<meta property="og:image" content="{BASE}/social-share.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="SourceScout — AI-Powered Product Research & Buying Guides">
<meta name="twitter:description" content="AI-powered product discovery, research, and practical buying guides.">
<meta name="twitter:image" content="{BASE}/social-share.png">

<script type="application/ld+json">
{json.dumps(schema, ensure_ascii=False, indent=2)}
</script>
{END}
"""

    head = re.search(
        r"<head\b[^>]*>",
        html,
        re.I,
    )

    if not head:
        raise SystemExit("❌ <head> not found")

    html = (
        html[:head.end()]
        + metadata
        + html[head.end():]
    )

    INDEX.write_text(
        html,
        encoding="utf-8",
    )

    print("✅ Homepage SEO metadata installed.")


if __name__ == "__main__":
    main()
