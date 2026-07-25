from marketplace_connectors.alibaba import discover_alibaba_products

try:
    products = discover_alibaba_products(
        keyword="portable solar power station",
        max_results=5,
    )

    print()
    print(f"Found {len(products)} products")
    print()

    for index, product in enumerate(products, start=1):
        print("=" * 60)
        print(f"PRODUCT {index}")
        print("ID:", product["product_id"])
        print("Title:", product["title"])
        print("Price:", product["price"])
        print("Rating:", product["rating"])
        print("Orders:", product["orders"])
        print("Supplier:", product["supplier"])
        print("Minimum Order:", product["moq"])
        print("Image:", product["image_url"])
        print("URL:", product["product_url"])

except Exception as error:
    print()
    print("❌ Alibaba connector error:")
    print(error)
