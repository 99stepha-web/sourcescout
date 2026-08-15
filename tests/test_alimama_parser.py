"""
Tests for the text-parsing logic in affiliate/alimama/parser.py.

Uses real captured page text (no live Playwright/network access) so
this stays fast and doesn't depend on an authenticated session.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from affiliate.alimama.parser import AlimamaParser

# Captured verbatim from a live pub.alimama.com detail page
# (2026-08-15, keyword "办公桌配件"), trimmed to the relevant section.
REAL_DETAIL_PAGE_SAMPLE = """320款组合办公桌配件大全工位配件屏风隔断卡座组装固定连接件扣
日推广量：0
热门商品
超千人种草
价格
到手价￥2.90
价格低于69.25%桌子配件
优惠
淘金币频道抵扣0.17元
包邮
查看优惠明细 >
佣金补贴
佣金率
5.40%
佣金
￥0.16
佣金率高于73.04%桌子配件
颜色分类
展开更多
商品二维码
加入收藏
创建淘礼金
立即推广
推广热度
近2小时
推广淘客数
0
推广销量
0
今日
推广淘客数
0
推广销量
0
月
推广淘客数
11
推广销量
57
历史表现
至
价格
"""

REAL_CARD_SAMPLE = """320款组合办公桌配件大全工位配件屏风隔断卡座组装固定连接件扣
淘金币频道抵扣0.17元
包邮
到手价￥2.90
佣金率
5.40%
佣金
￥0.16
超千人种草
同类热推
日推广销量：0
"""


class _FakeLocator:
    def __init__(self, text):
        self._text = text

    def inner_text(self):
        return self._text


class _FakePage:
    def __init__(self, text):
        self._text = text

    def locator(self, _selector):
        return _FakeLocator(self._text)


def test_extract_detail_metrics_from_real_sample():
    parser = AlimamaParser()

    metrics = parser._extract_detail_metrics(_FakePage(REAL_DETAIL_PAGE_SAMPLE))

    assert metrics["monthly_sales"] == 57
    assert metrics["monthly_promoters"] == 11
    assert metrics["today_sales"] == 0
    assert metrics["price_percentile"] == 69.25
    assert metrics["commission_percentile"] == 73.04


def test_extract_detail_metrics_missing_section_returns_none():
    parser = AlimamaParser()

    metrics = parser._extract_detail_metrics(_FakePage("no relevant text here"))

    assert metrics["monthly_sales"] is None
    assert metrics["price_percentile"] is None


def test_extract_card_metrics_price_commission_and_badges():
    parser = AlimamaParser()

    price, commission_rate, badges = parser._extract_card_metrics(
        _FakeLocator(REAL_CARD_SAMPLE)
    )

    assert price == 2.90
    assert commission_rate == 5.40
    assert "种草" in badges
