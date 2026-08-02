"""Offline tests for the blind gold audit (ADR-002 Option D). No API, no network.

The load-bearing tests here are the *blindness* ones. The audit's whole claim to
credibility is that the candidate set was chosen without reference to which
claims the judges got wrong, so that property is asserted mechanically rather
than promised in prose:

- ``select`` cannot read a judgments file — the test makes any attempt raise.
- selection is invariant to the gold labels, so it cannot be steered by them.
- every line of the worksheet's claim section is traceable to the source corpus
  or to a fixed structural template — nothing else can be smuggled in.
- the selected set demonstrably contains claims both judges scored correctly,
  which is only possible because selection ignored the verdicts.

The re-score path is exercised against hand-built fixtures, never against
invented labels on the real gold; the one test that touches the committed
artifacts pins the new scorer to ``score.score_judge`` rather than to a
published constant.
"""

import argparse
import builtins
import re
from pathlib import Path

import pytest
import yaml

import dataset
import gold_audit
from gold_audit import (
    SELECTION_RULES,
    audit_views,
    build_rescore_report,
    build_worksheet,
    judge_correct,
    parse_worksheet,
    rules_firing,
    select_claims,
    stats_for,
)
from score import score_judge

# ---------------------------------------------------------------------------
# Fixtures.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def real_claims():
    return dataset.load_yaml(dataset.CLAIMS_PATH)["claims"]


@pytest.fixture(scope="module")
def real_questions():
    return dataset.load_questions()


@pytest.fixture(scope="module")
def worksheet(real_claims, real_questions):
    return build_worksheet(select_claims(real_claims), real_questions)


def _claim(cid, text, label, qid="q-01", ctx="ctx-01"):
    return {
        "claim_id": cid,
        "question_id": qid,
        "context_id": ctx,
        "type": "grounded",
        "variant": "assertive",
        "claim_text": text,
        "label": label,
    }


@pytest.fixture
def toy_claims():
    """Six claims with a hand-designed judge-error pattern (see toy_judgments)."""
    return [
        _claim("c1", "The contract ceiling is $500 million.", "supported"),
        _claim("c2", "It only reports:", "supported"),
        _claim("c3", "The base is in Fort Rucker, Alabama.", "unsupported"),
        _claim("c4", "The demonstration involved 23 flights.", "supported"),
        _claim("c5", "19 ships", "supported"),
        _claim("c6", "I'd be happy to help with that.", "na"),
    ]


@pytest.fixture
def toy_judgments():
    """Judge A right on c1/c3/c4/c5; judge B right on c1/c3/c5. Both wrong on c2."""

    def payload(alias, verdicts):
        return {
            "meta": {"judge_alias": alias, "judge_model": f"model-{alias}"},
            "judgments": [
                {"claim_id": cid, "judge_label": v} for cid, v in verdicts.items()
            ],
        }

    a = payload(
        "alpha",
        {
            "c1": "supported",
            "c2": "unsupported",
            "c3": "unsupported",
            "c4": "supported",
            "c5": "supported",
            "c6": "supported",
        },
    )
    b = payload(
        "beta",
        {
            "c1": "supported",
            "c2": "unsupported",
            "c3": "unsupported",
            "c4": "unsupported",
            "c5": "supported",
            "c6": "supported",
        },
    )
    return [a, b]


# ---------------------------------------------------------------------------
# The pre-registered predicate.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,rule",
    [
        ("19 ships", "S1-short-fragment"),
        ("The Army", "S1-short-fragment"),
        ("However, it does not mention:", "S2-list-header"),
        (
            "Based on the passage, this launch is significant for two main reasons:",
            "S2-list-header",
        ),
        ("If you have additional context, I'd be happy to dig in.", "S3-offer-to-help"),
        ("Let me know if that helps and I can expand on any part of it.", "S3-offer-to-help"),
        (
            "To find out which nations participated, you would need to consult "
            "additional NATO reporting on the exercise.",
            "S4-external-referral",
        ),
        (
            "The specific figure may appear in the original source, which is not "
            "reproduced in the excerpt given here.",
            "S4-external-referral",
        ),
    ],
)
def test_each_rule_matches_the_shape_it_was_registered_for(text, rule):
    assert rule in rules_firing(text)


