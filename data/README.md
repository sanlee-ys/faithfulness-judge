# Data — the densified question set

`questions.yaml` is the **instrument** the rest of the project runs on: grounding
contexts + questions, engineered so that a QA model answering from the context
alone produces a healthy share of *unsupported* claims. That density is what lets
the faithfulness judge be tested on the hard case (catching fabrication) and not
just the easy one (blessing good answers).

Verify its shape yourself:

```bash
python3 scripts/inspect_questions.py           # summary
python3 scripts/inspect_questions.py --strict  # exit 1 on any structural problem
```

## Contexts are real, sourced, public-domain DVIDS text

Every context is an excerpt from a **DVIDS** (Defense Visual Information
Distribution Service) article — U.S. military public affairs, public domain as a
work of U.S. government employees. Each context carries a `source` block with the
article title and URL, so any labeler or reviewer can check a claim against the
original. Passages are excerpted, and occasionally lightly condensed, from the
article body (photo captions and pull-quotes stripped).

**Groundedness is defined against the excerpt, not the article.** The QA model
sees only the passage in `text`, so a claim is "supported" only if that passage
supports it — not if it's merely true, and not if it appears elsewhere in the
full article. Several questions exploit exactly this: they ask for something the
full article might contain but the excerpt does not.

This replaces the earlier synthetic-context draft. The scope doc always called
for the DVIDS corpus; the synthetic passages were a floor-only stand-in, now
retired in favor of the real thing.

## The operations / procurement skew is real and kept honest

DVIDS is government public affairs, so its coverage clusters in **operations**
(exercises, deployments) and **procurement** (contract awards, shipbuilding);
**industry** in the classifier's sense (company earnings, mergers) barely exists
there. The set spans all five classifier categories and all six domains, but the
mix leans ops/procurement by the nature of the source — the same skew the
`defense-news-classifier` repo documented for its DVIDS set. It's noted, not
hidden; a solid-tier expansion could broaden sources if category balance ever
mattered to a result (it doesn't for judging faithfulness).

## The densification taxonomy

Every question carries a `type`. Three of the four are "traps" designed to induce
unsupported claims; `grounded` is the control that keeps the judge honest about
precision.

| Type | What the context does | What a model tends to do | Tests the judge on |
| --- | --- | --- | --- |
| `grounded` | Fully supports a correct answer | Answer correctly | **Not** crying "unsupported" on good answers (precision / specificity) |
| `partial` | Supports part; the rest is absent | Answer the known part, then extrapolate the rest | Catching the extrapolated tail while crediting the grounded head |
| `unanswerable` | Says nothing on the topic | Refuse (good) or fabricate (bad) | Distinguishing a correct refusal from a fabrication |
| `false_premise` | Contradicts or omits a premise the question asserts | Accept the premise and confabulate | Catching a claim built on a premise the context never granted |

Each question also has a `note`: what the excerpt does and doesn't support. It is
**labeling guidance**, not a label — the human still labels the actual claims a
model generates, since a model can be unsupported in ways the note didn't
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

category (contexts): procurement 4, operations 4, technology 2, policy 1, industry 1
domain   (contexts): air 3, sea 3, land 2, cyber 2, multi 1, space 1
```

## The 40% is a target, not a guarantee — and that's the honest part

`meta.target_unsupported_claim_share: 0.40` is a **claim-level** target. This file
controls the **question-level** mix (62.5% traps). The two are not the same
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
  version: floor-0.2
  synthetic: false
  source: "DVIDS — U.S. military public affairs, public domain"
  target_unsupported_claim_share: 0.40
  densification_types: [grounded, partial, unanswerable, false_premise]
contexts:
  - id: ctx-01
    category: procurement        # classifier category
    domain: air                  # classifier operational_domain
    source:
      outlet: DVIDS
      id: "569395"               # DVIDS article id
      title: "..."
      url: "https://www.dvidshub.net/news/569395/..."
    text: |                      # the grounding excerpt (verbatim from the article)
      ...
    questions:
      - id: q-01
        type: grounded           # one of the four densification types
        question: "..."
        note: "what the excerpt supports / doesn't — labeling guidance, not a label"
```
