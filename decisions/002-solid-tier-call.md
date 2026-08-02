# ADR-002: The solid-tier call — what, if anything, to spend next

**Status:** **Proposed — decision packet, awaiting the owner's call.** Nothing in this
file has been enacted. No judge was re-run, no label was changed, no published number
was touched in preparing it.
**Date:** 2026-08-02
**Deciders:** San Lee

---

## The question

**Does this project spend a "solid tier" pass — a second labeler, a larger *n*, or a
third judge tier — or does it close at the floor and call the measurement done?**

[README.md](../README.md) and [CLAUDE.md](../CLAUDE.md) have both carried that as
"open, unscheduled" since 2026-07-18. [ADR-001](001-both-tiers-substantial.md) named
the three candidates and committed to none. This ADR assembles the evidence that
bears on the choice and recommends one.

## Context: what the floor actually measured

The published result ([evals/results.md](../evals/results.md)):

| Judge | Binary κ | Raw agreement (95% Wilson CI) | Unsupported recall |
|---|---|---|---|
| Opus (claude-opus-4-8) | 0.751 | 89.4% [84.2%, 93.0%] | 97.9% |
| Sonnet (claude-sonnet-5) | 0.716 | 88.4% [83.0%, 92.2%] | 89.6% |

ADR-001 concluded that neither κ nor unsupported recall separates the tiers. That
conclusion holds. What it did not do is ask *where the remaining disagreement lives* —
and that is the question the solid-tier call actually turns on, because each candidate
spend buys precision on a different axis.

Everything below is derived offline from the committed artifacts
(`data/claims.yaml`, `data/judgments_opus.yaml`, `data/judgments_sonnet.yaml`) using
this repo's own `collapse()` and `mcnemar_exact()` conventions. No API calls.

### Finding 1 — the recall gap is entirely a `partial`-boundary effect, not a fabrication-catching effect

The four discordant pairs behind the 97.9%-vs-89.6% recall gap are:

```
asrt-q-22-c2   asrt-q-22-c3   asrt-q-40-c4   help-q-22-c4
```

**All four carry gold label `partial`.** They enter the "unsupported" class only via
[SCOPE.md](../SCOPE.md) Decision 1's `partial → unsupported` collapse.

Restrict the universe to gold `unsupported` proper — the fabrication class, n = 36 —
and the tiers are **identical**: both judges miss exactly one claim, the same one
(`help-q-02-c5`). Discordant pairs b = 0, c = 0, McNemar p = 1.0.

So the phrase "recall on the fabrication class" in the README is doing more work than
the data supports. On actual fabrications the two tiers are indistinguishable at
35/36 each. The entire measured gap is a difference in how the tiers treat 12
borderline, hedged claims — and `partial` is, by the labeling guide's own admission,
the class where the human call is least crisp ("when unsure between `p` and `u`, it
won't change the headline number — label your honest read and move on",
[docs/labeling-guide.md](../docs/labeling-guide.md)).

### Finding 2 — on the headline axis the tiers are a statistical dead heat

Paired over all 189 scored claims, binary correctness against gold:

| | count |
|---|---|
| Opus wrong | 20 |
| Sonnet wrong | 22 |
| Opus right / Sonnet wrong | 5 |
| Sonnet right / Opus wrong | 3 |
| **McNemar exact** | **p = 0.727** |

Not merely "CIs overlap." The paired test on the headline axis is as null as a test
gets.

### Finding 3 — the two judges agree with each other far more than either agrees with the human

| Comparison | Binary agreement |
|---|---|
| Opus vs Sonnet | **95.8%** (181/189) |
| Opus vs human gold | 89.4% |
| Sonnet vs human gold | 88.4% |

This is the load-bearing number in the whole packet. The model axis is nearly
exhausted — swapping tiers moves 8 claims out of 189. The residual disagreement is
almost entirely *shared* between the tiers, which means it is a property of the
judge-vs-human construct, not of model capability. **Buying more model is buying
along the axis that has already saturated.**

### Finding 4 — the shared errors are one systematic pattern, and part of it is the gold

17 claims (9.0% of the set) are ones **both** judges get wrong. **16 of those 17 run
in the same direction: gold `supported` → judge binary `unsupported`.** Opus-only
errors: 3. Sonnet-only: 5.

Resolving just those 16 would move raw agreement from 89.4% → 97.9% (Opus) and
88.4% → 96.8% (Sonnet). The ceiling on this project's headline number is that one
pattern.

Reading the 16 against this repo's own rubric, several look like **gold defects, not
judge errors**:

