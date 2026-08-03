from playwright.sync_api import sync_playwright

ALIMAMA_URL = (
    "https://pub.alimama.com/portal/v2/pages/promo/goods/index.htm"
)


class AlimamaSearch:

    def search(self, keyword: str):

        p = sync_playwright().start()

        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
        )

        context = browser.new_context(
            storage_state="data/alimama_state.json",
        )

        page = context.new_page()

        # Give Alimama more time
        page.set_default_timeout(120000)

        # Don't wait for the entire page to finish
        page.goto(
            ALIMAMA_URL,
            wait_until="commit",
            timeout=120000,
        )

        print("\nSearch this keyword in Alimama:")
        print(keyword)

        input(
            "\nSearch manually, wait until products appear, then press ENTER..."
        )

        return page
