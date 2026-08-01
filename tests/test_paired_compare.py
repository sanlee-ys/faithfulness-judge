"""Offline tests for the paired comparison layer (no API key, no network).

Core properties (ported with the vendored core from defense-news-classifier
``tests/test_paired_compare.py`` @ 39edea4): canonicalization fails loud rather
than producing a lossy key, the group key is stable under irrelevant
differences and content-derived when no id exists, and the pairing rules
exclude exactly what they claim to while reporting each exclusion as a
diagnostic. On top of that, this repo's adapter is pinned: gold ``na`` is
unscorable, a judge with no verdict is unscored (abstained, not wrong), and
the committed Opus/Sonnet comparison is reproduced from the artifacts with no
published constant hardcoded.
"""

import math
from collections import Counter

import pytest

import dataset
import paired_compare
from paired_compare import (
    CanonicalizationError,
    Diagnostic,
    DiagnosticReason,
    Observation,
    Outcome,
    canonical_json,
    canonicalize,
    derive_group_key,
    diagnostic_counts,
    mcnemar_exact,
    observations_from_judgments,
    pair_observations,
    summarize_correctness,
    summarize_metric,
)
from score import collapse

# ---------------------------------------------------------------------------
# Canonicalization: fail loud, not lossy.
# ---------------------------------------------------------------------------


def test_dict_ordering_does_not_change_the_serialization():
    left = {"text": "a strike package", "id": "g001", "meta": {"b": 1, "a": 2}}
    right = {"meta": {"a": 2, "b": 1}, "id": "g001", "text": "a strike package"}
    assert canonical_json(left) == canonical_json(right)


def test_nested_structures_round_trip_with_sorted_keys():
    canonical = canonicalize({"b": [{"z": 1, "y": 2}], "a": None})
    assert list(canonical) == ["a", "b"]
    assert list(canonical["b"][0]) == ["y", "z"]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_numbers_are_rejected(value):
    with pytest.raises(CanonicalizationError, match="finite"):
        canonicalize({"score": value})


def test_circular_references_are_rejected():
    node = {"id": "a"}
    node["self"] = node
    with pytest.raises(CanonicalizationError, match="circular"):
        canonicalize(node)

    row = []
    row.append(row)
    with pytest.raises(CanonicalizationError, match="circular"):
        canonicalize(row)


def test_repeated_but_acyclic_references_are_fine():
    # The same object twice is not a cycle; a naive "seen" set would reject it.
    shared = {"a": 1}
    assert canonical_json({"x": shared, "y": shared}) == '{"x":{"a":1},"y":{"a":1}}'


@pytest.mark.parametrize(
    "value",
    [
        ("a", "b"),
        {"a", "b"},
        object(),
        {"nested": ("a",)},
    ],
)
def test_non_plain_containers_are_rejected(value):
    with pytest.raises(CanonicalizationError):
        canonicalize(value)


def test_non_string_mapping_keys_are_rejected():
    with pytest.raises(CanonicalizationError, match="keys must be strings"):
        canonicalize({1: "one"})


# ---------------------------------------------------------------------------
# Group keys.
# ---------------------------------------------------------------------------


def test_explicit_id_wins_and_is_trimmed():
    assert derive_group_key({"id": "  g001 ", "text": "x"}) == "g001"


def test_claim_id_field_is_the_key_for_this_repo():
    claim = {"claim_id": "asrt-q-01-c1", "label": "supported", "claim_text": "x"}
    assert derive_group_key(claim, id_field="claim_id") == "asrt-q-01-c1"


def test_missing_id_falls_back_to_a_content_hash():
    left = {"text": "a strike package", "source": "dvids"}
    right = {"source": "dvids", "text": "a strike package"}
    key = derive_group_key(left)
    assert len(key) == 64 and key == derive_group_key(right)
    assert key != derive_group_key({"text": "something else", "source": "dvids"})


def test_blank_id_falls_back_to_the_content_hash():
    # A blank id is not an identity -- two blank-id rows must not collide into
    # one group just because the field was empty.
    left = derive_group_key({"id": "   ", "text": "alpha"})
    right = derive_group_key({"id": "", "text": "bravo"})
    assert len(left) == 64 and len(right) == 64
    assert left != right


