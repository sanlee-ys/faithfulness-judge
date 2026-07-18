# faithfulness-judge

**Can an LLM judge be trusted to tell you when a grounded answer is making
things up?** This project measures that — on public defense text — and reports
how far the judge can be trusted, including where it can't.

## Results

**Both tiers are substantial faithfulness judges.** Measured against 191 scored
human-labeled claims:

| Judge | Binary κ | Raw agreement (95% Wilson CI) | Unsupported recall | Ternary κ |
|---|---|---|---|---|
| **Opus** (claude-opus-4-8) | **0.742** | 89.0% [83.8%, 92.7%] | 97.9% | 0.674 |
| **Sonnet** (claude-sonnet-5) | **0.696** | 87.4% [82.0%, 91.4%] | 89.6% | 0.654 |

Gold set: 193 claims (143 supported, 12 partial, 36 unsupported, 2 `na`);
n = 191 scored, `na` excluded. Binary κ collapses `partial` into `unsupported`
([SCOPE.md](SCOPE.md) Decision 1). 0 unparsed verdicts for either judge. Full
output, confusion matrices, and the misjudgment log: [evals/results.md](evals/results.md).

**What it means:** κ ≈ 0.70–0.74 with ~88% raw agreement and 90–98% recall on the
fabrication class puts both judges in "substantial agreement" territory — good
enough to use as an automated faithfulness check. Opus edges Sonnet on κ, **but
the confidence intervals overlap** (83.8–92.7 vs 82.0–91.4), so this is not
evidence that Opus is meaningfully better at the task. The one real separation is
**unsupported recall: 97.9% vs 89.6%** — Opus misses roughly one fabrication in
fifty where Sonnet misses one in ten. If catching made-up claims is the job, that
gap is the reason to pay; the overall agreement number is not.

For this task **the cheap tier is already good enough, and escalation buys
little.** That is the third "measure-before-escalate" verdict in this portfolio,
after BM25 grounding and tiered model routing — see
[ADR-001](decisions/001-both-tiers-substantial.md) for the decision record,
including the measurement artifact that nearly buried this result.

### Limits — read these before trusting the number

- **n = 191 claims.** The CIs are ~9 points wide. Differences smaller than that
  are noise, including the Opus-vs-Sonnet κ gap.
- **One labeler.** The gold is San's labels alone; there is **no inter-annotator
  agreement measured**, so the "human ground truth" here is one person's
  consistent reading of the rubric ([docs/labeling-guide.md](docs/labeling-guide.md)),
  not a validated consensus. A judge agreeing with this gold at κ=0.74 has not
  been shown to agree with *humans in general* at κ=0.74.
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
