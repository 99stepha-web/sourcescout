import json
import sqlite3

import pandas as pd
import streamlit as st


from analysis_service import analyze_and_save_product
from database import SessionLocal
from models import Product
from publishing_service import generate_and_save_article
from website_publisher import publish_product


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="AI Affiliate Product Scout",
    page_icon="🔎",
    layout="wide",
)


st.title("🔎 AI Affiliate Product Scout")

st.caption(
    "Discover, rank, analyze and prepare affiliate "
    "product opportunities for publication."
)


# --------------------------------------------------
# Database connection
# --------------------------------------------------

db = SessionLocal()


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def get_publishing_data(product_id):
    """
    Load publishing fields directly from SQLite.

    These fields were added through the publishing migration
    and may not yet exist in the SQLAlchemy Product model.
    """

    conn = sqlite3.connect("data/scout.db")
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        """
        SELECT
            slug,
            affiliate_url,
            image_url,
            article_title,
            article_content,
            publish_status,
            published_at
        FROM products
        WHERE id = ?
        """,
        (product_id,),
    ).fetchone()

    conn.close()

    if row is None:
        return None

    return dict(row)


def update_publish_status(
    product_id,
    new_status,
):
    """
    Update the publication status of a product.
    """

    conn = sqlite3.connect("data/scout.db")

    conn.execute(
        """
        UPDATE products
        SET publish_status = ?
        WHERE id = ?
        """,
        (
            new_status,
            product_id,
        ),
    )

    conn.commit()
    conn.close()

def get_public_product_url(slug):
    if not slug:
        return None

    return (
        "https://sourcescout.store/products/"
        f"{slug}.html"
    )

# --------------------------------------------------
# Load products
# --------------------------------------------------

products = (
    db.query(Product)
    .order_by(
        Product.opportunity_score.desc()
    )
    .all()
)


if not products:

    st.warning(
        "No products found. "
        "Run python seed_products.py first."
    )

    db.close()
    st.stop()


# --------------------------------------------------
# Dashboard metrics
# --------------------------------------------------

total_products = len(products)


analyzed_products = sum(
    1
    for product in products
    if product.ai_analyzed_at is not None
)


high_potential = sum(
    1
    for product in products
    if product.opportunity_score >= 80
)


col1, col2, col3 = st.columns(3)


col1.metric(
    "Products",
    total_products,
)


col2.metric(
    "High-Potential Finds",
    high_potential,
)


col3.metric(
    "Claude Analyzed",
    analyzed_products,
)


st.divider()


# --------------------------------------------------
# Product selection
# --------------------------------------------------

st.subheader(
    "🤖 Claude Product Analyst"
)


product_options = {
    (
        f"{product.title} "
        f"— {product.platform}"
    ): product.id
    for product in products
}


selected_label = st.selectbox(
    "Select a product",
    options=list(
        product_options.keys()
    ),
)


selected_product_id = (
    product_options[selected_label]
)


product = (
    db.query(Product)
    .filter(
        Product.id
        == selected_product_id
    )
    .first()
)


# --------------------------------------------------
# Basic product information
# --------------------------------------------------

info1, info2, info3, info4 = (
    st.columns(4)
)


info1.metric(
    "Opportunity Score",
    product.opportunity_score,
)


info2.metric(
    "Price",
    f"${product.price:,.2f}",
)


info3.metric(
    "Orders",
    f"{product.orders:,}",
)


info4.metric(
    "Rating",
    product.rating,
)


# --------------------------------------------------
# Claude analysis
# --------------------------------------------------

st.write("")


if product.ai_analyzed_at is None:

    st.info(
        "This product has not been "
        "analyzed by Claude."
    )


    if st.button(
        "🤖 Analyze with Claude",
        type="primary",
        key=f"analyze_{product.id}",
    ):

        with st.spinner(
            "Claude is analyzing "
            "the product..."
        ):

            try:

                analyze_and_save_product(
                    db,
                    product,
                )


                st.success(
                    "Analysis completed "
                    "and saved to SQLite."
                )


                st.rerun()


            except Exception as error:

                st.error(
                    "Claude analysis "
                    f"failed: {error}"
                )


else:

    st.success(
        "Claude analysis is already saved."
    )


    if st.button(
        "🔄 Re-analyze with Claude",
        key=f"reanalyze_{product.id}",
    ):

        with st.spinner(
            "Claude is re-analyzing "
            "the product..."
        ):

            try:

                analyze_and_save_product(
                    db,
                    product,
                )


                st.success(
                    "New analysis saved."
                )


                st.rerun()


            except Exception as error:

                st.error(
                    "Claude analysis "
                    f"failed: {error}"
                )


# --------------------------------------------------
# Display Claude analysis
# --------------------------------------------------

if product.ai_analyzed_at is not None:

    st.divider()


    st.subheader(
        "🧠 Claude Analysis"
    )


    score_col, decision_col = (
        st.columns(2)
    )


    score_col.metric(
        "AI Score",
        product.ai_score,
    )


    decision_col.metric(
        "Decision",
        product.ai_decision,
    )


    st.markdown(
        "### 🎯 Target Audience"
    )


    st.write(
        product.target_audience
    )


    st.markdown(
        "### 📱 Content Potential"
    )


    st.write(
        product.content_potential
    )


    st.markdown(
        "### 💡 Best Content Angle"
    )


    st.write(
        product.best_content_angle
    )


    st.markdown(
        "### 💰 Why It Could Sell"
    )


    st.write(
        product.why_it_could_sell
    )


    st.markdown(
        "### ⚠️ Risks"
    )


    st.write(
        product.risks
    )


    st.markdown(
        "### 🔍 Verification Needed"
    )


    st.write(
        product.verification_needed
    )


    st.caption(
        f"API usage: "
        f"{product.ai_input_tokens} "
        f"input tokens + "
        f"{product.ai_output_tokens} "
        f"output tokens"
    )


