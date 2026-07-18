"""Export claims to a CSV for labeling, and apply the filled CSV back.

Human gold-pass ergonomics: editing `label: null` across ~200 YAML entries is
miserable, so export a flat CSV (one row per claim, with its excerpt and question
inline for context), fill the `label` column in a spreadsheet, then apply it back
into claims.yaml. claims.yaml stays the source of truth; the CSV is a scratch pad.

Labels: s=supported, p=partial, u=unsupported, n=na (not a factual claim —
excluded from scoring). See docs/labeling-guide.md for the rubric.

Usage:
    uv run python src/labels.py label      # interactive terminal labeler (recommended)
    uv run python src/labels.py export     # claims.yaml -> data/labeling.csv (spreadsheet route)
    uv run python src/labels.py apply      # data/labeling.csv -> claims.yaml labels
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dataset  # noqa: E402  (path shim must run first)
from dataset import load_questions  # noqa: E402

LABELING_CSV = dataset.DATA_DIR / "labeling.csv"
FIELDS = ["claim_id", "type", "variant", "question", "context_excerpt", "claim_text", "label"]

# Accept single-letter shortcuts and full words; `na` = not a claim (excluded).
_NORMALIZE = {
    "s": "supported", "p": "partial", "u": "unsupported", "n": "na",
    "supported": "supported", "partial": "partial", "unsupported": "unsupported",
    "na": "na",
}


def export(claims_path: Path, out: Path) -> None:
    payload = dataset.load_yaml(claims_path)
    qmap = {q.id: q for q in load_questions()}
    rows = []
    for c in payload["claims"]:
        q = qmap.get(c["question_id"])
        rows.append(
            {
                "claim_id": c["claim_id"],
                "type": c["type"],
                "variant": c.get("variant", ""),
                "question": q.question if q else "",
                # collapse the excerpt's block-scalar newlines to one clean line
                "context_excerpt": " ".join(q.context_text.split()) if q else "",
                "claim_text": c["claim_text"],
                "label": "" if c.get("label") is None else c["label"],
            }
        )
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"exported {len(rows)} claims to {out}  (fill 'label' with s / p / u / n)")


def apply(claims_path: Path, csv_path: Path, out: Path) -> None:
    labels, bad = {}, []
    # utf-8-sig tolerates the BOM Excel prepends when saving as "CSV UTF-8"
    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            raw = (row.get("label") or "").strip().lower()
            if not raw:
                continue
            if raw not in _NORMALIZE:
                bad.append((row.get("claim_id", "?"), raw))
                continue
            labels[row["claim_id"]] = _NORMALIZE[raw]

    if bad:
        listing = "\n".join(f"  {cid}: {val!r}" for cid, val in bad)
        sys.exit(f"invalid labels (use s/p/u/n):\n{listing}")

    payload = dataset.load_yaml(claims_path)
    applied = 0
    for c in payload["claims"]:
        if c["claim_id"] in labels:
            c["label"] = labels[c["claim_id"]]
            applied += 1
    payload["meta"]["n_labeled"] = applied
    dataset.dump_yaml(out, payload)
    remaining = len(payload["claims"]) - applied
    print(f"applied {applied} labels to {out}  ({remaining} still unlabeled)")


def _wrap(text: str, width: int = 86, indent: str = "  ") -> str:
    import textwrap

    return "\n".join(
        textwrap.fill(line, width=width, initial_indent=indent, subsequent_indent=indent)
        for line in text.splitlines() or [""]
    )


def label_interactive(claims_path: Path) -> None:
    """One claim at a time in the terminal; saves after every answer; resumable."""
    payload = dataset.load_yaml(claims_path)
    claims = payload["claims"]
    qmap = {q.id: q for q in load_questions()}

    todo = [c for c in claims if c.get("label") is None]
    done = len(claims) - len(todo)
    if not todo:
        print(f"all {len(claims)} claims labeled — nothing to do.")
        return
    print(f"{len(todo)} to label ({done} already done). Saves after every answer;")
    print("Ctrl+C or q anytime — rerun to resume where you left off.\n")
    print("keys:  s = supported   p = partial   u = unsupported")
    print("       n = na (not a factual claim)   ? = rubric   q = quit\n")

    rubric = (
        "s supported    every part stated in, or clearly entailed by, the excerpt\n"
        "p partial      part grounded, part adds specifics the excerpt lacks\n"
        "u unsupported  fabricated fact / wrong value / accepted false premise;\n"
        "               world-true but excerpt-absent is STILL u\n"
        "n na           filler or meta ('I'd be happy to help') — no factual claim\n"
        "A correct refusal ('the passage doesn't say X', and it truly doesn't) = s"
    )

    last_ctx = None
    labeled_now = 0
    for c in todo:
        q = qmap.get(c["question_id"])
        if q and q.context_id != last_ctx:
            last_ctx = q.context_id
            print("=" * 88)
            print(f"CONTEXT {q.context_id}")
            print(_wrap(" ".join(q.context_text.split())))
        remaining = len(todo) - labeled_now
        print("-" * 88)
        if q:
            print(f"[{c['claim_id']}] ({c['type']}, {c.get('variant','')}, {remaining} left)")
            print(_wrap(f"Q: {q.question}"))
        print(_wrap(f"CLAIM: {c['claim_text']}", indent="  > "))

        while True:
            try:
                key = input("label [s/p/u/n, ?=help, q=quit] > ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                key = "q"
            if key == "?":
                print(rubric)
                continue
            if key == "q":
                dataset.dump_yaml(claims_path, payload)
                print(f"\nsaved. {labeled_now} labeled this session; "
                      f"{remaining - (1 if key != 'q' else 0)} remaining — rerun to resume.")
                return
            if key in _NORMALIZE:
                c["label"] = _NORMALIZE[key]
                labeled_now += 1
                payload["meta"]["n_labeled"] = sum(
                    1 for x in claims if x.get("label") is not None
                )
                dataset.dump_yaml(claims_path, payload)  # save every answer
                break
            print("  (s, p, u, n, ?, or q)")

    print(f"\ndone — all {len(claims)} claims labeled. Now:")
    print("  git add data/claims.yaml")
    print('  git commit -m "Gold labels"')
    print("  git push")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    lab = sub.add_parser("label")
    lab.add_argument("--claims", type=Path, default=dataset.CLAIMS_PATH)
    e = sub.add_parser("export")
    e.add_argument("--claims", type=Path, default=dataset.CLAIMS_PATH)
    e.add_argument("--out", type=Path, default=LABELING_CSV)
    a = sub.add_parser("apply")
    a.add_argument("--claims", type=Path, default=dataset.CLAIMS_PATH)
    a.add_argument("--csv", type=Path, default=LABELING_CSV)
    a.add_argument("--out", type=Path, default=dataset.CLAIMS_PATH)
    args = ap.parse_args()

    if args.cmd == "label":
        label_interactive(args.claims)
    elif args.cmd == "export":
        export(args.claims, args.out)
    else:
        if not args.csv.exists():
            sys.exit(f"{args.csv} not found — run `labels.py export` first.")
        apply(args.claims, args.csv, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
