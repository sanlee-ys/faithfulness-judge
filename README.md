# faithfulness-judge

**Can an LLM judge be trusted to tell you when a grounded answer is making
things up?** This project measures that — on public defense text — and reports
how far the judge can be trusted, including where it can't.

## Results

**Both tiers are substantial faithfulness judges.** Measured against
<!-- figure:gold_scored -->189 scored human-labeled claims, on the gold set as
audited 2026-08-02:

| Judge | Binary κ | Raw agreement (95% Wilson CI) | Unsupported recall | Ternary κ |
|---|---|---|---|---|
| **Opus** (<!-- figure:opus_model -->claude-opus-4-8) | <!-- figure:opus_binary_kappa -->**0.762** | <!-- figure:opus_agreement -->89.9% [<!-- figure:opus_agreement_ci_low -->84.8%, <!-- figure:opus_agreement_ci_high -->93.5%] | <!-- figure:opus_unsupported_recall -->97.9% | <!-- figure:opus_ternary_kappa -->0.692 |
| **Sonnet** (<!-- figure:sonnet_model -->claude-sonnet-5) | <!-- figure:sonnet_binary_kappa -->**0.716** | <!-- figure:sonnet_agreement -->88.4% [<!-- figure:sonnet_agreement_ci_low -->83.0%, <!-- figure:sonnet_agreement_ci_high -->92.2%] | <!-- figure:sonnet_unsupported_recall -->89.6% | <!-- figure:sonnet_ternary_kappa -->0.672 |

Gold set: <!-- figure:gold_claims -->193 claims (<!-- figure:gold_supported -->141 supported,
<!-- figure:gold_partial -->12 partial, <!-- figure:gold_unsupported -->36 unsupported,
<!-- figure:gold_na -->4 `na`); n = <!-- figure:gold_scored -->189 scored, `na` excluded.
Binary κ collapses `partial` into `unsupported`
([SCOPE.md](SCOPE.md) Decision 1). <!-- figure:unparsed_total -->0 unparsed verdicts for
either judge. Full output, confusion matrices, and the misjudgment log:
[evals/results.md](evals/results.md).

