from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)

from database import Base


class Product(Base):
    __tablename__ = "products"

    # --------------------------------------------------
    # Primary key
    # --------------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # --------------------------------------------------
    # Basic product information
    # --------------------------------------------------

    platform = Column(
        String(50),
        nullable=False,
    )

    product_id = Column(
        String(100),
        unique=True,
        nullable=False,
    )

    title = Column(
        String(500),
        nullable=False,
    )

    category = Column(
        String(100),
    )

    # --------------------------------------------------
    # Product metrics
    # --------------------------------------------------

    price = Column(
        Float,
        default=0,
    )

    original_price = Column(
        Float,
        default=0,
    )

    # No Python-side default: unlike price, these are frequently not
    # exposed by the marketplace at all, and SQLAlchemy's `default=`
    # fires even on an explicitly-passed None, which would silently
    # turn "unavailable" into a fabricated 0. Leave unset -> NULL.
    orders = Column(Integer)

    rating = Column(Float)

    # Marketplace product metadata
    supplier = Column(Text)
    moq = Column(String(200))
    price_text = Column(String(500))
    price_min = Column(Float)
    price_max = Column(Float)
    review_count = Column(Integer)

    supplier_score = Column(Float)

    commission_rate = Column(
        Float,
        default=0,
    )

    commission_amount = Column(Float)

    # --------------------------------------------------
    # Product selection intelligence
    #
    # Raw marketplace signals used by product_scoring.py. Left NULL
    # when the marketplace does not expose a metric for a given
    # product — never backfilled with a fabricated value.
    # --------------------------------------------------

    monthly_sales = Column(Integer)
    monthly_promoters = Column(Integer)
    today_sales = Column(Integer)

    price_percentile = Column(Float)
    commission_percentile = Column(Float)

    shop_rating = Column(Float)

    listing_date = Column(String(50))
    subcategory = Column(String(100))

    sales_velocity = Column(Float)
    review_velocity = Column(Float)

    last_seen_at = Column(DateTime)
    last_metrics_update = Column(DateTime)

    selection_score = Column(Float)
    selection_status = Column(String(50))
    selection_reason = Column(Text)

    # Comma-separated marketplace badge/trend labels as literally
    # displayed on the card (e.g. "热门商品,超千人种草") — never
    # inferred, only recorded when the marketplace shows them.
    badges = Column(Text)

    # --------------------------------------------------
    # Product URLs and images
    # --------------------------------------------------

    product_url = Column(
        Text,
    )

    affiliate_url = Column(
        Text,
    )

    image_url = Column(
        Text,
    )

    # --------------------------------------------------
    # Algorithm opportunity score
    # --------------------------------------------------

    opportunity_score = Column(
        Float,
        default=0,
    )


    # --------------------------------------------------
    # Content opportunity scoring
    # --------------------------------------------------

    content_opportunity_score = Column(
        Float,
        default=0,
    )

    content_opportunity_level = Column(
        String(20),
    )

    combined_priority_score = Column(
        Float,
        default=0,
    )

    # --------------------------------------------------
    # Targeted Product & Trend Research
    # --------------------------------------------------

    research_keyword = Column(
        String(500),
        nullable=True,
    )

    discovery_source = Column(
        String(100),
        nullable=True,
    )

    source_product_url = Column(
        Text,
        nullable=True,
    )

    trend_score = Column(
        Float,
        default=0,
    )

    video_potential_score = Column(
        Float,
        default=0,
    )

    has_demo_video = Column(
        Boolean,
        default=False,
    )

    cross_marketplace_status = Column(
        String(50),
        default="not_checked",
    )


    cross_marketplace_score = Column(
        Float,
        default=0,
    )

    cross_marketplace_match_source = Column(
        String(100),
        nullable=True,
    )

    cross_marketplace_match_url = Column(
        Text,
        nullable=True,
    )

    cross_marketplace_similarity = Column(
        Float,
        default=0,
    )


    research_intelligence_score = Column(
        Float,
        default=0,
    )

    research_intelligence_level = Column(
        String(20),
        nullable=True,
    )

    # --------------------------------------------------
    # Claude AI analysis
    # --------------------------------------------------

    ai_score = Column(
        Float,
    )

    editorial_decision = Column(
        String(50),
        nullable=True,
    )

    ai_decision = Column(
        String(20),
    )

    target_audience = Column(
        Text,
    )

    content_potential = Column(
        Text,
    )

    best_content_angle = Column(
        Text,
    )

    why_it_could_sell = Column(
        Text,
    )

    risks = Column(
        Text,
    )

    verification_needed = Column(
        Text,
    )

    # --------------------------------------------------
    # Claude API usage
    # --------------------------------------------------

    ai_input_tokens = Column(
        Integer,
        default=0,
    )

    ai_output_tokens = Column(
        Integer,
        default=0,
    )

    ai_analyzed_at = Column(
        DateTime,
    )

    # --------------------------------------------------
    # Product discovery status
    # --------------------------------------------------

    status = Column(
        String(50),
        default="DISCOVERED",
    )

    # --------------------------------------------------
    # Public content workflow
    #
    # These fields are used by content_service.py
    # and the Streamlit editorial workflow.
    # --------------------------------------------------

    public_title = Column(
        String(500),
    )

    public_slug = Column(
        String(500),
    )

    public_summary = Column(
        Text,
    )

    public_content = Column(
        Text,
    )

    content_status = Column(
        String(50),
        default="NOT_CREATED",
    )

    content_generated_at = Column(
        DateTime,
    )

    # --------------------------------------------------
    # Website publishing workflow
    #
    # These fields are used by publishing_service.py
    # and website_publisher.py.
    # --------------------------------------------------

    slug = Column(
        String(500),
    )

    publish_status = Column(
        String(50),
        default="draft",
    )

    article_title = Column(
        String(500),
    )

    article_content = Column(
        Text,
    )

    published_at = Column(
        DateTime,
    )

    # --------------------------------------------------
    # Record timestamps
    # --------------------------------------------------

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )
