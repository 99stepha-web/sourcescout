import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

print("PROJECT_ROOT:", PROJECT_ROOT)
print("PYTHONPATH:", sys.path[0])

from datetime import datetime

from agents.research_agent import ResearchAgent
from database import SessionLocal
from models import Product
from analysis_service import analyze_and_save_product
from publishing_service import generate_and_save_article
from affiliate.utils.url_utils import clean_affiliate_url
from product_scoring import calculate_selection_score, deduplicate_candidates, as_dict
from config.intelligence import SELECTION_CONFIG


def should_reanalyze(product):
    """
    Test I / idempotency: a product already analyzed with a saved
    article does not need another Claude analysis call just because
    the same keyword rediscovered it.
    """

    return not (product.ai_analyzed_at and product.article_content)


def should_regenerate_article(product):
    """
    Test I / idempotency: a PROMOTE product that already has a
    published article does not need another Claude article-generation
    call on rediscovery.
    """

    return not (product.article_content and product.slug)


def print_selection_report(keyword, report, scored, approved=0, review=0, skipped=0):
    print("\n" + "=" * 60)
    print("SOURCE SCOUT PRODUCT SELECTION REPORT")
    print("=" * 60)

    print(f"\nKeyword: {keyword}")

    print(f"\nMarketplace candidates: {report['marketplace_candidates']}")
    print(f"Category-valid: {report['category_valid']}")
    print(f"Passed hard filters: {report['passed_hard_filters']}")
    print(f"Ranked candidates: {report['ranked_candidates']}")
    print(f"Sent to Claude: {report['sent_to_claude']}")
    print(f"Approved: {approved}")
    print(f"Review: {review}")
    print(f"Skipped: {skipped}")

    top = sorted(
        scored, key=lambda pair: pair[1]["selection_score"], reverse=True
    )[:5]

    if top:
        print("\nTOP PRODUCTS")

        for i, (product, result) in enumerate(top, start=1):
            print(f"\n{i}. Product {product.id}: {product.title[:50]}")
            print(f"   Selection Score: {result['selection_score']}")

            for name, factor in result["breakdown"].items():
                shown = factor["score"] if factor["score"] is not None else "N/A"
                print(f"   {name.capitalize()}: {shown}")

    print("\n" + "=" * 60)


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
        # STAGE A + B — hard filter, dedup, opportunity ranking
        #
        # Runs entirely on already-stored marketplace data (no
        # Claude call) so weak/off-category products never reach the
        # expensive analysis step.
        # =====================================================

        print(
            "\n[Selection] Filtering and ranking candidates..."
        )

        survivors, dropped_duplicates = deduplicate_candidates(processed, keyword)

        for product, reason in dropped_duplicates:
            print(f"⏭️ Duplicate suppressed: Product {product.id} — {reason}")

        scored = []

        for product in survivors:
            result = calculate_selection_score(product, keyword)

            product.selection_score = result["selection_score"]
            product.selection_status = result["selection_status"]
            product.selection_reason = result["selection_reason"]

            scored.append((product, result))

        db.commit()

        category_valid = [
            p for p, r in scored if r["selection_status"] != "CATEGORY_MISMATCH"
        ]

        passed_hard_filter = [
            p for p, r in scored
            if r["selection_status"] not in ("CATEGORY_MISMATCH", "HARD_FILTERED")
        ]

        ranked = sorted(
            (p for p, r in scored if r["selection_status"] == "RANKED"),
            key=lambda p: p.selection_score,
            reverse=True,
        )

        claude_limit = SELECTION_CONFIG["claude_analysis_limit"]
        shortlisted = ranked[:claude_limit]

        report = {
            "marketplace_candidates": len(processed),
            "category_valid": len(category_valid),
            "passed_hard_filters": len(passed_hard_filter),
            "ranked_candidates": len(ranked),
            "sent_to_claude": len(shortlisted),
        }

        print(
            f"\n✅ {len(processed)} candidates -> "
            f"{len(category_valid)} category-valid -> "
            f"{len(passed_hard_filter)} passed hard filters -> "
            f"{len(ranked)} ranked -> "
            f"{len(shortlisted)} sent to Claude"
        )

        for product, result in scored:
            print(
                f"\nProduct {product.id}: {product.title[:40]}"
            )
            print(
                f"   Selection Score: {result['selection_score']} "
                f"({result['selection_status']})"
            )
            for name, factor in result["breakdown"].items():
                shown = factor["score"] if factor["score"] is not None else "N/A"
                print(f"   {name.capitalize()}: {shown}")
            if result["selection_status"] != "RANKED":
                print(f"   Reasons: {result['selection_reason']}")

        if not shortlisted:

            print(
                "\n❌ No candidates survived filtering/ranking."
            )

            print_selection_report(keyword, report, scored)

            return

        # =====================================================
        # 3. CLAUDE ANALYSIS
        # =====================================================

        print(
            "\n[3/5] Analyzing products with Claude..."
        )

        analyzed = []

        for product in shortlisted:

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
            if not should_reanalyze(product):

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

            print_selection_report(keyword, report, scored)

            return

        # =====================================================
        # 4. CONTENT GENERATION
        # =====================================================

        print(
            "\n[4/5] Generating articles..."
        )

        generated = []
        promoted = []
        review_products = []
        skipped_products = []

        needs_generation = []

        for product in analyzed:

            decision = (
                str(
                    product.ai_decision
                    or ""
                )
                .strip()
                .upper()
            )

            if decision == "REVIEW":
                review_products.append(product)
            elif decision != "PROMOTE":
                skipped_products.append(product)

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
            if not should_regenerate_article(product):

                print(
                    f"\n⏭️ Product {product.id} already has a "
                    "published article — skipping regeneration."
                )

                continue

            needs_generation.append(product)

        # Cap new article generation per run (cost control) —
        # prioritize the strongest candidates by selection score.
        article_limit = SELECTION_CONFIG["article_generation_limit"]

        needs_generation.sort(
            key=lambda p: p.selection_score or 0,
            reverse=True,
        )

        for product in needs_generation[article_limit:]:
            print(
                f"\n⏭️ Product {product.id} approved but over the "
                f"per-run article limit ({article_limit}) — will "
                "generate on a future run."
            )

        for product in needs_generation[:article_limit]:

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

        if promoted:

            print(
                "\n[5/5] Deploying website..."
            )

            import website_publisher

            website_publisher.deploy()

        else:

            print(
                "\n[5/5] Nothing approved for publishing "
                "— skipping deploy."
            )

        # =====================================================
        # SELECTION REPORT (item 25)
        # =====================================================

        print_selection_report(
            keyword,
            report,
            scored,
            approved=len(promoted),
            review=len(review_products),
            skipped=len(skipped_products),
        )

        if generated:

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
