from playwright.sync_api import sync_playwright

with sync_playwright() as p:

    browser = p.chromium.launch(
        channel="chrome",
        headless=False,
    )

    context = browser.new_context()

    page = context.new_page()

    page.goto("https://pub.alimama.com")

    print("\nLogin to Alimama manually.")
    input("\nAfter you are fully logged in, press ENTER...")

    context.storage_state(path="data/alimama_state.json")

    print("\nSaved login state to data/alimama_state.json")

    browser.close()