def test_an_ordinary_grounded_claim_is_not_selected():
    text = (
        "The demonstration involved 23 flights totaling 29.9 flight hours, "
        "conducted on an AH-64E Version 6 Apache Attack Helicopter."
    )
    assert rules_firing(text) == []


def test_rule_names_are_unique():
    names = [rule.name for rule in SELECTION_RULES]
    assert len(names) == len(set(names))


# ---------------------------------------------------------------------------
# Blindness.
# ---------------------------------------------------------------------------


def test_selection_is_invariant_to_the_gold_labels(real_claims):
    """A predicate that cannot see the label cannot be steered by it.

    Every label is rewritten to a single value; if selection changed, something
    in the path was reading the gold rather than the claim text.
    """
    baseline = [c["claim_id"] for c in select_claims(real_claims)]
    perturbed = [{**c, "label": "unsupported"} for c in real_claims]
    assert [c["claim_id"] for c in select_claims(perturbed)] == baseline
    blanked = [{**c, "label": None} for c in real_claims]
    assert [c["claim_id"] for c in select_claims(blanked)] == baseline


def test_selection_covers_the_whole_gold_set_including_na(real_claims):
    """The predicate is applied to all 193, not to the 189 scored claims.

    Auditing only the scored set would let labels move into `na` but never out
    of it, which can only shrink n — a directional bias (see select_claims).
    """
    assert len(real_claims) == 193
    selected_ids = {c["claim_id"] for c in select_claims(real_claims)}
    na_ids = {c["claim_id"] for c in real_claims if c["label"] == "na"}
    assert na_ids and na_ids <= selected_ids


def test_select_cannot_read_a_judgments_file(tmp_path, monkeypatch, real_claims):
    """The strongest form of the guarantee: make reading one impossible.

    Both the YAML loader and the raw file opener raise on any path naming a
    judgments artifact. `select` must still complete — which it can only do if
    it never looked.
    """
    real_load = dataset.load_yaml
    real_open = builtins.open

    def guarded_load(path):
        if "judgments" in str(path):
            raise AssertionError(f"select read a judgments file: {path}")
        return real_load(path)

    def guarded_open(file, *args, **kwargs):
        if "judgments" in str(file):
            raise AssertionError(f"select opened a judgments file: {file}")
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(dataset, "load_yaml", guarded_load)
    monkeypatch.setattr(builtins, "open", guarded_open)

    out = tmp_path / "worksheet.md"
    args = argparse.Namespace(claims=dataset.CLAIMS_PATH, out=out)
    assert gold_audit.cmd_select(args) == 0
    assert out.exists()
    assert len(select_claims(real_claims)) == out.read_text(encoding="utf-8").count(
        "AUDIT "
    )


# Line shapes the worksheet's claim section is allowed to contain. Anything
# that is not one of these must be verbatim source material (a claim, a
# question, or a line of a context excerpt) — see the test below.
_STRUCTURAL = (
    re.compile(r"^$"),
    re.compile(r"^### Context `[\w-]+`$"),
    re.compile(r"^#### `[\w-]+`$"),
    re.compile(r"^- selected by: [\w, -]+$"),
    re.compile(r"^- current label: \*\*(supported|partial|unsupported|na)\*\*$"),
    re.compile(r"^```$"),
    re.compile(r"^AUDIT [\w-]+ = \?$"),
)


