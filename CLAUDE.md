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

**The floor is complete.** Instrument built, 193-claim gold set hand-labeled, both judges
run and scored ([ADR-001](decisions/001-both-tiers-substantial.md)):

| Judge | Binary κ | Raw agreement (95% Wilson CI) | Unsupported recall |
|---|---|---|---|
| Opus (claude-opus-4-8) | 0.742 | 89.0% [83.8%, 92.7%] | 97.9% |
| Sonnet (claude-sonnet-5) | 0.696 | 87.4% [82.0%, 91.4%] | 89.6% |

Both tiers are substantial judges. **The CIs overlap — do not claim Opus is meaningfully
better.** The one real separation is unsupported recall (97.9% vs 89.6%).

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
  (20%) and manufactured a false tier gap (Sonnet κ=0.43 vs its real 0.696). `MAX_TOKENS`
  must stay large enough for the model's preamble plus the tool call. Full story:
  [ADR-001](decisions/001-both-tiers-substantial.md).
- **`na` is excluded from scoring; unparsed verdicts count as disagreements.** Both are
  deliberate in `score.py`. Counting unparsed as disagreement is what made the truncation
  bug *visible* instead of silently dropping 20% of the set. Keep it.
- **Don't re-run the judges to "double-check."** Judging costs API spend and the committed
  artifacts (`data/judgments_*.yaml`, `evals/results.md`) are the record. Re-run only when
  a number is actually inconsistent, or when the harness itself changed — and if you do,
  re-run **both** judges so the comparison comes from an identical call shape.
- **Read the misjudgment log before publishing any number.** That is what caught the
  truncation artifact one commit before it shipped. When a model scores unexpectedly
  badly, inspect the raw outputs before believing the metric.
- **Don't overclaim.** This is a floor: n=191, **one labeler with no inter-annotator
  agreement measured**, single pass, DVIDS operations/procurement skew. A soft number
  dressed up as solid is the only real failure mode this project has.

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

uv run python scripts/inspect_questions.py --strict   # validate the instrument
uv run python src/generate_answers.py --variant assertive --dry-run  # prompts, no API call
uv run python src/build_gold_set.py              # answers -> claims.yaml (offline)
uv run python src/labels.py export               # claims.yaml -> data/labeling.csv
uv run python src/labels.py apply                # csv -> back into claims.yaml
uv run python src/judge.py --judge opus --dry-run     # drop --dry-run to spend
uv run python src/score.py                       # -> evals/results.md
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
- Prefer clear, readable code with short comments over clever one-liners.

## Working across multiple sessions

Each session runs fresh and can't see another's uncommitted work — the only shared
coordination point is `main`.

- **One concern per session → one branch → one PR.** If the deliverable doesn't fit in a
  sentence, it's two sessions.
- **Check open PRs and branches before starting.** A 10-second look prevents duplicate work.
- **Branch from fresh `main`, merge fast, delete the branch on merge.**
- **Serialize the collision hotspots:** `README.md`, `pyproject.toml`, `uv.lock`,
  `data/claims.yaml`, `evals/results.md`. Safe to parallelize: separate `src/` modules,
  separate test files, isolated docs.
- **Generated artifacts can't be merged.** `claims.yaml`, `judgments_*.yaml`, and
  `results.md` are regenerated wholesale — when several pieces of work feed one, author the
  content in parallel but keep the regeneration in one hand.

## Definition of done (floor)

1. 40 answers generated, densified, committed with source spans. ✅
2. ~150+ claims hand-labeled ternary — the gold set (landed at 193). ✅
3. Both judges run, labels produced for the same claims. ✅
4. `evals/` output: κ + raw agreement with CIs, confusion matrix, per-class recall, the
   Sonnet-vs-Opus gap, and a misjudgment log. ✅
5. README leading with the number and stating the floor honestly. ✅

**Open, unscheduled (solid tier, none committed):** a second labeler (the only thing that
upgrades the ground truth from *consistent* to *validated*), larger n to tighten the CIs,
or a third judge tier (Haiku) to complete the cost/quality curve.

## Owner-only calls

- **Repo visibility (private → public) is San's call.** Do not change it.
- **Any outward publication or portfolio linking is San's call.**

## Windows / environment notes

- San is on **Windows/PowerShell**. No `&&` chaining in PowerShell; no `echo >` redirects
  (they write UTF-16).
- `uv` here auto-loads `.env`. If it's missing or corrupt, `uv run --no-env-file ...`
  bypasses it — and none of the offline work (tests, lint, scoring, docs) needs a key.
- If `uv sync` hits Windows Defender file-lock races (`Access is denied`, a different
  package each retry), don't retry piecemeal: `uv venv --clear && uv sync` rebuilds clean.

## Links — verify before sending (hard rule)

Links given in chat must resolve: **full `github.com/<owner>/<repo>/blob/<ref>/<path>`
URLs only**, **verify the path exists on the ref before sending** (unverified → say so),
and **branch links are perishable** (prefer `main` once merged).
