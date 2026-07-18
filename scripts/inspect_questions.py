#!/usr/bin/env python3
"""Validate and summarize the densified question set.

Reads data/questions.yaml, checks its structure, and prints the distribution of
densification types, categories, and domains. The point is to let anyone verify
the instrument's shape by running it, rather than trusting a hand-count.

Usage:
    python3 scripts/inspect_questions.py            # validate + print summary
    python3 scripts/inspect_questions.py --strict   # exit 1 on any warning

Only dependency beyond the standard library is PyYAML.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - guidance only
    sys.exit("PyYAML is required: pip install pyyaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = REPO_ROOT / "data" / "questions.yaml"

VALID_TYPES = {"grounded", "partial", "unanswerable", "false_premise"}
CONTEXT_FIELDS = {"id", "category", "domain", "text", "questions"}
QUESTION_FIELDS = {"id", "type", "question", "note"}


def load() -> dict:
    if not QUESTIONS.exists():
        sys.exit(f"not found: {QUESTIONS}")
    with QUESTIONS.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def validate(data: dict) -> list[str]:
    """Return a list of problem strings (empty means clean)."""
    problems: list[str] = []
    seen_ctx: set[str] = set()
    seen_q: set[str] = set()

    for ctx in data.get("contexts", []):
        missing = CONTEXT_FIELDS - ctx.keys()
        if missing:
            problems.append(f"context {ctx.get('id', '?')}: missing {sorted(missing)}")
        cid = ctx.get("id", "?")
        if cid in seen_ctx:
            problems.append(f"duplicate context id: {cid}")
        seen_ctx.add(cid)

        if not str(ctx.get("text", "")).strip():
            problems.append(f"context {cid}: empty text")

        for q in ctx.get("questions", []):
            qmissing = QUESTION_FIELDS - q.keys()
            if qmissing:
                problems.append(f"question {q.get('id', '?')}: missing {sorted(qmissing)}")
            qid = q.get("id", "?")
            if qid in seen_q:
                problems.append(f"duplicate question id: {qid}")
            seen_q.add(qid)
            if q.get("type") not in VALID_TYPES:
                problems.append(f"question {qid}: bad type {q.get('type')!r}")

    return problems


def summarize(data: dict) -> None:
    contexts = data.get("contexts", [])
    questions = [q for ctx in contexts for q in ctx.get("questions", [])]

    by_type = Counter(q["type"] for q in questions)
    by_cat = Counter(ctx["category"] for ctx in contexts)
    by_dom = Counter(ctx["domain"] for ctx in contexts)
    total = len(questions)

    print(f"contexts:  {len(contexts)}")
    print(f"questions: {total}\n")

    print("densification type      count   share")
    print("-" * 40)
    # grounded is the control class; traps are the other three.
    trap = 0
    for t in ("grounded", "partial", "unanswerable", "false_premise"):
        n = by_type.get(t, 0)
        if t != "grounded":
            trap += n
        print(f"{t:<22}{n:>6}{n / total:>8.1%}")
    print("-" * 40)
    print(f"{'trap subtotal':<22}{trap:>6}{trap / total:>8.1%}")

    print("\ncategory (contexts):", dict(by_cat))
    print("domain   (contexts):", dict(by_dom))


def main() -> int:
    strict = "--strict" in sys.argv[1:]
    data = load()
    problems = validate(data)
    summarize(data)
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print(f"  - {p}")
        return 1 if strict else 0
    print("\nOK: no structural problems.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
