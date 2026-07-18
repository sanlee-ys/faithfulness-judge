# Scope — Faithfulness-Judge Validation (floor version)

## The question

**How well can an LLM judge detect unsupported claims, measured against human
labels, on public defense text?**

The deliverable is a measurement *of the measurer* — not "does my QA system
hallucinate," but "can an LLM be trusted to tell me whether an answer is
grounded."

## Why this is distinct from the classifier

The [defense-news-classifier](https://github.com/sanlee-ys/defense-news-classifier)
measures classification quality against cheap, objective labels. This project
measures **judge reliability** against expensive, subjective labels — the
opposite ground-truth regime. It reuses that project's machinery (LLM-judge
harness, Wilson confidence intervals, gold-set discipline) but answers a
question the classifier deliberately couldn't. The honest contribution is
publishing both the agreement number *and* the floor below which it can't be
trusted.

## In scope (floor)

- **~40 grounded QA answers** over public defense text (reuse the DVIDS / public
  corpus), **adversarially densified** so ~40% of claims are unsupported —
  questions deliberately under-grounded so the minority class populates without
  a 600-claim slog.
- **~150 claims hand-labeled**: `supported` / `partial` / `unsupported`, each
  judged against its cited span. This is the human gold; the project depends on
  it.
- **Two LLM judges** (see Decision 3) labeling the same 150 blind.
- **Headline:** judge-vs-human Cohen's κ + raw agreement with confidence
  intervals, a confusion breakdown, and **judge recall on the `unsupported`
  class** (catching the made-up stuff is the hard job).
- **README leads with** the agreement number and an explicit **"below this κ I
  wouldn't trust the judge" floor statement.**

## Out of scope

- A polished / interactive QA product — the QA system is a fixture to generate
  answers, not a deliverable.
- Retrieval optimization, embeddings, multi-judge ensembles, large *n* (all
  "solid tier" or later, not the floor).
- **Reducing** hallucination. This measures the ruler; it does not move the
  number.

## Decisions (locked)

1. **Label schema — ternary, report both.** Label
   `supported` / `partial` / `unsupported`; collapse `partial → unsupported` for
   the headline binary κ, keep ternary in the appendix. Shows the ambiguity was
   seen, costs nothing.
2. **Claim decomposition — frozen, not judged.** Decompose the gold answers into
   claims once, by hand / deterministically, and freeze that split. The judge
   only *rates* pre-split claims — isolating the one variable under test
   (rating), not splitting. Avoids double circularity.
3. **Judge tier — run both.** Run Sonnet and Opus judges on the same 150 (cheap
   at this *n*), lead with whichever agrees better, and report the gap.
   "Opus κ=X, Sonnet κ=Y" is itself a finding, and honors the "escalate only
   where it pays" model-tier standard.

## Definition of done (floor)

1. 40 answers generated, densified, committed with source spans.
2. 150 claims hand-labeled (ternary) — the gold set.
3. Both judges run, labels produced for the same 150.
4. `evals/` output: κ + raw agreement with CIs, confusion matrix, per-class
   recall, Sonnet-vs-Opus gap, and a misjudgment log (the claims where
   judge ≠ human — the interesting ones).
5. README leading with the number and stating the floor honestly.

## Risk to name in the README, not hide

If κ lands mediocre (~0.4–0.6, plausible for faithfulness), **that is the
result** — "here's how hard this is to automate, here's the floor." The only
real failure mode is a *soft* number dressed up as solid.
