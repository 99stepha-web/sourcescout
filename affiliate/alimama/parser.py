from playwright.sync_api import Page


class AlimamaParser:

    def parse(self, page: Page):

        products = []

        commission_nodes = page.locator("text=佣金率")

        count = commission_nodes.count()

        print(f"\nFound {count} commission labels")

        for i in range(min(count, 20)):

            try:

                text = (
                    commission_nodes
                    .nth(i)
                    .locator("xpath=ancestor::div[6]")
                    .inner_text()
                )

                print("\n====================")
                print(text[:600])

                products.append({
                    "raw_text": text,
                })

            except Exception:
                continue

        return products
