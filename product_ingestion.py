from database import SessionLocal
from models import Product
from affiliate.utils.url_utils import clean_affiliate_url


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

                # Sales
                orders=int(
                    item.get(
                        "orders",
                        item.get(
                            "monthly_sales",
                            0
                        ),
                    )
                ),

                rating=float(
                    item.get(
                        "rating",
                        0
                    )
                ),

                review_count=int(
                    item.get(
                        "review_count",
                        0
                    )
                ),

                # Supplier
                supplier=item.get(
                    "supplier",
                    item.get(
                        "shop_name",
                        "",
                    ),
                ),

                supplier_score=float(
                    item.get(
                        "supplier_score",
                        0
                    )
                ),

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

                status="DISCOVERED",
            )

            self.db.add(product)

            saved.append(product)

        self.db.commit()

        return saved
