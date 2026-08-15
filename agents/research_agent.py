from affiliate.alimama.search import AlimamaSearch
from affiliate.alimama.parser import AlimamaParser
from product_ingestion import ProductIngestion


class ResearchAgent:

    def __init__(self):
        self.search_agent = AlimamaSearch()
        self.parser = AlimamaParser()
        self.ingestion = ProductIngestion()

    def research(self, keyword: str):

        print(f"\nSearching: {keyword}")

        page = self.search_agent.search(keyword)

        try:
            # -------------------------------------------------
            # Parse product + affiliate URL
            # -------------------------------------------------

            results = self.parser.parse(page)

            if not results:
                print("\n❌ No Alimama results returned.")
                return []

            print(
                f"\n✅ Parser returned "
                f"{len(results)} product(s)"
            )

            # -------------------------------------------------
            # Add research keyword
            # -------------------------------------------------

            for product in results:
                product["keyword"] = keyword

            # -------------------------------------------------
            # Save ALL discovered products into SQLite
            # -------------------------------------------------

            products = self.ingestion.ingest(results)

            print(
                f"\n✅ Saved {len(products)} product(s) "
                f"into SQLite"
            )

            # -------------------------------------------------
            # IMPORTANT:
            # ProductIngestion returns SQLAlchemy objects.
            # Keep every successfully discovered product.
            # Do not reduce the research result to the first item.
            # -------------------------------------------------

            if len(products) > 1:
                print(
                    f"\n✅ Multi-product research active: "
                    f"{len(products)} candidates available."
                )

            # -------------------------------------------------
            # Confirm affiliate URL
            # -------------------------------------------------

            for product in products:

                print(
                    "\n----------------------------------------"
                )

                print(
                    f"Product: {product.title}"
                )

                print(
                    f"Affiliate URL: "
                    f"{product.affiliate_url}"
                )

                print(
                    "----------------------------------------"
                )

            return products

        finally:

            try:
                page.context.browser.close()
            except Exception:
                pass
