"""Assert the eval figures restated in README.md and CLAUDE.md against evals/results.md.

WHY THIS EXISTS. `CLAUDE.md` carries a standing rule: "if evals/results.md disagrees
with the numbers in the README or ADR-001, something was re-run: reconcile before
writing anything." ADR-003 mechanized half of it — CI regenerates `evals/results.md`
and fails if the committed artifact is not exactly what `src/score.py` produces. That
half is *artifact vs code*. This script is the other half, *claim vs artifact*: the
README and CLAUDE.md restate kappa, agreement, CI bounds, recall and gold-set counts,
and until now nothing checked that those restatements still matched.

This is a `SYS-019` concern — what may be *claimed* about a measurement — not a
`SYS-017` one. **Nothing here gates on a value.** Kappa is free to move; the figures
written down about it just have to move with it. There is no floor and no threshold.

HOW A FIGURE OPTS IN. Precede it with an invisible marker — the same convention
`learning-notes/scripts/check_published_metrics.py` and the architecture repo's
`check_program_metrics.py` use, so one habit covers every repo:

    | **Opus** | <!-- figure:opus_binary_kappa -->**0.751** | ...

The key names are derived from `evals/results.md` itself (see `parse_artifact`), so a
new judge alias produces `<alias>_*` keys automatically and the checker cannot drift
from the artifact it protects. Nothing is hardcoded here but the artifact's *layout*.

WHERE A MARKER MAY GO. Anywhere except the start of a line. In CommonMark/GFM a line
beginning with `<!--` opens an *HTML block*: it closes the paragraph above it and
suspends inline markdown parsing until the next blank line. A line-initial marker
therefore splits a paragraph on the rendered page and leaves `code` spans showing as
literal backticks — while the source looks fine and this checker reports a clean pass.
It shipped that way once (ADR-004, corrected same day). A marker must always follow
text on its line; wrap the prose around it rather than onto the next line.

THAT ONE RULE IS SWEPT OVER EVERY MARKDOWN FILE, AND THE REST ARE NOT. `DOCUMENTS` is
deliberately two files, and stays two: `decisions/` is excluded because an ADR is a
*dated record* of what was true when it was written, and `SYS-009`'s guarantee-vs-
observation rule says such a document must not be re-synced to today's numbers.
Widening the *value* check to it would manufacture exactly the pressure to rewrite
history that the exclusion exists to prevent.

The placement rule is a different kind of question, and the difference is the whole
argument for splitting it out:

  - The value, unknown-key, exempt-block and unmarked-figure rules ask "is this number
    still current?" That is only meaningful for a present-tense claim. Correctly narrow.
  - Placement asks "does this file render correctly?" A line-initial marker breaks the
    page whether the figure beside it is live, historical or exempt. Correctly universal.

So `sweep_paths` walks every `.md` in the tree and applies the placement rule alone.
Nothing it finds can pressure anyone to restate a number; the fix is always to move a
marker onto the end of the previous line. `decisions/004-assert-published-figures.md`
carries a line-initial marker today — inside a fenced block, where it is documenting
this very convention, which is legal and stays legal because code is skipped.

HOW A FIGURE OPTS OUT. Some published numbers are deliberately not current. Three
kinds have turned up so far, which is the argument for a *reason* over a *category*:

  - A record of an event. `README.md` says a 2026-07-19 re-scoring "moved Opus kappa
    0.742 -> 0.751", and that the 2026-08-02 audit moved Opus 0.751 -> 0.762. Those
    stay as written however far kappa moves afterwards — and note the pre-audit 0.751
    now sits one line from the live 0.762.
  - A view from a different harness. The drift-restricted 0.752 comes from
    `gold_audit.py rescore`, which reports three gold views; `score.py` scores one.
  - A statistic `score.py` never computes. Every McNemar p (0.125, 0.508) is from
    ADR-001/ADR-002, and the judge-vs-judge agreement 95.8% compares the two judges to
    each other rather than to the human gold.

All are wrapped in a block that names the reason (shown here split for legibility —
in real prose neither marker may begin its line):

    ... In July, <!-- figure-exempt: why this is not current -->kappa moved
    0.742 -> 0.751<!-- /figure-exempt -->, and ...

One form, not two (no inline variant), because an exemption is a claim about a
*region of prose* — "this passage is history" — and a block is what says that. The
reason is mandatory: an unexplained exemption is indistinguishable from a mistake.

An exempt block exempts its contents from the unmarked-figure scan below and nothing
else. A `figure:` marker inside one is still checked — the two mechanisms answer
different questions ("is this number accounted for?" vs "does it match?").

THE UNMARKED-FIGURE SCAN. Opt-in marking alone leaves a hole the sibling checks live
with and this repo should not: a figure added later, unmarked, is never checked and
reads as covered. So every token shaped like one of this artifact's figures — a
three-decimal kappa (`0.751`) or a one-decimal percentage (`89.4%`) — must be either
marked or inside an exempt block. This is a narrow net on purpose. It does **not**
catch bare counts (`189`, `48`) or approximations (`kappa ~ 0.72-0.75`, `~89%`); those
are marked where they are exact restatements and otherwise stay a human's job.

FAILURE POLICY (matches the sibling checks):
  - marked value mismatches artifact -> exit 1
  - unknown figure key               -> exit 1, a typo checks nothing and passes forever
  - unmarked figure-shaped token     -> exit 1, mark it or exempt it with a reason
  - marker at the start of a line    -> exit 1, it silently breaks the rendered page.
                                        This one is checked in every markdown file in
                                        the repo, not just in DOCUMENTS.
  - exempt block with no reason,
    or an unbalanced block           -> exit 1
  - zero marked figures              -> exit 1, a check verifying nothing reads as a pass
  - artifact missing or unparseable  -> exit 1. Unlike the sibling checks, the artifact
                                        here is a committed local file, not a network
                                        fetch: absence is a repo defect, not an outage.

Run locally:
    uv run python scripts/check_published_figures.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_PATH = REPO_ROOT / "evals" / "results.md"
DOCUMENTS = ("README.md", "CLAUDE.md")

# Directories the placement sweep does not own. `.claude` is load-bearing rather than
# tidiness: it holds agent worktrees, which are entire second checkouts of this repo, so
# walking it would report every finding twice under a path nobody edits. The rest are
# version control, virtual environments, tool caches and vendored trees; `node_modules`
# is listed although nothing here creates one, so the set does not have to be
# rediscovered if something ever does. Same shape as the architecture repo's decision-log
# sweep, which walks the whole tree for the same reason.
SWEEP_SKIP_DIRS = frozenset(
    {
        ".git",
        ".claude",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "site",
    }
)

# The value must both start and end alphanumeric, so a figure that ends a sentence
# ("kappa is 0.751.") does not capture the full stop and compare unequal forever.
MARKER = re.compile(
    r"<!--\s*figure:([A-Za-z0-9_]+)\s*-->\s*\**\s*"
    r"([0-9A-Za-z](?:[0-9A-Za-z.\-]*[0-9A-Za-z])?%?)"
)
EXEMPT_OPEN = re.compile(r"<!--\s*figure-exempt:(.*?)-->", re.S)
EXEMPT_CLOSE = re.compile(r"<!--\s*/figure-exempt\s*-->")

# Deliberately narrow: the two shapes score.py renders that are unmistakably eval
# figures. Widening this to bare integers would flag every "40 questions" in the
# prose and force an exemption list longer than the marker list.
FIGURE_SHAPED = re.compile(r"\b0\.\d{3}\b|\b\d{1,3}\.\d%")

# A marker must never be the first thing on its line. In CommonMark/GFM a line
# beginning with "<!--" opens an *HTML block*, which closes the paragraph above it
# and suspends markdown parsing until a blank line — so a line-initial marker
# silently splits a paragraph and leaves `backticks` rendering literally. The
# markers are supposed to be invisible; this is the one placement where they are
# not, and it is invisible in the source, so it gets a rule rather than a habit.
#
# This is also the one rule swept over every markdown file in the repo rather than over
# DOCUMENTS alone — see "THAT ONE RULE IS SWEPT..." above for why the others are not.
LINE_INITIAL_MARKER = re.compile(r"^[ \t]*(<!--\s*/?\s*figure)", re.M)

# Markdown code, fenced or inline. Everything inside is invisible to this check.
# CLAUDE.md documents this very convention, and documenting a marker must not *be*
# one — otherwise the example block would register as a real (reasonless) exemption.
# The same applies to figures quoted inside a shell transcript: a code sample is not
# a published claim.
_CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)

TERNARY = ("supported", "partial", "unsupported")
BINARY_UNSUPPORTED = ("partial", "unsupported")

_GOLD_LINE = re.compile(r"^Gold set: (\d+) claims; label distribution: (.+)$", re.M)
_JUDGE_HEADING = re.compile(r"^## Judge: (\S+) \((\S+)\)\s*$", re.M)
_N_SCORED = re.compile(
    r"^- n scored: \*\*(\d+)\*\* \(na excluded; (\d+) unparsed", re.M
)
_BINARY_LINE = re.compile(
    r"^- \*\*Binary kappa \(headline\): ([\d.]+)\*\*.* raw agreement "
    r"([\d.]+%) \[95% CI ([\d.]+%), ([\d.]+%)\]",
    re.M,
)
_TERNARY_LINE = re.compile(
    r"^- Ternary kappa: ([\d.]+).* raw agreement ([\d.]+%)", re.M
)
_CLASS_ROW = re.compile(r"^\| (\w+) \| ([\d.]+%) \| ([\d.]+%) \| (\d+) \|$", re.M)
_CONFUSION = re.compile(
    r"Ternary confusion \(rows = human gold\):\n```\n(.*?)\n```", re.S
)


class ArtifactError(RuntimeError):
    """evals/results.md could not be parsed into the figures it publishes."""


def _parse_confusion(block: str) -> dict[str, dict[str, int]]:
    """Parse score.py's fixed-width ternary confusion block into rows[gold][judge]."""
    lines = [ln for ln in block.splitlines() if ln.strip()]
    if len(lines) != len(TERNARY) + 1:
        raise ArtifactError(
            f"confusion block has {len(lines)} non-blank lines, expected "
            f"{len(TERNARY) + 1} (a header plus one row per ternary label)"
        )
    columns = lines[0].replace("(judge ->)", "").split()
    rows: dict[str, dict[str, int]] = {}
    for line in lines[1:]:
        parts = line.split()
        label, counts = parts[0], parts[1:]
        if len(counts) != len(columns):
            raise ArtifactError(
                f"confusion row '{label}' has {len(counts)} counts for "
                f"{len(columns)} columns"
            )
        rows[label] = {c: int(n) for c, n in zip(columns, counts, strict=True)}
    missing = [c for c in TERNARY if c not in rows or c not in columns]
    if missing:
        raise ArtifactError(f"confusion block is missing label(s): {missing}")
    return rows


