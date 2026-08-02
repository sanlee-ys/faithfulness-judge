"""Blind, pre-registered audit of the human gold set — ADR-002, Option D.

The gold set is one labeler's work and this repo's own rule is that it is not
above audit. But auditing labels *while looking at the claims the judges got
wrong* is how a gold set drifts toward its judges: correct enough of the shared
errors and kappa rises, and the rise measures the audit's motivation rather
than the judge. ADR-002's four-part guard exists to stop that, and this module
is its mechanism.

Two subcommands, deliberately separated:

``select``
    Applies the **pre-registered structural predicate** (``SELECTION_RULES``
    below, and ADR-002 "The pre-registered selection rule") to **every** claim
    in ``data/claims.yaml`` and writes a worksheet for the human adjudicator.
    This path **never opens** ``data/judgments_*.yaml`` — selection is a pure
    function of ``claim_text``, so the resulting set necessarily contains
    claims the judges scored correctly as well as ones they did not, and the
    adjudicator cannot tell which is which. That is what makes it blind.
    Enforced by ``tests/test_gold_audit.py``.

``rescore``
    Phase 2. Reads the filled worksheet **and** the committed judgment files,
    and reports kappa / raw agreement / unsupported recall three ways: under
    the original gold, under the fully audited gold, and under an audited gold
    where only the corrections landing on claims **no judge got wrong** are
    applied. The third view is the drift check — if the headline only moves in
    view 2 and not in view 3, the correction tracked the judges, and the number
    should not be published as a gold-quality improvement.

Neither subcommand calls an API, and neither re-runs a judge: judging is a
committed artifact (see CLAUDE.md, "Don't re-run the judges"). ``rescore``
writes nothing by default — it prints. Applying audited labels back into
``data/claims.yaml`` is a separate, deliberate act.

Run (offline, no API key):

    uv run python src/gold_audit.py select      # -> data/gold-audit-worksheet.md
    uv run python src/gold_audit.py rescore     # after the worksheet is filled
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dataset  # noqa: E402  (path shim must run first)
from dataset import load_questions  # noqa: E402
from labels import NORMALIZE  # noqa: E402
from paired_compare import mcnemar_exact  # noqa: E402
from score import BINARY, TERNARY, cohens_kappa, collapse, per_class, wilson_ci  # noqa: E402

WORKSHEET_PATH = dataset.DATA_DIR / "gold-audit-worksheet.md"

#: Claims at or below this many whitespace-separated tokens are treated as
#: possible non-self-contained fragments of the frozen split (rule S1).
SHORT_CLAIM_MAX_WORDS = 8

# The parse target on each claim's fill-in line. `?` is the unfilled sentinel.
_AUDIT_LINE = re.compile(r"^\s*AUDIT\s+(\S+)\s*=\s*(\S*)\s*$", re.MULTILINE)
_UNFILLED = "?"


@dataclass(frozen=True)
class SelectionRule:
    """One pre-registered structural predicate over a claim's text.

    Structural means: it reads ``claim_text`` and nothing else. Not the gold
    label, not a judge verdict, not whether anything disagreed about it.
    """

    name: str
    description: str
    matches: Callable[[str], bool]


def _matches_any(pattern: str) -> Callable[[str], bool]:
    """Build a case-insensitive regex predicate over a claim's text."""
    compiled = re.compile(pattern, re.IGNORECASE)
    return lambda text: compiled.search(text) is not None


