# faithfulness-judge

**Can an LLM judge be trusted to tell you when a grounded answer is making
things up?** This project measures that — on public defense text — and reports
how far the judge can be trusted, including where it can't.

## Results

**Both tiers are substantial faithfulness judges.** Measured against 189 scored
human-labeled claims:

| Judge | Binary κ | Raw agreement (95% Wilson CI) | Unsupported recall | Ternary κ |
|---|---|---|---|---|
| **Opus** (claude-opus-4-8) | **0.751** | 89.4% [84.2%, 93.0%] | 97.9% | 0.682 |
| **Sonnet** (claude-sonnet-5) | **0.716** | 88.4% [83.0%, 92.2%] | 89.6% | 0.672 |

Gold set: 193 claims (141 supported, 12 partial, 36 unsupported, 4 `na`);
n = 189 scored, `na` excluded. Binary κ collapses `partial` into `unsupported`
([SCOPE.md](SCOPE.md) Decision 1). 0 unparsed verdicts for either judge. Full
output, confusion matrices, and the misjudgment log: [evals/results.md](evals/results.md).

**What it means:** κ ≈ 0.72–0.75 with ~89% raw agreement and 90–98% recall on the
fabrication class puts both judges in "substantial agreement" territory — good
enough to use as an automated faithfulness check. Opus edges Sonnet on κ, **but
the confidence intervals overlap** (84.2–93.0 vs 83.0–92.2), so this is not
evidence that Opus is meaningfully better at the task.

**The same objection applies to unsupported recall.** 97.9% vs 89.6% is 47 vs 43
catches out of 48. Only the disagreeing pairs carry information: Opus caught 4 that
Sonnet missed and Sonnet caught 0 that Opus missed, so McNemar's exact test gives
**p = 0.125**. The direction is consistent (no reversals in 48 chances), but four
discordant pairs cannot establish the size of the gap. An earlier version of this
README advanced that gap as the reason to pay for the premium tier; the test is the
correction ([ADR-001 Amendment](decisions/001-both-tiers-substantial.md#amendment-2026-07-19)).

**So: neither axis separates the tiers on this set.** For this task **the cheap
tier is already good enough, and escalation is not evidenced** — the third
"measure-before-escalate" verdict in this portfolio, after BM25 grounding and
tiered model routing. If the recall gap is real, showing it needs a larger
`unsupported` class than 48, which is what the solid tier below would buy. See
[ADR-001](decisions/001-both-tiers-substantial.md) for the decision record,
including the measurement artifact that nearly buried this result.

### Limits — read these before trusting the number

- **n = 189 scored claims** (193 gold, 4 `na` excluded). The CIs are ~9 points
  wide. Differences smaller than that are noise — that includes the
  Opus-vs-Sonnet κ gap **and** the unsupported-recall gap, whose denominator is
  only 48.
- **One labeler.** The gold is San's labels alone; there is **no inter-annotator
  agreement measured**, so the "human ground truth" here is one person's
  consistent reading of the rubric ([docs/labeling-guide.md](docs/labeling-guide.md)),
  not a validated consensus. A judge agreeing with this gold at κ=0.75 has not
  been shown to agree with *humans in general* at κ=0.75.
- **The gold set has been corrected once.** Two claims labeled `supported` were
  filler with no factual assertion — an offer to help and a suggestion to check the
  original source — which the rubric names as canonical `na`. Re-labeling and
  re-scoring moved Opus κ 0.742 → 0.751 and Sonnet κ 0.696 → 0.716; unsupported
  recall was unchanged. Single-labeler ground truth is worth auditing, not just
  declaring.
- **Floor tier.** Single pass, no ensembles, no prompt tuning of the judges, no
  retrieval. This measures the ruler as built, not the best achievable ruler.
- **Domain skew.** Claims come from public DVIDS text, which skews toward
  operations and procurement reporting over short passages. Faithfulness judging
  over long documents, technical specifications, or other domains is untested here.
- **Below κ ≈ 0.6 I wouldn't trust an automated verdict unreviewed.** Both judges
  clear that bar on this set; neither clears the bar for using a verdict as a
  final answer without a human in the loop on anything consequential.

## The question

Not "does the QA system hallucinate?" but "**can an LLM be trusted to tell me
whether an answer is grounded?**" The deliverable is a measurement *of the
measurer*: how well an LLM judge's supported/unsupported verdicts agree with a
human's, on claims drawn from answers over public defense reporting.

## Why it's distinct

The [defense-news-classifier](https://github.com/sanlee-ys/defense-news-classifier)
measures classification quality against **cheap, objective** labels. This
project measures **judge reliability** against **expensive, subjective** labels —
the opposite ground-truth regime, and the harder one. It reuses that project's
harness (LLM judge, Wilson confidence intervals, gold-set discipline) but
answers a question objective labels can't. If the agreement comes out mediocre,
that is the result, stated plainly — a floor is a finding.

## Method (floor version)

- ~40 grounded QA answers over public defense text, **adversarially densified**
  so ~40% of claims are unsupported (the minority class is the hard one, so it
  gets populated on purpose rather than fished for).
- 193 claims hand-labeled `supported` / `partial` / `unsupported` / `na` against
  their cited spans — the human gold.
- Two judges (Sonnet + Opus) rate the same claims blind; scored by Cohen's κ, raw
  agreement, per-class recall on the `unsupported` class, and a log of every
  claim where judge ≠ human.

Three method decisions are locked in [SCOPE.md](SCOPE.md): ternary labels
reported both ways, claim decomposition frozen up front (the judge only rates,
never splits), and both judge tiers run so the Sonnet-vs-Opus gap is itself a
finding.

## Status

**Floor complete.** Instrument built, 193-claim gold set hand-labeled, both
judges run and scored — the numbers above are the deliverable. Whether to spend
a "solid tier" pass (a second labeler to tighten the CI, larger n, or a third
judge tier to complete the cost/quality curve) is an open call, not scheduled.

All text is public or synthetic — no proprietary or non-public data anywhere in
this project.
