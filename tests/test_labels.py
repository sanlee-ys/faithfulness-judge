"""The label CSV round-trip preserves claim ids and writes labels back."""

import csv

import dataset
from labels import apply, export


def _seed_claims(path):
    dataset.dump_yaml(
        path,
        {
            "meta": {"n_claims": 2},
            "claims": [
                {"claim_id": "asrt-q-01-c1", "question_id": "q-01", "context_id": "ctx-01",
                 "type": "grounded", "variant": "assertive", "claim_text": "A.", "label": None},
                {"claim_id": "help-q-02-c1", "question_id": "q-02", "context_id": "ctx-01",
                 "type": "partial", "variant": "helpful", "claim_text": "B.", "label": None},
            ],
        },
    )


def test_export_writes_a_row_per_claim(tmp_path):
    claims = tmp_path / "claims.yaml"
    out = tmp_path / "labeling.csv"
    _seed_claims(claims)
    export(claims, out)
    rows = list(csv.DictReader(out.open()))
    assert [r["claim_id"] for r in rows] == ["asrt-q-01-c1", "help-q-02-c1"]
    assert all(r["label"] == "" for r in rows)  # starts blank


def test_apply_writes_labels_back_and_normalizes_shortcuts(tmp_path):
    claims = tmp_path / "claims.yaml"
    csv_path = tmp_path / "labeling.csv"
    _seed_claims(claims)
    export(claims, csv_path)

    # Fill labels with a shortcut and a full word; leave nothing blank here.
    rows = list(csv.DictReader(csv_path.open()))
    rows[0]["label"] = "s"           # -> supported
    rows[1]["label"] = "unsupported"
    with csv_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    apply(claims, csv_path, claims)
    out = dataset.load_yaml(claims)
    labels = {c["claim_id"]: c["label"] for c in out["claims"]}
    assert labels == {"asrt-q-01-c1": "supported", "help-q-02-c1": "unsupported"}
    assert out["meta"]["n_labeled"] == 2