# --------------------------------------------------
# Product publishing pipeline
# --------------------------------------------------

if product.ai_analyzed_at is not None:

    st.divider()


    st.subheader(
        "🚀 Product Publishing Pipeline"
    )


    publishing_data = (
        get_publishing_data(
            product.id
        )
    )


    if publishing_data is None:

        st.error(
            "Publishing data could not "
            "be loaded for this product."
        )


    else:

        status = (
            publishing_data.get(
                "publish_status"
            )
            or "draft"
        )


        st.write(
            f"**Publishing status:** "
            f"`{status}`"
        )


        # ------------------------------------------
        # Generate article
        # ------------------------------------------

        if not publishing_data.get(
            "article_content"
        ):

            st.info(
                "No SourceScout article "
                "has been generated yet."
            )


            if st.button(
                "✍️ Generate SourceScout Article",
                type="primary",
                key=(
                    f"generate_article_"
                    f"{product.id}"
                ),
            ):

                with st.spinner(
                    "Claude is creating "
                    "the SourceScout article..."
                ):

                    try:

                        result = (
                            generate_and_save_article(
                                product.id
                            )
                        )


                        st.success(
                            "Article generated "
                            "and permanently "
                            "saved to SQLite."
                        )


                        st.caption(
                            f"API usage: "
                            f"{result['usage']['input_tokens']} "
                            f"input tokens / "
                            f"{result['usage']['output_tokens']} "
                            f"output tokens"
                        )


                        st.rerun()


                    except Exception as error:

                        st.error(
                            "Article generation "
                            f"failed: {error}"
                        )


        # ------------------------------------------
        # Article preview
        # ------------------------------------------

        else:

            try:

                article = json.loads(
                    publishing_data[
                        "article_content"
                    ]
                )


            except json.JSONDecodeError:

                article = None


                st.error(
                    "The saved article content "
                    "is not valid JSON."
                )


            if article:

                st.markdown(
                    "### 👀 Article Preview"
                )


                st.markdown(
                    f"# "
                    f"{publishing_data['article_title']}"
                )


                if article.get(
                    "excerpt"
                ):

                    st.caption(
                        article["excerpt"]
                    )


                st.markdown("---")


                if article.get(
                    "introduction"
                ):

                    st.write(
                        article[
                            "introduction"
                        ]
                    )


                if article.get(
                    "why_it_stands_out"
                ):

                    st.markdown(
                        "### Why it stands out"
                    )


                    st.write(
                        article[
                            "why_it_stands_out"
                        ]
                    )


                if article.get(
                    "who_its_for"
                ):

                    st.markdown(
                        "### Who it's for"
                    )


                    st.write(
                        article[
                            "who_its_for"
                        ]
                    )


                if article.get(
                    "things_to_consider"
                ):

                    st.markdown(
                        "### Things to consider"
                    )


                    st.write(
                        article[
                            "things_to_consider"
                        ]
                    )


                if article.get(
                    "verdict"
                ):

                    st.markdown(
                        "### SourceScout perspective"
                    )


                    st.write(
                        article[
                            "verdict"
                        ]
                    )


                st.markdown("---")


                st.caption(
                    "Review all product claims "
                    "before approving this article."
                )


                # ----------------------------------
                # Approval workflow
                # ----------------------------------

                if status in (
                    "draft",
                    "content_generated",
                ):

                    st.warning(
                        "This article has not "
                        "been approved for "
                        "public publication."
                    )


                    if st.button(
                        "✅ Approve for Publishing",
                        type="primary",
                        key=(
                            f"approve_article_"
                            f"{product.id}"
                        ),
                    ):

                        update_publish_status(
                            product.id,
                            "approved",
                        )


                        st.success(
                            "Article approved "
                            "for publishing."
                        )


                        st.rerun()


               elif status == "approved":

    st.success(
        "✅ This article is approved and ready "
        "to publish to the SourceScout website."
    )

    if st.button(
        "🚀 Publish to Website",
        type="primary",
        key=f"publish_website_{product.id}",
    ):

        with st.spinner(
            "Publishing article, updating the website "
            "and deploying to Cloudflare..."
        ):

            try:

                publish_product(
                    product.id
                )

                update_publish_status(
                    product.id,
                    "published",
                )

                st.success(
                    "🎉 Article published successfully!"
                )

                st.rerun()

            except Exception as error:

                st.error(
                    f"Publishing failed: {error}"
                )

                elif status == "published":

                    st.success(
                        "🌐 This article is "
                        "marked as published."
                    )


# --------------------------------------------------
# All product opportunities
# --------------------------------------------------

st.divider()


st.subheader(
    "🔥 All Product Opportunities"
)


data = []


for item in products:

    item_publishing = (
        get_publishing_data(
            item.id
        )
    )


    publish_status = (
        item_publishing.get(
            "publish_status"
        )
        if item_publishing
        else None
    )


    data.append(
        {
            "Platform": item.platform,
            "Product": item.title,
            "Category": item.category,
            "Price": item.price,
            "Orders": item.orders,
            "Rating": item.rating,
            "Algorithm Score": (
                item.opportunity_score
            ),
            "AI Score": item.ai_score,
            "AI Decision": (
                item.ai_decision
            ),
            "Scout Status": (
                item.status
            ),
            "Publishing Status": (
                publish_status
            ),
        }
    )


df = pd.DataFrame(
    data
)


st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
)


# --------------------------------------------------
# Close database session
# --------------------------------------------------

db.close()
