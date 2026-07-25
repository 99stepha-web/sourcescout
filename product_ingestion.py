from datetime import datetime
from typing import Any

from database import SessionLocal
from models import Product

from utils.data_cleaning import (
    clean_text,
    clean_float,
    clean_int,
)


# --------------------------------------------------
# Data cleaning helpers
# --------------------------------------------------

def old_clean_text(value, default=""):
    if value is None:
        return default

    return str(value).strip()


def old_clean_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def old_clean_int(value, default=0):
    try:
        if value is None or value == "":
            return default

        return int(float(value))

    except (TypeError, ValueError):
        return default


# --------------------------------------------------
# Product validation
# --------------------------------------------------

def validate_product_data(data: dict[str, Any]):

    required_fields = [
        "platform",
        "product_id",
        "title",
    ]

    missing_fields = []

    for field in required_fields:

        value = data.get(field)

        if value is None or str(value).strip() == "":
            missing_fields.append(field)

    if missing_fields:

        raise ValueError(
            "Missing required product fields: "
            + ", ".join(missing_fields)
        )


# --------------------------------------------------
# Normalize marketplace product
# --------------------------------------------------

def normalize_product_data(data: dict[str, Any]):

    validate_product_data(data)

    return {

        "platform": clean_text(
            data.get("platform")
        ),

        "product_id": clean_text(
            data.get("product_id")
        ),

        "title": clean_text(
            data.get("title")
        ),

        "category": clean_text(
            data.get("category"),
            "Uncategorized",
        ),

        "price": clean_float(
            data.get("price")
        ),

        "original_price": clean_float(
            data.get("original_price")
        ),

        "orders": clean_int(
            data.get("orders")
        ),

        "rating": clean_float(
            data.get("rating")
        ),

        "supplier": clean_text(
            data.get("supplier")
        ),

        "moq": clean_text(
            data.get("moq")
        ),

        "price_text": clean_text(
            data.get("price_text")
        ),

        "price_min": clean_float(
            data.get(
                "price_min",
                data.get("price"),
            )
        ),

        "price_max": clean_float(
            data.get("price_max")
        ),

        "review_count": clean_int(
            data.get("review_count")
        ),

        "supplier_score": clean_float(
            data.get("supplier_score")
        ),

        "commission_rate": clean_float(
            data.get("commission_rate")
        ),

        "product_url": clean_text(
            data.get("product_url")
        ),

        "affiliate_url": clean_text(
            data.get("affiliate_url")
        ),

        "image_url": clean_text(
            data.get("image_url")
        ),
    }


# --------------------------------------------------
# Opportunity scoring
# --------------------------------------------------