def test_unhashable_record_without_an_id_fails_loud():
    with pytest.raises(CanonicalizationError):
        derive_group_key({"text": "alpha", "score": math.nan})


# ---------------------------------------------------------------------------
# Pairing rules.
# ---------------------------------------------------------------------------


def scored(group_key, arm, score):
    return Observation(group_key, arm, Outcome.SCORED, score=score)


def test_one_sided_observation_is_excluded_and_flagged():
    result = pair_observations(
        [scored("g001", "base", 1.0), scored("g002", "base", 0.0)],
        [scored("g001", "cand", 1.0)],
    )
    assert [pair.group_key for pair in result.pairs] == ["g001"]
    assert result.total_groups == 2
    assert result.diagnostics == [
        Diagnostic(
            "g002",
            "cand",
            DiagnosticReason.MISSING_OBSERVATION,
            "no observation from candidate arm",
        )
    ]
    lift = summarize_correctness(result.pairs)
    assert lift.total_pairs == 1 and lift.eligible_pairs == 1


def test_duplicate_observation_drops_the_group_and_is_flagged():
    result = pair_observations(
        [scored("g001", "base", 1.0), scored("g001", "base", 0.0)],
        [scored("g001", "cand", 1.0)],
    )
    assert result.pairs == []
    assert [d.reason for d in result.diagnostics] == [
        DiagnosticReason.DUPLICATE_OBSERVATION
    ]
    assert "2 observations" in result.diagnostics[0].detail


def test_errored_and_blank_sides_are_paired_but_never_scored():
    result = pair_observations(
        [
            scored("g001", "base", 1.0),
            Observation("g002", "base", Outcome.ERRORED, detail="500"),
            scored("g003", "base", 1.0),
        ],
        [
            scored("g001", "cand", 0.0),
            scored("g002", "cand", 1.0),
            Observation("g003", "cand", Outcome.UNSCORED),
        ],
    )
    assert len(result.pairs) == 3
    lift = summarize_correctness(result.pairs)
    # Only g001 has both sides scored, so the rates are over n=1, not n=3 --
    # the errored and blank rows are excluded, not imputed as failures.
    assert lift.total_pairs == 3
    assert lift.eligible_pairs == 1
    assert lift.baseline_pass_rate == 1.0
    assert lift.candidate_pass_rate == 0.0
    assert lift.lift == -1.0
    counts = diagnostic_counts(result.diagnostics)
    assert counts["harness-error"] == 1
    assert counts["missing-score"] == 1
    assert counts["missing-observation"] == 0


def test_unscorable_outcome_is_reported_under_its_own_reason():
    result = pair_observations(
        [Observation("g001", "base", Outcome.UNSCORABLE, detail="no answer key")],
        [scored("g001", "cand", 1.0)],
    )
    assert diagnostic_counts(result.diagnostics)["unscorable-outcome"] == 1
    assert summarize_correctness(result.pairs).eligible_pairs == 0


def test_empty_comparison_reports_none_not_zero():
    lift = summarize_correctness([])
    assert lift.baseline_pass_rate is None
    assert lift.candidate_pass_rate is None
    assert lift.lift is None
    assert lift.p_value == 1.0


def test_wins_ties_and_mcnemar_over_discordant_pairs():
    pairs = pair_observations(
        [scored(f"g{i:03d}", "base", 0.0) for i in range(8)],
        [scored(f"g{i:03d}", "cand", 1.0) for i in range(8)],
    ).pairs
    lift = summarize_correctness(pairs)
    assert (lift.candidate_wins, lift.baseline_wins, lift.ties) == (8, 0, 0)
    assert lift.lift == 1.0
    assert lift.p_value == pytest.approx(0.0078125)


def test_mcnemar_matches_the_adr_001_hand_computation():
    # b=4, c=0 discordant pairs is the ADR-001 recall comparison; the exact
    # two-sided binomial gives 2 * (1/2)^4 = 0.125.
    assert mcnemar_exact(0, 4) == pytest.approx(0.125)
    assert mcnemar_exact(4, 0) == pytest.approx(0.125)
    assert mcnemar_exact(0, 0) == 1.0


