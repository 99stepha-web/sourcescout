import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not API_KEY:
    raise ValueError("ANTHROPIC_API_KEY was not found in .env")

client = Anthropic(api_key=API_KEY)


SYSTEM_PROMPT = """
You are a product opportunity analyst for an affiliate marketing business.

The business promotes products through educational and deal-focused content
on X and Threads.

Your job is to evaluate whether a product is worth promoting.

Rules:
- Never invent product facts.
- Never assume authenticity.
- Never invent discounts, sales numbers, certifications, or supplier claims.
- Distinguish provided facts from your own marketing analysis.
- Consider whether the product has an interesting social-media content angle.
- Consider the likely target audience.
- Identify important information that must be verified before promotion.
- Be conservative when information is incomplete.

A field showing 0, empty, or "unknown" means that data point was not
captured during research — it does NOT mean the real-world value is zero.
Distinguish two different situations and choose the decision accordingly:

- INSUFFICIENT DATA: several key fields (orders, rating, supplier score)
  are all missing/zero and there is nothing else to judge the product on.
  This alone is not evidence the product is bad. Use REVIEW and say what
  data is missing in "verification_needed".
- BAD PRODUCT: the fields that ARE present show real negative signal
  (e.g. a genuinely low rating with a real review count, a price far out
  of line with the category, an obviously mismatched or low-quality
  listing). Use SKIP and say why in "risks".

Use PROMOTE only when the available evidence is genuinely positive, not
merely absent.

Return ONLY valid JSON using exactly this structure:

{
    "ai_score": 0,
    "decision": "PROMOTE",
    "target_audience": "",
    "content_potential": "",
    "best_content_angle": "",
    "why_it_could_sell": "",
    "risks": "",
    "verification_needed": ""
}

The ai_score must be between 0 and 100.

The decision must be exactly one of:
PROMOTE
REVIEW
SKIP

Keep every text field concise.
"""


def analyze_product(product):
    product_information = f"""
Platform: {product.platform}
Product: {product.title}
Category: {product.category}
Price: {product.price}
Original Price: {product.original_price}
Orders: {product.orders}
Rating: {product.rating}
Review Count: {product.review_count}
Supplier: {product.supplier}
Supplier Score: {product.supplier_score}
Commission Rate: {product.commission_rate}%
Algorithmic Opportunity Score: {product.opportunity_score}
Research Keyword: {product.research_keyword}
Product URL: {product.product_url}
Image URL: {product.image_url}
"""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=500,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    "Analyze this affiliate product opportunity:\n\n"
                    + product_information
                ),
            }
        ],
    )

    raw_response = response.content[0].text.strip()

    print("\n========== CLAUDE RAW RESPONSE ==========\n")
    print(raw_response)
    print("\n=========================================\n")

    # Remove Markdown code fences if Claude returned them
    if raw_response.startswith("```"):
        raw_response = raw_response.replace("```json", "")
        raw_response = raw_response.replace("```", "")
        raw_response = raw_response.strip()

    # Extract the JSON object even if Claude adds text before/after it
    start = raw_response.find("{")
    end = raw_response.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(
            "Claude did not return a valid JSON object.\n\n"
            f"Response:\n{raw_response}"
        )

    json_text = raw_response[start:end + 1]

    try:
        analysis = json.loads(json_text)
    except json.JSONDecodeError as e:
        print("\n===== JSON PARSE ERROR =====")
        print(e)
        print("\n===== JSON RECEIVED =====")
        print(json_text)
        print("===========================\n")
        raise

    return {
        "analysis": analysis,
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }
