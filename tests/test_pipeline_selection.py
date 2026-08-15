"""
Test I: an already-published product rediscovered by the same
keyword should not trigger another Claude analysis or article
generation call — idempotency/cost-control at the pipeline
orchestration level (scripts/run_pipeline.py).
"""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from run_pipeline import should_reanalyze, should_regenerate_article


def test_new_product_should_be_analyzed_and_generated():
    product = SimpleNamespace(
        ai_analyzed_at=None, article_content=None, slug=None
    )

    assert should_reanalyze(product) is True
    assert should_regenerate_article(product) is True


def test_already_published_product_skips_both():
    product = SimpleNamespace(
        ai_analyzed_at="2026-08-01", article_content="{...}", slug="some-slug"
    )

    assert should_reanalyze(product) is False
    assert should_regenerate_article(product) is False


def test_previously_review_or_skip_product_gets_reanalyzed_on_rediscovery():
    # e.g. a prior REVIEW/SKIP decision: analyzed, but no article was
    # ever generated. Conditions may have changed, so this should get
    # a fresh look rather than being permanently stuck at REVIEW/SKIP.
    product = SimpleNamespace(
        ai_analyzed_at="2026-08-01", article_content=None, slug=None
    )

    assert should_reanalyze(product) is True
    assert should_regenerate_article(product) is True