def test_no_line_of_the_claim_section_carries_anything_but_source_data(
    worksheet, real_claims, real_questions
):
    """The blindness property, asserted line by line.

    Every line in the worksheet's claim section is either a fixed structural
    token (heading, rule list, fill-in line) or text lifted verbatim from
    claims.yaml / questions.yaml. There is no third category, so there is
    nowhere for a verdict, an agreement flag, or a "this one was contested"
    hint to live.
    """
    corpus = " ".join(
        [" ".join(c["claim_text"].split()) for c in real_claims]
        + [" ".join(q.question.split()) for q in real_questions]
        + [" ".join(q.context_text.split()) for q in real_questions]
    )
    rule_names = {rule.name for rule in SELECTION_RULES}

    _, _, claim_section = worksheet.partition("## The 30 claims")
    assert claim_section, "claim section marker not found"

    for line in claim_section.splitlines():
        if any(pattern.match(line) for pattern in _STRUCTURAL):
            if line.startswith("- selected by: "):
                named = {n.strip() for n in line[len("- selected by: "):].split(",")}
                assert named <= rule_names, f"unknown rule name in: {line}"
            continue
        if line.startswith("**Q ("):
            line = line.split("**", 2)[2].strip()
        elif line.startswith("> "):
            line = line[2:]
        assert " ".join(line.split()) in corpus, f"untraceable worksheet line: {line!r}"


def test_the_generator_introduces_no_verdict_vocabulary(worksheet, real_claims, real_questions):
    """No model name or verdict word may enter except as quoted source text.

    Stated as a subset rather than an absence because the DVIDS excerpts
    genuinely contain words like "agreement": the property that matters is
    that every such occurrence is traceable to the corpus, so the *generator*
    contributed none of them.
    """
    corpus = " ".join(
        [c["claim_text"] for c in real_claims]
        + [q.question for q in real_questions]
        + [q.context_text for q in real_questions]
    ).lower()
    lowered = worksheet.partition("## The 30 claims")[2].lower()
    for token in ("opus", "sonnet", "claude", "verdict", "judge", "agree", "contested"):
        if token in lowered:
            assert token in corpus, f"{token!r} was added by the generator"


def test_worksheet_states_the_blindness_contract(worksheet):
    """The disclosure has to be in the instrument, not only in the ADR."""
    header = " ".join(worksheet.partition("## The 30 claims")[0].lower().split())
    assert "tells you nothing about how any model labeled these claims" in header
    assert "correctness pass, not a tuning pass" in header
    assert "structural" in header


def test_the_selected_set_contains_claims_both_judges_scored_correctly(real_claims):
    """The property that makes the audit blind, checked against the artifacts.

    This test — unlike the selector — is allowed to read the judgments, because
    proving the candidate set is not the misjudgment log requires looking at
    both. If selection had been driven by judge errors this would fail.
    """
    selected = {c["claim_id"] for c in select_claims(real_claims)}
    gold = {c["claim_id"]: c["label"] for c in real_claims}
    arms = [
        dataset.load_yaml(p) for p in sorted(dataset.DATA_DIR.glob("judgments_*.yaml"))
    ]
    assert len(arms) >= 2

    both_right = 0
    for cid in selected:
        if gold[cid] in (None, "na"):
            continue
        verdicts = [
            {j["claim_id"]: j["judge_label"] for j in a["judgments"]}.get(cid)
            for a in arms
        ]
        if all(judge_correct(gold[cid], v) for v in verdicts):
            both_right += 1
    assert both_right > 0, "the selected set tracks the judge errors — not blind"


# ---------------------------------------------------------------------------
# Worksheet round trip.
# ---------------------------------------------------------------------------


def test_a_generated_worksheet_is_born_unfilled(worksheet):
    with pytest.raises(ValueError, match="unfilled"):
        parse_worksheet(worksheet)


def _fill(text, answers):
    for cid, letter in answers.items():
        text = text.replace(f"AUDIT {cid} = ?", f"AUDIT {cid} = {letter}")
    return text


