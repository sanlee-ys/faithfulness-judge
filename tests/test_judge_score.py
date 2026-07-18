"""Judge prompt/parse and the scoring math, all offline."""

import math

from judge import build_prompt, parse_verdict
from score import cohens_kappa, collapse, per_class, wilson_ci


def test_judge_prompt_contains_passage_and_claim_only():
    p = build_prompt("Some  passage\ntext.", "A claim.")
    assert "Some passage text." in p  # whitespace collapsed
    assert "A claim." in p
    # blind: nothing about types, variants, or human labels
    for leak in ("variant", "false_premise", "gold", "human"):
        assert leak not in p.lower()


def test_parse_verdict_tolerates_noise():
    assert parse_verdict("supported") == "supported"
    assert parse_verdict("  Unsupported.") == "unsupported"
    assert parse_verdict("Answer: partial") == "partial"
    assert parse_verdict("hard to say") is None
    # two different verdict words -> ambiguous -> None
    assert parse_verdict("supported or unsupported") is None


def test_collapse():
    assert collapse("partial") == "unsupported"
    assert collapse("supported") == "supported"
    assert collapse("unsupported") == "unsupported"


def test_kappa_perfect_and_chance():
    labels = ("supported", "unsupported")
    perfect = [("supported", "supported")] * 5 + [("unsupported", "unsupported")] * 5
    assert cohens_kappa(perfect, labels) == 1.0
    # independent judge: agreement no better than chance -> kappa ~ 0
    chance = [
        ("supported", "supported"), ("supported", "unsupported"),
        ("unsupported", "supported"), ("unsupported", "unsupported"),
    ]
    assert abs(cohens_kappa(chance, labels)) < 1e-9


def test_kappa_known_value():
    # Classic worked example: po=0.7, pe=0.5 -> kappa = 0.4
    labels = ("a", "b")
    pairs = (
        [("a", "a")] * 35 + [("a", "b")] * 15 + [("b", "a")] * 15 + [("b", "b")] * 35
    )
    assert math.isclose(cohens_kappa(pairs, labels), 0.4, abs_tol=1e-9)


def test_per_class_recall_precision():
    pairs = [
        ("unsupported", "unsupported"),
        ("unsupported", "supported"),   # miss
        ("supported", "supported"),
        ("supported", "unsupported"),   # false alarm
    ]
    pc = per_class(pairs, ("supported", "unsupported"))
    assert pc["unsupported"]["recall"] == 0.5
    assert pc["unsupported"]["precision"] == 0.5
    assert pc["unsupported"]["gold_n"] == 2


def test_wilson_ci_sane():
    lo, hi = wilson_ci(90, 100)
    assert 0.80 < lo < 0.90 < hi < 0.95
    assert wilson_ci(0, 0) == (0.0, 0.0)
