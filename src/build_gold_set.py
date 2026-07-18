"""Build the combined gold set to hand-label, from one or more answer runs.

Merges multiple prompt-variant answer files into a single claims.yaml, tagging
each claim with the variant it came from. The point is coverage: the `assertive`
run supplies blatant fabrications and the `helpful` run supplies subtle ungrounded
elaborations, so the judge is validated against both kinds of unfaithfulness.

Reuses the frozen splitter in decompose.py (one home for the split), and prefixes
claim ids with a short variant tag so ids stay unique across runs.

Usage:
    uv run python src/build_gold_set.py        # combine assertive + helpful
    uv run python src/build_gold_set.py --answers data/answers_assertive.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dataset  # noqa: E402  (path shim must run first)
from decompose import split_claims  # noqa: E402

# Short, stable id prefixes per variant.
_TAG = {"assertive": "asrt", "helpful": "help", "grounded": "grnd"}


def build(answer_files: list[Path]) -> dict:
    claims = []
    sources = {}
    for path in answer_files:
        payload = dataset.load_yaml(path)
        meta = payload.get("meta", {})
        variant = meta.get("prompt_variant", "unknown")
        tag = _TAG.get(variant, variant[:4])
        n = 0
        for ans in payload.get("answers", []):
            for i, text in enumerate(split_claims(ans.get("answer") or ""), start=1):
                claims.append(
                    {
                        "claim_id": f"{tag}-{ans['id']}-c{i}",
                        "question_id": ans["id"],
                        "context_id": ans["context_id"],
                        "type": ans["type"],
                        "variant": variant,
                        "claim_text": text,
                        "label": None,  # human fills: supported / partial / unsupported
                    }
                )
                n += 1
        sources[variant] = {"model": meta.get("model"), "file": path.name, "n_claims": n}

    return {
        "meta": {
            "sources": sources,
            "labels_allowed": list(dataset.CLAIM_LABELS),
            "binary_collapse": "partial -> unsupported for the headline binary kappa",
            "n_claims": len(claims),
        },
        "claims": claims,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--answers",
        nargs="+",
        type=Path,
        default=[
            dataset.answers_path("assertive"),
            dataset.answers_path("helpful"),
        ],
    )
    ap.add_argument("--out", type=Path, default=dataset.CLAIMS_PATH)
    args = ap.parse_args()

    missing = [str(p) for p in args.answers if not p.exists()]
    if missing:
        sys.exit(f"missing answer files: {', '.join(missing)}")

    payload = build(args.answers)
    dataset.dump_yaml(args.out, payload)
    print(
        f"wrote {payload['meta']['n_claims']} claims from "
        f"{len(args.answers)} runs to {args.out}"
    )
    for variant, info in payload["meta"]["sources"].items():
        print(f"  {variant:<10} {info['n_claims']:>4} claims")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
