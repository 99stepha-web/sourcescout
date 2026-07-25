"""

Verify that the new Core Scoring Engine produces the same
Opportunity Score as the legacy implementation.

Run:

    python scripts/verify_opportunity_engine.py
"""


from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


from product_ingestion import calculate_opportunity_score as legacy_score
from core.scoring_engine import calculate_opportunity_score as new_score


TEST_PRODUCTS = [
    {
        "name": "High Demand Product",
        "orders": 12000,
        "rating": 4.9,
        "review_count": 850,
        "supplier": "Gold Supplier",
        "supplier_score": 95,
        "commission_rate": 5,
        "price": 18.5,
        "price_min": 18.5,
        "moq": "1",
        "price_text": "",
    },
    {
        "name": "Medium Product",
        "orders": 600,
        "rating": 4.4,
        "review_count": 65,
        "supplier": "Verified Supplier",
        "supplier_score": 82,
        "commission_rate": 3,
        "price": 42,
        "price_min": 42,
        "moq": "10",
        "price_text": "",
    },
    {
        "name": "Low Demand Product",
        "orders": 8,
        "rating": 3.9,
        "review_count": 2,
        "supplier": "",
        "supplier_score": 0,
        "commission_rate": 1,
        "price": 150,
        "price_min": 150,
        "moq": "100",
        "price_text": "",
    },
]

print("=" * 70)
print("Opportunity Engine Verification")
print("=" * 70)

all_match = True

for product in TEST_PRODUCTS:

    old = legacy_score(product)
    new = new_score(product)["opportunity_score"]

    match = abs(old - new) < 0.01

    print(f"\n{product['name']}")
    print(f"Legacy : {old}")
    print(f"New    : {new}")

    if match:
        print("✅ MATCH")
    else:
        print("❌ DIFFERENT")
        all_match = False

print("\n" + "=" * 70)

if all_match:
    print("🎉 ALL TESTS PASSED")
else:
    print("⚠️ Differences detected")
