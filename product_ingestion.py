from datetime import datetime

from database import SessionLocal
from models import Product
from affiliate.utils.url_utils import clean_affiliate_url


def _num(value, cast):
    """
    Cast value with cast (int/float), preserving None as None instead
    of coercing missing marketplace data into a fabricated 0.
    """

    if value is None:
        return None

    return cast(value)


class ProductIngestion:

    def __init__(self, db=None):
        self.db = db or SessionLocal()

    def ingest(self, products):

        saved = []

        for item in products:

            title = item.get(
                "title",
                ""
            ).strip()

            if not title:
                continue

            platform = item.get(
                "platform",
                "alimama"
            )

            product_id = item.get(
                "product_id",
                "",
            )

            # -------------------------------------------------
            # Find existing product.
            # Prefer platform + product_id (the strongest
            # identifier). Fall back to title only when no
            # product_id is available.
            # -------------------------------------------------

            if product_id:
                existing = (
                    self.db.query(Product)
                    .filter(
                        Product.platform == platform,
                        Product.product_id == product_id,
                    )
                    .first()
                )
            else:
                existing = (
                    self.db.query(Product)
                    .filter(
                        Product.platform == platform,
                        Product.title == title,
                    )
                    .first()
                )

            # -------------------------------------------------
            # UPDATE EXISTING PRODUCT
            # -------------------------------------------------

            if existing:

                # Always update the real affiliate URL when
                # a new Alimama promotion generates one.
                raw_affiliate_url = item.get(
                    "affiliate_url",
                    "",
                )

                new_affiliate_url = clean_affiliate_url(
                    raw_affiliate_url
                )

                print(
                    "\n🔄 EXISTING PRODUCT UPDATE"
                )
                print(
                    f"Product ID: {existing.id}"
                )
                print(
                    f"Incoming affiliate URL: "
                    f"{raw_affiliate_url}"
                )
                print(
                    f"Clean affiliate URL: "
                    f"{new_affiliate_url}"
                )

                if new_affiliate_url:
                    existing.affiliate_url = new_affiliate_url
                    print(
                        "✅ Affiliate URL updated."
                    )
                else:
                    print(
                        "❌ Incoming affiliate URL could not "
                        "be cleaned."
                    )

                new_product_url = item.get(
                    "product_url",
                    "",
                )

                if new_product_url:
                    existing.product_url = new_product_url

                new_image_url = item.get(
                    "image_url",
                    "",
                )

                if new_image_url:
                    existing.image_url = new_image_url

                keyword = item.get(
                    "keyword",
                    "",
                )

                if keyword:
                    existing.research_keyword = keyword

                if item.get("commission_rate") is not None:
                    existing.commission_rate = float(
                        item.get(
                            "commission_rate",
                            0,
                        )
                    )

                # Refresh whatever marketplace signals this scrape
                # captured. Only overwrite a field when the new scrape
                # actually reports a value for it — a metric that was
                # visible before and isn't now (e.g. a transient page
                # render gap) shouldn't be wiped back to unknown.
                for field in (
                    "commission_amount", "monthly_sales", "monthly_promoters",
                    "today_sales", "price_percentile", "commission_percentile",
                    "shop_rating", "badges", "orders", "rating", "review_count",
                    "supplier_score",
                ):
                    value = item.get(field)
                    if value is not None:
                        setattr(existing, field, value)

                if item.get("shop_name"):
                    existing.supplier = item.get("shop_name")

                existing.last_seen_at = datetime.utcnow()
                existing.status = "DISCOVERED"

                saved.append(existing)

                continue

            # -------------------------------------------------
            # CREATE NEW PRODUCT
            # -------------------------------------------------

            product = Product(

                platform=platform,

                product_id=item.get(
                    "product_id",
                    title,
                ),

                title=title,

                category=item.get(
                    "category",
                    "Coffee",
                ),

                # Pricing
                price=float(
                    item.get("price", 0)
                ),

                original_price=float(
                    item.get(
                        "original_price",
                        0
                    )
                ),

                price_text=item.get(
                    "price_text",
                    "",
                ),

                price_min=float(
                    item.get("price_min", 0)
                ),

                price_max=float(
                    item.get("price_max", 0)
                ),

                # Sales — never fabricated: a metric the marketplace
                # didn't expose stays NULL, not 0.
                orders=_num(
                    item.get("orders", item.get("monthly_sales")),
                    int,
                ),

                rating=_num(item.get("rating"), float),

                review_count=_num(item.get("review_count"), int),

                # Supplier
                supplier=item.get(
                    "supplier",
                    item.get(
                        "shop_name",
                        "",
                    ),
                ),

                supplier_score=_num(item.get("supplier_score"), float),

                moq=item.get(
                    "moq",
                    "",
                ),

                # Affiliate
                commission_rate=float(
                    item.get(
                        "commission_rate",
                        0
                    )
                ),

                commission_amount=_num(item.get("commission_amount"), float),

                # Selection-intelligence raw signals (see product_scoring.py)
                monthly_sales=_num(item.get("monthly_sales"), int),
                monthly_promoters=_num(item.get("monthly_promoters"), int),
                today_sales=_num(item.get("today_sales"), int),
                price_percentile=_num(item.get("price_percentile"), float),
                commission_percentile=_num(item.get("commission_percentile"), float),
                shop_rating=_num(item.get("shop_rating"), float),
                badges=item.get("badges") or None,

                # URLs
                product_url=item.get(
                    "product_url",
                    "",
                ),

                affiliate_url=clean_affiliate_url(
                    item.get(
                        "affiliate_url",
                        "",
                    )
                ),

                image_url=item.get(
                    "image_url",
                    "",
                ),

                # Discovery
                discovery_source="alimama",

                research_keyword=item.get(
                    "keyword",
                    "",
                ),

                last_seen_at=datetime.utcnow(),

                status="DISCOVERED",
            )

            self.db.add(product)

            saved.append(product)

        self.db.commit()

        return saved
