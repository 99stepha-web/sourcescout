import re
import uuid

from playwright.sync_api import Page

from affiliate.utils.url_utils import extract_stable_product_id
from product_scoring import extract_badges
import category_taxonomy


class AlimamaParser:

    TAOBAO_URL_PATTERN = re.compile(
        r"https?://(?:s\.click\.taobao\.com|m\.tb\.cn)/[A-Za-z0-9._/?=&%:-]+"
    )

    def parse(self, page: Page):

        MAX_PRODUCTS = 10

        cards = page.locator(
            "div[data-spm='GoodsListItem']"
        )

        count = cards.count()

        print(f"\\nCards found: {count}")

        if count == 0:
            return []

        product_snapshots = []

        # =====================================================
        # STEP 1
        # SNAPSHOT PRODUCT DATA BEFORE OPENING ANY PRODUCT
        # =====================================================

        limit = min(count, MAX_PRODUCTS)

        print(
            f"\\nProcessing {limit} products..."
        )

        for index in range(limit):

            try:
                card = cards.nth(index)

                title = self._extract_title(card)
                product_url = self._extract_product_url(card)
                image_url = self._extract_image_url(card)
                price, commission_rate, badges = self._extract_card_metrics(card)
                shop_name = self._extract_shop_name(card)

                if not title:
                    print(
                        f"⚠️ Product {index + 1}: "
                        "title not found. Skipping."
                    )
                    continue

                if not product_url:
                    print(
                        f"⚠️ Product {index + 1}: "
                        "product URL not found. Skipping."
                    )
                    continue

                product_snapshots.append(
                    {
                        "index": index + 1,
                        "title": title,
                        "product_url": product_url,
                        "image_url": image_url,
                        "price": price,
                        "commission_rate": commission_rate,
                        "badges": badges,
                        "shop_name": shop_name,
                    }
                )

            except Exception as e:
                print(
                    f"⚠️ Could not snapshot product "
                    f"{index + 1}: {e}"
                )

        if not product_snapshots:
            print(
                "\\n❌ No usable products could be "
                "snapshotted."
            )
            return []

        print(
            f"\\n✅ Snapshotted "
            f"{len(product_snapshots)} products"
        )

        # =====================================================
        # STEP 2
        # PROCESS EACH PRODUCT IN ITS OWN PAGE
        # =====================================================

        results = []

        for snapshot in product_snapshots:

            index = snapshot["index"]
            title = snapshot["title"]
            product_url = snapshot["product_url"]
            image_url = snapshot["image_url"]
            price = snapshot["price"]
            commission_rate = snapshot["commission_rate"]
            badges = snapshot["badges"]
            shop_name = snapshot["shop_name"]

            print(
                "\\n========================================"
            )
            print(
                f"PRODUCT {index}/{len(product_snapshots)}"
            )
            print(
                "========================================"
            )

            print(
                f"Title: {title}"
            )

            print(
                f"Product URL: {product_url}"
            )

            print(
                f"Image: {image_url}"
            )

            detail_page = None

            try:

                # -------------------------------------------------
                # OPEN PRODUCT DIRECTLY
                # -------------------------------------------------

                print(
                    "\\nOpening product in new page..."
                )

                detail_page = page.context.new_page()

                detail_page.goto(
                    product_url,
                    wait_until="domcontentloaded",
                    timeout=30000,
                )

                detail_page.wait_for_timeout(2500)

                print(
                    f"Current URL: {detail_page.url}"
                )

                detail_metrics = self._extract_detail_metrics(detail_page)

                # -------------------------------------------------
                # FIND PROMOTION BUTTON
                # -------------------------------------------------

                print(
                    "\\nLooking for 立即推广..."
                )

                promotion_selector = (
                    "button.good-card-promotion-btn"
                )

                try:

                    detail_page.wait_for_selector(
                        promotion_selector,
                        state="visible",
                        timeout=15000,
                    )

                except Exception:

                    print(
                        "⚠️ Promotion button did not "
                        "become visible."
                    )

                    # Fallback to text selector.
                    try:

                        text_button = detail_page.get_by_text(
                            "立即推广",
                            exact=True,
                        )

                        if text_button.count() == 0:

                            print(
                                "⚠️ 立即推广 not found. "
                                "Skipping product."
                            )

                            continue

                        promotion_button = (
                            text_button.first
                        )

                    except Exception:

                        print(
                            "⚠️ 立即推广 not found. "
                            "Skipping product."
                        )

                        continue

                else:

                    promotion_buttons = (
                        detail_page.locator(
                            promotion_selector
                        )
                    )

                    if promotion_buttons.count() == 0:

                        print(
                            "⚠️ No promotion button. "
                            "Skipping product."
                        )

                        continue

                    promotion_button = (
                        promotion_buttons.first
                    )

                # -------------------------------------------------
                # CLICK PROMOTION BUTTON
                # -------------------------------------------------

                try:

                    promotion_button.click(
                        timeout=10000
                    )

                except Exception as click_error:

                    print(
                        f"⚠️ Normal click failed: "
                        f"{click_error}"
                    )

                    try:

                        promotion_button.click(
                            force=True,
                            timeout=5000,
                        )

                    except Exception as force_error:

                        print(
                            f"❌ Force click failed: "
                            f"{force_error}"
                        )

                        continue

                print(
                    "\\nClicked 立即推广."
                )

                print(
                    "Waiting for promotion dialog..."
                )

                detail_page.wait_for_timeout(3000)

                # -------------------------------------------------
                # EXTRACT TAOBAO AFFILIATE URL
                # -------------------------------------------------

                affiliate_url = (
                    self._extract_affiliate_url(
                        detail_page
                    )
                )

                if not affiliate_url:

                    print(
                        "❌ Affiliate URL could not "
                        "be extracted."
                    )

                    continue

                print(
                    "\\n✅ Product captured."
                )

                print(
                    f"Affiliate URL: {affiliate_url}"
                )

                # -------------------------------------------------
                # COMPLETE PRODUCT RECORD
                # -------------------------------------------------

                product = {
                    "platform": "alimama",

                    "product_id": (
                        extract_stable_product_id(product_url)
                        or str(uuid.uuid4())
                    ),

                    "title": title,

                    # Derived from the title via the same taxonomy the
                    # website catalog and category-relevance filter
                    # already use — was previously hardcoded to
                    # "Coffee" for every product regardless of what it
                    # actually was (a leftover from before this parser
                    # was generalized beyond coffee machines), which
                    # fed Claude a false fact it correctly flagged as
                    # a credibility risk.
                    "category": category_taxonomy.category_for(title) or "General",

                    "price": price,

                    "original_price": 0.0,

                    "price_text": "",

                    "price_min": 0.0,

                    "price_max": 0.0,

                    # TODO(orders/rating/supplier_score): not yet extracted.
                    #
                    # These are left at 0/empty rather than guessed. The
                    # saved session in data/alimama_state.json is expired
                    # (verified 2026-08-15: navigating a real product_url
                    # with it redirects to the pub.alimama.com login gate
                    # instead of the detail page), so the actual detail
                    # page / promotion-dialog DOM for these fields has not
                    # been inspected live and selectors must not be
                    # guessed against it.
                    #
                    # "monthly_sales" and "shop_name" ARE visible on the
                    # search-results card itself (see _extract_card_metrics
                    # for price/commission_rate, extracted the same way),
                    # while monthly_sales/monthly_promoters/today_sales and
                    # the price/commission category percentiles come from
                    # the detail page's "推广热度" section (see
                    # _extract_detail_metrics).
                    #
                    # NOT AVAILABLE anywhere on pub.alimama.com (verified
                    # live 2026-08-15, both card and detail page): product
                    # rating and review count. This is an affiliate/
                    # promotion portal, not the consumer Taobao product
                    # page — it exposes commission/sales/DSR data to
                    # affiliates, not customer review text. A shop DSR
                    # quality section (综合体验/宝贝描述/卖家服务/物流服务)
                    # exists in the DOM but was empty/unpopulated for every
                    # sampled product, so it isn't read here — left as a
                    # future addition once a sample with real DSR values is
                    # found. Left NULL rather than fabricated.
                    "orders": detail_metrics["monthly_sales"],

                    "monthly_sales": detail_metrics["monthly_sales"],

                    "monthly_promoters": detail_metrics["monthly_promoters"],

                    "today_sales": detail_metrics["today_sales"],

                    "price_percentile": detail_metrics["price_percentile"],

                    "commission_percentile": detail_metrics["commission_percentile"],

                    "rating": None,

                    "review_count": None,

                    "supplier": shop_name,

                    "shop_name": shop_name,

                    "shop_rating": None,

                    "supplier_score": None,

                    "badges": badges,

                    "moq": "",

                    "commission_rate": commission_rate,

                    "commission_amount": round(price * commission_rate / 100, 2) if price and commission_rate else None,

                    "product_url": product_url,

                    "affiliate_url": affiliate_url,

                    "image_url": image_url,

                    "keyword": "",

                    "status": "DISCOVERED",
                }

                results.append(product)

            except Exception as e:

                print(
                    f"❌ Product {index} failed: {e}"
                )

            finally:

                if detail_page is not None:

                    try:
                        detail_page.close()
                    except Exception:
                        pass

        # =====================================================
        # FINAL RESULTS
        # =====================================================

        print(
            "\\n========================================"
        )

        print(
            f"✅ MULTI-PRODUCT RESULTS: "
            f"{len(results)}"
        )

        print(
            "========================================"
        )

        for index, product in enumerate(
            results,
            start=1,
        ):

            print(
                f"\\nProduct {index}: "
                f"{product['title']}"
            )

            print(
                f"Affiliate: "
                f"{product['affiliate_url']}"
            )

        return results


    def _extract_title(self, card):

        # First try image alt.
        try:

            images = card.locator("img")

            for i in range(images.count()):

                alt = (
                    images.nth(i)
                    .get_attribute("alt")
                    or ""
                ).strip()

                if (
                    alt
                    and alt not in {
                        "主图",
                        "图片",
                        "商品图片",
                    }
                    and len(alt) > 5
                ):
                    return alt

        except Exception:
            pass

        # Then inspect text lines.
        try:

            text = card.inner_text()

            excluded = (
                "佣金率",
                "佣金",
                "价格",
                "到手价",
                "主图",
                "图片",
                "店铺名称",
                "月推广销量",
                "官方旗舰店",
                "包邮",
                "立即推广",
                "一键复制",
            )

            for line in text.splitlines():

                line = line.strip()

                if len(line) < 10:
                    continue

                if any(
                    word in line
                    for word in excluded
                ):
                    continue

                return line

        except Exception:
            pass

        return ""

    # =========================================================
    # PRICE + COMMISSION RATE
    #
    # Read from the card's always-visible main body text (price
    # and commission rate are shown directly on the card, not
    # inside the hover-only tooltip section), so this does not
    # require simulating a hover interaction.
    # =========================================================

    PRICE_PATTERN = re.compile(
        r"(?:到手价|88VIP价)\D{0,10}([\d,]+\.\d{1,2})"
    )

    COMMISSION_PATTERN = re.compile(
        r"佣金率\D{0,10}(\d+(?:\.\d+)?)%"
    )

    def _extract_card_metrics(self, card):

        price = 0.0
        commission_rate = 0.0
        badges = ""

        try:
            text = card.inner_text()
        except Exception:
            return price, commission_rate, badges

        price_match = self.PRICE_PATTERN.search(text)

        if price_match:
            try:
                price = float(
                    price_match.group(1).replace(",", "")
                )
            except ValueError:
                pass

        commission_match = self.COMMISSION_PATTERN.search(text)

        if commission_match:
            try:
                commission_rate = float(
                    commission_match.group(1)
                )
            except ValueError:
                pass

        badges = ",".join(extract_badges(text))

        return price, commission_rate, badges

    # =========================================================
    # SHOP NAME
    #
    # Only present in the card's hover-only tooltip section. This
    # runs during the read-only snapshot phase (before any product
    # page is opened), so it does not interact with cards after a
    # navigation change — hovering doesn't navigate anything.
    # =========================================================

    SHOP_NAME_PATTERN = re.compile(r"店铺名称[：:]\s*([^\n]+)")

    def _extract_shop_name(self, card):

        try:
            card.hover(timeout=5000)
            card.page.wait_for_timeout(600)
            text = card.inner_text()
        except Exception:
            return ""

        match = self.SHOP_NAME_PATTERN.search(text)

        return match.group(1).strip() if match else ""

    # =========================================================
    # DETAIL PAGE METRICS
    #
    # The "推广热度" (promotion heat) section on the detail page
    # exposes real monthly/daily sales for this specific listing,
    # plus how it compares on price/commission to its own category
    # ("价格低于X%同类" / "佣金率高于X%同类") — all directly
    # displayed by the marketplace, not derived/estimated here.
    # =========================================================

    def _extract_detail_metrics(self, detail_page):

        metrics = {
            "monthly_sales": None,
            "monthly_promoters": None,
            "today_sales": None,
            "price_percentile": None,
            "commission_percentile": None,
        }

        # This section renders asynchronously and can take several
        # seconds longer than the rest of the page — wait for it
        # explicitly rather than guessing a fixed delay. If it never
        # appears, the metrics genuinely aren't available for this
        # listing; that's a real "unavailable" state, not a bug.
        try:
            detail_page.wait_for_selector(
                "text=价格低于", timeout=10000
            )
        except Exception:
            pass

        try:
            text = detail_page.locator("body").inner_text()
        except Exception:
            return metrics

        price_pct = re.search(r"价格低于([\d.]+)%", text)
        if price_pct:
            metrics["price_percentile"] = float(price_pct.group(1))

        commission_pct = re.search(r"佣金率高于([\d.]+)%", text)
        if commission_pct:
            metrics["commission_percentile"] = float(commission_pct.group(1))

        heat_start = text.find("推广热度")
        history_start = text.find("历史表现")

        if heat_start != -1:
            section = text[heat_start:history_start if history_start != -1 else heat_start + 500]

            today_match = re.search(
                r"今日\s*推广淘客数\s*(\d+)\s*推广销量\s*(\d+)", section
            )
            if today_match:
                metrics["today_sales"] = int(today_match.group(2))

            month_match = re.search(
                r"月\s*推广淘客数\s*(\d+)\s*推广销量\s*(\d+)", section
            )
            if month_match:
                metrics["monthly_promoters"] = int(month_match.group(1))
                metrics["monthly_sales"] = int(month_match.group(2))

        return metrics

    # =========================================================
    # PRODUCT URL
    # =========================================================

    def _extract_product_url(self, card):

        try:

            links = card.locator("a")

            for i in range(links.count()):

                href = (
                    links.nth(i)
                    .get_attribute("href")
                )

                if not href:
                    continue

                if href.startswith("//"):
                    href = "https:" + href

                elif href.startswith("/"):
                    href = (
                        "https://pub.alimama.com"
                        + href
                    )

                return href

        except Exception:
            pass

        return ""

    # =========================================================
    # IMAGE URL
    # =========================================================

    def _extract_image_url(self, card):

        try:

            images = card.locator("img")

            for i in range(images.count()):

                image = images.nth(i)

                src = (
                    image.get_attribute("src")
                    or image.get_attribute("data-src")
                    or image.get_attribute("data-lazy-src")
                    or ""
                )

                if not src:
                    continue

                if src.startswith("//"):
                    src = "https:" + src

                return src

        except Exception:
            pass

        return ""

    # =========================================================
    # AFFILIATE URL
    # =========================================================

    def _extract_affiliate_url(self, page):

        print(
            "\n--- EXTRACTING TAOBAO AFFILIATE URL ---"
        )

        # -----------------------------------------------------
        # 一键复制
        # -----------------------------------------------------

        try:

            copy_buttons = page.get_by_text(
                "一键复制",
                exact=True,
            )

            count = copy_buttons.count()

            print(
                f"Found {count} 一键复制 button(s)"
            )

            if count > 0:

                try:

                    page.context.grant_permissions(
                        [
                            "clipboard-read",
                            "clipboard-write",
                        ],
                        origin="https://pub.alimama.com",
                    )

                except Exception:
                    pass

                copy_buttons.last.click()

                print(
                    "\nClicked 一键复制."
                )

                page.wait_for_timeout(1000)

                clipboard = page.evaluate(
                    """
                    async () => {
                        try {
                            return await navigator.clipboard.readText();
                        } catch (e) {
                            return "";
                        }
                    }
                    """
                )

                if clipboard:

                    print(
                        "\n--- CLIPBOARD CONTENT ---"
                    )

                    print(clipboard)

                    url = self._find_url(
                        clipboard
                    )

                    if url:

                        print(
                            "\n✅ Affiliate URL "
                            "found from clipboard."
                        )

                        return url

        except Exception as e:

            print(
                f"\n⚠️ Clipboard extraction failed: {e}"
            )

        # -----------------------------------------------------
        # Visible text fallback
        # -----------------------------------------------------

        for frame in page.frames:

            try:

                text = frame.locator(
                    "body"
                ).inner_text()

                url = self._find_url(text)

                if url:
                    return url

            except Exception:
                continue

        # -----------------------------------------------------
        # HTML fallback
        # -----------------------------------------------------

        try:

            html = page.content()

            url = self._find_url(html)

            if url:
                return url

        except Exception:
            pass

        return ""

    # =========================================================
    # FIND URL
    # =========================================================

    def _find_url(self, text):

        if not text:
            return ""

        text = str(text).strip()

        # -----------------------------------------------------
        # CASE 1: Markdown affiliate link
        #
        # [https://m.tb.cn/h.xxxxx](https://m.tb.cn/h.xxxxx)
        # -----------------------------------------------------

        markdown_match = re.search(
            r"\]\((https://(?:m\.tb\.cn|s\.click\.taobao\.com)/[^)\s]+)\)",
            text,
        )

        if markdown_match:
            return markdown_match.group(1).strip()

        # -----------------------------------------------------
        # CASE 2: Plain Taobao affiliate URL
        # -----------------------------------------------------

        plain_match = re.search(
            r"https://(?:m\.tb\.cn|s\.click\.taobao\.com)/[^\s\)\]\"<>]+",
            text,
        )

        if plain_match:
            return plain_match.group(0).rstrip(
                ')]}>,\'"'
            )

        return ""