# ---------------------------------------------------------------------------
# THE PRE-REGISTERED SELECTION RULE.
#
# Committed before the candidate set existed (ADR-002; see the PR's commit
# order). Written from ADR-002's guard item 1 and the canonical `na` shapes in
# docs/labeling-guide.md, then executed once over all 193 claims. No pattern
# was added, removed, or tightened after seeing which claims it selected, and
# no judge verdict was consulted at any point.
#
# A claim is selected iff it matches AT LEAST ONE rule below.
# ---------------------------------------------------------------------------
SELECTION_RULES: tuple[SelectionRule, ...] = (
    SelectionRule(
        name="S1-short-fragment",
        description=(
            f"{SHORT_CLAIM_MAX_WORDS} words or fewer. The frozen splitter "
            "(SCOPE.md Decision 2) emits list items and sentence fragments as "
            "standalone claims; below this length a claim is often not "
            "self-contained, and a claim that cannot be evaluated in isolation "
            "is a decomposition artifact rather than a judgeable assertion."
        ),
        matches=lambda text: len(text.split()) <= SHORT_CLAIM_MAX_WORDS,
    ),
    SelectionRule(
        name="S2-list-header",
        description=(
            "Ends with a colon. A colon-terminated header introduces a list "
            "rather than asserting anything on its own, so the rubric's "
            "'not a factual claim' test should resolve the same way for every "
            "instance of the shape."
        ),
        matches=lambda text: text.rstrip().endswith(":"),
    ),
    SelectionRule(
        name="S3-offer-to-help",
        description=(
            "Offers further assistance or asks the reader for more input — "
            "the 'I'd be happy to help' shape docs/labeling-guide.md names as "
            "canonical `na`."
        ),
        matches=_matches_any(
            r"\b(?:happy to help"
            r"|glad to help"
            r"|i can help|i could help|i can assist|i can answer"
            r"|i'd be (?:happy|glad)|i would be (?:happy|glad)"
            r"|let me know"
            r"|feel free to"
            r"|if you (?:have|can provide|can share|provide|share))\b"
        ),
    ),
    SelectionRule(
        name="S4-external-referral",
        description=(
            "Directs the reader to material outside the excerpt — the "
            "'you may want to check the original source' shape "
            "docs/labeling-guide.md names as canonical `na`."
        ),
        matches=_matches_any(
            r"\b(?:you (?:may|might|would|will|should) (?:want|need) to"
            r"|original source|source document"
            r"|additional (?:source|report|document|information|context|text)"
            r"|other sources?|further (?:sources?|reading|documentation)"
            r"|(?:consult|refer to|review|check) "
            r"(?:the )?(?:original|additional|other|further|primary|source|full))\b"
        ),
    ),
)


# ---------------------------------------------------------------------------
# 1. Selection — claim text in, claim ids out. No verdicts, ever.
# ---------------------------------------------------------------------------


def rules_firing(claim_text: str) -> list[str]:
    """Names of every selection rule this claim's text matches, in rule order.

    Args:
        claim_text: The claim as frozen by the splitter.

    Returns:
        Matching rule names; empty when the claim is not selected.
    """
    return [rule.name for rule in SELECTION_RULES if rule.matches(claim_text)]


def select_claims(claims: Iterable[Mapping[str, object]]) -> list[dict]:
    """Apply the pre-registered predicate to every claim, in file order.

    Deliberately takes the whole claim set, not a filtered one: the predicate
    is applied to all 193 gold claims (the 189 scored plus the 4 already
    labeled ``na``). Auditing only the scored 189 would let labels move *into*
    ``na`` but never out of it, which can only shrink *n* — a directional bias.
    ADR-002 Finding 4's colon-header inconsistency spans both sides of that
    line, so both sides have to be in view.

    Args:
        claims: Claim records from ``data/claims.yaml``.

    Returns:
        One dict per selected claim: the original record plus ``rules``, the
        list of rule names that fired. Order follows ``claims.yaml``.
    """
    selected = []
    for claim in claims:
        fired = rules_firing(str(claim["claim_text"]))
        if fired:
            selected.append({**dict(claim), "rules": fired})
    return selected


# ---------------------------------------------------------------------------
# 2. The worksheet — the instrument San fills in.
# ---------------------------------------------------------------------------