def test_a_filled_worksheet_round_trips(real_claims, real_questions):
    selected = select_claims(real_claims)
    sheet = build_worksheet(selected, real_questions)
    ids = [c["claim_id"] for c in selected]
    filled = _fill(sheet, {cid: "s" for cid in ids})
    parsed = parse_worksheet(filled, expected_ids=ids)
    assert parsed == {cid: "supported" for cid in ids}


def test_all_four_letters_and_their_long_forms_parse():
    sheet = "\n".join(
        [
            "AUDIT a = s",
            "AUDIT b = p",
            "AUDIT c = U",
            "AUDIT d = n",
            "AUDIT e = unsupported",
        ]
    )
    assert parse_worksheet(sheet) == {
        "a": "supported",
        "b": "partial",
        "c": "unsupported",
        "d": "na",
        "e": "unsupported",
    }


def test_an_invalid_letter_is_refused():
    with pytest.raises(ValueError, match="invalid labels"):
        parse_worksheet("AUDIT a = x")


def test_a_duplicate_entry_is_refused():
    with pytest.raises(ValueError, match="duplicate"):
        parse_worksheet("AUDIT a = s\nAUDIT a = u")


def test_a_missing_or_unexpected_id_is_refused():
    with pytest.raises(ValueError, match="missing from the worksheet"):
        parse_worksheet("AUDIT a = s", expected_ids=["a", "b"])
    with pytest.raises(ValueError, match="not in the selected set"):
        parse_worksheet("AUDIT a = s\nAUDIT z = s", expected_ids=["a"])


# ---------------------------------------------------------------------------
# Re-score — fixtures only, plus one tie-down against the committed artifacts.
# ---------------------------------------------------------------------------


def test_stats_for_matches_the_existing_scorer_on_the_committed_artifacts(real_claims):
    """Pin the new scorer to score.py rather than to a published constant.

    If these ever diverge, the audit's "corrected" numbers would not be
    comparable to the published ones, which is the quiet way a re-score lies.
    """
    gold = {c["claim_id"]: c["label"] for c in real_claims}
    for path in sorted(dataset.DATA_DIR.glob("judgments_*.yaml")):
        payload = dataset.load_yaml(path)
        verdicts = {j["claim_id"]: j["judge_label"] for j in payload["judgments"]}
        mine = stats_for(real_claims, gold, verdicts)
        _, theirs = score_judge(real_claims, path)
        assert mine["n"] == theirs["n"]
        assert mine["kappa_binary"] == pytest.approx(theirs["kappa_binary"])
        assert mine["kappa_ternary"] == pytest.approx(theirs["kappa_ternary"])
        assert mine["agree_binary"] == pytest.approx(theirs["agree_binary"])
        assert mine["unsupported_recall"] == pytest.approx(
            theirs["per_class_binary"]["unsupported"]["recall"]
        )


def test_audit_views_report_the_overlap_with_judge_errors(toy_claims, toy_judgments):
    # c2 is a both-judges-wrong claim; c5 is a neither-judge-wrong claim.
    views = audit_views(toy_claims, {"c2": "na", "c5": "unsupported"}, toy_judgments)
    assert views["changed"] == {"c2": "na", "c5": "unsupported"}
    assert views["overlap"]["both judges wrong"] == 1
    assert views["overlap"]["neither judge wrong"] == 1
    assert views["overlap"].get("exactly one judge wrong", 0) == 0


def test_confirmations_are_not_counted_as_changes(toy_claims, toy_judgments):
    """Re-affirming a label is the expected outcome and must not read as drift."""
    everything_confirmed = {c["claim_id"]: c["label"] for c in toy_claims}
    views = audit_views(toy_claims, everything_confirmed, toy_judgments)
    assert views["changed"] == {}
    assert sum(views["overlap"].values()) == 0