def test_diagnostic_counts_lists_every_reason_even_at_zero():
    counts = diagnostic_counts([])
    assert set(counts) == {reason.value for reason in DiagnosticReason}
    assert set(counts.values()) == {0}


# ---------------------------------------------------------------------------
# Continuous metrics.
# ---------------------------------------------------------------------------


def test_summarize_metric_skips_pairs_missing_a_side():
    pairs = pair_observations(
        [
            Observation("g001", "base", Outcome.SCORED, 1.0, {"latency_ms": 100.0}),
            Observation("g002", "base", Outcome.SCORED, 1.0, {}),
        ],
        [
            Observation("g001", "cand", Outcome.SCORED, 1.0, {"latency_ms": 80.0}),
            Observation("g002", "cand", Outcome.SCORED, 1.0, {"latency_ms": 60.0}),
        ],
    ).pairs
    metric = summarize_metric(pairs, "latency_ms")
    assert metric.total_pairs == 2
    assert metric.eligible_pairs == 1
    assert metric.baseline_mean == 100.0
    assert metric.candidate_mean == 80.0
    assert metric.mean_delta == -20.0


def test_summarize_metric_with_no_eligible_pairs_reports_none():
    metric = summarize_metric([], "latency_ms")
    assert metric.baseline_mean is None and metric.mean_delta is None


# ---------------------------------------------------------------------------
# Judgments adapter.
# ---------------------------------------------------------------------------


def make_payload(alias, verdicts):
    return {
        "meta": {"judge_alias": alias},
        "judgments": [
            {"claim_id": cid, "judge_label": label} for cid, label in verdicts
        ],
    }


CLAIMS = [
    {"claim_id": "c1", "label": "supported"},
    {"claim_id": "c2", "label": "partial"},
    {"claim_id": "c3", "label": "unsupported"},
    {"claim_id": "c4", "label": "na"},
    {"claim_id": "c5", "label": None},
    {"claim_id": "c6", "label": "supported"},
]


def test_adapter_outcomes_na_abstention_and_binary_scoring():
    payload = make_payload(
        "opus",
        [
            ("c1", "supported"),  # binary match -> 1.0
            ("c2", "unsupported"),  # partial collapses to unsupported -> 1.0
            ("c3", "supported"),  # miss -> 0.0
            ("c4", "supported"),  # gold na -> unscorable regardless of verdict
            # c5 unlabeled -> unscorable; c6 has no verdict -> unscored
        ],
    )
    observations = observations_from_judgments(CLAIMS, payload)
    assert [o.outcome for o in observations] == [
        Outcome.SCORED,
        Outcome.SCORED,
        Outcome.SCORED,
        Outcome.UNSCORABLE,
        Outcome.UNSCORABLE,
        Outcome.UNSCORED,
    ]
    assert [o.score for o in observations[:3]] == [1.0, 1.0, 0.0]
    assert all(o.arm == "opus" for o in observations)
    assert observations[5].detail == "no verdict from judge"


def test_adapter_treats_unrecognized_verdict_as_abstention():
    payload = make_payload("opus", [("c1", "maybe")])
    (observation,) = observations_from_judgments(CLAIMS[:1], payload)
    assert observation.outcome is Outcome.UNSCORED
    assert "maybe" in observation.detail


def test_adapter_restriction_defines_the_universe():
    payload = make_payload(
        "opus", [("c1", "supported"), ("c2", "supported"), ("c3", "unsupported")]
    )
    restricted = observations_from_judgments(
        CLAIMS, payload, restrict_gold="unsupported"
    )
    # Universe = collapsed-gold unsupported only: c2 (partial gold) and c3. The
    # na and unlabeled claims are outside any restricted universe, not
    # unscorable.
    assert [o.group_key for o in restricted] == ["c2", "c3"]
    assert [o.score for o in restricted] == [0.0, 1.0]


def test_adapter_rejects_a_non_binary_restriction():
    with pytest.raises(ValueError, match="restrict_gold"):
        observations_from_judgments(CLAIMS, make_payload("opus", []), "partial")


# ---------------------------------------------------------------------------
# End-to-end against the committed artifacts.
# ---------------------------------------------------------------------------


