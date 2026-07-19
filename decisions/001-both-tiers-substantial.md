# ADR-001: Both judge tiers are substantial — and the first Sonnet number was a measurement artifact

**Status:** Accepted; **amended 2026-07-19** (see [Amendment](#amendment-2026-07-19))
**Date:** 2026-07-18
**Deciders:** San Lee

---

## Context

[SCOPE.md](../SCOPE.md) Decision 3 committed to running **both** judge tiers
(claude-sonnet-5 and claude-opus-4-8) over the same gold set, leading with whichever
agreed better and reporting the gap — on the reasoning that "Opus κ=X, Sonnet κ=Y" is
itself a finding, and that the portfolio's model-tier standard escalates only where the
eval shows it pays.

The floor was built to answer that: 40 densified QA answers over public DVIDS text,
decomposed into **193 frozen claims**, hand-labeled ternary
(`supported`/`partial`/`unsupported`/`na`) by one labeler against each claim's cited
excerpt. Both judges then rated the same claims blind. Scoring collapses `partial` into
`unsupported` for the headline binary κ, excludes `na`, and counts any unparsed verdict
as a disagreement (n = 189 scored, post-amendment).

The measured result (`evals/results.md`):

| Judge | Binary κ | Raw agreement (95% Wilson CI) | Unsupported recall | Ternary κ |
|---|---|---|---|---|
| **Opus** (claude-opus-4-8) | **0.751** | 89.4% [84.2%, 93.0%] | 97.9% | 0.682 |
| **Sonnet** (claude-sonnet-5) | **0.716** | 88.4% [83.0%, 92.2%] | 89.6% | 0.672 |

Human binary unsupported share: 48/189 = 25.4%. 0 unparsed verdicts for either judge.

### The first run said something different, and it was wrong

The **initial** scoring run reported Opus 0.70 / **Sonnet 0.43** — a dramatic tier gap,
and exactly the kind of result that makes a satisfying headline. It was an artifact of
the harness, not a property of the model.

`max_tokens=10` was set to force a one-word verdict. Sonnet, unlike Opus, tended to
preface its answer with a clause of reasoning — so it was **truncated before ever
emitting the verdict word on 39 of the 191 then-scored claims (20%)**. Those unparsed verdicts scored as
disagreements, and the resulting κ collapsed. On the 152 claims Sonnet actually answered,
its κ was already ≈0.70 — the number it holds today.

This was caught by **reading the misjudgment log before publishing**: the Sonnet failures
were not distributed like judgment errors, they were empty. A tier-gap headline was one
commit away from shipping.

The fix took two attempts. Assistant-message **prefill** — seeding the reply so the model
continues from a fixed token — is the standard trick here and was tried first
(`592d914`), but is **rejected by claude-sonnet-5 and claude-opus-4-8**. The working fix
(`e6a18ab`) forces the verdict through a **tool-use enum**: a `record_verdict` tool whose
schema constrains the verdict to the label set, invoked with
`tool_choice={"type": "tool", "name": "record_verdict"}`. The model may reason freely; the
verdict arrives in a structured block that cannot be truncated into ambiguity.

## Decision

**Record both tiers as substantial judges, do not claim Opus is meaningfully better, and
keep the forced-tool-use verdict as load-bearing.** Concretely:

- **Report the result as "both tiers work."** κ ≈ 0.72–0.75, ~89% raw agreement,
  90–98% recall on the fabrication class. Both are usable as automated faithfulness
  checks at this task.
- **Do not headline the Opus/Sonnet κ gap.** The CIs overlap (84.2–93.0 vs 83.0–92.2) at
  n=189. The gap is not resolvable at this sample size and the README states so.
- **Do not headline the unsupported-recall gap either** (amended 2026-07-19; this bullet
  formerly named it "the defensible reason to escalate"). 97.9% vs 89.6% is 47 vs 43 of
  48. Discordant pairs are 4–0 in Opus's favor with no reversals, but McNemar's exact test
  gives p = 0.125. The direction is consistent; the sample cannot size the gap. Report it
  with the test, never as a standalone reason to pay.
- **The `record_verdict` forced tool call stays.** No reverting to prefill (unsupported by
  these models) and no reverting to a bare `max_tokens=10` one-word prompt (reintroduces
  the 20%-unparsed artifact). `max_tokens` must stay large enough for preamble.
- **Scoring conventions stay as built:** `na` excluded, unparsed verdicts counted as
  disagreements. Counting unparsed as disagreement is deliberate — it is what made the
  artifact visible rather than silently dropping 20% of the set.

## Consequences

- **"Measure before escalating" now has a third data point.** After BM25 grounding and
  tiered model routing in the classifier repo, this is the third measured verdict landing
  on *escalation barely pays*. The pattern is no longer a one-off.
- **The honest headline is a modest one.** "The cheap tier is already good enough" is less
  impressive than a clean tier gap, and it is what the data supports. The overlapping-CI
  caveat is stated in the README rather than buried.
- **The floor's limits bound every claim above.** n=189, **a single labeler with no
  inter-annotator agreement measured**, one pass with no judge prompt tuning, and DVIDS
  operations/procurement-skewed short passages. κ=0.751 against *this* gold does not
  establish κ=0.751 against humans in general.
- **The harness bug is the transferable lesson, not a footnote.** A plausible,
  publication-ready result was produced by a truncation setting. The generalization:
  **when a model's scores are unexpectedly bad, inspect the raw outputs before believing
  the metric** — and constrain critical outputs structurally (tool-use enums) rather than
  by token budget.
- **Open, unscheduled:** a second labeler (the only thing that upgrades the ground truth
  from consistent to validated), larger n to tighten the CIs, or a Haiku tier to complete
  the cost/quality curve. All "solid tier," none committed.

## Alternatives Considered

| Option | Reason Not Chosen |
|--------|-------------------|
| Lead with "Opus is the better judge" | The κ CIs overlap at n=189, and the recall gap is McNemar p=0.125. Neither axis supports the claim, and the portfolio's bar is that a soft number dressed as solid is the only real failure mode ([SCOPE.md](../SCOPE.md)). |
| Publish the original Sonnet κ=0.43 tier gap | It was false — a `max_tokens` truncation on 20% of claims, not model behavior. |
| Keep prefill as the verdict mechanism | Rejected outright by claude-sonnet-5 / claude-opus-4-8 (`592d914` failed); the tool-use enum is the supported path. |
| Drop unparsed verdicts instead of scoring them as disagreements | Dropping them would have hidden the 20% truncation entirely and shipped the false gap. Counting them as disagreements is what surfaced the bug. |
| Retro-fix by re-running only Sonnet | Both judges were re-run under the corrected harness so the two numbers come from an identical call shape — a mixed-harness comparison would be its own artifact. |
| Recommend Sonnet outright on cost | Defensible on κ. The 8-point recall gap on the fabrication class is the metric that would matter for catching hallucinations, but at 4 discordant pairs (p=0.125) it is not established. That trade is the caller's to make; the ADR reports it rather than picking. |

---

## Amendment (2026-07-19)

Two corrections, both found by auditing this repo's own claims rather than by new
measurement. No judges were re-run; scoring is offline, so the cost was zero.

**1. Two gold labels violated the rubric.** `asrt-q-07-c3` and `help-q-13-c3` were
labeled `supported`. Both are filler with no factual assertion — an offer to help
("I'd be happy to help pinpoint...") and a suggestion to consult the source ("you
may want to check the original source..."). Those are near-verbatim the two
canonical `na` examples in [docs/labeling-guide.md](../docs/labeling-guide.md). They
are now `na`, which excludes them from scoring.

Effect: n 191 → 189, and both κ figures rose slightly.

| Judge | Binary κ before → after | Raw agreement before → after | Unsupported recall |
|---|---|---|---|
| Opus | 0.742 → **0.751** | 89.0% → **89.4%** | 97.9% (unchanged) |
| Sonnet | 0.696 → **0.716** | 87.4% → **88.4%** | 89.6% (unchanged) |

Recall is unchanged because neither corrected claim was in the `unsupported` class.

`meta.labels_allowed` in `claims.yaml` also never listed `na` despite two claims
already using it. Fixed.

**2. The unsupported-recall claim was an overclaim.** The original Decision named
97.9% vs 89.6% as "the defensible reason to escalate, and the only one" — three
sentences after discounting the κ gap for overlapping CIs. Same small-sample
objection, *smaller* denominator (48), opposite treatment. McNemar's exact test on
the discordant pairs (b=4, c=0) gives p = 0.125. The bullet is reversed above.

**Why this matters more than the numbers.** This project exists to catch soft
numbers dressed as solid, and it shipped one in its own headline for a week. The
labeling error is the concrete instance of the "one labeler, no inter-annotator
agreement" limit the ADR already listed as a hypothetical. Both are now stated in
the README rather than quietly fixed.
