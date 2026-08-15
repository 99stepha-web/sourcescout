import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print("PROJECT_ROOT:", PROJECT_ROOT)
print("PYTHONPATH:", sys.path[0])

from agents.research_agent import ResearchAgent
from database import SessionLocal
from models import Product
from analysis_service import analyze_and_save_product
from publishing_service import generate_and_save_article
from affiliate.utils.url_utils import clean_affiliate_url


def main():

    if len(sys.argv) < 2:
        print("Usage:")
        print('python scripts/run_pipeline.py "<keyword>"')
        sys.exit(1)

    keyword = " ".join(sys.argv[1:]).strip()

    print("\n========== SOURCE SCOUT PIPELINE ==========")
    print(f"Keyword: {keyword}")

    # =========================================================
    # 1. RESEARCH
    # =========================================================

    print("\n[1/5] Researching Alimama...")

    agent = ResearchAgent()

    results = agent.research(keyword)

    if not results:
        print("\n❌ No products found.")
        return

    print(
        f"\n✅ Research returned "
        f"{len(results)} product(s)"
    )

    # =========================================================
    # 2. DATABASE
    # =========================================================

    print("\n[2/5] Processing database products...")

    db = SessionLocal()

    processed = []

    try:

        for index, result in enumerate(
            results,
            start=1,
        ):

            print(
                f"\n--- Product {index} ---"
            )

            # ResearchAgent may return either:
            #
            # 1. SQLAlchemy Product object
            # 2. dictionary
            #
            # Handle both.

            if isinstance(result, Product):

                # ResearchAgent uses its own SQLAlchemy session.
                # Never reuse that ORM instance in this session.
                #
                # Reload the product by primary key so this
                # pipeline owns the persistent instance.

                source_product_id = result.id

                product = (
                    db.query(Product)
                    .filter(
                        Product.id == source_product_id
                    )
                    .first()
                )

                if product is None:

                    print(
                        f"❌ Product ID "
                        f"{source_product_id} "
                        f"was not found in this session."
                    )

                    continue

                title = (
                    product.title
                    or ""
                ).strip()

                affiliate_url = (
                    product.affiliate_url
                    or ""
                ).strip()

                print(
                    "Result type: SQLAlchemy Product "
                    "(reloaded into pipeline session)"
                )

            elif isinstance(result, dict):

                title = (
                    result.get("title", "")
                    or ""
                ).strip()

                affiliate_url = (
                    result.get(
                        "affiliate_url",
                        "",
                    )
                    or ""
                ).strip()

                product = None

                product_id = result.get(
                    "product_id"
                )

                if product_id:

                    product = (
                        db.query(Product)
                        .filter(
                            Product.product_id
                            == str(product_id)
                        )
                        .first()
                    )

                if product is None and title:

                    product = (
                        db.query(Product)
                        .filter(
                            Product.title
                            == title
                        )
                        .first()
                    )

                print(
                    "Result type: dictionary"
                )

            else:

                print(
                    f"⚠️ Unsupported result type: "
                    f"{type(result)}"
                )

                continue

            print(
                f"Title: {title}"
            )

            print(
                f"Incoming affiliate URL: "
                f"{affiliate_url}"
            )

            if product is None:

                print(
                    "❌ Product does not exist "
                    "in SQLite."
                )

                continue

            # -------------------------------------------------
            # FINAL AFFILIATE URL NORMALIZATION
            # -------------------------------------------------

            clean_url = clean_affiliate_url(
                affiliate_url
            )

            if not clean_url:

                print(
                    "❌ Could not extract a valid "
                    "Taobao affiliate URL."
                )

                continue

            product.affiliate_url = clean_url

            product.research_keyword = keyword

            db.commit()
            db.refresh(product)

            print(
                f"✅ Clean affiliate URL: "
                f"{product.affiliate_url}"
            )

            print(
                f"✅ Database Product ID: "
                f"{product.id}"
            )

            processed.append(product)

        if not processed:

            print(
                "\n❌ No database products "
                "available for analysis."
            )

            return

        # =====================================================
        # 3. CLAUDE ANALYSIS
        # =====================================================

        print(
            "\n[3/5] Analyzing products with Claude..."
        )

        analyzed = []

        for product in processed:

            print(
                f"\n========== AI ANALYSIS =========="
            )

            print(
                f"ID: {product.id}"
            )

            print(
                f"Title: {product.title}"
            )

            # Skip re-analysis (and the Claude call it costs) for a
            # product that already has a saved analysis and a
            # generated article. Re-discovering the same product on
            # a later run of the same keyword should not burn a new
            # API call and rewrite an unchanged article; the affiliate
            # URL is still refreshed on every publish regardless.
            if product.ai_analyzed_at and product.article_content:

                print(
                    "⏭️ Already analyzed with an existing "
                    "article — skipping re-analysis."
                )

                analyzed.append(product)

                continue

            try:

                product = analyze_and_save_product(
                    db,
                    product,
                )

                print(
                    f"AI Score: "
                    f"{product.ai_score}"
                )

                print(
                    f"Decision: "
                    f"{product.ai_decision}"
                )

                analyzed.append(product)

            except Exception as e:

                print(
                    f"❌ Claude analysis failed: "
                    f"{e}"
                )

        if not analyzed:

            print(
                "\n❌ No products were analyzed."
            )

            return

        # =====================================================
        # 4. CONTENT GENERATION
        # =====================================================

        print(
            "\n[4/5] Generating articles..."
        )

        generated = []
        promoted = []

        for product in analyzed:

            decision = (
                str(
                    product.ai_decision
                    or ""
                )
                .strip()
                .upper()
            )

            if decision != "PROMOTE":

                print(
                    f"\n⏭️ SKIPPING Product "
                    f"{product.id}"
                )

                print(
                    f"Claude decision: {decision or 'UNKNOWN'}"
                )

                continue

            promoted.append(product)

            # Already has a saved article from a previous run and
            # nothing about the analysis changed this time (see the
            # matching skip in step 3) — don't burn another Claude
            # call regenerating unchanged article text. The website
            # deploy step still runs below and will pick up any
            # affiliate URL refresh from ingestion regardless.
            if product.article_content and product.slug:

                print(
                    f"\n⏭️ Product {product.id} already has a "
                    "published article — skipping regeneration."
                )

                continue

            print(
                f"\n========== ARTICLE =========="
            )

            print(
                f"Product ID: "
                f"{product.id}"
            )

            print(
                f"Title: "
                f"{product.title}"
            )

            try:

                article = (
                    generate_and_save_article(
                        product.id
                    )
                )

                generated.append(
                    article
                )

                print(
                    "✅ Article generated"
                )

                print(
                    f"Slug: "
                    f"{article['slug']}"
                )

            except Exception as e:

                print(
                    f"❌ Article generation "
                    f"failed: {e}"
                )

        # =====================================================
        # 5. WEBSITE DEPLOYMENT
        # =====================================================

        if not promoted:

            print(
                "\n[5/5] Nothing approved "
                "for publishing."
            )

            print(
                "\n⚠️ Pipeline finished."
            )

            return

        print(
            "\n[5/5] Deploying website..."
        )

        import website_publisher

        website_publisher.deploy()

        print(
            "\n========================================"
        )

        print(
            "✅ SOURCE SCOUT PIPELINE COMPLETE"
        )

        print(
            "========================================"
        )

        for article in generated:

            print(
                f"\nProduct ID: "
                f"{article['product_id']}"
            )

            print(
                f"Title: "
                f"{article['article_title']}"
            )

            print(
                f"Slug: "
                f"{article['slug']}"
            )

            print(
                f"Status: "
                f"{article['publish_status']}"
            )

    finally:

        db.close()


if __name__ == "__main__":
    main()
