"""Offline tests for the published-figure check (ADR-004). No API, no network.

The load-bearing tests here are the **failure** ones. A guard run only against
content it passes exercises nothing but its happy path, and this repo has been
bitten once already by a check that looked green because it was measuring the
wrong thing. So every way this script is supposed to fail gets a test:

- a marked figure that disagrees with the artifact
- a key the artifact does not publish (a typo checks nothing and passes forever)
- a figure-shaped token nobody marked or exempted
- an exempt block with no reason, and one that is never closed
- zero markers at all — a check verifying nothing reads as a pass
- an artifact that is missing, unparseable, or disagrees with itself

The parser is also tested against the *committed* artifact, because its whole
point is that the expected values are read out of `evals/results.md` rather than
hardcoded here — a test that asserted constants would reintroduce the drift.
"""

import pytest

import check_published_figures as cpf
from check_published_figures import (
    ArtifactError,
    check_documents,
    parse_artifact,
    run,
    same_value,
)

ARTIFACT = cpf.ARTIFACT_PATH.read_text(encoding="utf-8")

# A stand-in for the parsed artifact, so the document tests do not move whenever
# the real figures do.
PUBLISHED = {
    "opus_binary_kappa": "0.751",
    "opus_agreement": "89.4%",
    "gold_scored": "189",
}


def write(tmp_path, text, name="DOC.md"):
    (tmp_path / name).write_text(text, encoding="utf-8")
    return tmp_path


# --- the parser reads its expectations out of the artifact -------------------


def test_parses_the_committed_artifact():
    published = parse_artifact(ARTIFACT)
    for key in ("gold_claims", "gold_scored", "gold_binary_unsupported"):
        assert key in published
    for alias in ("opus", "sonnet"):
        for suffix in (
            "model",
            "binary_kappa",
            "agreement",
            "agreement_ci_low",
            "agreement_ci_high",
            "ternary_kappa",
            "unsupported_recall",
            "unsupported_catches",
        ):
            assert f"{alias}_{suffix}" in published


def test_scored_n_is_the_gold_set_minus_na():
    published = parse_artifact(ARTIFACT)
    assert int(published["gold_scored"]) == int(published["gold_claims"]) - int(
        published["gold_na"]
    )


def test_binary_unsupported_class_is_partial_plus_unsupported():
    """SCOPE.md Decision 1's collapse, and the denominator the README quotes."""
    published = parse_artifact(ARTIFACT)
    assert int(published["gold_binary_unsupported"]) == int(
        published["gold_partial"]
    ) + int(published["gold_unsupported"])
    assert published["opus_unsupported_gold_n"] == published["gold_binary_unsupported"]


def test_catches_come_from_the_confusion_matrix_not_from_rounded_recall():
    """'47 vs 43 of 48' must not depend on how score.py rounds the percentage."""
    published = parse_artifact(ARTIFACT)
    for alias in ("opus", "sonnet"):
        catches = int(published[f"{alias}_unsupported_catches"])
        gold_n = int(published[f"{alias}_unsupported_gold_n"])
        recall = float(published[f"{alias}_unsupported_recall"].rstrip("%")) / 100
        assert catches == pytest.approx(recall * gold_n, abs=0.5)
        assert catches <= gold_n


def test_artifact_that_disagrees_with_itself_is_rejected():
    broken = ARTIFACT.replace("n scored: **189**", "n scored: **188**", 1)
    with pytest.raises(ArtifactError, match="disagrees with itself"):
        parse_artifact(broken)


def test_artifact_with_no_judge_sections_is_rejected():
    header = ARTIFACT.split("## Judge:")[0]
    with pytest.raises(ArtifactError, match="Judge"):
        parse_artifact(header)


def test_artifact_missing_the_gold_line_is_rejected():
    broken = ARTIFACT.replace("Gold set:", "Gold sset:", 1)
    with pytest.raises(ArtifactError, match="Gold set"):
        parse_artifact(broken)


def test_artifact_with_a_mangled_confusion_block_is_rejected():
    broken = ARTIFACT.replace(
        "      partial            0           11            1\n", ""
    )
    with pytest.raises(ArtifactError):
        parse_artifact(broken)


# --- the happy path, against the real repo ----------------------------------


def test_the_repo_documents_match_the_artifact():
    """The live check. Fails the suite for the same reason it fails CI."""
    assert cpf.main() == 0


def test_a_matching_figure_passes():
    doc = "Opus scored <!-- figure:opus_binary_kappa -->**0.751** on the gold set."
    problems, checked, exempt = check_documents({"DOC.md": doc}, PUBLISHED)
    assert problems == []
    assert (checked, exempt) == (1, 0)


def test_a_figure_ending_a_sentence_does_not_swallow_the_full_stop():
    doc = "Opus scored <!-- figure:opus_binary_kappa -->0.751."
    problems, checked, _ = check_documents({"DOC.md": doc}, PUBLISHED)
    assert problems == []
    assert checked == 1


def test_a_percent_sign_is_optional_in_prose():
    """A CI bound written as '84.2-93.0' still matches the artifact's '84.2%'."""
    assert same_value("89.4", "89.4%")
    assert same_value("89.4%", "89.4%")
    assert not same_value("89.5", "89.4%")


def test_a_model_id_compares_as_a_string():
    assert same_value("claude-opus-4-8", "claude-opus-4-8")
    assert not same_value("claude-opus-4-7", "claude-opus-4-8")


# --- failure paths -----------------------------------------------------------


