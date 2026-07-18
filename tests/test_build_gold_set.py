"""The gold-set combiner tags variants and keeps claim ids unique across runs."""

import dataset
from build_gold_set import build


def _write(path, variant, answers):
    dataset.dump_yaml(path, {"meta": {"prompt_variant": variant, "model": "m"}, "answers": answers})


def test_combines_and_tags_variants(tmp_path):
    a = tmp_path / "answers_assertive.yaml"
    h = tmp_path / "answers_helpful.yaml"
    _write(a, "assertive", [
        {"id": "q-01", "context_id": "ctx-01", "type": "grounded",
         "answer": "The contract is large. It grew."},
    ])
    _write(h, "helpful", [
        {"id": "q-01", "context_id": "ctx-01", "type": "grounded",
         "answer": "The contract is large."},
    ])

    out = build([a, h])

    # 2 claims from assertive + 1 from helpful.
    assert out["meta"]["n_claims"] == 3
    ids = [c["claim_id"] for c in out["claims"]]
    assert ids == ["asrt-q-01-c1", "asrt-q-01-c2", "help-q-01-c1"]  # unique, tagged
    variants = {c["variant"] for c in out["claims"]}
    assert variants == {"assertive", "helpful"}
    assert all(c["label"] is None for c in out["claims"])
    assert out["meta"]["sources"]["assertive"]["n_claims"] == 2
    assert out["meta"]["sources"]["helpful"]["n_claims"] == 1
