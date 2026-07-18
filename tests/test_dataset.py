"""The loader flattens the real question set correctly."""

from dataset import load_questions


def test_loads_all_forty_questions():
    questions = load_questions()
    assert len(questions) == 40
    assert len({q.id for q in questions}) == 40  # ids unique


def test_every_question_carries_its_context():
    for q in load_questions():
        assert q.context_text  # non-empty grounding excerpt
        assert q.type in {"grounded", "partial", "unanswerable", "false_premise"}
        assert q.context_id.startswith("ctx-")


def test_context_count():
    assert len({q.context_id for q in load_questions()}) == 12