def _search(pattern: re.Pattern[str], text: str, what: str) -> re.Match[str]:
    match = pattern.search(text)
    if match is None:
        raise ArtifactError(f"could not find {what}")
    return match


def parse_artifact(text: str) -> dict[str, str]:
    """Extract every figure evals/results.md publishes, keyed for the markers.

    Values are kept as the strings score.py rendered ('0.751', '89.4%', '48') so a
    marked figure is compared against exactly what the artifact says.
    """
    published: dict[str, str] = {}

    gold = _search(_GOLD_LINE, text, "the 'Gold set:' line")
    counts = {label: 0 for label in (*TERNARY, "na")}
    for part in gold.group(2).split(","):
        label, _, n = part.strip().rpartition(" ")
        counts[label] = int(n)
    published["gold_claims"] = gold.group(1)
    for label, n in counts.items():
        published[f"gold_{label}"] = str(n)

    # `na` is excluded from scoring, so this is the n every judge is scored over —
    # which is what the prose means by "n = 189 scored". Cross-checked below.
    scored = int(gold.group(1)) - counts["na"]
    published["gold_scored"] = str(scored)
    # SCOPE.md Decision 1 collapses partial into unsupported for the headline.
    binary_unsupported = counts["partial"] + counts["unsupported"]
    published["gold_binary_unsupported"] = str(binary_unsupported)

    headings = list(_JUDGE_HEADING.finditer(text))
    if not headings:
        raise ArtifactError("no '## Judge: <alias> (<model>)' sections found")

    unparsed_total = 0
    for i, heading in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        section = text[heading.start() : end]
        alias, model = heading.group(1), heading.group(2)
        published[f"{alias}_model"] = model

        n_scored = _search(_N_SCORED, section, f"the 'n scored' line for {alias}")
        published[f"{alias}_n_scored"] = n_scored.group(1)
        published[f"{alias}_unparsed"] = n_scored.group(2)
        unparsed_total += int(n_scored.group(2))
        if int(n_scored.group(1)) != scored:
            raise ArtifactError(
                f"{alias} is scored over n={n_scored.group(1)} but the gold set has "
                f"{scored} non-na claims — the artifact disagrees with itself"
            )

        binary = _search(_BINARY_LINE, section, f"the binary kappa line for {alias}")
        published[f"{alias}_binary_kappa"] = binary.group(1)
        published[f"{alias}_agreement"] = binary.group(2)
        published[f"{alias}_agreement_ci_low"] = binary.group(3)
        published[f"{alias}_agreement_ci_high"] = binary.group(4)

        ternary = _search(_TERNARY_LINE, section, f"the ternary kappa line for {alias}")
        published[f"{alias}_ternary_kappa"] = ternary.group(1)
        published[f"{alias}_ternary_agreement"] = ternary.group(2)

        rows = _CLASS_ROW.findall(section)
        if not rows:
            raise ArtifactError(f"no per-class table rows for {alias}")
        for cls, recall, precision, gold_n in rows:
            published[f"{alias}_{cls}_recall"] = recall
            published[f"{alias}_{cls}_precision"] = precision
            published[f"{alias}_{cls}_gold_n"] = gold_n
        unsupported_n = published.get(f"{alias}_unsupported_gold_n")
        if unsupported_n is not None and int(unsupported_n) != binary_unsupported:
            raise ArtifactError(
                f"{alias}'s binary unsupported class has gold n={unsupported_n} but "
                f"the gold distribution implies {binary_unsupported}"
            )

        confusion = _search(_CONFUSION, section, f"the confusion block for {alias}")
        counts_by_gold = _parse_confusion(confusion.group(1))
        # "47 vs 43 catches out of 48": gold binary-unsupported claims the judge also
        # called binary-unsupported. Taken from the confusion matrix rather than from
        # round(recall * n) so it does not depend on the displayed rounding.
        published[f"{alias}_unsupported_catches"] = str(
            sum(
                counts_by_gold[g][j]
                for g in BINARY_UNSUPPORTED
                for j in BINARY_UNSUPPORTED
            )
        )

    published["unparsed_total"] = str(unparsed_total)
    return published


