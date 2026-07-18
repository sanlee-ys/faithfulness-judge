"""Score judge verdicts against the human gold labels. Offline; no API.

For each judgments file present (data/judgments_*.yaml), computes agreement with
the human labels in data/claims.yaml:

- raw agreement + Cohen's kappa, ternary (s/p/u) and binary (partial collapsed
  into unsupported — SCOPE.md Decision 1), with a 95% Wilson CI on raw agreement
- per-class precision/recall and the confusion matrix
- recall on the binary `unsupported` class — the judge's hard job
- a misjudgment log (every claim where judge != human), the interesting cases

`na` gold labels are excluded (not factual claims); unparsed judge verdicts are
counted as disagreements (a judge that can't answer is wrong, not excused).

Writes evals/results.md and prints the same summary.
"""

from __future__ import annotations

import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dataset  # noqa: E402  (path shim must run first)

EVALS_DIR = dataset.REPO_ROOT / "evals"
TERNARY = ("supported", "partial", "unsupported")
BINARY = ("supported", "unsupported")


def collapse(label: str) -> str:
    return "unsupported" if label == "partial" else label


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a proportion."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def cohens_kappa(pairs: list[tuple[str, str]], labels: tuple[str, ...]) -> float:
    """Cohen's kappa over (gold, judge) pairs restricted to `labels`."""
    n = len(pairs)
    if n == 0:
        return float("nan")
    po = sum(1 for g, j in pairs if g == j) / n
    gold_marg = Counter(g for g, _ in pairs)
    judge_marg = Counter(j for _, j in pairs)
    pe = sum(gold_marg[c] * judge_marg[c] for c in labels) / (n * n)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def per_class(pairs: list[tuple[str, str]], labels: tuple[str, ...]) -> dict:
    out = {}
    for c in labels:
        tp = sum(1 for g, j in pairs if g == c and j == c)
        gold_n = sum(1 for g, _ in pairs if g == c)
        judged_n = sum(1 for _, j in pairs if j == c)
        out[c] = {
            "recall": tp / gold_n if gold_n else float("nan"),
            "precision": tp / judged_n if judged_n else float("nan"),
            "gold_n": gold_n,
        }
    return out


def confusion(pairs: list[tuple[str, str]], labels: tuple[str, ...]) -> str:
    width = max(len(c) for c in labels) + 2
    header = " " * width + "".join(f"{c:>{width}}" for c in labels) + "   (judge ->)"
    lines = [header]
    for g in labels:
        row = Counter(j for gg, j in pairs if gg == g)
        lines.append(f"{g:>{width}}" + "".join(f"{row.get(c, 0):>{width}}" for c in labels))
    return "\n".join(lines)


def score_judge(claims: list[dict], judgments_path: Path) -> tuple[str, dict]:
    payload = dataset.load_yaml(judgments_path)
    alias = payload["meta"]["judge_alias"]
    verdicts = {j["claim_id"]: j["judge_label"] for j in payload["judgments"]}

    pairs_t, misses, unparsed = [], [], 0
    for c in claims:
        gold = c["label"]
        if gold in (None, "na"):
            continue
        judge = verdicts.get(c["claim_id"])
        if judge is None:
            unparsed += 1
            judge = "__unparsed__"  # counts as disagreement everywhere
        pairs_t.append((gold, judge))
        if judge != gold:
            misses.append((c, gold, judge))

    pairs_b = [(collapse(g), collapse(j) if j in TERNARY else j) for g, j in pairs_t]
    n = len(pairs_t)
    agree_t = sum(1 for g, j in pairs_t if g == j)
    agree_b = sum(1 for g, j in pairs_b if g == j)
    lo_b, hi_b = wilson_ci(agree_b, n)

    stats = {
        "alias": alias,
        "model": payload["meta"]["judge_model"],
        "n": n,
        "unparsed": unparsed,
        "kappa_ternary": cohens_kappa(pairs_t, TERNARY),
        "kappa_binary": cohens_kappa(pairs_b, BINARY),
        "agree_binary": agree_b / n if n else float("nan"),
        "agree_binary_ci": (lo_b, hi_b),
        "agree_ternary": agree_t / n if n else float("nan"),
        "per_class_binary": per_class(pairs_b, BINARY),
        "confusion_ternary": confusion(pairs_t, TERNARY),
        "misses": misses,
    }

    md = [
        f"## Judge: {alias} ({stats['model']})",
        "",
        f"- n scored: **{n}** (na excluded; {unparsed} unparsed verdicts counted "
        "as disagreements)",
        f"- **Binary kappa (headline): {stats['kappa_binary']:.3f}** — raw agreement "
        f"{stats['agree_binary']:.1%} [95% CI {lo_b:.1%}, {hi_b:.1%}]",
        f"- Ternary kappa: {stats['kappa_ternary']:.3f} — raw agreement "
        f"{stats['agree_ternary']:.1%}",
        "",
        "| class (binary) | recall | precision | gold n |",
        "| --- | --- | --- | --- |",
    ]
    for cls in BINARY:
        pc = stats["per_class_binary"][cls]
        md.append(
            f"| {cls} | {pc['recall']:.1%} | {pc['precision']:.1%} | {pc['gold_n']} |"
        )
    md += ["", "Ternary confusion (rows = human gold):", "```",
           stats["confusion_ternary"], "```", ""]
    if misses:
        md.append(f"### Misjudgments ({len(misses)})")
        md.append("")
        for c, gold, judge in misses:
            md.append(f"- `{c['claim_id']}` gold **{gold}** / judge **{judge}** — "
                      f"{c['claim_text']}")
        md.append("")
    return "\n".join(md), stats


def main() -> int:
    payload = dataset.load_yaml(dataset.CLAIMS_PATH)
    claims = payload["claims"]
    unlabeled = sum(1 for c in claims if c["label"] is None)
    if unlabeled:
        sys.exit(
            f"{unlabeled} claims are still unlabeled — finish the gold pass "
            "(src/labels.py label) before scoring."
        )

    judgment_files = sorted(dataset.DATA_DIR.glob("judgments_*.yaml"))
    if not judgment_files:
        sys.exit("no data/judgments_*.yaml found — run src/judge.py first.")

    gold_dist = Counter(c["label"] for c in claims)
    by_variant = defaultdict(Counter)
    for c in claims:
        by_variant[c.get("variant", "?")][c["label"]] += 1

    sections = [
        "# Results — judge vs human gold",
        "",
        f"Gold set: {len(claims)} claims; label distribution: "
        + ", ".join(f"{k} {v}" for k, v in sorted(gold_dist.items())),
        "By variant: "
        + "; ".join(
            f"{v}: " + ", ".join(f"{k} {n}" for k, n in sorted(cnt.items()))
            for v, cnt in sorted(by_variant.items())
        ),
        "",
    ]
    for path in judgment_files:
        section, stats = score_judge(claims, path)
        sections.append(section)
        print(f"{stats['alias']}: binary kappa {stats['kappa_binary']:.3f}, "
              f"agreement {stats['agree_binary']:.1%} "
              f"[{stats['agree_binary_ci'][0]:.1%}, {stats['agree_binary_ci'][1]:.1%}], "
              f"unsupported recall "
              f"{stats['per_class_binary']['unsupported']['recall']:.1%}")

    EVALS_DIR.mkdir(exist_ok=True)
    out = EVALS_DIR / "results.md"
    out.write_text("\n".join(sections), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
