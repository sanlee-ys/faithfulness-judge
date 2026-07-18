"""Generate QA answers over the densified question set (excerpt-only grounding).

For each question, the model sees ONLY the context excerpt and the question — no
full article, no outside knowledge is invited. The answers are the fixture the
faithfulness judge (and the human) will later rate claim by claim; this script
just produces them, reproducibly and with its settings recorded.

Design decision — the QA prompt (surfaced, not silently chosen):
  The prompt materially moves the hallucination rate, so it is a named, swappable
  constant, not buried in a call. Two variants:

    grounded (default) — mirrors a real RAG deployment: "use only the passage; if
      it isn't there, say so." The harder, more meaningful test — it measures the
      judge against hallucination that survives best-practice grounding.
    helpful — "answer as specifically as you can," no grounding guard. Produces
      more fabrication; useful if `grounded` leaves the unsupported class too thin
      to estimate the judge's recall on it.

  Default is `grounded`. If the measured unsupported-claim share comes in well
  under the 40% target (SCOPE.md), rerun with `--variant helpful` — that choice
  is a measurement, not a default.

The QA model under test defaults to the SYS-002 workhorse (Sonnet). The *judge*
tiers (Sonnet vs Opus) are a separate, later slice — don't conflate them.

Usage:
    uv run python src/generate_answers.py                 # generate all (needs a key)
    uv run python src/generate_answers.py --variant helpful
    uv run python src/generate_answers.py --dry-run       # print prompts, no API calls
    uv run python src/generate_answers.py --limit 3       # first 3 questions only
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dataset  # noqa: E402  (path shim must run first)
from dataset import Question

# The QA model under test. Separate from the judge model tiers (a later slice).
DEFAULT_MODEL = "claude-sonnet-5"
# Newer models (e.g. claude-sonnet-5) reject an explicit `temperature`
# ("temperature is deprecated for this model"), so we omit it by default and
# only send it when a caller explicitly passes --temperature (for older models).
DEFAULT_TEMPERATURE = None
MAX_TOKENS = 400

PROMPT_VARIANTS = {
    "grounded": (
        "You are answering a reader's question about a short news passage. "
        "Use only information stated in the passage. If the passage does not "
        "contain the answer, say so plainly rather than guessing."
    ),
    "helpful": (
        "You are answering a reader's question about a short news passage. "
        "Answer the question as helpfully and specifically as you can."
    ),
}


def build_prompt(question: Question, variant: str) -> tuple[str, str]:
    """Return (system, user) for one question. Pure — no network, easy to test."""
    system = PROMPT_VARIANTS[variant]
    user = f"Passage:\n{question.context_text}\n\nQuestion: {question.question}"
    return system, user


def call_model(
    client, system: str, user: str, model: str, temperature: float | None
) -> str:
    """Isolated API call, so everything around it stays testable offline."""
    kwargs = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    # Only send temperature when explicitly set — newer models reject it.
    if temperature is not None:
        kwargs["temperature"] = temperature
    resp = client.messages.create(**kwargs)
    return "".join(block.text for block in resp.content if block.type == "text").strip()


def generate(
    variant: str,
    model: str,
    temperature: float | None,
    dry_run: bool,
    limit: int | None,
) -> dict:
    questions = dataset.load_questions()
    if limit is not None:
        questions = questions[:limit]

    client = None
    if not dry_run:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit(
                "ANTHROPIC_API_KEY is not set. Set it and rerun, or use --dry-run "
                "to build prompts without calling the API."
            )
        import anthropic

        client = anthropic.Anthropic()

    answers = []
    for q in questions:
        system, user = build_prompt(q, variant)
        if dry_run:
            print(f"--- {q.id} [{q.type}] ---\nSYSTEM: {system}\n{user}\n")
            answer = None
        else:
            answer = call_model(client, system, user, model, temperature)
            print(f"{q.id} [{q.type}] done")
        answers.append(
            {
                "id": q.id,
                "context_id": q.context_id,
                "type": q.type,
                "question": q.question,
                "answer": answer,
            }
        )

    return {
        "meta": {
            "model": model,
            "prompt_variant": variant,
            "temperature": temperature,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "n_questions": len(answers),
            "grounding": "excerpt-only",
        },
        "answers": answers,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--variant", choices=sorted(PROMPT_VARIANTS), default="grounded")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help="omitted by default; set only for older models that accept it",
    )
    ap.add_argument("--dry-run", action="store_true", help="print prompts, no API calls")
    ap.add_argument("--limit", type=int, default=None, help="only the first N questions")
    args = ap.parse_args()

    payload = generate(
        variant=args.variant,
        model=args.model,
        temperature=args.temperature,
        dry_run=args.dry_run,
        limit=args.limit,
    )
    if args.dry_run:
        print(f"[dry-run] built {payload['meta']['n_questions']} prompts, wrote nothing.")
        return 0

    dataset.dump_yaml(dataset.ANSWERS_PATH, payload)
    print(f"wrote {len(payload['answers'])} answers to {dataset.ANSWERS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
