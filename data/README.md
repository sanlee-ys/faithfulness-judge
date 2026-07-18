# Data — the densified question set

`questions.yaml` is the **instrument** the rest of the project runs on: a set of
grounding contexts + questions, engineered so that a QA model answering from the
context alone produces a healthy share of *unsupported* claims. That density is
what lets the faithfulness judge be tested on the hard case (catching
fabrication) and not just the easy one (blessing good answers).

Verify its shape yourself:

```bash
python3 scripts/inspect_questions.py        # summary
python3 scripts/inspect_questions.py --strict   # exit 1 on any structural problem
```

## Contexts are synthetic and controlled — a deliberate deviation from the scope

The scope doc says "reuse the DVIDS / public corpus." This floor set instead
uses **synthetic, public-affairs-style passages** written for this repo. The
reason is methodological, not convenience: measuring a *judge* requires the
ground truth ("what does the context support?") to be crisp and knowable. With a
passage written to have known boundaries, "unsupported" is defined precisely; a
hand-labeler and the judge are arguing over the same fixed evidence. Real
scraped snippets are shorter, leakier, and drag in world knowledge that muddies
whether a claim is grounded *in the passage* or merely true.

All passages are clearly fictional — invented companies (`Meridian Aerospace`),
platforms (`KX-90`), and units (`3rd Expeditionary Brigade`). No real program,
contract, unit, or operation is described.

**Upgrade path (solid tier):** swap in real DVIDS passages (U.S. military public
affairs, public domain) as contexts. The questions and the densification design
port over; only the `text` blocks change. Left for later on purpose — the floor
earns the method first.

## The densification taxonomy

Every question carries a `type`. Three of the four are "traps" designed to
induce unsupported claims; `grounded` is the control that keeps the judge
honest about precision.

| Type | What the context does | What a model tends to do | Tests the judge on |
| --- | --- | --- | --- |
| `grounded` | Fully supports a correct answer | Answer correctly | **Not** crying "unsupported" on good answers (precision / specificity) |
| `partial` | Supports part; the rest is absent | Answer the known part, then extrapolate the rest | Catching the extrapolated tail while crediting the grounded head |
| `unanswerable` | Says nothing on the topic | Refuse (good) or fabricate (bad) | Distinguishing a correct refusal from a fabrication |
| `false_premise` | Contradicts or omits a premise the question asserts | Accept the premise and confabulate | Catching a claim built on a premise the context never granted |

Each question also has a `note`: what the context does and doesn't support. It
is **labeling guidance**, not a label — the human still labels the actual claims
a model generates, since a model can be unsupported in ways the note didn't
anticipate (or correctly refuse where the note expected fabrication).

## Measured mix (from `inspect_questions.py`)

```
contexts:  12
questions: 40

grounded        15   37.5%
partial         12   30.0%
unanswerable     6   15.0%
false_premise    7   17.5%
trap subtotal   25   62.5%
```

Contexts span the classifier's five categories (procurement, operations, policy,
technology, industry) and six domains (air, land, sea, cyber, space, multi), so
the instrument isn't concentrated in one slice of the domain.

## The 40% is a target, not a guarantee — and that's the honest part

`meta.target_unsupported_claim_share: 0.40` is a **claim-level** target. This
file controls the **question-level** mix (62.5% traps). The two are not the same
number: each answer decomposes into several claims, a trap question still yields
some supported claims, and a model that refuses an `unanswerable` question
produces *no* fabricated claim at all.

So the real unsupported-claim share is **measured in the answer-generation
slice**, not asserted here. If it lands materially off 40%, the fix is to
rebalance this file (shift questions between types) and regenerate — the mix is a
tunable hypothesis, and the measurement is what settles it. Claiming a
by-construction 40% would be exactly the kind of soft number this project exists
to avoid.

## File format

```yaml
meta:
  version: floor-0.1
  synthetic: true
  target_unsupported_claim_share: 0.40
  densification_types: [grounded, partial, unanswerable, false_premise]
contexts:
  - id: ctx-01
    category: procurement        # classifier category
    domain: air                  # classifier operational_domain
    text: |                      # the grounding passage (synthetic)
      ...
    questions:
      - id: q-01
        type: grounded           # one of the four densification types
        question: "..."
        note: "what the context supports / doesn't — labeling guidance, not a label"
```