def same_value(shown: str, published: str) -> bool:
    """Compare numerically where possible.

    The '%' is stripped from both sides: prose legitimately writes a CI bound as
    '84.2-93.0' where the artifact renders '84.2%'. Non-numeric values (model ids)
    fall back to an exact string compare.
    """
    try:
        return abs(float(shown.rstrip("%")) - float(published.rstrip("%"))) < 1e-9
    except ValueError:
        return shown.strip() == published.strip()


def _in_code(spans: list[tuple[int, int]], position: int) -> bool:
    return any(lo <= position < hi for lo, hi in spans)


def _exempt_spans(
    text: str, code: list[tuple[int, int]]
) -> tuple[list[tuple[int, int]], list[str]]:
    """Pair figure-exempt open/close markers into spans; report malformed blocks."""
    opens = [
        (m.start(), m.group(1))
        for m in EXEMPT_OPEN.finditer(text)
        if not _in_code(code, m.start())
    ]
    closes = [
        m.end() for m in EXEMPT_CLOSE.finditer(text) if not _in_code(code, m.start())
    ]
    problems: list[str] = []
    if len(opens) != len(closes):
        problems.append(
            f"{len(opens)} 'figure-exempt:' opener(s) but {len(closes)} "
            "'/figure-exempt' closer(s) - every block must be closed."
        )
    spans: list[tuple[int, int]] = []
    for (start, reason), close in zip(opens, closes, strict=False):
        if not reason.strip():
            problems.append(
                "a figure-exempt block gives no reason. Say why the figure is not "
                "current (history, or not produced by score.py)."
            )
        if close < start:
            problems.append("a '/figure-exempt' closer appears before its opener.")
            continue
        spans.append((start, close))
    return spans, problems