def load_committed():
    claims = dataset.load_yaml(dataset.CLAIMS_PATH)["claims"]
    opus = dataset.load_yaml(dataset.DATA_DIR / "judgments_opus.yaml")
    sonnet = dataset.load_yaml(dataset.DATA_DIR / "judgments_sonnet.yaml")
    return claims, opus, sonnet


def test_reproduces_the_committed_binary_comparison():
    # Cross-validation against the comparison score.py already does per-judge:
    # run the paired layer over the committed artifacts and check every count
    # against a from-scratch computation. No published constant is hardcoded --
    # both sides are derived from the files, so only the two implementations
    # disagreeing can fail this.
    claims, opus, sonnet = load_committed()
    result, lift, report = paired_compare.compare_judgment_files(
        dataset.DATA_DIR / "judgments_opus.yaml",
        dataset.DATA_DIR / "judgments_sonnet.yaml",
    )

    opus_verdicts = {j["claim_id"]: j["judge_label"] for j in opus["judgments"]}
    sonnet_verdicts = {j["claim_id"]: j["judge_label"] for j in sonnet["judgments"]}
    tallies = Counter()
    scorable = 0
    for claim in claims:
        if claim["label"] in (None, "na"):
            continue
        o = opus_verdicts.get(claim["claim_id"])
        s = sonnet_verdicts.get(claim["claim_id"])
        if o is None or s is None:
            continue
        scorable += 1
        gold = collapse(claim["label"])
        tallies["opus"] += collapse(o) == gold
        tallies["sonnet"] += collapse(s) == gold
        if (collapse(o) == gold) and (collapse(s) != gold):
            tallies["opus_wins"] += 1
        elif (collapse(s) == gold) and (collapse(o) != gold):
            tallies["sonnet_wins"] += 1

    assert lift.eligible_pairs == scorable
    assert lift.baseline_pass_rate == pytest.approx(tallies["opus"] / scorable)
    assert lift.candidate_pass_rate == pytest.approx(tallies["sonnet"] / scorable)
    assert lift.baseline_wins == tallies["opus_wins"]
    assert lift.candidate_wins == tallies["sonnet_wins"]
    # Every group is a structural pair: both judges rated the whole gold set.
    assert diagnostic_counts(result.diagnostics)["missing-observation"] == 0
    assert "PAIRED COMPARISON" in report and "HARNESS HEALTH" in report


def test_reproduces_the_adr_001_recall_comparison():
    # The restricted run is ADR-001's hand-rolled unsupported-recall McNemar,
    # re-derived from the artifacts rather than quoted.
    claims, opus, sonnet = load_committed()
    _, lift, _ = paired_compare.compare_judgment_files(
        dataset.DATA_DIR / "judgments_opus.yaml",
        dataset.DATA_DIR / "judgments_sonnet.yaml",
        restrict_gold="unsupported",
    )

    opus_verdicts = {j["claim_id"]: j["judge_label"] for j in opus["judgments"]}
    sonnet_verdicts = {j["claim_id"]: j["judge_label"] for j in sonnet["judgments"]}
    universe = [
        c
        for c in claims
        if c["label"] not in (None, "na") and collapse(c["label"]) == "unsupported"
    ]
    opus_hits = sum(
        collapse(opus_verdicts[c["claim_id"]]) == "unsupported" for c in universe
    )
    sonnet_hits = sum(
        collapse(sonnet_verdicts[c["claim_id"]]) == "unsupported" for c in universe
    )
    opus_only = sum(
        (collapse(opus_verdicts[c["claim_id"]]) == "unsupported")
        and (collapse(sonnet_verdicts[c["claim_id"]]) != "unsupported")
        for c in universe
    )
    sonnet_only = sum(
        (collapse(sonnet_verdicts[c["claim_id"]]) == "unsupported")
        and (collapse(opus_verdicts[c["claim_id"]]) != "unsupported")
        for c in universe
    )

    assert lift.eligible_pairs == len(universe)
    assert lift.baseline_pass_rate == pytest.approx(opus_hits / len(universe))
    assert lift.candidate_pass_rate == pytest.approx(sonnet_hits / len(universe))
    assert lift.baseline_wins == opus_only
    assert lift.candidate_wins == sonnet_only
    assert lift.p_value == pytest.approx(
        mcnemar_exact(sonnet_only, opus_only)
    )
