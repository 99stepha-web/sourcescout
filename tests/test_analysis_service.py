import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis_service import _apply_score_decision_guardrail


def test_promote_with_high_score_stays_promote():
    assert _apply_score_decision_guardrail(85, "PROMOTE") == "PROMOTE"


def test_promote_with_mid_score_is_downgraded_to_review():
    assert _apply_score_decision_guardrail(55, "PROMOTE") == "REVIEW"


def test_promote_with_low_score_is_downgraded_to_skip():
    assert _apply_score_decision_guardrail(30, "PROMOTE") == "SKIP"


def test_skip_and_review_are_never_upgraded():
    assert _apply_score_decision_guardrail(95, "SKIP") == "SKIP"
    assert _apply_score_decision_guardrail(95, "REVIEW") == "REVIEW"


def test_missing_score_does_not_change_decision():
    assert _apply_score_decision_guardrail(None, "PROMOTE") == "PROMOTE"
