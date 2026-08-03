# CLAUDE.md — Faithfulness Judge

## Project

A measurement project that answers one question: **how well can an LLM judge detect
unsupported claims, measured against human labels, on public defense text?**

The deliverable is a measurement *of the measurer*. Not "does my QA system hallucinate,"
but "can an LLM be trusted to tell me whether an answer is grounded." Built on **public
DVIDS text only** (U.S. military public affairs, public domain) — no proprietary or
non-public data anywhere in this project.

This is a personal portfolio project. **The measured eval result is the centerpiece, not
a working demo.** The QA system here is a fixture for generating answers, not a product.

## Read these first

| Doc | What it holds |
|---|---|
| [SCOPE.md](SCOPE.md) | The question, in/out of scope, and the **three locked decisions** |
| [data/README.md](data/README.md) | The instrument: densification taxonomy, DVIDS sourcing, the pipeline |
| [docs/labeling-guide.md](docs/labeling-guide.md) | The human labeling rubric and the three consistency calls |
| [evals/results.md](evals/results.md) | The scored output, confusion matrices, misjudgment log |
| [decisions/](decisions/) | ADRs — the durable record of what was decided and why |

## Current state

**The floor is complete and the gold has been audited.** Instrument built, 193-claim gold
set hand-labeled, both judges run and scored
([ADR-001](decisions/001-both-tiers-substantial.md)), gold audited blind under a
pre-registered rule ([ADR-002](decisions/002-solid-tier-call.md)). Canonical figures, on
the **audited** gold:

| Judge | Binary κ | Raw agreement (95% Wilson CI) | Unsupported recall |
|---|---|---|---|
| Opus (<!-- figure:opus_model -->claude-opus-4-8) | <!-- figure:opus_binary_kappa -->0.762 | <!-- figure:opus_agreement -->89.9% [<!-- figure:opus_agreement_ci_low -->84.8%, <!-- figure:opus_agreement_ci_high -->93.5%] | <!-- figure:opus_unsupported_recall -->97.9% |
| Sonnet (<!-- figure:sonnet_model -->claude-sonnet-5) | <!-- figure:sonnet_binary_kappa -->0.716 | <!-- figure:sonnet_agreement -->88.4% [<!-- figure:sonnet_agreement_ci_low -->83.0%, <!-- figure:sonnet_agreement_ci_high -->92.2%] | <!-- figure:sonnet_unsupported_recall -->89.6% |

Both tiers are substantial judges. n = <!-- figure:gold_scored -->189 scored
(<!-- figure:gold_claims -->193 gold, <!-- figure:gold_na -->4 `na` excluded) — the audit's
two changes cancel in the class distribution, so *n* and the <!-- figure:gold_supported -->141/<!-- figure:gold_partial -->12/<!-- figure:gold_unsupported -->36/<!-- figure:gold_na -->4
split are unchanged from the floor.

**Never publish the Opus κ rise as a judge-quality improvement.** <!-- figure-exempt: the pre-audit value — a record of what the audit moved, not a current figure -->0.751<!-- /figure-exempt -->
→ <!-- figure:opus_binary_kappa -->0.762 is the
fully-audited view; restricted to corrections on claims no judge got wrong it is <!-- figure-exempt: the drift-restricted view, produced by gold_audit.py rescore — evals/results.md scores one gold view and publishes no key for this -->0.752<!-- /figure-exempt -->,
flat. ADR-002's own pre-registered criterion says a rise that does not survive that
restriction tracked the judges and is not a gold-quality result. Every publication of these
figures carries both views. **The headline of the audit is "the gold held: 28 of 30
confirmed"** — a consistency result, not "κ improved."

