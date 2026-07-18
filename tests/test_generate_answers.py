"""Prompt construction is correct and offline — no API key, no network."""

import pytest

from dataset import load_questions
from generate_answers import PROMPT_VARIANTS, build_prompt, generate


@pytest.fixture
def one_question():
    return load_questions()[0]


def test_prompt_includes_passage_and_question(one_question):
    system, user = build_prompt(one_question, "grounded")
    assert one_question.context_text in user
    assert one_question.question in user
    assert system == PROMPT_VARIANTS["grounded"]


def test_variant_changes_the_system_prompt(one_question):
    grounded_sys, _ = build_prompt(one_question, "grounded")
    helpful_sys, _ = build_prompt(one_question, "helpful")
    assert grounded_sys != helpful_sys
    # The grounding guard only appears in the grounded variant.
    assert "say so" in grounded_sys
    assert "say so" not in helpful_sys


def test_dry_run_builds_all_prompts_without_calling_api():
    # dry_run must never construct a client or need a key.
    payload = generate(
        variant="grounded", model="x", temperature=0.0, dry_run=True, limit=None
    )
    assert payload["meta"]["n_questions"] == 40
    assert all(a["answer"] is None for a in payload["answers"])
    assert payload["meta"]["grounding"] == "excerpt-only"