**The gold set was audited, and it held: 28 of 30 adjudicated claims came back
unchanged.** That consistency result is the finding. Opus's κ moved
<!-- figure-exempt: the pre-audit value — a record of what the audit moved, not a current figure -->0.751<!-- /figure-exempt -->
→ <!-- figure:opus_binary_kappa -->0.762
in the process and **that rise must not be read as the judges being better than
previously published** — restricting the corrections to claims neither judge got
wrong, the drift check [ADR-002](decisions/002-solid-tier-call.md) pre-registered
before any label was looked at, leaves Opus at
<!-- figure-exempt: the drift-restricted view, produced by gold_audit.py rescore — evals/results.md scores one gold view and publishes no key for this -->0.752<!-- /figure-exempt -->, essentially flat. The rise
does not survive the restriction, which means it tracks the audit reaching a claim
both judges had gotten wrong rather than a gold-quality improvement. Both views are
published in full:
[ADR-002 Phase-2 Result](decisions/002-solid-tier-call.md#phase-2-result-2026-08-02).

**What it means:** κ ≈ 0.72–0.76 with ~89–90% raw agreement puts both judges in
"substantial agreement" territory — good enough to use as an automated
faithfulness check. Opus edges Sonnet on κ, **but the confidence intervals
overlap** (<!-- figure:opus_agreement_ci_low -->84.8–<!-- figure:opus_agreement_ci_high -->93.5
vs <!-- figure:sonnet_agreement_ci_low -->83.0–<!-- figure:sonnet_agreement_ci_high -->92.2),
so this is not evidence that Opus is meaningfully better at the task.

**The same objection applies to unsupported recall — and the class it is measured
over is not the one its name suggests.** <!-- figure:opus_unsupported_recall -->97.9%
vs <!-- figure:sonnet_unsupported_recall -->89.6% is <!-- figure:opus_unsupported_catches -->47
vs <!-- figure:sonnet_unsupported_catches -->43 catches out of
<!-- figure:gold_binary_unsupported -->48, and that denominator is the *binary*
`unsupported` class, which has `partial` collapsed into it. Restrict to gold
`unsupported` proper — outright fabrication, n = <!-- figure:gold_unsupported -->36 — and
the two tiers are **identical**: both miss the same single claim,
35/36 each, zero discordant pairs. All four discordant pairs behind the recall gap
carry gold label `partial`. So the gap measures how the tiers treat
<!-- figure:gold_partial -->12 borderline
hedged claims, in the label class the rubric itself calls least crisp — not how
well they catch fabrication. On those four pairs McNemar's exact test gives
<!-- figure-exempt: McNemar's exact test is computed in ADR-001/ADR-002, not by score.py — evals/results.md publishes no key for it -->**p = 0.125**<!-- /figure-exempt -->:
the direction is consistent (no reversals in <!-- figure:gold_binary_unsupported -->48
chances), but four
pairs cannot establish the size of a gap. An earlier version of this README
advanced it as the reason to pay for the premium tier and described it as "recall
on the fabrication class"; the significance test and the class restriction are the
two corrections
([ADR-001 Amendment](decisions/001-both-tiers-substantial.md#amendment-2026-07-19),
[ADR-002 Finding 1](decisions/002-solid-tier-call.md)).

**So: neither axis separates the tiers on this set.** Paired over all
<!-- figure:gold_scored -->189 scored
claims on binary correctness, Opus is right where Sonnet is wrong 6 times and
Sonnet right where Opus is wrong 3 times —
<!-- figure-exempt: McNemar's exact test is computed in ADR-002, not by score.py — evals/results.md publishes no key for it -->McNemar exact **p = 0.508**<!-- /figure-exempt -->, about as
null as a test gets. For this task **the cheap tier is already good enough, and
escalation is not evidenced** — the third "measure-before-escalate" verdict in
this portfolio, after BM25 grounding and tiered model routing. See
[ADR-001](decisions/001-both-tiers-substantial.md) for the decision record,
including the measurement artifact that nearly buried this result, and
[ADR-002](decisions/002-solid-tier-call.md) for the evidence that what now limits
these numbers is the ground truth rather than the model.

### Limits — read these before trusting the number

- **n = <!-- figure:gold_scored -->189 scored claims**
  (<!-- figure:gold_claims -->193 gold, <!-- figure:gold_na -->4 `na` excluded). The CIs
  are ~9 points wide. Differences smaller than that are noise — that includes the
  Opus-vs-Sonnet κ gap **and** the unsupported-recall gap, whose denominator is
  only <!-- figure:gold_binary_unsupported -->48.
- **One labeler.** The gold is San's labels alone; there is **no inter-annotator
  agreement measured**, so the "human ground truth" here is one person's
  consistent reading of the rubric ([docs/labeling-guide.md](docs/labeling-guide.md)),
  not a validated consensus. A judge agreeing with this gold at κ=0.76 has not
  been shown to agree with *humans in general* at κ=0.76. **The 2026-08-02 audit
  does not change this.** It is a single-labeler *consistency* audit — the same
  person re-reading his own labels against the rubric, blind to how the models
  scored them. That measures whether the gold is self-consistent. It cannot
  measure whether it is right, and it is never inter-annotator agreement.
- **The gold set has been audited twice, and moved both times.** In July, two
  claims labeled `supported` turned out to be filler with no factual assertion,
  which the rubric names as canonical `na`;
  <!-- figure-exempt: a record of the 2026-07-19 re-scoring event, not current figures. These four kappas describe what moved on that date and stay as written however far kappa moves afterwards -->re-scoring
  moved Opus κ 0.742 → 0.751 and Sonnet κ 0.696 → 0.716.<!-- /figure-exempt -->
  In August, a pre-registered blind audit re-read 30
  structurally selected claims and changed 2 — one more instance of that same
  offer-to-help shape, and one reversal *of* a July correction, where the claim
  does assert that the excerpt omits a detail and so is a correct refusal rather
  than filler. Single-labeler ground truth is worth auditing, not just declaring
  — and the second audit is also the evidence that the first one was incomplete.
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

**Floor complete, and the solid-tier call is closed.** Instrument built,
193-claim gold set hand-labeled, both judges run and scored, and the gold itself
audited under a pre-registered blind rule — the numbers above are the deliverable.

The open call was "spend a solid-tier pass — a second labeler, larger n, or a
third judge tier?" It was ruled on 2026-08-02: **none of the three**
([ADR-002](decisions/002-solid-tier-call.md)). The measured reason is that the
model axis is already saturated — <!-- figure-exempt: judge-vs-judge agreement, computed in ADR-002 Finding 3 — score.py scores each judge against the human gold and publishes no key for this -->the two judges agree with *each other* 95.8% of
the time<!-- /figure-exempt --> while agreeing with the human 88–90%, so the residual disagreement is a
property of the judge-vs-human construct, not of model capability. What that
leaves binding is ground-truth quality, so the spend went to a $0 blind audit of
the gold instead of to more model or more n. A Haiku tier remains available as a
separate concern, not a scheduled one.

All text is public or synthetic — no proprietary or non-public data anywhere in
this project.