def placement_problems(name: str, text: str, code: list[tuple[int, int]]) -> list[str]:
    """Every marker in `text` that opens a markdown HTML block by starting its line.

    Line numbers are counted on `text` exactly as handed in — which must be the RAW
    file, never a code-stripped copy. Stripping a fenced block to nothing shifts every
    line after it, so the reported number points at the wrong place, and a confidently
    wrong line number is worse than none. Code is skipped by POSITION instead, via the
    `code` spans, which is why they are a parameter rather than recomputed here.
    """
    problems: list[str] = []
    for match in LINE_INITIAL_MARKER.finditer(text):
        if _in_code(code, match.start(1)):
            continue
        line = text.count("\n", 0, match.start(1)) + 1
        problems.append(
            f"{name}:{line}: a figure marker is the first thing on this line. "
            "That opens a markdown HTML block, which splits the paragraph and "
            "stops inline formatting until the next blank line. Move the marker "
            "onto the end of the previous line - it must always follow text."
        )
    return problems


def sweep_paths(root: Path, documents: tuple[str, ...] = DOCUMENTS) -> list[Path]:
    """Every markdown file under `root` that the value rules do not already cover.

    The complement of `documents`, not the whole tree, so a file checked by
    `check_documents` is not reported twice for the same misplaced marker. Union of the
    two is every `.md` in the repo, which is the coverage the placement rule claims.
    """
    already = {(root / name).resolve() for name in documents}
    found: list[Path] = []
    for path in root.rglob("*.md"):
        if not path.is_file():
            continue
        if SWEEP_SKIP_DIRS & set(path.relative_to(root).parts):
            continue
        if path.resolve() in already:
            continue
        found.append(path)
    return sorted(found)


