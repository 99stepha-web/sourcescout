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

        page.set_default_timeout(120000)

        page.goto(
            ALIMAMA_URL,
            wait_until="domcontentloaded",
            timeout=120000,
        )

        page.wait_for_load_state("networkidle")

        page.wait_for_timeout(5000)

        try:

            search_box = page.locator("input").first

            search_box.click()

            search_box.fill(keyword)

            page.keyboard.press("Enter")

            page.wait_for_load_state("networkidle")

            page.wait_for_timeout(5000)

        except Exception:

            print(f"\nSearch keyword: {keyword}")

            input(
                "\nSearch manually once, wait until products appear, then press ENTER..."
            )

        cards = page.locator("div[data-spm='GoodsListItem']")

        print(f"\nFound {cards.count()} products")

        if cards.count() == 0:

            page.pause()

        return page