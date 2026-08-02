# ADR-002: The solid-tier call — what, if anything, to spend next

**Status:** **Accepted — Option D**, ruled 2026-08-02. San signed off on the four-part
guard explicitly, which was the part of the recommendation that needed an owner rather
than an agent. Execution is phased: **phase 1 (this PR)** pre-registers the selection
rule and builds the blind worksheet; **phase 2** re-scores after the adjudications exist.
No judge has been re-run and no published number has been touched.
**Date:** 2026-08-02 (packet), 2026-08-02 (ruling)
**Deciders:** San Lee

The analysis below is preserved as written — it is the record of what was decided and
why, not a document to be revised after the fact. The ruling and the pre-registered
selection rule are appended at the end, under
[Ruling (2026-08-02)](#ruling-2026-08-02).

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

---

## Ruling (2026-08-02)

**Option D.** Run the blind, pre-registered gold audit under the four-part guard,
re-score offline, and close the solid-tier call. San signed off on the guard
explicitly — the ADR named that sign-off as the thing an agent must not supply for
itself, and it was given rather than assumed.

Options A, B, and C are declined for the reasons in the table above: A leaves a known
rubric violation published on a public repo whose thesis is catching exactly that, B is
a new front buying precision on the axis Findings 1–3 show is saturated, and C is
blocked on a person who does not exist for this project.

### Execution is two phases, and the split is the guard

Phase 1 (this PR) ships the *instrument* and nothing else. Phase 2 runs only once San's
adjudications exist.

| Phase | What lands | What must **not** happen |
|---|---|---|
| **1** | This ruling; the pre-registered selection rule below, in words and in code (`src/gold_audit.py`); the blind worksheet (`data/gold-audit-worksheet.md`); the offline re-score path and its tests. | No label is adjudicated, proposed, or changed. No number is re-scored or published. `README.md` and `evals/results.md` are untouched. |
| **2** | The filled worksheet; the corrected numbers reported **both ways**; the README/CLAUDE.md updates; the call closed. | No judge is re-run. Nothing is published from the fully-audited view alone. |

The phase split is not ceremony. **The rule has to be committed before the candidate set
exists**, or "pre-registered" is a claim about intent rather than a fact about the
repository. In this PR the rule and the worksheet it produced are separate commits, in
that order, so the sequence is checkable rather than asserted.

**Who labels.** San adjudicates. No model may adjudicate, relabel, or propose a label for
any gold claim — a model-labeled gold turns this project into the circular eval it exists
to avoid, and no amount of care in the prompt changes that. The agent's job was to build
the instrument and stop.

### The pre-registered selection rule

Canonical implementation: `SELECTION_RULES` in
[`src/gold_audit.py`](../src/gold_audit.py). It is **structural** in the strict sense —
each rule is a predicate over the claim's own text and nothing else. Not the gold label,
not a judge verdict, not whether anything disagreed about the claim.

> **A claim is selected if and only if it matches at least one of:**
>
> - **S1 — short fragment.** The claim is **8 whitespace-separated words or fewer.** The
>   frozen splitter (SCOPE.md Decision 2) emits list items and sentence fragments as
>   standalone claims; below this length a claim is often not self-contained, and a claim
>   that cannot be evaluated in isolation is a decomposition artifact rather than a
>   judgeable assertion.
> - **S2 — list header.** The claim, after trailing whitespace is stripped, **ends with a
>   colon.** A colon-terminated header introduces a list rather than asserting anything on
>   its own, so the rubric's "not a factual claim" test should resolve the same way for
>   every instance of the shape.
> - **S3 — offer to help.** The claim **offers further assistance or asks the reader for
>   more input** — the "I'd be happy to help" shape that
>   [docs/labeling-guide.md](../docs/labeling-guide.md) names as canonical `na`.
> - **S4 — external referral.** The claim **directs the reader to material outside the
>   excerpt** — the "you may want to check the original source" shape that the labeling
>   guide also names as canonical `na`.

S1 and S2 are exact and need no interpretation. S3 and S4 are fixed case-insensitive
pattern sets, given verbatim in the module; they are frozen with this ADR and are not to
be adjusted after the fact.

```python
SHORT_CLAIM_MAX_WORDS = 8

def selected(claim_text: str) -> bool:
    return (
        len(claim_text.split()) <= SHORT_CLAIM_MAX_WORDS      # S1
        or claim_text.rstrip().endswith(":")                  # S2
        or _OFFER_TO_HELP.search(claim_text) is not None       # S3
        or _EXTERNAL_REFERRAL.search(claim_text) is not None   # S4
    )
```

The rule was written from this ADR's guard item 1 and the labeling guide's canonical `na`
examples, then executed **once**. No pattern was added, removed, or tightened after
seeing which claims it selected, and no judge verdict was consulted at any point in
constructing it.

### Why it is applied to every claim, and why that is what makes it blind

**The predicate is applied to all 193 gold claims** — the 189 scored, plus the 4 already
labeled `na`.

That is the whole mechanism. Because selection cannot see a verdict, the candidate set
**necessarily contains claims both judges scored correctly** alongside claims they did
not, and the adjudicator cannot tell which is which. A set assembled from the claims the
judges failed on would not be an audit; it would be the misjudgment log with a new name,
and correcting it would move κ by construction. `tests/test_gold_audit.py` asserts this
mechanically rather than trusting the prose: selection is invariant to the gold labels,
the `select` path raises if it so much as opens a judgments file, every line of the
worksheet is traceable to `claims.yaml`/`questions.yaml` or to a fixed template, and the
selected set is checked to contain claims both judges got right.

Including the 4 existing `na` claims is deliberate and is a small extension of what the
packet described. Auditing only the scored 189 would let labels move **into** `na` but
never out of it, which can only shrink *n* — a directional bias in an audit whose entire
purpose is to not have one. Finding 4's colon-header inconsistency straddles that line
(`help-q-07-c3` and `help-q-36-c2` are `supported`; `help-q-21-c1` and `help-q-22-c1` are
`na`), so both sides have to be in view for the shape to be adjudicated consistently.

### The worksheet, and why it is markdown

`data/gold-audit-worksheet.md`, generated by `uv run python src/gold_audit.py select`.
It carries, per claim: the claim id, the claim text, the context excerpt and question
needed to judge it, the current gold label, and which structural rule put it there. It
carries **no** judge verdict, no agreement flag, and no indication that a claim was ever
contested.

Markdown rather than the CSV route `src/labels.py` uses for the full gold pass: at ~30
claims spreadsheet ergonomics stop paying, the context excerpts are multi-sentence
paragraphs that a CSV cell renders unreadable, the instruction header and rubric have to
travel *with* the worksheet (a CSV cannot carry them), and grouping claims under their
shared context lets the adjudicator hold one excerpt in mind at a time — the labeling
guide's own advice.

### The re-score path

`uv run python src/gold_audit.py rescore`, offline, no API key, no judge re-run. It
reports κ, raw agreement with Wilson CIs, ternary κ, unsupported recall, and the paired
McNemar test under **three** gold views:

1. the original gold (the published baseline),
2. the fully audited gold,
3. the audited gold with corrections applied **only** where no judge erred under the
   original gold.

View 3 is guard item 3 made mechanical. A correction landing on a claim every judge
already got right can never raise agreement, so if the headline moves in view 2 but not
in view 3, the correction tracked the judges and the rise is not a gold-quality result.
The report also states, per guard item 3, how many changed claims were shared judge
errors, single-judge errors, and neither.

Guard item 4 is enforced in the report text itself: the output states that this is a
single-labeler consistency audit and **not** inter-annotator agreement, so the "one
labeler, no IAA measured" limit survives Option D intact and stays in the README.

### Consequences

- **The solid-tier call is decided but not yet closed.** It closes in phase 2, when the
  corrected numbers land. Until then `README.md` and `evals/results.md` continue to carry
  the floor's published figures unchanged, which is correct: no number has moved.
- **One README correction is queued, not made.** Finding 1 showed that "recall on the
  fabrication class" overstates what the data supports — restricted to gold `unsupported`
  proper the two tiers are identical at 35/36. The phrasing is deliberately left alone in
  phase 1 so that every published figure moves at once, in phase 2, against one audited
  gold rather than in two uncoordinated passes.
- **A Haiku tier still rides after D, if wanted.** Unchanged from the packet: it is a
  separate concern, and running it against a gold with unrepaired defects would only have
  to be re-scored afterward.
- **The instrument outlives this audit.** `src/gold_audit.py` is a general blind-audit
  harness for this gold set: a future audit changes `SELECTION_RULES` and re-runs. The
  discipline it encodes — pre-register the selection, adjudicate blind, publish the
  drift-restricted view beside the headline — is the transferable part, and it is
  cheaper to keep than to rebuild.