- **`help-q-07-c6`** is labeled `supported`:
  *"If you have additional text or a source document that includes details about the
  fielding decision and timeline, please share it and I can help answer your question
  based on that information."*
  That is an offer to help — near-verbatim the shape of `asrt-q-07-c3`, which the
  [ADR-001 Amendment](001-both-tiers-substantial.md#amendment-2026-07-19) corrected to
  `na` on 2026-07-19. **It survived that audit.** A third rubric violation is still in
  the gold set.

- **Colon-terminated list headers are labeled inconsistently.** `help-q-07-c3`
  ("However, it does not mention:") and `help-q-36-c2` ("It only reports:") are
  `supported`. `help-q-21-c1` ("Based on the passage:") and `help-q-22-c1` ("Based on
  the passage, this launch is significant for two main reasons:") are `na`. Same
  shape, opposite labels.

- **`help-q-18-c3` is the two-word fragment "The Army"**, labeled `supported`. The
  judge sees only the passage and that fragment — never the answer it was cut from —
  so it is not a judgeable claim in isolation.

That last point generalizes. Claims of **≤ 8 words draw a judge disagreement 32% of
the time (6/19)** versus **11% (19/170)** for longer claims — a 3× concentration of
error on the shortest claims, which are exactly the ones the frozen splitter produced
as non-self-contained fragments.

None of this has been changed. It is reported here as evidence, per this repo's rule
that the gold set is not above audit.

### Finding 5 — powering the recall gap costs far more than it is worth

If the recall gap were still the thing worth chasing, here is the price. The observed
discordance rate is 4/48 = 8.3% per binary-unsupported claim, and a two-sided exact
McNemar needs **≥ 6 discordant pairs with zero reversals** to clear p < 0.05
(m=5 → p = 0.0625; m=6 → p = 0.0312).

Power to reach p < 0.05, by size of the binary-unsupported class:

| gold binary-unsupported *n* | power if direction is deterministic | if direction-prob 0.9 | if 0.8 |
|---|---|---|---|
| **48 (today)** | 0.21 | 0.11 | 0.05 |
| 100 | 0.85 | 0.54 | 0.28 |
| 150 | 0.99 | 0.80 | 0.48 |
| 300 | 1.00 | 0.99 | 0.83 |

A defensible target is ~150 binary-unsupported claims — **3.1× today's 48.** Claim
yield by prompt variant is 53.7% binary-unsupported for `assertive` (36/67) and 9.8%
for `helpful` (12/122), so even an assertive-only expansion — the cheapest possible
mix, and one that would skew the set away from the subtle failure mode `helpful` was
added to cover — needs **~280 assertive claims, roughly +190 new hand labels**, plus
the 40–80 new sourced DVIDS contexts and questions to generate them from.

And per Finding 1, what that spend would buy is a precise measurement of a
`partial`-boundary difference, assessed against a single labeler's calls in the label
class that labeler is least sure about. **More precision on a construct that is itself
unreliable is not more knowledge.**

## Options

| # | Option | Cost | What it buys | Risk |
|---|---|---|---|---|
| **A** | **Close at the floor.** Flip README/CLAUDE.md status from "open, unscheduled" to closed; no further measurement. | 1 session. $0 API. | The open decision closes. Fully consistent with "no new fronts." | Leaves Finding 4 on a **public** repo whose entire thesis is catching soft numbers dressed as solid. A skeptical reader who reads the misjudgment log beside the labeling guide finds the third rubric violation the project did not catch. That is the do-nothing cost, and it is the same failure mode this repo has already shipped once. |
| **B** | **Larger *n*.** Expand the instrument and gold set to ~150 binary-unsupported claims to power the recall gap. | +190 hand labels minimum, 40–80 new sourced contexts/questions, both judges re-run over the expanded set. Multiple sessions; real API spend. | 80% power on a `partial`-boundary difference between tiers. | The most expensive option, buying precision on the axis Findings 1–3 show is both saturated and mis-described. Squarely the "new front" the current direction memo rules out. |
| **C** | **Second labeler.** A second human labels the 189 claims; report human-human κ. | 189 relabels by someone who is not San. $0 API. | The only thing that upgrades the gold from *consistent* to *validated*, and the only option that measures the limit the README calls out first. | Blocked on a person who does not currently exist for this project. Parking the call on an unavailable resource is Option A with extra steps and no closure. |
| **D** | **Blind gold audit, then close.** Re-label a *pre-specified, structurally selected* slice of the gold set blind to judge verdicts; re-score offline; publish the corrected numbers and the audit method; close the solid-tier call. | ~1 session. **$0 API — judges are not re-run.** San adjudicates ~25–30 flagged claims. | Directly attacks the binding constraint (Finding 4). Turns "how much of the judge-human gap is actually the human?" into a measured answer — which is on-thesis for a project about measuring the measurer. Closes the call with a result rather than a shrug. | Still one labeler: this is an *audit*, not inter-annotator agreement, and must never be written up as validation. Carries a real methodological trap — see below. |

Option D's method is not novel here: the 2026-07-19 amendment did exactly this at
smaller scope and recorded that "no judges were re-run; scoring is offline, so the cost
was zero."

**A third judge tier (Haiku) is not in the table.** SCOPE.md named it, and it is cheap
— one judge run over 189 committed claims, and `src/paired_compare.py` already exists
to compare it offline. But Findings 2 and 3 say the model axis is saturated at the top,
so a third point at the *cheap* end measures the one stretch of the curve where a bend
would be informative — which is a genuine argument *for* it. It is left out because it
is a separate concern from the gold-quality question, and because running it against a
gold set with known unrepaired defects would just have to be re-scored afterward. If it
is wanted, it should ride **after** D, as its own branch and PR.

## The trap in Option D, and the guard

Auditing labels *while looking at the claims the judges got wrong* is precisely how a
gold set drifts toward the judges. Correct enough of the 17 shared errors and κ rises —
but the rise measures the audit's motivation, not the judge. That would manufacture
exactly the soft-number-dressed-as-solid failure this project exists to catch, and it
would be much harder to spot than the `max_tokens` artifact was.

The guard, if D is chosen:

1. **Pre-register the selection rule before looking at any verdict.** Select claims by
   *structure*, not by whether a judge disagreed — e.g. claims ≤ 8 words; claims ending
   in a colon; claims matching the offer-to-help / meta-aside shapes the labeling guide
   names as canonical `na`. Commit the rule first.
2. **Audit blind.** The adjudication pass must not have the judge verdicts in view.
3. **Report the overlap honestly.** State how many audited claims happened to be shared
   errors, and publish the corrected κ *both* ways — full audit, and audit restricted to
   claims no judge got wrong — so the reader can see whether the correction tracked the
   judges.
4. **Never call the result inter-annotator agreement.** It is a single-labeler
   consistency audit. The "one labeler, no IAA measured" limit survives D intact and
   must stay in the README.

## Recommendation

**Option D.** Run the blind, pre-registered gold audit under the guard above, re-score
offline, publish the corrected numbers with the audit method, and close the solid-tier
call in the same PR.

Why:

- **It is the only option that touches the binding constraint.** Findings 2 and 3 show
  the model axis moves 8 claims in 189 and is statistically null; Finding 4 shows a
  single shared error pattern accounts for 8.5 points of raw agreement, and that part
  of that pattern is defective gold. Ground-truth quality — not model tier, not sample
  size — is what every number in this repo is currently limited by.
- **It is measure-first, and the measurement is cheap.** $0 API, no judge re-runs, one
  session. Option B costs 190 hand labels to sharpen a comparison Finding 1 shows is
  mis-described; D costs ~30 adjudications to fix the thing that actually binds.
- **The negative result is already written and should ship as one.** "Neither tier
  separates, the model axis is saturated, and the residual gap is the human" is a
  sharper and more honest headline than the current one, and it is the third
  measure-before-escalate verdict this portfolio has landed. D lets that be stated with
  a number behind it.
- **It finishes rather than opens.** The direction is finish-the-spine and polish. D
  closes a seven-month-old open decision inside one session and leaves the repo with no
  outstanding call. B opens a new front; C parks indefinitely; A closes the call while
  leaving a known defect published on a public repo.

The one thing D must not do is quietly become "relabel until κ looks better." That is
what the four-part guard is for, and it is the part of this recommendation that most
needs the owner's explicit sign-off rather than an agent's judgment.

## What a one-word ruling executes

| Ruling | What happens next |
|---|---|
| **D** | New branch: commit the pre-registered selection rule, export the selected claims blind, San adjudicates, `src/score.py` re-runs offline, README + CLAUDE.md + this ADR updated to Accepted, solid-tier call closed. |
| **A** | One-line status flip in README and CLAUDE.md; this ADR recorded as Rejected-in-favor-of-A, with Finding 4 written into the README's Limits section so the defect is disclosed rather than silently carried. |
| **C** | Parked with a named labeler and a date, or it is Option A. |
| **B** | Needs its own scoping session; it is a new front, not a polish pass. |