def check_placement(root: Path, paths: list[Path]) -> list[str]:
    """Apply the placement rule — and only it — to every path in `paths`.

    Deliberately returns nothing but problems: this pass has no figures to count and no
    values to compare, because the question it asks ("does this file render?") does not
    depend on whether the number beside the marker is current.
    """
    problems: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        code = [m.span() for m in _CODE.finditer(text)]
        name = path.relative_to(root).as_posix()
        problems += placement_problems(name, text, code)
    return problems


def check_documents(
    documents: dict[str, str], published: dict[str, str]
) -> tuple[list[str], int, int]:
    """Check every marked figure and every unmarked figure-shaped token.

    Returns (problems, figures checked, exempt blocks seen).
    """
    problems: list[str] = []
    checked = 0
    exempt_blocks = 0
    known = ", ".join(sorted(published))

    for name, text in sorted(documents.items()):
        code = [m.span() for m in _CODE.finditer(text)]
        spans, span_problems = _exempt_spans(text, code)
        problems += [f"{name}: {p}" for p in span_problems]
        exempt_blocks += len(spans)

        problems += placement_problems(name, text, code)

        covered: list[tuple[int, int]] = []
        for match in MARKER.finditer(text):
            if _in_code(code, match.start()):
                continue
            key, shown = match.group(1), match.group(2)
            covered.append(match.span(2))
            if key not in published:
                problems.append(
                    f"{name}: figure key '{key}' is not published by "
                    f"evals/results.md. Known keys: {known}."
                )
                continue
            checked += 1
            if not same_value(shown, published[key]):
                problems.append(
                    f"{name}: '{key}' is written as {shown} but evals/results.md "
                    f"says {published[key]}. The artifact is the source of truth."
                )

        for figure in FIGURE_SHAPED.finditer(text):
            start, stop = figure.span()
            if any(lo <= start and stop <= hi for lo, hi in covered):
                continue
            if any(lo <= start < hi for lo, hi in spans):
                continue
            if _in_code(code, start):
                continue
            line = text.count("\n", 0, start) + 1
            problems.append(
                f"{name}:{line}: '{figure.group(0)}' looks like an eval figure but "
                "is neither marked with '<!-- figure:<key> -->' nor inside a "
                "'<!-- figure-exempt: ... -->' block. An unmarked figure is never "
                "checked and drifts silently."
            )

    return problems, checked, exempt_blocks