def test_a_stale_figure_fails():
    doc = "Opus scored <!-- figure:opus_binary_kappa -->0.742 on the gold set."
    problems, checked, _ = check_documents({"DOC.md": doc}, PUBLISHED)
    assert checked == 1
    assert len(problems) == 1
    assert "0.742" in problems[0] and "0.751" in problems[0]


def test_an_unknown_key_fails():
    """A typo must not check nothing and pass forever."""
    doc = "Opus scored <!-- figure:opus_binry_kappa -->0.751 on the gold set."
    problems, checked, _ = check_documents({"DOC.md": doc}, PUBLISHED)
    assert checked == 0
    assert len(problems) == 1
    assert "not published by" in problems[0]


def test_an_unmarked_figure_fails():
    doc = "Opus scored 0.751 and agreed 89.4% of the time."
    problems, _, _ = check_documents({"DOC.md": doc}, PUBLISHED)
    assert len(problems) == 2
    assert all("neither marked" in p for p in problems)
    assert any("'0.751'" in p for p in problems)
    assert any("'89.4%'" in p for p in problems)


def test_an_unmarked_figure_reports_its_line():
    doc = "intro\n\nOpus scored 0.751.\n"
    problems, _, _ = check_documents({"DOC.md": doc}, PUBLISHED)
    assert problems[0].startswith("DOC.md:3:")


def test_a_marker_only_covers_the_token_it_precedes():
    """One marker does not license a second, unrelated figure beside it."""
    doc = "<!-- figure:opus_agreement -->89.4% and also 93.0%."
    problems, checked, _ = check_documents({"DOC.md": doc}, PUBLISHED)
    assert checked == 1
    assert len(problems) == 1
    assert "'93.0%'" in problems[0]


def test_an_exempt_block_covers_its_contents():
    doc = (
        "<!-- figure-exempt: a record of the 2026-07-19 re-scoring -->"
        "kappa moved 0.742 to 0.751<!-- /figure-exempt -->"
    )
    problems, checked, exempt = check_documents({"DOC.md": doc}, PUBLISHED)
    assert problems == []
    assert (checked, exempt) == (0, 1)


def test_an_exempt_block_without_a_reason_fails():
    doc = "<!-- figure-exempt: -->kappa moved to 0.742<!-- /figure-exempt -->"
    problems, _, _ = check_documents({"DOC.md": doc}, PUBLISHED)
    assert len(problems) == 1
    assert "no reason" in problems[0]


def test_an_unclosed_exempt_block_fails():
    doc = "<!-- figure-exempt: history -->kappa moved to 0.742"
    problems, _, _ = check_documents({"DOC.md": doc}, PUBLISHED)
    assert any("closer" in p for p in problems)


def test_a_marker_inside_an_exempt_block_is_still_checked():
    """The two mechanisms answer different questions; exempting is not silencing."""
    doc = (
        "<!-- figure-exempt: history -->"
        "<!-- figure:opus_binary_kappa -->0.742"
        "<!-- /figure-exempt -->"
    )
    problems, checked, exempt = check_documents({"DOC.md": doc}, PUBLISHED)
    assert (checked, exempt) == (1, 1)
    assert len(problems) == 1
    assert "0.751" in problems[0]


def test_markers_inside_code_are_documentation_not_markers():
    """CLAUDE.md documents this convention; documenting it must not invoke it."""
    doc = (
        "Opt in with `<!-- figure:opus_binary_kappa -->0.751`, opt out with\n"
        "`<!-- figure-exempt: reason --> ... <!-- /figure-exempt -->`.\n"
        "```\nkappa 0.999\n```\n"
    )
    problems, checked, exempt = check_documents({"DOC.md": doc}, PUBLISHED)
    assert problems == []
    assert (checked, exempt) == (0, 0)


# --- exit codes --------------------------------------------------------------


def test_zero_markers_fails(tmp_path):
    """A check that verifies nothing reads exactly like a check that passed."""
    root = write(tmp_path, "No figures are restated here at all.\n")
    assert run(cpf.ARTIFACT_PATH, root, ("DOC.md",)) == 1


def test_a_clean_document_exits_zero(tmp_path):
    published = parse_artifact(ARTIFACT)
    kappa = published["opus_binary_kappa"]
    root = write(tmp_path, f"Opus scored <!-- figure:opus_binary_kappa -->{kappa}.\n")
    assert run(cpf.ARTIFACT_PATH, root, ("DOC.md",)) == 0


def test_a_stale_document_exits_one(tmp_path):
    root = write(tmp_path, "Opus scored <!-- figure:opus_binary_kappa -->0.001.\n")
    assert run(cpf.ARTIFACT_PATH, root, ("DOC.md",)) == 1


def test_a_missing_document_exits_one(tmp_path):
    assert run(cpf.ARTIFACT_PATH, tmp_path, ("ABSENT.md",)) == 1


def test_a_missing_artifact_exits_one(tmp_path):
    """Unlike the sibling checks this is a local committed file, so absence is
    a repo defect, not a network outage — it fails rather than skipping."""
    root = write(tmp_path, "Opus scored <!-- figure:opus_binary_kappa -->0.751.\n")
    assert run(tmp_path / "nope.md", root, ("DOC.md",)) == 1


def test_an_unparseable_artifact_exits_one(tmp_path):
    artifact = tmp_path / "results.md"
    artifact.write_text("# Results\n\nnothing parseable here\n", encoding="utf-8")
    root = write(tmp_path, "Opus scored <!-- figure:opus_binary_kappa -->0.751.\n")
    assert run(artifact, root, ("DOC.md",)) == 1
