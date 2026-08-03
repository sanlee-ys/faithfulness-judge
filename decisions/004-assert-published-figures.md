# ADR-004: Assert the figures restated in README.md and CLAUDE.md against `evals/results.md`

**Status:** Accepted
**Date:** 2026-08-02
**Deciders:** San Lee

---

## Context

[ADR-003](003-score-in-ci.md) closed one half of a standing rule in `CLAUDE.md`:

> if `evals/results.md` disagrees with the numbers in the README or ADR-001, something was
> re-run: reconcile before writing anything

CI now regenerates `evals/results.md` with `src/score.py` and fails if the committed artifact
is not exactly what the code produces. That is **artifact vs code**. ADR-003 explicitly scoped
out the other half and named it correctly:

> The `README.md` and `CLAUDE.md` figures are still reconciled against `evals/results.md` **by
> hand**. SYS-017 names this separately and correctly as a `SYS-019` concern.

[`system/SYS-017`](https://github.com/sanlee-ys/architecture/blob/main/decisions/SYS-017-evals-as-ci.md)
calls it "a worthwhile move that is not on this ladder: the README's restated figures could be
asserted against `evals/results.md` (SYS-019 tier 1 or 2) today, which fixes a claim-drift risk
without touching CI's eval posture at all."

This is the larger of the two holes, and it is the one that matters most on **this** repo.
`README.md` and `CLAUDE.md` restate fourteen distinct figures between them — κ, raw agreement,
both Wilson bounds, unsupported recall, ternary κ, the gold-set class distribution, *n*, the
`47 vs 43 of 48` catch counts and both judge model ids. Every one was reconciled by a person
remembering to. The repo is **public**, and its entire thesis is that a soft number dressed as
a solid one is the failure mode worth catching; a README quoting a κ the artifact no longer
supports is that failure mode, in the shop window.

The timing is not incidental. [ADR-002](002-solid-tier-call.md) phase 2 — the blind gold audit
— moves labels, and therefore moves every figure above. A guard that is in place *before* the
figures move is worth more than one added after.

## Decision

**Add `scripts/check_published_figures.py`, run it in `tests.yml`, and require every restated
figure in `README.md` and `CLAUDE.md` to be either marked and matching, or explicitly exempted
with a reason.**

### 1. The expected values are parsed out of the artifact, never hardcoded

`parse_artifact()` reads `evals/results.md` and derives a key→value map from what `score.py`
actually wrote: the `Gold set:` line, each `## Judge: <alias> (<model>)` section, its kappa and
agreement lines, its per-class table and its ternary confusion block.

A checker holding its own copy of the numbers would be a third place for them to drift, which
is the problem rather than the fix. Because keys are derived from the artifact's own structure,
a third judge tier produces `haiku_*` keys with no edit here.

Two values are **derived** rather than read verbatim, because the prose quotes them and the
artifact does not print them:

- `gold_scored` = claims − `na`, which is what "n = 189 scored" means.
- `<alias>_unsupported_catches` = gold binary-unsupported claims the judge also called
  binary-unsupported, summed **out of the confusion matrix** — the `47 vs 43` in the README.
  Taken from the matrix rather than `round(recall × n)` so the figure does not depend on how
  `score.py` rounds a displayed percentage.

The parser also asserts the artifact agrees with itself — each judge's *n* must equal
claims − `na`, and each judge's binary-unsupported gold *n* must equal partial + unsupported —
and raises rather than returning a half-parsed map.

### 2. A figure opts in with an invisible marker

```
| **Opus** | <!-- figure:opus_binary_kappa -->**0.751** | ...
```

Same convention as `learning-notes/scripts/check_published_metrics.py` and the architecture
repo's `check_program_metrics.py`, so one habit covers every repo. HTML comments render as
nothing, so the published page is unchanged.

### 3. A figure opts out with a **block** that must give a reason

Some published numbers are deliberately not current, and asserting them would be wrong. There
turn out to be three kinds, which is itself an argument for a reason rather than a taxonomy:

- **Records of an event.** `README.md` says a 2026-07-19 re-scoring "moved Opus κ 0.742 →
  0.751 and Sonnet κ 0.696 → 0.716", and that the 2026-08-02 audit moved Opus 0.751 → 0.762.
  Those sentences stay true however far κ moves afterwards. The pre-audit `0.751` in
  particular sits one line from the live `0.762` — the same literal was the headline a day
  earlier.
- **Views produced by a different harness.** The drift-restricted `0.752` comes from
  `gold_audit.py rescore`, which reports three gold views. `score.py` scores one, so
  `evals/results.md` has no key for it.
- **Statistics `score.py` does not compute at all.** Every McNemar *p* (`0.125`, `0.508`) is
  from ADR-001/ADR-002, and the judge-vs-judge agreement `95.8%` compares the two judges to
  *each other* rather than to the human gold.

```
<!-- figure-exempt: why this is not a current figure --> ... <!-- /figure-exempt -->
```

**Why a block and not an ignore list.** An ignore list lives away from the prose it governs, so
it goes stale silently and it cannot say *which* `0.751` it means — and the historical sentence
above quotes the same literal value as the live table. The exemption has to sit on the text.

**Why one exempt marker and not a `historical` / `not-from-this-artifact` taxonomy.** Both
cases need a *reason* far more than they need a *category*, and a category tag is a second
thing to keep consistent for no gain. The reason is mandatory: an unexplained exemption is
indistinguishable from a mistake, which is the state this ADR exists to end.

**An exempt block exempts from the unmarked-figure scan and nothing else.** A `figure:` marker
inside one is still checked. The two mechanisms answer different questions — "is this number
accounted for?" versus "does it match?" — and collapsing them would make "exempt" mean
"silenced".

### 4. An unmarked figure-shaped token fails the build

Opt-in marking alone leaves a hole the sibling checks live with and this repo should not: a
figure added later, unmarked, is never checked, and a partially-covered guard reads exactly
like a fully-covered one. So every token shaped like one of this artifact's figures — a
three-decimal kappa (`0.751`) or a one-decimal percentage (`89.4%`) — must be marked, exempted,
or inside code.

The net is **deliberately narrow**. It does not catch bare counts (`189`, `48`) or
approximations (`κ ≈ 0.72–0.75`, `~89%`, `90–98% recall`). Widening it to bare integers would
flag every "40 answers" in the prose and force an exemption list longer than the marker list.
Exact restatements of counts *are* marked; they simply are not enforced by the scan.

Markdown code — fenced or inline — is invisible to all of this, because `CLAUDE.md` documents
this very convention and documenting a marker must not *be* one.

### 5. Failure policy

| Condition | Result |
|---|---|
| Marked value disagrees with the artifact | exit 1 |
| Unknown figure key | exit 1 — a typo checks nothing and passes forever |
| Figure-shaped token neither marked nor exempted | exit 1 |
| Exempt block with no reason, or never closed | exit 1 |
| **Zero marked figures** | **exit 1** |
| Artifact missing or unparseable | exit 1 |

**Zero markers is a failure.** A checker that finds nothing to verify prints a pass and reads
like one. This is a house rule earned from real incidents and `check_published_metrics.py`
enforces it; the same reasoning is why ADR-003 deletes `evals/results.md` before regenerating
it.

**A missing artifact is a failure, and this is where we diverge from the sibling.**
`check_published_metrics.py` exits 0 loudly when it cannot fetch, because it reads another
repo's artifact over the network and a GitHub outage must not redden an unrelated build. Here
the artifact is a committed local file that ADR-003 already asserts is current. Absence is a
repo defect, not weather, so it fails.

### 6. Scope: `README.md` and `CLAUDE.md`, not the ADRs

The `decisions/` files quote figures too, and are deliberately **not** checked. ADR-002 says it
outright — "the analysis below is preserved as written — it is the record of what was decided
and why, not a document to be revised after the fact." An ADR's figures are dated observations.
Asserting them would demand editing the record every time a number moves, which is precisely
backwards, and applying the scan to them would need dozens of exemptions on documents that must
not be edited at all.

### 7. No floors, no thresholds — this is SYS-019, not SYS-017 tier 2

Nothing here gates on a **value**. κ is free to move; the sentences written about it just have
to move with it. This governs what may be *claimed* about a measurement, not whether the
measurement clears a bar. ADR-003's refusal stands unchanged and for the same reason: one
measurement has no noise band under it, and CI cannot manufacture a second sample.

At the time of writing all 66 marked figures already matched. This locks in a correct state
rather than repairing a broken one — which is the right time to add a guard, not evidence that
it was unnecessary.

## Downstream surfaces

- **`scripts/check_published_figures.py`** — the mechanism. The `rstrip`-safe value pattern (a
  marked value must start *and* end alphanumeric) is not cosmetic: without it a figure ending a
  sentence captures the full stop and compares unequal forever. A test pins that.
- **`.github/workflows/tests.yml`** — one new step, deliberately **after** the ADR-003 staleness
  check. Checking the prose against an artifact not yet known to be current would only prove
  that two files agree, which they can do while both are stale.
- **`README.md`, `CLAUDE.md`** — now carry markers. The markers are load-bearing; stripping one
  as source-tidying re-opens the hole for that figure, and the unmarked-figure scan is what
  makes that fail loudly instead of silently.
- **`CLAUDE.md`'s standing caution** — "Half of this is now mechanical" is now **both halves**,
  and the marker convention is documented there because that is where an agent reads it.
- **`pyproject.toml`** — `pythonpath` gains `"scripts"` so the checker is importable by tests.
  This also makes `scripts/inspect_questions.py` importable; harmless.
- **`src/score.py`** — its output layout is now load-bearing twice over. A formatting change
  breaks the parser here as well as the ADR-003 diff. The parser fails loudly with a message
  saying so; it must be updated, not silenced.
- **[ADR-002](002-solid-tier-call.md) phase 2** — landed first, in #19, while this was being
  built, and it moved exactly what was expected: Opus κ 0.751 → 0.762, agreement 89.4% →
  89.9%, both CI bounds, ternary κ, and supported recall. This change is therefore marked
  against the **audited** figures, not the floor's. Going forward the check **requires the
  reconciled prose to land in the same PR as the regenerated artifact**, which is what
  ADR-002's own reconcile discipline already asks for — the figures a future audit must not
  forget are now enumerated by a machine rather than by a reader's diligence. The 2026-07-19
  history sentence, the pre-audit `0.751`, and the drift-restricted `0.752` are exempt and
  **must stay** exempt; a later re-score must not "update" them.
- **Nothing in this ADR touches the gold set, the labels, or the judges.** ADR-002's ruling
  reserves adjudication to San; no model may adjudicate, relabel, or propose a label for any
  gold claim. This change reads published prose and a committed artifact and nothing else.
- **`system/SYS-019`** — this is a rollout row for it, and the first in this repo.
- **`decisions/`** — this repo has no `lint_decisions.py`, unlike `kb-agent` and the classifier,
  so this `## Downstream surfaces` section is convention rather than enforced. Included because
  it is the section that gets skipped, and the sweep that follows then misses a file.

## Consequences

- **The claim-drift hole ADR-003 left open is closed.** Both halves of the `CLAUDE.md` reconcile
  rule are now mechanical: artifact vs code, and claim vs artifact.
- **Editing a published figure is now a two-place edit that CI verifies** — the artifact and the
  prose. That is the point, and it is the cost.
- **The prose is slightly noisier at the source and identical when rendered.** The table rows in
  particular are long lines now. Judged worth it: the alternative is a figure nothing checks.
- **A new figure written into README.md without a marker fails the build.** Intended, and the
  most likely surprising red. The error names the file, the line, the token, and both fixes.
  It has already earned itself once: marking up the post-audit README by hand, the scan caught
  a `95.8%` in the Status section that a careful read had missed, in a paragraph a hundred
  lines below the results table. Opt-in marking alone would have reported a confident pass
  with that figure uncovered.
- **Approximations remain a human's job.** `κ ≈ 0.72–0.75` and `~89%` are not marked and cannot
  be. If phase 2 moves κ materially, those phrasings need re-reading by a person; the checker
  will not say so. This is a stated limit, not an oversight.
- **A `score.py` formatting change now breaks two checks instead of one.** Both fail loudly with
  directed messages.

## Alternatives Considered

| Option | Reason Not Chosen |
|--------|-------------------|
| Hardcode the expected figures in the checker | Creates a third copy of the numbers, so the checker itself becomes something that can drift from the artifact it protects. Self-defeating. |
| Opt-in markers only, with no unmarked-figure scan (the sibling repos' shape) | Leaves the hole that a figure added later is never checked, while the check still reports a confident pass. Same class of defect as "zero markers reads as a pass", which the house already refuses. The sibling lives with it because its notes are mostly prose examples; here the two scanned files are almost entirely restated figures. |
| Require *every* number in the prose to be marked | The scanned files legitimately carry counts, dates, ADR numbers, and statistics from other sources. The exemption list would be longer than the marker list and would rot. The narrow two-shape net catches the figures that actually move. |
| An ignore list of historical values, in the script or a config file | Lives away from the prose it governs, cannot distinguish two occurrences of the same literal (`0.751` appears both as the live κ and inside the 2026-07-19 history sentence), and goes stale invisibly. |
| Mark historical figures with `<!-- figure-historical: ... -->` as a distinct kind | Two marker kinds to keep consistent for no mechanical gain. The p = 0.125 case is not historical at all — it is simply not produced by `score.py` — so the taxonomy would need a third kind immediately. One exempt marker with a mandatory free-text reason covers both and tells a future reader more. |
| An inline exempt form as well as the block form | A second convention to document and test for a marginal reduction in verbosity. An exemption is a claim about a region of prose; a block is what says that. |
| Also assert the figures in `decisions/*.md` | ADRs are dated records, preserved as written by ADR-002's own instruction. Asserting them would require rewriting history whenever a number moves. |
| Warn instead of failing (`continue-on-error`) | An unenforced check reports green from stale prose, which is the written human rule again with more YAML. ADR-003 rejected the same option for the same reason. |
| Run it as a pytest test only, not a CI step | It is a repo-hygiene guard over published prose, not a unit test of the measurement, and a named CI step says what failed without reading a traceback. It is *also* covered by tests, which is how the failure paths get exercised. |
| Have CI rewrite the prose to match the artifact | Launders a changed published claim into history with no review — the same objection ADR-003 raised to CI committing the regenerated artifact. A human has to look at a number before it is published. |
| Set a floor on κ while we are in here | Out of scope and refused on the merits by ADR-003: one measurement, no noise band. This ADR is SYS-019 (what may be claimed), not SYS-017 tier 2 (whether the value is enforced). |
| Wait until ADR-002 phase 2 lands, then add the guard | The figures move *during* phase 2, which is exactly when an enumeration of what must be reconciled is worth most. Adding it afterwards would mean the one transition it was built for went unguarded. |
