# HANDOFF — 2026-07-18 — chair: OPUS

_You are a fresh session with zero prior context. Read `CLAUDE.md`, `SCOPE.md`,
and `docs/labeling-guide.md` before acting. The numbers you need are all in this
doc and in `evals/results.md` — do not recompute or re-run the judges to get
them. Escalate on anomaly, not task type._

## State

- **Branch:** `claude/project-ideas-p2xi8b` (the only dev branch; PR #1 targets `main`).
- **PR #1** is an **open draft**: "Floor build: instrument, QA pipeline, and 193-claim gold set." It needs its body finalized and to be flipped to ready-for-review (see job below).
- **Repo is private.** Going public is San's call — do not change visibility.
- **The floor is functionally complete.** Pipeline built, 193-claim gold set hand-labeled by San (the human ground truth), both judges run, scored. Everything is committed and pushed. `uv run pytest` is green (29 tests); `uv run ruff check src/ tests/` clean.

### The result (final, clean — from `evals/results.md`)

Gold set: **193 claims** — 143 supported, 12 partial, 36 unsupported, 2 na.
Scored n = **191** (2 `na` excluded). Human binary unsupported share: 48/191 = **25.1%**.

| Judge | Binary κ | Raw agreement (95% Wilson CI) | Unsupported recall | Ternary κ |
|---|---|---|---|---|
| **Opus** (claude-opus-4-8) | **0.742** | 89.0% [83.8%, 92.7%] | 97.9% | 0.674 |
| **Sonnet** (claude-sonnet-5) | **0.696** | 87.4% [82.0%, 91.4%] | 89.6% | 0.654 |

Binary κ = partial collapsed into unsupported (SCOPE Decision 1). 0 unparsed verdicts for both judges.

**What it means (write the README/ADR to say this, no more):**
- Both tiers are **substantial** faithfulness judges (κ ≈ 0.70–0.74, ~88% agreement with a human, 90–98% fabrication recall).
- Opus edges Sonnet, **but the CIs overlap** (83.8–92.7 vs 82.0–91.4). Do **not** claim Opus is meaningfully better. The one real edge is recall (97.9% vs 89.6%). Honest framing: for this task the cheap tier is already good enough; the premium tier's gain is marginal.
- This is the third "measure-before-escalate" verdict in the portfolio (after BM25 grounding and tiered routing), landing on "escalation barely pays."

### The artifact story (this is a headline, not a footnote)

The **first** scoring run reported Opus 0.70 / **Sonnet 0.43** — a false gap. Cause: `max_tokens=10` truncated Sonnet's verdict on **39/191 (20%)** of claims (it prefaced with reasoning and got cut off before the verdict word); those were scored as disagreements. On the claims Sonnet *did* answer, its κ was already 0.70. Fix: force the verdict through a tool-use enum (`record_verdict`), since assistant-message **prefill is not supported** by these models (that was a failed intermediate fix — commit `592d914`, superseded by `e6a18ab`). Real Sonnet κ = 0.696. **Caught by reading the misjudgment log before publishing** — that's the rigor signal worth surfacing.

## Your job this session

All drafting within an established pattern → Opus chair. No API key needed for any of this (scoring/judging is already done; do NOT re-run the judges).

1. **Write the README headline** — replace the `## Results` "pending" block in `README.md` (line ~7) with the results table above and the framing under "What it means." Keep the repo's ethos from `SCOPE.md`: **lead with the number, state limits honestly.** Limits to include: n=191, **single labeler** (San; no inter-annotator agreement), floor tier, DVIDS operations/procurement skew. Don't overclaim the Opus/Sonnet gap (CIs overlap).
2. **Draft an ADR** — no `decisions/` dir exists yet; create `decisions/001-both-tiers-substantial.md` (mirror the classifier repo's `NNN-title.md` ADR style: Context / Decision / Consequences). Record **two** things: (a) the both-tiers-substantial verdict with the numbers, and (b) the truncation-artifact lesson + the forced-tool-use fix (prefill unsupported → enum tool). Link it from the README.
3. **Finalize PR #1 and flip it out of draft.** Update the PR body to reflect the final result (currently it still says "Next: human gold pass"). Then mark ready-for-review. PR: https://github.com/sanlee-ys/faithfulness-judge/pull/1
4. Regenerate nothing — there is no build step. After edits: `uv run ruff check src/ tests/` and `uv run pytest -q` must stay green, then commit + push to `claude/project-ideas-p2xi8b`.

## Queued for other tiers

- **Fable (judgment call, later):** decide whether this floor is done or whether to spend a "solid tier" pass — tighten the CI with a second labeler / larger n, or add a third judge tier (Haiku) to complete the cost/quality curve. This is a strategy call, not a specified task.
- **Owner (San):** decide if/when the repo goes public and whether to link it from the portfolio surfaces.

## Escalate if

- The numbers in `evals/results.md` don't match this doc's table → something was re-run or the gold changed; stop and reconcile before writing the README.
- Any claim in `data/claims.yaml` has `label: null` → the gold set was disturbed; do not score against a partial gold.
- You feel tempted to re-run `judge.py`/`score.py` to "double-check" — don't, unless a number is actually inconsistent. Re-running costs API spend and the committed artifacts are the record.

## Standing cautions (paid-for lessons)

- **The forced tool-use verdict is load-bearing.** `judge.py` uses `record_verdict` (enum) with `tool_choice`. Assistant-message **prefill is rejected** by claude-sonnet-5 / claude-opus-4-8 — do not "simplify" back to prefill or to a bare `max_tokens=10` one-word prompt; that reintroduces the 20%-unparsed artifact.
- **`na` is excluded from scoring; unparsed verdicts count as disagreements.** Keep that in `score.py` — it's deliberate.
- **Don't overclaim.** This is a floor: one labeler, n=191, wide-ish CIs. State it as such (San's voice: skeptical-senior-engineer bar, negative/limited results stated plainly, AI assist named as method not confession).
- **San is on Windows/PowerShell.** No `&&` chaining, no `echo >` (writes UTF-16). His `uv` auto-loads `.env`; if it's missing/corrupt, `uv run --no-env-file ...` bypasses it. None of this session's work needs a key anyway.

## Owner-only actions pending

- Repo visibility (private → public): San's call.
- Any outward publication / linking from portfolio: San's call.
