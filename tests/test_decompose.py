"""The frozen claim splitter is deterministic and sane."""

from decompose import decompose, split_claims


def test_splits_sentences():
    answer = "The contract is worth $500 million. It went to AeroVironment."
    assert split_claims(answer) == [
        "The contract is worth $500 million.",
        "It went to AeroVironment.",
    ]


def test_handles_bullets_and_newlines():
    answer = "Findings:\n- mobility was rated well\n- the tablet glared in sunlight"
    claims = split_claims(answer)
    assert "mobility was rated well" in claims
    assert "the tablet glared in sunlight" in claims
    assert "Findings:" in claims


def test_collapses_internal_whitespace():
    assert split_claims("A   messy    sentence here.") == ["A messy sentence here."]


def test_does_not_split_on_abbreviations():
    # "Ft." and "Aug." must not end a sentence — this whole thing is one claim.
    answer = "The unit deployed to Ft. Carson from June 15 – Aug. 14, 2020."
    assert split_claims(answer) == [
        "The unit deployed to Ft. Carson from June 15 – Aug. 14, 2020."
    ]


def test_does_not_split_on_acronyms():
    answer = "The U.S. payload launched. It reached orbit."
    assert split_claims(answer) == ["The U.S. payload launched.", "It reached orbit."]


def test_strips_markdown_and_enumerators():
    answer = "Two firsts:\n1. **First effort**\n2. Second launch"
    assert split_claims(answer) == ["Two firsts:", "First effort", "Second launch"]


def test_empty_answer_yields_no_claims():
    assert split_claims("") == []
    assert split_claims(None or "") == []


def test_determinism():
    answer = "One claim. Two claim. Three claim."
    assert split_claims(answer) == split_claims(answer)


def test_decompose_builds_labelable_claims():
    answers_payload = {
        "meta": {"model": "m", "prompt_variant": "grounded"},
        "answers": [
            {
                "id": "q-01",
                "context_id": "ctx-01",
                "type": "grounded",
                "question": "How much?",
                "answer": "It is $500 million. AeroVironment won it.",
            }
        ],
    }
    out = decompose(answers_payload)
    assert out["meta"]["n_claims"] == 2
    first = out["claims"][0]
    assert first["claim_id"] == "q-01-c1"
    assert first["question_id"] == "q-01"
    assert first["label"] is None  # awaiting the human gold pass
    assert out["meta"]["labels_allowed"] == ["supported", "partial", "unsupported"]