_HEADER = """# Gold-set audit worksheet — ADR-002, Option D (phase 1)

**What this is.** A blind consistency audit of this repo's human gold labels.
The claims below were picked by a **structural** rule that was written and
committed *before* this file was generated: it reads each claim's text and
nothing else. It was applied to all 193 gold claims.

**This file deliberately tells you nothing about how any model labeled these
claims.** No verdicts, no agreement flags, no marking of which claims were
contested. That is the point: a gold set audited toward its judges stops being
ground truth, and the resulting number would be exactly the soft-number-dressed-
as-solid failure this project exists to catch. If you find yourself trying to
recall what the models said about a claim, that instinct is the thing the blind
design is protecting against.

**This is a correctness pass, not a tuning pass.** For each claim ask only:
*does the rubric, applied to this excerpt, give this label?* If it does, keep
the label. Changing a label because a different one "feels better" is drift.
Most rows should come back unchanged.

## How to fill it in

Replace the `?` on each `AUDIT` line with one letter. **Every line must be
filled**, including the ones you are confirming — a blank is indistinguishable
from a skip, so the re-score refuses to run until all of them carry a letter.

| Letter | Label | Rule |
| --- | --- | --- |
| `s` | supported | Every part of the claim is stated in, or unambiguously entailed by, the excerpt. |
| `p` | partial | Mixed — part grounded, part adds specifics the excerpt doesn't contain; or directionally right but overstated. |
| `u` | unsupported | Asserts something the excerpt doesn't support — fabricated fact, wrong value, false premise. Contradictions count here. |
| `n` | na | Not a factual claim (filler, meta-aside, an offer to help). Excluded from scoring. |

The three consistency calls, unchanged from
[docs/labeling-guide.md](labeling-guide.md):

1. **A correct refusal is `supported`.** *"The passage doesn't state the cost"* —
   when it indeed doesn't — is a true statement about the passage. Only `u` if
   it claims something is absent that is actually in the excerpt.
2. **World-true but excerpt-absent is `unsupported`.** The model knowing the
   real answer does not make the answer grounded.
3. **Filler / meta is `na`.** No factual assertion to grade.

Binary kappa collapses `partial` into `unsupported` and drops `na`, so a
`p`-vs-`u` coin flip does not move the headline. Label your honest read.

When every line is filled:

```
uv run python src/gold_audit.py rescore
```

That re-scores offline against the committed judgments — no API calls, no judge
re-runs — and reports the corrected numbers *both* ways, including the view
restricted to claims no judge got wrong, so any drift toward the judges is
visible rather than buried.
"""


def _wrap_context(text: str, width: int = 88) -> str:
    """Collapse a block-scalar excerpt to one paragraph, wrapped for reading."""
    import textwrap

    return textwrap.fill(" ".join(text.split()), width=width)


def build_worksheet(
    selected: Sequence[Mapping[str, object]],
    questions: Sequence[dataset.Question],
) -> str:
    """Render the blind worksheet as markdown.

    Markdown rather than the CSV route ``labels.py`` uses for the full gold
    pass: at ~30 claims spreadsheet ergonomics stop paying, the context
    excerpts are multi-sentence paragraphs that a CSV cell renders unreadable,
    the instruction header and rubric have to travel *with* the worksheet
    (a CSV cannot carry them), and grouping by context lets the adjudicator
    hold one excerpt in mind at a time — the labeling guide's own advice.

    Args:
        selected: Output of ``select_claims``.
        questions: Loaded question records, for the excerpt and question text.

    Returns:
        The complete worksheet document.
    """
    qmap = {q.id: q for q in questions}
    rule_desc = "\n".join(
        f"- **{rule.name}** — {rule.description}" for rule in SELECTION_RULES
    )
    fired = Counter(name for c in selected for name in c["rules"])
    tally = ", ".join(f"{name} {fired[name]}" for name in sorted(fired))

    lines = [
        _HEADER,
        "## The pre-registered selection rule",
        "",
        "A claim is selected if it matches **at least one** of:",
        "",
        rule_desc,
        "",
        f"Applied to all 193 gold claims, this selected **{len(selected)}**. "
        f"Rules firing: {tally} (a claim may match more than one).",
        "",
        "---",
        "",
        f"## The {len(selected)} claims",
        "",
    ]

    last_context = None
    for claim in selected:
        question = qmap.get(str(claim["question_id"]))
        context_id = str(claim["context_id"])
        if context_id != last_context:
            last_context = context_id
            lines += [
                f"### Context `{context_id}`",
                "",
                _wrap_context(question.context_text) if question else "_(no context)_",
                "",
            ]
        if question:
            lines += [f"**Q ({claim['question_id']}):** {question.question}", ""]
        lines += [
            f"#### `{claim['claim_id']}`",
            "",
            f"> {claim['claim_text']}",
            "",
            f"- selected by: {', '.join(str(r) for r in claim['rules'])}",
            f"- current label: **{claim['label']}**",
            "",
            "```",
            f"AUDIT {claim['claim_id']} = {_UNFILLED}",
            "```",
            "",
        ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 3. Parsing the filled worksheet.
# ---------------------------------------------------------------------------


def parse_worksheet(text: str, expected_ids: Sequence[str] | None = None) -> dict:
    """Read the adjudications back out of a filled worksheet.

    Fails loudly rather than partially: an unfilled line, an unknown letter, a
    duplicate id, or (when ``expected_ids`` is given) a missing or unexpected
    id all raise. A half-parsed audit silently scored is the same class of
    error as scoring against a partial gold.

    Args:
        text: The worksheet document.
        expected_ids: Claim ids the worksheet is required to cover exactly.

    Returns:
        ``{claim_id: label}`` with labels normalized to the full words.

    Raises:
        ValueError: On any unfilled, malformed, duplicated, missing, or
            unexpected entry.
    """
    found: dict[str, str] = {}
    unfilled: list[str] = []
    invalid: list[tuple[str, str]] = []
    duplicated: list[str] = []

    for claim_id, raw in _AUDIT_LINE.findall(text):
        if claim_id in found or claim_id in duplicated:
            duplicated.append(claim_id)
            continue
        value = raw.strip().lower()
        if value in ("", _UNFILLED):
            unfilled.append(claim_id)
            continue
        if value not in NORMALIZE:
            invalid.append((claim_id, raw))
            continue
        found[claim_id] = NORMALIZE[value]

    problems = []
    if unfilled:
        problems.append(f"{len(unfilled)} still unfilled: {', '.join(unfilled)}")
    if invalid:
        listing = ", ".join(f"{cid}={raw!r}" for cid, raw in invalid)
        problems.append(f"invalid labels (use s/p/u/n): {listing}")
    if duplicated:
        problems.append(f"duplicate AUDIT lines: {', '.join(sorted(set(duplicated)))}")
    if expected_ids is not None:
        expected = set(expected_ids)
        seen = set(found) | set(unfilled) | {cid for cid, _ in invalid}
        missing = sorted(expected - seen)
        extra = sorted(seen - expected)
        if missing:
            problems.append(f"missing from the worksheet: {', '.join(missing)}")
        if extra:
            problems.append(f"not in the selected set: {', '.join(extra)}")
    if problems:
        raise ValueError("worksheet is not ready to score:\n  - " + "\n  - ".join(problems))
    return found


# ---------------------------------------------------------------------------
# 4. Re-scoring — offline, three views.
# ---------------------------------------------------------------------------


def _verdicts(payload: Mapping) -> tuple[str, dict[str, str]]:
    """Pull ``(judge_alias, {claim_id: verdict})`` out of a judgments payload."""
    return (
        payload["meta"]["judge_alias"],
        {j["claim_id"]: j["judge_label"] for j in payload["judgments"]},
    )


def judge_correct(gold: str, verdict: str | None) -> bool:
    """Binary correctness, using ``score.py``'s published conventions.

    A missing or unrecognized verdict is **wrong**, not excused — the
    convention that made the ADR-001 truncation bug visible.
    """
    if verdict is None or verdict not in TERNARY:
        return False
    return collapse(verdict) == collapse(gold)


def stats_for(
    claims: Sequence[Mapping],
    gold: Mapping[str, str],
    verdicts: Mapping[str, str],
) -> dict:
    """Score one judge against one gold mapping, mirroring ``score.score_judge``.

    Args:
        claims: Claim records (for ids and ordering).
        gold: ``{claim_id: label}`` — the effective gold for this view.
        verdicts: ``{claim_id: judge_label}``.

    Returns:
        ``n``, binary/ternary kappa, raw binary agreement and its Wilson CI,
        and recall on the binary ``unsupported`` class.
    """
    pairs_t = []
    for claim in claims:
        label = gold.get(str(claim["claim_id"]))
        if label in (None, "na"):
            continue
        verdict = verdicts.get(str(claim["claim_id"]))
        pairs_t.append((label, verdict if verdict in TERNARY else "__unparsed__"))
    pairs_b = [(collapse(g), collapse(j) if j in TERNARY else j) for g, j in pairs_t]
    n = len(pairs_t)
    agree_b = sum(1 for g, j in pairs_b if g == j)
    return {
        "n": n,
        "kappa_binary": cohens_kappa(pairs_b, BINARY),
        "kappa_ternary": cohens_kappa(pairs_t, TERNARY),
        "agree_binary": agree_b / n if n else float("nan"),
        "agree_binary_ci": wilson_ci(agree_b, n),
        "unsupported_recall": per_class(pairs_b, BINARY)["unsupported"]["recall"],
    }


def paired_p(
    claims: Sequence[Mapping],
    gold: Mapping[str, str],
    a_verdicts: Mapping[str, str],
    b_verdicts: Mapping[str, str],
) -> tuple[int, int, float]:
    """Discordant counts and exact McNemar p between two judges under one gold."""
    a_only = b_only = 0
    for claim in claims:
        cid = str(claim["claim_id"])
        label = gold.get(cid)
        if label in (None, "na"):
            continue
        a_right = judge_correct(label, a_verdicts.get(cid))
        b_right = judge_correct(label, b_verdicts.get(cid))
        if a_right and not b_right:
            a_only += 1
        elif b_right and not a_right:
            b_only += 1
    return a_only, b_only, mcnemar_exact(a_only, b_only)


def audit_views(
    claims: Sequence[Mapping],
    adjudications: Mapping[str, str],
    judgment_payloads: Sequence[Mapping],
) -> dict:
    """Build the three gold views and the change/judge-error overlap accounting.

    Judge errors are computed under the **original** gold — the state the
    audit was blind to — so "claims no judge got wrong" means what it meant
    before any label moved.

    Args:
        claims: Claim records from ``data/claims.yaml``.
        adjudications: ``{claim_id: label}`` from the filled worksheet.
        judgment_payloads: Parsed ``data/judgments_*.yaml`` payloads.

    Returns:
        ``golds`` (three ``{claim_id: label}`` mappings), ``changed`` (the ids
        whose label moved), and ``overlap`` (how many changes landed on claims
        both / exactly one / neither judge got wrong).
    """
    original = {str(c["claim_id"]): c["label"] for c in claims}
    changed = {
        cid: label
        for cid, label in adjudications.items()
        if cid in original and original[cid] != label
    }

    arms = [_verdicts(p) for p in judgment_payloads]
    n_wrong: dict[str, int] = {}
    for cid, label in original.items():
        if label in (None, "na"):
            n_wrong[cid] = 0
            continue
        n_wrong[cid] = sum(
            0 if judge_correct(label, verdicts.get(cid)) else 1 for _, verdicts in arms
        )

    fully_audited = {**original, **changed}
    # Guard item 3: applying only the corrections that land where every judge
    # was already right isolates the part of the audit that cannot mechanically
    # flatter the judges. If the headline moves in `fully_audited` but not
    # here, the correction tracked the judges.
    no_judge_error_only = {
        **original,
        **{cid: label for cid, label in changed.items() if n_wrong.get(cid, 0) == 0},
    }

    overlap = Counter()
    for cid in changed:
        wrong = n_wrong.get(cid, 0)
        if wrong == 0:
            overlap["neither judge wrong"] += 1
        elif wrong == len(arms):
            overlap["both judges wrong"] += 1
        else:
            overlap["exactly one judge wrong"] += 1

    return {
        "golds": {
            "original gold (published baseline)": original,
            "fully audited gold": fully_audited,
            "audited, corrections on no-judge-error claims only": no_judge_error_only,
        },
        "changed": changed,
        "original": original,
        "overlap": overlap,
        "n_arms": len(arms),
    }


def build_rescore_report(
    claims: Sequence[Mapping],
    adjudications: Mapping[str, str],
    judgment_payloads: Sequence[Mapping],
) -> str:
    """Format the phase-2 re-score: three gold views, both judges, plus overlap."""
    views = audit_views(claims, adjudications, judgment_payloads)
    arms = [_verdicts(p) for p in judgment_payloads]
    changed = views["changed"]
    original = views["original"]

    lines = [
        "=" * 78,
        "GOLD AUDIT RE-SCORE -- ADR-002 Option D, phase 2 (offline; no judge re-run)",
        "=" * 78,
        "",
        f"Adjudicated : {len(adjudications)} claims",
        f"Changed     : {len(changed)}",
        f"Confirmed   : {len(adjudications) - len(changed)}",
        "",
    ]
    if changed:
        lines.append("Changes:")
        for cid in sorted(changed):
            lines.append(f"  {cid:20s} {original.get(cid)} -> {changed[cid]}")
        lines.append("")

    lines += [
        "-" * 78,
        "OVERLAP WITH JUDGE ERRORS (ADR-002 guard, item 3)",
        "-" * 78,
        "Judge errors are counted under the ORIGINAL gold -- the state the audit",
        "was blind to. A correction concentrated on claims the judges got wrong is",
        "the drift signature; corrections spread across both is what a genuine",
        "gold defect looks like.",
        "",
    ]
    for bucket in ("both judges wrong", "exactly one judge wrong", "neither judge wrong"):
        lines.append(f"  changed, {bucket:24s}: {views['overlap'].get(bucket, 0)}")
    lines.append("")

    for view_name, gold in views["golds"].items():
        lines += ["-" * 78, view_name.upper(), "-" * 78, ""]
        for alias, verdicts in arms:
            s = stats_for(claims, gold, verdicts)
            lo, hi = s["agree_binary_ci"]
            lines += [
                f"  {alias}",
                f"    n scored          : {s['n']}",
                f"    binary kappa      : {s['kappa_binary']:.3f}",
                f"    raw agreement     : {s['agree_binary']:.1%} "
                f"[95% CI {lo:.1%}, {hi:.1%}]",
                f"    ternary kappa     : {s['kappa_ternary']:.3f}",
                f"    unsupported recall: {s['unsupported_recall']:.1%}",
            ]
        if len(arms) == 2:
            (a_alias, a_v), (b_alias, b_v) = arms
            a_only, b_only, p = paired_p(claims, gold, a_v, b_v)
            lines += [
                "",
                f"  paired ({a_alias} vs {b_alias}, binary correctness):",
                f"    {a_alias} right / {b_alias} wrong: {a_only}",
                f"    {b_alias} right / {a_alias} wrong: {b_only}",
                f"    McNemar exact p = {p:.4f}",
            ]
        lines.append("")

    lines += [
        "=" * 78,
        "READ THIS BEFORE PUBLISHING ANY NUMBER ABOVE",
        "=" * 78,
        "This is a single-labeler consistency audit. It is NOT inter-annotator",
        "agreement, and the 'one labeler, no IAA measured' limit survives it intact",
        "(ADR-002 guard, item 4). If the corrected kappa rises in the fully-audited",
        "view but not in the no-judge-error view, the audit tracked the judges and",
        "the rise is not a gold-quality result.",
        "=" * 78,
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------


def cmd_select(args: argparse.Namespace) -> int:
    """Write the blind worksheet. Never touches data/judgments_*.yaml."""
    claims = dataset.load_yaml(args.claims)["claims"]
    selected = select_claims(claims)
    if not selected:
        sys.exit("the selection rule matched no claims — check SELECTION_RULES")
    args.out.write_text(
        build_worksheet(selected, load_questions()), encoding="utf-8"
    )
    fired = Counter(name for c in selected for name in c["rules"])
    print(f"selected {len(selected)} of {len(claims)} claims -> {args.out}")
    for name in sorted(fired):
        print(f"  {name:22s} {fired[name]}")
    print("\nFill every `AUDIT <id> = ?` line with s / p / u / n, then:")
    print("  uv run python src/gold_audit.py rescore")
    return 0


def cmd_rescore(args: argparse.Namespace) -> int:
    """Re-score offline against the filled worksheet."""
    if not args.worksheet.exists():
        sys.exit(f"{args.worksheet} not found — run `gold_audit.py select` first.")
    claims = dataset.load_yaml(args.claims)["claims"]
    expected = [c["claim_id"] for c in select_claims(claims)]
    try:
        adjudications = parse_worksheet(
            args.worksheet.read_text(encoding="utf-8"), expected_ids=expected
        )
    except ValueError as exc:
        sys.exit(str(exc))

    judgment_files = sorted(dataset.DATA_DIR.glob("judgments_*.yaml"))
    if not judgment_files:
        sys.exit("no data/judgments_*.yaml found — nothing to re-score against.")
    payloads = [dataset.load_yaml(p) for p in judgment_files]

    report = build_rescore_report(claims, adjudications, payloads)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
        print(f"wrote {args.out}\n")
    print(report)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sel = sub.add_parser("select", help="write the blind audit worksheet")
    sel.add_argument("--claims", type=Path, default=dataset.CLAIMS_PATH)
    sel.add_argument("--out", type=Path, default=WORKSHEET_PATH)
    sel.set_defaults(func=cmd_select)

    res = sub.add_parser("rescore", help="re-score offline from a filled worksheet")
    res.add_argument("--claims", type=Path, default=dataset.CLAIMS_PATH)
    res.add_argument("--worksheet", type=Path, default=WORKSHEET_PATH)
    res.add_argument("--out", type=Path, help="also write the report here")
    res.set_defaults(func=cmd_rescore)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
