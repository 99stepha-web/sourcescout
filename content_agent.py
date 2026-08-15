import os
import json
import re

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)


def create_slug(text):
    """Convert a product title into a URL-friendly slug."""

    text = text.lower().strip()

    text = re.sub(
        r"[^a-z0-9\s-]",
        "",
        text,
    )

    text = re.sub(
        r"[\s-]+",
        "-",
        text,
    )

    return text.strip("-")


def generate_product_article(product, analysis):
    """
    Generate an editorial SourceScout product article.

    The real affiliate URL is preserved outside the
    Claude-generated editorial text.
    """

    affiliate_url = (
        product.get("affiliate_url", "")
        or ""
    ).strip()

    prompt = f"""
You are the senior product editor for SourceScout,
an independent product-discovery and buying-research website.

PRODUCT DATA:

Name: {product.get('name', '')}
Marketplace: {product.get('marketplace', '')}
Price: {product.get('price', '')}
Original Price: {product.get('original_price', '')}
Rating: {product.get('rating', '')}
Orders: {product.get('orders', '')}
Category: {product.get('category', '')}

PRODUCT ANALYSIS:

AI Score: {analysis.get('ai_score', '')}
Decision: {analysis.get('decision', '')}
Target Audience: {analysis.get('target_audience', '')}
Content Potential: {analysis.get('content_potential', '')}
Best Content Angle: {analysis.get('best_content_angle', '')}
Why It Could Sell: {analysis.get('why_it_could_sell', '')}
Risks: {analysis.get('risks', '')}
Verification Needed: {analysis.get('verification_needed', '')}

Write a useful, natural product-discovery article.

IMPORTANT RULES:

- Do not claim SourceScout personally tested the product unless explicitly stated.
- Do not invent specifications, materials, shipping times, guarantees, or discounts.
- Clearly distinguish marketplace information from verified facts.
- Mention meaningful risks when relevant.
- Do not use exaggerated phrases such as "must-buy" or "guaranteed."
- Keep the tone independent and editorial.
- Do not mention Claude or AI.
- Do not include an affiliate URL in the editorial fields.
- Do not include Markdown.
- Return valid JSON only.

Return exactly this structure:

{{
    "article_title": "SEO-friendly editorial title",
    "excerpt": "One short summary under 160 characters",
    "introduction": "Opening paragraph",
    "why_it_stands_out": "Two or three useful paragraphs",
    "who_its_for": "Description of the likely buyer",
    "things_to_consider": "Balanced limitations and considerations",
    "verdict": "Short editorial conclusion"
}}
"""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1800,
        temperature=0.4,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    raw_text = (
        response.content[0]
        .text
        .strip()
    )

    # Remove accidental Markdown JSON fences.
    raw_text = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        raw_text,
        flags=re.IGNORECASE,
    ).strip()

    article = json.loads(raw_text)

    # ---------------------------------------------------------
    # Preserve the real affiliate URL OUTSIDE Claude output.
    # ---------------------------------------------------------

    return {
        "slug": create_slug(
            product.get(
                "name",
                "product",
            )
        ),

        "article_title": article[
            "article_title"
        ],

        "article_content": json.dumps(
            article,
            ensure_ascii=False,
        ),

        "affiliate_url": affiliate_url,

        "publish_status": "ready",

        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }
