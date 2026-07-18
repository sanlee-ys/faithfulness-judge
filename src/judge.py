"""Run an LLM judge over the gold-set claims (blind to the human labels).

For each claim, the judge sees ONLY the context excerpt and the claim text — not
the question type, not the variant, and never the human label — and must answer
with one word: supported / partial / unsupported. Definitions in the prompt
mirror docs/labeling-guide.md so the judge and the human are graded against the
same rubric.

Two judge tiers (SCOPE.md Decision 3): run both, report both, lead with whichever
agrees better with the human gold.

    uv run python src/judge.py --judge sonnet     # -> data/judgments_sonnet.yaml
    uv run python src/judge.py --judge opus       # -> data/judgments_opus.yaml
    uv run python src/judge.py --judge sonnet --dry-run

Judgments are per-tier files, committed once produced. Scoring against the gold
labels is a separate, offline step: src/score.py.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dataset  # noqa: E402  (path shim must run first)
from dataset import load_questions  # noqa: E402

JUDGES = {
    "sonnet": "claude-sonnet-5",
    "opus": "claude-opus-4-8",
}
MAX_TOKENS = 64  # room for the forced tool call

# Mirrors docs/labeling-guide.md. The judge rates the claim against the passage
# only — world knowledge is explicitly excluded, matching the human rubric.
SYSTEM = (
    "You are grading whether a claim is supported by a source passage.\n"
    "Judge the claim ONLY against the passage. Ignore whether the claim is true "
    "in the real world — if the passage does not contain it, it is not supported.\n\n"
    "Record exactly one verdict with the record_verdict tool:\n"
    "supported — every part of the claim is stated in, or unambiguously entailed "
    "by, the passage. A claim that correctly says the passage lacks some "
    "information counts as supported.\n"
    "partial — part of the claim is grounded in the passage, but part adds "
    "specifics the passage does not contain.\n"
    "unsupported — the claim asserts something the passage does not support: a "
    "fabricated fact, a wrong value, an inference beyond the text, or a premise "
    "the passage contradicts."
)

# Forcing this tool guarantees a clean enum verdict — no free-text truncation or
# unparsed replies (the failure mode that sank the first Sonnet run).
VERDICT_TOOL = {
    "name": "record_verdict",
    "description": "Record the faithfulness verdict for the claim.",
    "input_schema": {
        "type": "object",
        "properties": {
            "verdict": {
                "type": "string",
                "enum": ["supported", "partial", "unsupported"],
            }
        },
        "required": ["verdict"],
    },
}

_VALID = {"supported", "partial", "unsupported"}


def build_prompt(context_text: str, claim_text: str) -> str:
    passage = " ".join(context_text.split())
    return f"Passage:\n{passage}\n\nClaim:\n{claim_text}"


def parse_verdict(raw: str) -> str | None:
    """Pull a verdict out of free text; None if none found. Text fallback only."""
    word = raw.strip().lower().strip(".:!\"'")
    if word in _VALID:
        return word
    tokens = [t.strip(".:!\"'") for t in word.split()]
    hits = [t for t in tokens if t in _VALID]
    return hits[0] if hits else None


def extract_verdict(resp) -> str | None:
    """Read the verdict from the forced tool call; fall back to any text."""
    for block in resp.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "record_verdict":
            v = (block.input or {}).get("verdict")
            if v in _VALID:
                return v
    raw = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    return parse_verdict(raw)


def judge_claims(alias: str, dry_run: bool, limit: int | None) -> dict:
    model = JUDGES[alias]
    payload = dataset.load_yaml(dataset.CLAIMS_PATH)
    claims = payload["claims"]
    if limit is not None:
        claims = claims[:limit]
    ctx = {q.id: q.context_text for q in load_questions()}

    client = None
    if not dry_run:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("ANTHROPIC_API_KEY is not set (use --dry-run to preview prompts).")
        import anthropic

        client = anthropic.Anthropic()

    judgments, unparsed = [], 0
    for c in claims:
        prompt = build_prompt(ctx[c["question_id"]], c["claim_text"])
        if dry_run:
            verdict = None
        else:
            resp = client.messages.create(
                model=model,
                max_tokens=MAX_TOKENS,
                system=SYSTEM,
                messages=[{"role": "user", "content": prompt}],
                tools=[VERDICT_TOOL],
                tool_choice={"type": "tool", "name": "record_verdict"},
            )
            verdict = extract_verdict(resp)
            if verdict is None:
                unparsed += 1
                print(f"  ! {c['claim_id']}: no verdict in response")
            else:
                print(f"{c['claim_id']}: {verdict}")
        judgments.append({"claim_id": c["claim_id"], "judge_label": verdict})

    return {
        "meta": {
            "judge_alias": alias,
            "judge_model": model,
            "judged_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "n_claims": len(judgments),
            "n_unparsed": unparsed,
            "blind": "judge saw excerpt + claim only; no type/variant/human label",
        },
        "judgments": judgments,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judge", choices=sorted(JUDGES), required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    payload = judge_claims(args.judge, args.dry_run, args.limit)
    if args.dry_run:
        print(f"[dry-run] built {payload['meta']['n_claims']} prompts, wrote nothing.")
        return 0
    out = dataset.DATA_DIR / f"judgments_{args.judge}.yaml"
    dataset.dump_yaml(out, payload)
    print(f"wrote {payload['meta']['n_claims']} judgments to {out}")
    print("next: uv run python src/score.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
