from database import SessionLocal
from models import Product
from claude_agent import analyze_product


db = SessionLocal()

try:
    product = (
        db.query(Product)
        .order_by(Product.opportunity_score.desc())
        .first()
    )

    if not product:
        print("No products found.")
        raise SystemExit

    print("\nAnalyzing:")
    print(product.title)

    result = analyze_product(product)

    analysis = result["analysis"]
    usage = result["usage"]

    print("\n--- CLAUDE ANALYSIS ---")

    print("AI Score:", analysis["ai_score"])
    print("Decision:", analysis["decision"])
    print("Target Audience:", analysis["target_audience"])
    print("Content Potential:", analysis["content_potential"])
    print("Best Content Angle:", analysis["best_content_angle"])
    print("Why It Could Sell:", analysis["why_it_could_sell"])
    print("Risks:", analysis["risks"])
    print(
        "Verification Needed:",
        analysis["verification_needed"],
    )

    print("\n--- API USAGE ---")
    print("Input tokens:", usage["input_tokens"])
    print("Output tokens:", usage["output_tokens"])

finally:
    db.close()