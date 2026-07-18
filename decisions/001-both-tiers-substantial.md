# ADR-001: Both judge tiers are substantial — and the first Sonnet number was a measurement artifact

**Status:** Accepted
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
as a disagreement (n = 191 scored).

The measured result (`evals/results.md`):

| Judge | Binary κ | Raw agreement (95% Wilson CI) | Unsupported recall | Ternary κ |
|---|---|---|---|---|
| **Opus** (claude-opus-4-8) | **0.742** | 89.0% [83.8%, 92.7%] | 97.9% | 0.674 |
| **Sonnet** (claude-sonnet-5) | **0.696** | 87.4% [82.0%, 91.4%] | 89.6% | 0.654 |

Human binary unsupported share: 48/191 = 25.1%. 0 unparsed verdicts for either judge.

### The first run said something different, and it was wrong

The **initial** scoring run reported Opus 0.70 / **Sonnet 0.43** — a dramatic tier gap,
and exactly the kind of result that makes a satisfying headline. It was an artifact of
the harness, not a property of the model.

`max_tokens=10` was set to force a one-word verdict. Sonnet, unlike Opus, tended to
preface its answer with a clause of reasoning — so it was **truncated before ever
emitting the verdict word on 39 of 191 claims (20%)**. Those unparsed verdicts scored as
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

- **Report the result as "both tiers work."** κ ≈ 0.70–0.74, ~88% raw agreement,
  90–98% recall on the fabrication class. Both are usable as automated faithfulness
  checks at this task.
- **Do not headline the Opus/Sonnet κ gap.** The CIs overlap (83.8–92.7 vs 82.0–91.4) at
  n=191. The gap is not resolvable at this sample size and the README states so.
- **Do name the one real separation: unsupported recall, 97.9% vs 89.6%.** That is the
  defensible reason to escalate for this task, and the only one.
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
- **The floor's limits bound every claim above.** n=191, **a single labeler with no
  inter-annotator agreement measured**, one pass with no judge prompt tuning, and DVIDS
  operations/procurement-skewed short passages. κ=0.742 against *this* gold does not
  establish κ=0.742 against humans in general.
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
| Lead with "Opus is the better judge" | The κ CIs overlap at n=191. The claim isn't supported, and the portfolio's bar is that a soft number dressed as solid is the only real failure mode ([SCOPE.md](../SCOPE.md)). |
| Publish the original Sonnet κ=0.43 tier gap | It was false — a `max_tokens` truncation on 20% of claims, not model behavior. |
| Keep prefill as the verdict mechanism | Rejected outright by claude-sonnet-5 / claude-opus-4-8 (`592d914` failed); the tool-use enum is the supported path. |
| Drop unparsed verdicts instead of scoring them as disagreements | Dropping them would have hidden the 20% truncation entirely and shipped the false gap. Counting them as disagreements is what surfaced the bug. |
| Retro-fix by re-running only Sonnet | Both judges were re-run under the corrected harness so the two numbers come from an identical call shape — a mixed-harness comparison would be its own artifact. |
| Recommend Sonnet outright on cost | Defensible on κ, but the 8-point recall gap on the fabrication class is the metric that matters for catching hallucinations. That trade is the caller's to make; the ADR reports it rather than picking. |
