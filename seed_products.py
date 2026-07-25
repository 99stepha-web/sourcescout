from database import Base, SessionLocal, engine
from models import Product
from scoring import calculate_opportunity_score


SAMPLE_PRODUCTS = [
    {
        "platform": "Alibaba",
        "product_id": "ALI-001",
        "title": "Automatic PET Bottle Filling Machine",
        "category": "Machinery",
        "price": 2800,
        "original_price": 3500,
        "orders": 240,
        "rating": 4.8,
        "supplier_score": 4.9,
        "commission_rate": 8,
    },
    {
        "platform": "Alibaba",
        "product_id": "ALI-002",
        "title": "Portable Solar Power Station 2000W",
        "category": "Energy",
        "price": 389,
        "original_price": 599,
        "orders": 1204,
        "rating": 4.9,
        "supplier_score": 4.8,
        "commission_rate": 10,
    },
    {
        "platform": "Alibaba",
        "product_id": "ALI-003",
        "title": "Commercial Ice Block Making Machine",
        "category": "Machinery",
        "price": 4500,
        "original_price": 5200,
        "orders": 87,
        "rating": 4.7,
        "supplier_score": 4.8,
        "commission_rate": 12,
    },
    {
        "platform": "Taobao",
        "product_id": "TB-001",
        "title": "Premium Vintage Streetwear Jacket",
        "category": "Fashion",
        "price": 42,
        "original_price": 75,
        "orders": 3890,
        "rating": 4.9,
        "supplier_score": 4.7,
        "commission_rate": 9,
    },
    {
        "platform": "Taobao",
        "product_id": "TB-002",
        "title": "Minimalist Japanese Style Shoulder Bag",
        "category": "Fashion",
        "price": 18,
        "original_price": 35,
        "orders": 8500,
        "rating": 4.8,
        "supplier_score": 4.6,
        "commission_rate": 11,
    },
]


def seed_database():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        for product_data in SAMPLE_PRODUCTS:

            existing_product = (
                db.query(Product)
                .filter(
                    Product.product_id
                    == product_data["product_id"]
                )
                .first()
            )

            if existing_product:
                print(
                    f"⏭️ Already exists: "
                    f"{product_data['title']}"
                )
                continue

            product = Product(**product_data)

            product.opportunity_score = (
                calculate_opportunity_score(product)
            )

            db.add(product)

            print(
                f"✅ Added: {product.title} "
                f"— Score: {product.opportunity_score}"
            )

        db.commit()

        print("\n🚀 Product Scout database seeded successfully.")

    except Exception as error:
        db.rollback()
        print(f"❌ Error: {error}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()