def run(artifact_path: Path, root: Path, documents: tuple[str, ...] = DOCUMENTS) -> int:
    """Check `documents` under `root` against the artifact. Returns an exit code."""
    try:
        artifact_text = artifact_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read {artifact_path}: {exc}", file=sys.stderr)
        return 1
    try:
        published = parse_artifact(artifact_text)
    except ArtifactError as exc:
        print(
            f"ERROR: {artifact_path} did not parse: {exc}\n"
            "This check reads its expected values out of the artifact, so a layout "
            "change in src/score.py lands here. Update the parser, do not silence it.",
            file=sys.stderr,
        )
        return 1

    texts: dict[str, str] = {}
    for name in documents:
        path = root / name
        if not path.is_file():
            print(f"ERROR: {path} does not exist.", file=sys.stderr)
            return 1
        texts[name] = path.read_text(encoding="utf-8")

    problems, checked, exempt_blocks = check_documents(texts, published)
    swept = sweep_paths(root, documents)
    problems += check_placement(root, swept)

    if problems:
        print("PUBLISHED FIGURES DO NOT MATCH evals/results.md:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}\n", file=sys.stderr)
        print(
            "evals/results.md is regenerated by src/score.py and asserted current by "
            "CI (ADR-003). If the numbers moved, reconcile the prose - do not edit "
            "the artifact to match the prose.",
            file=sys.stderr,
        )
        return 1

    if checked == 0:
        print(
            "No figure markers found. Either they were dropped or this check is "
            "inert - both are failures, because a check that verifies nothing reads "
            "as a pass.",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK - {checked} restated figure(s) in {', '.join(documents)} match "
        f"evals/results.md ({exempt_blocks} exempt block(s) skipped)."
    )
    # Say what each pass actually reached. A guard narrower than its claim surface reads
    # as full coverage unless it reports its own scope — the same property SYS-019 asks
    # of every check here, and the reason the value rules and the placement rule are
    # counted separately rather than summed into one reassuring number.
    print(
        f"     marker placement additionally checked in {len(swept)} further "
        f"markdown file(s); the value rules deliberately do not reach them."
    )
    return 0


def main() -> int:
    return run(ARTIFACT_PATH, REPO_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