**Neither axis separates the tiers — do not claim Opus is meaningfully better.** Unchanged
by the audit. The κ CIs overlap; <!-- figure-exempt: McNemar's exact tests are computed in ADR-001/ADR-002, not by score.py — evals/results.md publishes no keys for them -->the
paired McNemar on binary correctness is p = 0.5078 (6/3)<!-- /figure-exempt -->; and the
unsupported-recall gap (<!-- figure:opus_unsupported_recall -->97.9%
vs <!-- figure:sonnet_unsupported_recall -->89.6% = <!-- figure:opus_unsupported_catches -->47
vs <!-- figure:sonnet_unsupported_catches -->43 of <!-- figure:gold_binary_unsupported -->48) is <!-- figure-exempt: McNemar's exact test is computed in ADR-001, not by score.py — evals/results.md publishes no key for it -->McNemar exact
p = 0.125<!-- /figure-exempt --> on 4 discordant pairs — **all four of which carry gold label
`partial`**, so restricted to gold `unsupported` proper
(n = <!-- figure:gold_unsupported -->36) the tiers are identical at 35/36 each. An
earlier version of this file named that recall gap as "the one real separation"; that was
the overclaim, corrected 2026-07-19
([ADR-001 Amendment](decisions/001-both-tiers-substantial.md#amendment-2026-07-19)), and
"recall on the fabrication class" was the residue of it, corrected 2026-08-02.

## Locked decisions (from SCOPE.md — don't relitigate without an ADR)

1. **Ternary labels, report both.** Label `supported`/`partial`/`unsupported`; collapse
   `partial → unsupported` for the headline binary κ, keep ternary in the appendix.
2. **Claim decomposition is frozen, not judged.** Claims are split once, deterministically,
   and frozen. The judge only *rates* pre-split claims, never re-splits — that isolates the
   one variable under test and avoids double circularity.
3. **Both judge tiers run.** The Sonnet-vs-Opus gap is itself a finding, and it honors the
   model-tier standard: escalate only where the eval shows it pays.

## Standing cautions (paid-for lessons — these cost real time)

- **The forced tool-use verdict is load-bearing.** `judge.py` records verdicts through a
  `record_verdict` tool with an enum schema and `tool_choice`. Do **not** "simplify" it
  back to a bare one-word prompt with a tight `max_tokens`, and do **not** try
  assistant-message **prefill** — prefill is *rejected* by claude-sonnet-5 and
  claude-opus-4-8. An earlier `max_tokens=10` truncated Sonnet's verdict on 39/191 claims
  (20%) and manufactured a false tier gap (Sonnet κ=0.43 vs its real ≈0.70). `MAX_TOKENS`
  must stay large enough for the model's preamble plus the tool call. Full story:
  [ADR-001](decisions/001-both-tiers-substantial.md).
- **`na` is excluded from scoring; unparsed verdicts count as disagreements.** Both are
  deliberate in `score.py`. Counting unparsed as disagreement is what made the truncation
  bug *visible* instead of silently dropping 20% of the set. Keep it.
- **Don't re-run the judges to "double-check."** Judging costs API spend and the committed
  artifacts (`data/judgments_*.yaml`, `evals/results.md`) are the record. Re-run only when
  a number is actually inconsistent, or when the harness itself changed — and if you do,
  re-run **both** judges so the comparison comes from an identical call shape.
- **Never score against a partial gold.** If any claim in `data/claims.yaml` has
  `label: null`, the gold set has been disturbed (a re-run of `build_gold_set.py` wipes
  labels back to null). Stop and reconcile — do not score, and do not publish a number
  computed over a partial set. Likewise, if `evals/results.md` disagrees with the numbers
  in the README or ADR-001, something was re-run: reconcile before writing anything.
  **Both halves of this are now mechanical.** CI runs `src/score.py` on every push and PR
  and fails if the committed `evals/results.md` isn't exactly what the code produces
  ([ADR-003](decisions/003-score-in-ci.md), `system/SYS-017` tier 1) — that is *artifact vs
  code*. Then `scripts/check_published_figures.py` asserts every figure this file and the
  README restate **against** that artifact
  ([ADR-004](decisions/004-assert-published-figures.md), `system/SYS-019`) — that is *claim
  vs artifact*. Any change that moves the numbers must commit the regenerated
  `evals/results.md` **and** the reconciled prose in the same PR. Note neither check gates on
  a **value**: κ is free to move, and there is deliberately no floor, because one measurement
  has no noise band under it. **ADRs are not checked** — they are dated records and their
  figures stay as written.
- **Figures in `README.md` and `CLAUDE.md` are marked, and the marks are load-bearing.**
  A restated figure opts in with `<!-- figure:<key> -->` immediately before it; the keys are
  derived from `evals/results.md` itself. A figure that is deliberately *not* current — a
  record of a past re-scoring, a drift-restricted view from `gold_audit.py`, or a statistic
  `score.py` doesn't produce (every McNemar *p* here) — goes inside
  `<!-- figure-exempt: reason --> ... <!-- /figure-exempt -->`, and the reason is required.
  An unmarked, unexempted κ or one-decimal percentage **fails the build**: an unmarked
  figure is never checked and drifts silently. Don't strip a marker to "clean up" the
  source — they render as nothing. **Never start a line with a marker.** In GFM a line
  beginning with `<!--` opens an HTML block, which splits the paragraph and stops inline
  formatting until the next blank line — so a line-initial marker breaks the rendered page
  while looking fine in the source. That fails the build too.
- **Read the misjudgment log before publishing any number.** That is what caught the
  truncation artifact one commit before it shipped. When a model scores unexpectedly
  badly, inspect the raw outputs before believing the metric.
- **Don't overclaim.** This is a floor: n=189, **one labeler with no inter-annotator
  agreement measured**, single pass, DVIDS operations/procurement skew. A soft number
  dressed up as solid is the only real failure mode this project has, and it has happened
  here once already
  ([ADR-001 Amendment](decisions/001-both-tiers-substantial.md#amendment-2026-07-19)).
  **Before publishing any tier comparison, run the significance test, not just the delta.**
- **The gold set is not above audit — and one audit was not enough.** The 2026-07-19 pass
  caught two claims mislabeled against this repo's own rubric. The 2026-08-02 blind audit
  then found a **third** instance of the same offer-to-help shape that had survived the
  first pass, *and* reversed one of the first pass's own calls (`help-q-13-c3`, which does
  assert that the excerpt omits a detail and is therefore a correct refusal, not filler).
  If a claim is filler, a meta-aside, or an offer to help, it is `na` — but check whether it
  also makes an assertion about the excerpt before calling it filler, and do not trust a
  label just because it is committed, or just because a previous audit already touched it.

## Tech stack

- Python 3.11+, deliberately minimal deps: `anthropic` + `pyyaml` (dev: `pytest`, `ruff`).
- LLM via the **Anthropic API**. Key from `ANTHROPIC_API_KEY` — **never hardcode keys**.
- Structured output via **tool use with an enum schema**, not prompt-and-parse.
- No `[build-system]` — this is a uv *application*, not a package. Imports resolve via
  pytest's `pythonpath = ["src"]` plus a small path shim in each script, matching the
  sibling repos' flat-`src` layout.
- Scoring is plain Python (Cohen's κ, Wilson intervals, confusion matrices) — no ML
  framework, matching the classifier repo's ADR-004 call.
- Style: **ruff** at line length 88, targeting py311.

```bash
uv sync --group dev                              # build the env
uv run pytest                                    # 29 offline tests, no key needed
uv run ruff check src/ tests/                    # lint
uv run python scripts/check_published_figures.py # README/CLAUDE.md figures vs the artifact

uv run python scripts/inspect_questions.py --strict   # validate the instrument
uv run python src/generate_answers.py --variant assertive --dry-run  # prompts, no API call
uv run python src/build_gold_set.py              # answers -> claims.yaml (offline)
uv run python src/labels.py export               # claims.yaml -> data/labeling.csv
uv run python src/labels.py apply                # csv -> back into claims.yaml
uv run python src/judge.py --judge opus --dry-run     # drop --dry-run to spend
uv run python src/score.py                       # -> evals/results.md

uv run python src/gold_audit.py select           # -> data/gold-audit-worksheet.md
uv run python src/gold_audit.py rescore          # after the worksheet is filled
```

The judging and answer-generation steps cost money; everything else is offline. Both
`generate_answers.py` and `judge.py` take `--dry-run` and `--limit` — use them.

## Project structure

```
data/       questions.yaml (the instrument), answers_<variant>.yaml,
            claims.yaml (the gold set), judgments_<judge>.yaml
src/        dataset.py (paths/loaders), generate_answers.py, decompose.py (frozen
            splitter), build_gold_set.py, labels.py (CSV round-trip), judge.py, score.py
scripts/    inspect_questions.py (instrument validator)
evals/      results.md — κ, CIs, confusion, per-class recall, misjudgment log
decisions/  ADRs
tests/      offline tests; no test may require an API key
```

Pipeline:

```
questions.yaml ─generate_answers.py─▶ answers_<variant>.yaml ─build_gold_set.py─▶
claims.yaml ─labels.py─▶ human gold ─judge.py─▶ judgments_<judge>.yaml ─score.py─▶ results.md
```

## How to work with me

- **Explain the key decisions** briefly as you make them (why this metric, why this prompt
  shape) so the code is understood, not just run.
- Work in **small steps** on anything ambiguous or consequential; report at the end for
  mechanical, already-decided batches.
- When there's a real design choice (how to handle a `partial`, whether a claim is one
  claim or two), **surface it and ask** rather than silently picking.
- **Verify before asserting.** Check the committed artifacts before making a claim about a
  number. Don't recompute what `evals/results.md` already records, and don't state a fact
  about the data you haven't looked at.

<!-- shared:parallel-sessions v1 -->
## Working across parallel sessions (hard rule)

Sessions cannot see each other's uncommitted work — **`main` is the only shared coordination point**. So: **one concern per session → one branch → one PR**; check open PRs and branches before starting; branch from fresh `main` and merge fast; **serialize the collision hotspots** and parallelize by independent *file*, not by task; keep the wiring for any generated or aggregated file in one hand. Full rule + the triple-build incident that produced it: [agent-ops `conventions/parallel-sessions.md`](https://github.com/sanlee-ys/agent-ops/blob/main/conventions/parallel-sessions.md).
<!-- /shared:parallel-sessions -->

**This repo's collision hotspots:** `README.md`, `pyproject.toml`, `uv.lock`,
`data/claims.yaml`, `evals/results.md`. Safe to parallelize: separate `src/` modules,
separate test files, isolated docs.

**The generated artifacts are the sharp edge here.** `claims.yaml`, `judgments_*.yaml`, and
`results.md` are regenerated wholesale, so two sessions touching them do not merge — they
overwrite. One hand does the regeneration.

## Definition of done (floor)

1. 40 answers generated, densified, committed with source spans. ✅
2. ~150+ claims hand-labeled ternary — the gold set (landed at 193). ✅
3. Both judges run, labels produced for the same claims. ✅
4. `evals/` output: κ + raw agreement with CIs, confusion matrix, per-class recall, the
   Sonnet-vs-Opus gap, and a misjudgment log. ✅
5. README leading with the number and stating the floor honestly. ✅

**Solid tier: CLOSED 2026-08-02.** [ADR-002](decisions/002-solid-tier-call.md) ruled
**Option D** — a blind, pre-registered audit of the gold set, $0 API, no judge re-runs —
over a second labeler, larger *n*, or a Haiku tier, and both phases have now landed. Phase
1 shipped the instrument (`src/gold_audit.py`, `data/gold-audit-worksheet.md`); phase 2
shipped San's 30 adjudications, the 2 resulting label changes, the re-scored artifact, and
the corrected figures reported both ways. **There is no open call in this repo.**

Read ADR-002's *Ruling* and *Phase-2 Result* sections before touching anything in this
area. Still binding: **no model may adjudicate, relabel, or propose a label for any gold
claim** — that is the rule that keeps this from becoming the circular eval it exists to
avoid — and the selection rule is frozen. A future audit changes `SELECTION_RULES` and
re-runs; it does not edit the worksheet in place.

**A Haiku tier is the only thing left on the shelf**, and it is a separate concern, not a
continuation of this one: one judge run over the 189 committed claims, its own branch and
PR, `src/paired_compare.py` already there to score it offline. It was deliberately left out
of ADR-002 so it would not ride on a gold with unrepaired defects. That objection is now
gone, which makes it cheap — but it costs API spend and nobody has asked for it.

## Owner-only calls

- **This repo is PUBLIC** (flipped 2026-07-18, once the floor result was real and its
  limits were stated). Treat everything here as world-readable: no keys, no local paths,
  no employer specifics, and **no references to San's private repos**.
- **Any outward publication or portfolio linking is still San's call** — being public is
  not the same as being promoted. Don't link it from a portfolio surface, résumé, or
  writeup without asking.

## Windows / environment notes

- San is on **Windows/PowerShell**. No `&&` chaining in PowerShell; no `echo >` redirects
  (they write UTF-16).
- `uv` here auto-loads `.env`. If it's missing or corrupt, `uv run --no-env-file ...`
  bypasses it — and none of the offline work (tests, lint, scoring, docs) needs a key.
- If `uv sync` hits Windows Defender file-lock races (`Access is denied`, a different
  package each retry), don't retry piecemeal: `uv venv --clear && uv sync` rebuilds clean.

<!-- shared:links-verify v1 -->
## Links — verify before sending (hard rule)

Links given in chat must resolve: **full `github.com/<owner>/<repo>/blob/<ref>/<path>` URLs only**, **verify the path exists on the ref before sending** (unverified → say so), and **branch links are perishable** (prefer `main` once merged). Full rule + rationale: [agent-ops `conventions/links-verify.md`](https://github.com/sanlee-ys/agent-ops/blob/main/conventions/links-verify.md).
<!-- /shared:links-verify -->