def calculate_opportunity_score(data):
    """
    Calculate a marketplace-aware opportunity score.

    Maximum score: 100

    Factors:
    - Demand: 30 points
    - Rating and review confidence: 25 points
    - Supplier confidence: 15 points
    - Price accessibility: 15 points
    - MOQ accessibility: 10 points
    - Affiliate commission: 5 points
    """

    score = 0.0

    orders = clean_int(
        data.get("orders")
    )

    rating = clean_float(
        data.get("rating")
    )

    review_count = clean_int(
        data.get("review_count")
    )

    supplier = clean_text(
        data.get("supplier")
    )

    supplier_score = clean_float(
        data.get("supplier_score")
    )

    commission_rate = clean_float(
        data.get("commission_rate")
    )

    price = clean_float(
        data.get(
            "price_min",
            data.get("price"),
        )
    )

    moq = clean_text(
        data.get("moq")
    ).lower()

    price_text = clean_text(
        data.get("price_text")
    ).lower()


    # ----------------------------------------------
    # 1. Demand — maximum 30 points
    # ----------------------------------------------

    if orders >= 10000:
        score += 30

    elif orders >= 5000:
        score += 27

    elif orders >= 1000:
        score += 23

    elif orders >= 500:
        score += 19

    elif orders >= 100:
        score += 14

    elif orders >= 20:
        score += 8

    elif orders > 0:
        score += 4


    # ----------------------------------------------
    # 2. Rating + review confidence — max 25
    # ----------------------------------------------

    if rating >= 4.8:
        rating_points = 18

    elif rating >= 4.5:
        rating_points = 15

    elif rating >= 4.0:
        rating_points = 10

    elif rating > 0:
        rating_points = 4

    else:
        rating_points = 0


    if review_count >= 500:
        review_points = 7

    elif review_count >= 100:
        review_points = 6

    elif review_count >= 20:
        review_points = 4

    elif review_count >= 5:
        review_points = 2

    elif review_count > 0:
        review_points = 1

    else:
        review_points = 0


    score += (
        rating_points
        + review_points
    )


    # ----------------------------------------------
    # 3. Supplier confidence — maximum 15
    # ----------------------------------------------

    if supplier_score >= 90:
        score += 15

    elif supplier_score >= 80:
        score += 13

    elif supplier_score >= 70:
        score += 10

    elif supplier_score > 0:
        score += 6

    elif supplier:
        # Verified marketplace supplier information
        # exists, but no numerical score is available.
        score += 5


    # ----------------------------------------------
    # 4. Price accessibility — maximum 15
    # ----------------------------------------------

    # Detect listings where the displayed price is
    # likely a component/unit measurement rather than
    # the price of one complete retail product.

    unit_pricing_terms = (
        "watt",
        "watts",
        "meter",
        "meters",
        "kilogram",
        "kilograms",
        "kg",
        "ton",
        "tons",
    )

    has_unit_pricing = any(
        term in moq
        for term in unit_pricing_terms
    )


    if has_unit_pricing:

        # Do not reward an artificially low unit price.
        price_points = 3


    elif 10 <= price <= 100:

        price_points = 15


    elif 100 < price <= 300:

        price_points = 12


    elif 300 < price <= 1000:

        price_points = 8


    elif price > 1000:

        price_points = 4


    elif 0 < price < 10:

        # Low prices can be legitimate, but marketplace
        # listings frequently use sample/component prices.
        price_points = 6


    else:

        price_points = 0


    score += price_points


    # ----------------------------------------------
    # 5. MOQ accessibility — maximum 10
    # ----------------------------------------------

    import re

    moq_match = re.search(
        r"\d+(?:\.\d+)?",
        moq,
    )


    if has_unit_pricing:

        moq_points = 2


    elif moq_match:

        moq_quantity = float(
            moq_match.group()
        )


        if moq_quantity <= 1:

            moq_points = 10


        elif moq_quantity <= 5:

            moq_points = 8


        elif moq_quantity <= 20:

            moq_points = 6


        elif moq_quantity <= 100:

            moq_points = 4


        else:

            moq_points = 2


    else:

        # Unknown MOQ should not receive the same
        # reward as a confirmed low MOQ.

        moq_points = 3


    score += moq_points


    # ----------------------------------------------
    # 6. Affiliate commission — maximum 5
    # ----------------------------------------------

    if commission_rate >= 15:
        score += 5

    elif commission_rate >= 10:
        score += 4

    elif commission_rate >= 5:
        score += 3

    elif commission_rate > 0:
        score += 1


    return round(
        min(
            max(score, 0),
            100,
        ),
        1,
    )


# --------------------------------------------------
# Find existing product
# --------------------------------------------------

def find_existing_product(
    db,
    platform,
    product_id,
):

    return (
        db.query(Product)
        .filter(
            Product.platform == platform,
            Product.product_id == product_id,
        )
        .first()
    )


# --------------------------------------------------
# Import or update one product
# --------------------------------------------------

