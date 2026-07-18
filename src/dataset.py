"""Shared loading for the faithfulness-judge pipeline.

One place that knows where the data files live and how to flatten the nested
question set into per-question records. Every script imports this so paths and
the question schema have a single home.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"

QUESTIONS_PATH = DATA_DIR / "questions.yaml"
ANSWERS_PATH = DATA_DIR / "answers.yaml"
CLAIMS_PATH = DATA_DIR / "claims.yaml"

# Labels a human applies to each claim during the gold pass. `partial` collapses
# to `unsupported` for the headline binary kappa (SCOPE.md, Decision 1).
CLAIM_LABELS = ("supported", "partial", "unsupported")


@dataclass(frozen=True)
class Question:
    """A single question paired with the context excerpt that grounds it."""

    id: str
    context_id: str
    category: str
    domain: str
    type: str
    question: str
    context_text: str
    note: str


def load_questions(path: Path = QUESTIONS_PATH) -> list[Question]:
    """Flatten questions.yaml into a list of Question records, preserving order."""
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    out: list[Question] = []
    for ctx in data.get("contexts", []):
        text = str(ctx["text"]).strip()
        for q in ctx.get("questions", []):
            out.append(
                Question(
                    id=q["id"],
                    context_id=ctx["id"],
                    category=ctx["category"],
                    domain=ctx["domain"],
                    type=q["type"],
                    question=q["question"],
                    context_text=text,
                    note=q.get("note", ""),
                )
            )
    return out


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def dump_yaml(path: Path, payload: dict) -> None:
    """Write YAML with stable key order and readable block strings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(
            payload,
            fh,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            width=88,
        )