def test_the_three_views_separate_a_judge_tracking_correction(
    toy_claims, toy_judgments
):
    """The drift check, end to end.

    Dropping c2 (which both judges got wrong) raises agreement; the
    no-judge-error view excludes exactly that correction, so it cannot. When
    the two views disagree, the correction tracked the judges — which is
    precisely what the reader is supposed to be able to see.
    """
    views = audit_views(toy_claims, {"c2": "na", "c5": "unsupported"}, toy_judgments)
    golds = views["golds"]
    alpha = {j["claim_id"]: j["judge_label"] for j in toy_judgments[0]["judgments"]}
    beta = {j["claim_id"]: j["judge_label"] for j in toy_judgments[1]["judgments"]}

    original = golds["original gold (published baseline)"]
    audited = golds["fully audited gold"]
    restricted = golds["audited, corrections on no-judge-error claims only"]

    assert stats_for(toy_claims, original, alpha)["n"] == 5
    assert stats_for(toy_claims, original, alpha)["agree_binary"] == pytest.approx(0.8)
    assert stats_for(toy_claims, original, beta)["agree_binary"] == pytest.approx(0.6)

    # c2 leaves the scored set entirely; c5 becomes a claim both judges miss.
    assert stats_for(toy_claims, audited, alpha)["n"] == 4
    assert stats_for(toy_claims, audited, alpha)["agree_binary"] == pytest.approx(0.75)
    assert stats_for(toy_claims, audited, beta)["agree_binary"] == pytest.approx(0.5)

    # Only the c5 correction survives here, and a correction on a claim every
    # judge already got right can never raise agreement.
    assert stats_for(toy_claims, restricted, alpha)["n"] == 5
    assert stats_for(toy_claims, restricted, alpha)["agree_binary"] == pytest.approx(0.6)
    assert stats_for(toy_claims, restricted, beta)["agree_binary"] == pytest.approx(0.4)


def test_a_missing_verdict_still_counts_as_a_disagreement(toy_claims):
    """score.py's load-bearing convention must survive into the audit layer."""
    gold = {c["claim_id"]: c["label"] for c in toy_claims}
    assert judge_correct("supported", None) is False
    assert judge_correct("supported", "not-a-label") is False
    stats = stats_for(toy_claims, gold, {})
    assert stats["n"] == 5
    assert stats["agree_binary"] == pytest.approx(0.0)


def test_the_rescore_report_carries_the_guard_language(toy_claims, toy_judgments):
    report = build_rescore_report(
        toy_claims, {"c2": "na", "c5": "unsupported"}, toy_judgments
    )
    assert "OVERLAP WITH JUDGE ERRORS" in report
    assert "no-judge-error" in report
    assert "NOT inter-annotator" in report
    assert "c2" in report and "c5" in report


def test_rescore_refuses_an_unfilled_worksheet(tmp_path, monkeypatch, toy_claims):
    claims_path = tmp_path / "claims.yaml"
    claims_path.write_text(
        yaml.safe_dump({"meta": {}, "claims": toy_claims}), encoding="utf-8"
    )
    sheet = tmp_path / "worksheet.md"
    sheet.write_text(
        build_worksheet(select_claims(toy_claims), []), encoding="utf-8"
    )
    monkeypatch.setattr(dataset, "DATA_DIR", tmp_path)
    args = argparse.Namespace(
        claims=claims_path, worksheet=sheet, out=None
    )
    with pytest.raises(SystemExit, match="unfilled"):
        gold_audit.cmd_rescore(args)


def test_the_committed_worksheet_matches_the_pre_registered_rule(real_claims):
    """The shipped worksheet must be exactly what the committed rule produces.

    If the two ever diverge, the pre-registration is no longer describing the
    artifact San actually adjudicated.
    """
    path = Path(dataset.DATA_DIR) / "gold-audit-worksheet.md"
    if not path.exists():  # pragma: no cover - the file ships with the repo
        pytest.skip("worksheet not generated yet")
    shipped = path.read_text(encoding="utf-8")
    ids_in_file = re.findall(r"^AUDIT (\S+) = ", shipped, re.MULTILINE)
    assert ids_in_file == [c["claim_id"] for c in select_claims(real_claims)]