def ingest_product(
    data,
    db=None,
):

    owns_session = False

    if db is None:

        db = SessionLocal()

        owns_session = True


    try:

        normalized = normalize_product_data(
            data
        )

        normalized[
            "opportunity_score"
        ] = calculate_opportunity_score(
            normalized
        )


        existing_product = (
            find_existing_product(
                db,
                normalized["platform"],
                normalized["product_id"],
            )
        )


        if existing_product:

            # Update marketplace information

            existing_product.title = (
                normalized["title"]
            )

            existing_product.category = (
                normalized["category"]
            )

            existing_product.price = (
                normalized["price"]
            )

            existing_product.original_price = (
                normalized["original_price"]
            )

            existing_product.orders = (
                normalized["orders"]
            )

            existing_product.rating = (
                normalized["rating"]
            )

            existing_product.supplier = (
                normalized["supplier"]
            )

            existing_product.moq = (
                normalized["moq"]
            )

            existing_product.price_text = (
                normalized["price_text"]
            )

            existing_product.price_min = (
                normalized["price_min"]
            )

            existing_product.price_max = (
                normalized["price_max"]
            )

            existing_product.review_count = (
                normalized["review_count"]
            )

            existing_product.supplier_score = (
                normalized["supplier_score"]
            )

            existing_product.commission_rate = (
                normalized["commission_rate"]
            )

            existing_product.product_url = (
                normalized["product_url"]
            )

            # Only replace affiliate URL when
            # a new non-empty value is provided.

            if normalized["affiliate_url"]:

                existing_product.affiliate_url = (
                    normalized["affiliate_url"]
                )


            # Only replace image when available.

            if normalized["image_url"]:

                existing_product.image_url = (
                    normalized["image_url"]
                )


            existing_product.opportunity_score = (
                normalized[
                    "opportunity_score"
                ]
            )


            db.commit()

            db.refresh(
                existing_product
            )


            result = {

                "action": "updated",

                "product_id":
                    existing_product.id,

                "marketplace_product_id":
                    existing_product.product_id,

                "title":
                    existing_product.title,

                "opportunity_score":
                    existing_product.opportunity_score,
            }


        else:

            product = Product(

                platform=normalized[
                    "platform"
                ],

                product_id=normalized[
                    "product_id"
                ],

                title=normalized[
                    "title"
                ],

                category=normalized[
                    "category"
                ],

                price=normalized[
                    "price"
                ],

                original_price=normalized[
                    "original_price"
                ],

                orders=normalized[
                    "orders"
                ],

                rating=normalized[
                    "rating"
                ],

                supplier=normalized[
                    "supplier"
                ],

                moq=normalized[
                    "moq"
                ],

                price_text=normalized[
                    "price_text"
                ],

                price_min=normalized[
                    "price_min"
                ],

                price_max=normalized[
                    "price_max"
                ],

                review_count=normalized[
                    "review_count"
                ],

                supplier_score=normalized[
                    "supplier_score"
                ],

                commission_rate=normalized[
                    "commission_rate"
                ],

                product_url=normalized[
                    "product_url"
                ],

                affiliate_url=normalized[
                    "affiliate_url"
                ],

                image_url=normalized[
                    "image_url"
                ],

                opportunity_score=normalized[
                    "opportunity_score"
                ],

                status="DISCOVERED",

                publish_status="draft",
            )


            db.add(
                product
            )

            db.commit()

            db.refresh(
                product
            )


            result = {

                "action": "created",

                "product_id":
                    product.id,

                "marketplace_product_id":
                    product.product_id,

                "title":
                    product.title,

                "opportunity_score":
                    product.opportunity_score,
            }


        return result


    except Exception:

        db.rollback()

        raise


    finally:

        if owns_session:

            db.close()


# --------------------------------------------------
# Import multiple products
# --------------------------------------------------

def ingest_products(
    products,
):

    db = SessionLocal()

    results = {

        "created": 0,

        "updated": 0,

        "failed": 0,

        "products": [],

        "errors": [],
    }


    try:

        for data in products:

            try:

                result = ingest_product(
                    data,
                    db=db,
                )

                action = result[
                    "action"
                ]

                results[
                    action
                ] += 1

                results[
                    "products"
                ].append(
                    result
                )


            except Exception as error:

                db.rollback()

                results[
                    "failed"
                ] += 1

                results[
                    "errors"
                ].append(
                    {
                        "title":
                            data.get(
                                "title",
                                "Unknown product",
                            ),

                        "error":
                            str(error),
                    }
                )


        return results


    finally:

        db.close()


# --------------------------------------------------
# Test ingestion
# --------------------------------------------------

if __name__ == "__main__":

    test_product = {

        "platform":
            "Alibaba",

        "product_id":
            "REAL-TEST-001",

        "title":
            "Smart Portable Mini Projector",

        "category":
            "Electronics",

        "price":
            59.99,

        "original_price":
            89.99,

        "orders":
            1250,

        "rating":
            4.8,

        "supplier_score":
            92,

        "commission_rate":
            8,

        "product_url":
            "https://example.com/product",

        "affiliate_url":
            "",

        "image_url":
            "",
    }


    result = ingest_product(
        test_product
    )


    print()

    print(
        "✅ Product ingestion test completed."
    )

    print(
        result
    )
