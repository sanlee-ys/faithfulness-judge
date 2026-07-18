# faithfulness-judge

**Can an LLM judge be trusted to tell you when a grounded answer is making
things up?** This project measures that — on public defense text — and reports
how far the judge can be trusted, including where it can't.

## Results

_Pending._ Once the gold set is labeled and the judges are scored, this section
leads with the headline: **judge-vs-human agreement (Cohen's κ) with confidence
intervals, and the floor below which the judge's verdict isn't trustworthy.**
No number is reported here until it's earned — see [SCOPE.md](SCOPE.md) for the
plan that produces it.

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
- ~150 claims hand-labeled `supported` / `partial` / `unsupported` against their
  cited spans — the human gold.
- Two judges (Sonnet + Opus) rate the same 150 blind; scored by Cohen's κ, raw
  agreement, per-class recall on the `unsupported` class, and a log of every
  claim where judge ≠ human.

Three method decisions are locked in [SCOPE.md](SCOPE.md): ternary labels
reported both ways, claim decomposition frozen up front (the judge only rates,
never splits), and both judge tiers run so the Sonnet-vs-Opus gap is itself a
finding.

## Status

Scope locked; building the QA fixture and the densified question set. All text
is public or synthetic — no proprietary or non-public data anywhere in this
project.
