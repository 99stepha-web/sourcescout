from pathlib import Path
from playwright.sync_api import sync_playwright


class AlibabaSearch:

    def __init__(self):
        pass

    def search(self, keyword: str, page: int = 1):

        url = (
            "https://www.alibaba.com/trade/search"
            f"?SearchText={keyword.replace(' ', '+')}"
            f"&page={page}"
        )

        chrome_profile = (
            Path.home()
            / "Library/Application Support/Google/Chrome/SourceScout"
        )

        with sync_playwright() as p:

            context = p.chromium.launch_persistent_context(
                user_data_dir=str(chrome_profile),
                channel="chrome",
                headless=False,
                viewport={"width": 1600, "height": 900},
            )

            page = context.new_page()

            import json

            def log_response(response):
                try:
                    if "application/json" in response.headers.get(
                        "content-type", ""
                    ):
                        print("\nJSON:", response.url)

                        data = response.json()

                        if isinstance(data, dict):
                            print(
                                json.dumps(
                                    data,
                                    ensure_ascii=False,
                                )[:1000]
                            )
                except Exception:
                    pass

            page.on("response", log_response)

            page.goto(
                url,
                wait_until="domcontentloaded",
            )

            print(
                "\nLog in to Alibaba if requested."
                "\nAfter the page finishes loading,"
                "\npress ENTER in Terminal..."
            )

            input()

            html = page.content()

            context.close()

            return html
