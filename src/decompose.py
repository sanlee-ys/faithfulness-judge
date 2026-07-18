"""Decompose generated answers into atomic claims — the units the human labels.

Per SCOPE.md Decision 2, decomposition is *frozen*: answers are split into claims
once, deterministically, and the judge later only *rates* these pre-split claims.
Fixing the split isolates the variable under test (rating) from a confound
(splitting) and keeps the judge from decomposing-and-rating in one circular step.

The splitter is deliberately simple: sentence segmentation on terminal
punctuation and line/bullet boundaries. A sentence occasionally carries more than
one claim; that coarseness is a documented floor limitation (a claim-extraction
model is the solid-tier upgrade), not a hidden one. Determinism is the point — the
same answers always yield the same claim set, so labels stay attached.

Output: data/claims.yaml, each claim with `label: null` for the human to fill
(supported / partial / unsupported).

Usage:
    uv run python src/decompose.py            # data/answers.yaml -> data/claims.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dataset  # noqa: E402  (path shim must run first)

_MIN_CLAIM_CHARS = 3  # drop stray fragments like a lone bullet or "OK."

# Abbreviations whose trailing period must NOT be treated as a sentence end.
_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "jr", "sr", "st", "ft", "mt", "col", "sgt", "gen",
    "adm", "lt", "capt", "gov", "sen", "rep", "vs", "no", "etc",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct",
    "nov", "dec",
}

_DOT = "\x00"  # placeholder standing in for a protected period during splitting
_MARKDOWN = re.compile(r"\*\*|\*|__|`")  # strip emphasis / code marks
_ENUMERATOR = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s+", re.MULTILINE)  # list markers
_ACRONYM = re.compile(r"\b(?:[A-Za-z]\.){2,}")  # U.S. , a.m. , U.K.
_ABBREV = re.compile(r"\b([A-Za-z]+)\.")
_SPLIT = re.compile(r"(?<=[.!?])\s+|[\n\r]+")


def _protect_periods(text: str) -> str:
    """Hide periods that end abbreviations/acronyms so we don't split on them."""
    text = _ACRONYM.sub(lambda m: m.group(0).replace(".", _DOT), text)

    def _abbr(m: re.Match) -> str:
        if m.group(1).lower() in _ABBREVIATIONS:
            return m.group(1) + _DOT
        return m.group(0)

    return _ABBREV.sub(_abbr, text)


def split_claims(answer: str) -> list[str]:
    """Deterministically split one answer into atomic claim strings.

    Sentence segmentation that guards against the two things that fragment real
    answers: abbreviations/acronyms (Ft., U.S., Aug.) and Markdown/list marks.
    """
    if not answer:
        return []
    text = _MARKDOWN.sub("", answer.strip())
    text = _ENUMERATOR.sub("", text)
    text = _protect_periods(text)

    claims = []
    for part in _SPLIT.split(text):
        claim = " ".join(part.replace(_DOT, ".").split())  # restore + collapse ws
        if len(claim) >= _MIN_CLAIM_CHARS and re.search(r"[A-Za-z0-9]", claim):
            claims.append(claim)
    return claims


def decompose(answers_payload: dict) -> dict:
    claims = []
    for ans in answers_payload.get("answers", []):
        for i, claim_text in enumerate(split_claims(ans.get("answer") or ""), start=1):
            claims.append(
                {
                    "claim_id": f"{ans['id']}-c{i}",
                    "question_id": ans["id"],
                    "context_id": ans["context_id"],
                    "type": ans["type"],
                    "claim_text": claim_text,
                    "label": None,  # human fills: supported / partial / unsupported
                }
            )

    return {
        "meta": {
            "source_answers": {
                "model": answers_payload.get("meta", {}).get("model"),
                "prompt_variant": answers_payload.get("meta", {}).get("prompt_variant"),
            },
            "labels_allowed": list(dataset.CLAIM_LABELS),
            "binary_collapse": "partial -> unsupported for the headline binary kappa",
            "n_claims": len(claims),
        },
        "claims": claims,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--answers", type=Path, default=dataset.ANSWERS_PATH)
    ap.add_argument("--out", type=Path, default=dataset.CLAIMS_PATH)
    args = ap.parse_args()

    if not args.answers.exists():
        sys.exit(
            f"{args.answers} not found — run src/generate_answers.py first "
            "(needs ANTHROPIC_API_KEY)."
        )

    payload = decompose(dataset.load_yaml(args.answers))
    dataset.dump_yaml(args.out, payload)
    print(f"wrote {payload['meta']['n_claims']} claims to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
