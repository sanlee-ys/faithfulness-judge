# ADR-003: Run `score.py` in CI and assert `evals/results.md` is current — SYS-017 tier 1, with no floor

**Status:** Accepted
**Date:** 2026-08-02
**Deciders:** San Lee

---

## Context

[`system/SYS-017`](https://github.com/sanlee-ys/architecture/blob/main/decisions/SYS-017-evals-as-ci.md)
(adopted 2026-08-02) defines a four-rung ladder for evals-as-CI and places this repo at
**tier 0** — "measured, not gated." Its evidence is exact: `tests.yml` is `ruff` + `pytest`,
deliberately keyless; the agreement statistics are computed by `src/score.py`, which is offline and
reads committed label files; **nothing in CI runs it.**

SYS-017's rollout calls this "the cheapest tier-1 move in the fleet," and the reason is that the
precondition that blocked the sibling repo does not exist here. Tier 1's entry condition is **corpus
provenance** — CI must reconstruct every input from version-controlled sources. `score.py` reads
`data/claims.yaml` and `data/judgments_*.yaml`, both committed. There is nothing to clone, no
absolute path, no API key, and nothing paid to defer. Per SYS-017 section 2, a repo with nothing
paid to defer gets **one** leg, not a ceremonial second one.

But this repo's harness differs from `kb-agent`'s in a way that changes what "run the eval in CI"
should mean. `kb-agent`'s retrieval eval queries a freshly built index, so each run produces new
information. **`score.py` is a pure function of committed files, and its output is itself a
committed file** (`evals/results.md`). A CI step that merely invokes it and discards the result can
only fail if the code crashes. That is close enough to a no-op to be worth naming, and it runs
straight into SYS-017's second house corollary: *a gate that cannot fail is theater.*

There is a matching gap on the artifact side. `CLAUDE.md` carries a **written human rule**:

> if `evals/results.md` disagrees with the numbers in the README or ADR-001, something was re-run:
> reconcile before writing anything

Nothing enforces it. `evals/results.md` is committed, deterministic, and regenerable, and until now
the only thing standing between it and the code that produces it was a person remembering to
re-run.

## Decision

**Run `score.py` on every push and pull request, and assert that the committed `evals/results.md`
is exactly what it produces.** Two steps appended to `tests.yml`, after the existing suite.

### 1. Regenerate, having deleted the artifact first

```yaml
rm evals/results.md
uv run python src/score.py
```

The `rm` is the liveness clause and is the reason this is a real check rather than a decorative
one. Without it, a regression that stopped `score.py` writing the file would leave git's checked-out
copy in place, the diff below would find nothing, and the step would pass **vacuously**. Deleting
first means the artifact has to be *produced*, not merely *matched*. This mirrors the classifier's
rule that a missing provenance sidecar is a failure and not a skip — otherwise `rm` is a
one-command bypass.

### 2. Fail if the committed artifact is stale

```yaml
git diff --exit-code -- evals/results.md   # with a directed error message
```

This mechanizes the machine-checkable half of the `CLAUDE.md` rule. `score.py` is the **sole
writer** of that file — `gold_audit.py` writes only to its `--out` path — so there is exactly one
producer and the check has one meaning.

**CI never writes the baseline back.** On drift it fails and tells a human to run `score.py` and
commit, including a reminder to reconcile `README.md` and `CLAUDE.md` if the numbers moved. A job
that regenerated and committed the artifact itself would launder a changed measurement into the
history with no review, which is the failure this check exists to prevent.

### 3. No floors, no threshold — deliberately

Nothing here gates on a **value**. Kappa is free to move; the only requirement is that the
committed file move with it. This is tier 1 and stops there, for the reason SYS-017 gives
explicitly: *tier 2 should not be assumed to follow*, because **an agreement statistic measured
once has no noise band under it**, and a floor without one is an aspiration wearing a measured
number's clothes. That is the same refusal the classifier's `scale_region_eval.py` encodes in code
rather than prose, and `classifier/ADR-014`'s house rule states as "thresholds after measurement,
never before."

Concretely, the numbers this repo publishes today — Opus κ 0.751 / 89.4% agreement / 97.9%
unsupported recall, Sonnet κ 0.716 / 88.4% / 89.6% — are **one** pass each. Repeating them in CI
does not add a sample, because CI recomputes the same deterministic function over the same
committed bytes; it will return the identical figure every time. A second *sample* would require
re-running the judges, which costs money and which `CLAUDE.md` explicitly forbids doing to
"double-check." So the noise band tier 2 needs cannot be manufactured by running CI more often, and
this decision does not pretend otherwise.

### 4. What is deliberately not in scope

The `README.md` and `CLAUDE.md` figures are still reconciled against `evals/results.md` **by hand**.
SYS-017 names this separately and correctly as a `SYS-019` concern — "a worthwhile move that is not
on this ladder" — because it governs what may be *claimed* about a measurement rather than whether
the measurement is *enforced*. Asserting those restated figures against the artifact is a real and
cheap improvement, and it is a different change from this one.

## Downstream surfaces

- **`.github/workflows/tests.yml`** — the two new steps. This is the tier-1 mechanism. If the `rm`
  is removed as "unnecessary," the drift check silently becomes able to pass vacuously; that is the
  one edit here that looks like a cleanup and is not.
- **`evals/results.md`** — now a checked artifact rather than a convention. Any change that moves
  the numbers must commit the regenerated file in the same PR, or CI fails.
- **`src/score.py`** — its output is now load-bearing for a CI check. A change to its *formatting*
  (not just its arithmetic) will fail the build until the artifact is regenerated. That is intended;
  it is also the most likely source of a surprising red build.
- **`CLAUDE.md`** — the standing caution "if `evals/results.md` disagrees with the numbers in the
  README or ADR-001, something was re-run" is now **half-enforced**. Updated to say which half is
  mechanical and which half is still on the reader.
- **`README.md`** — restates κ, agreement and recall figures. **Not enforced by this change**;
  see scope note above. Unmodified here.
- **[ADR-002](002-solid-tier-call.md) phase 2** — the blind gold audit will change labels, and
  `gold_audit.py rescore` plus a `score.py` re-run will move `evals/results.md`. This check does not
  obstruct that; it requires the regenerated artifact to land in the same PR as the labels, which is
  what ADR-002's own reconcile discipline already asks for. Worth knowing before phase 2 starts:
  the first PR that adjudicates a label will fail CI until `score.py` is re-run.
- **`system/SYS-017`** — this is its `faithfulness-judge` rollout row, `0 → 1`. Its fleet table
  records this repo at tier 0 and goes stale with this merge. The table is a dated observation by
  its own classification and is not enforced.
- **`decisions/`** — this repo has no `lint_decisions.py`, unlike `kb-agent` and the classifier, so
  the `## Downstream surfaces` section here is convention rather than enforced. Included because the
  section is the step that gets skipped, and the sweep that follows then misses a file.

## Consequences

- **The eval can now fail the build — but only on staleness, never on a number.** That distinction
  is the whole design. A red build here means "the committed artifact disagrees with the code," not
  "the judge got worse."
- **A `score.py` formatting change becomes a two-file change.** Mildly annoying, and correct: the
  artifact is part of the published record, not a scratch file.
- **Tier 2 remains genuinely blocked, and not by plumbing.** It needs a second *sample*, which needs
  a paid judge re-run. Nothing about running CI more often produces one. Recorded so a later reader
  does not mistake "the eval runs in CI now" for "a floor is one step away."
- **The claim-drift risk on `README.md` is untouched.** Known, scoped out, and the larger of the two
  remaining holes.
- **Runtime cost is negligible** — no API, no model download, no index build. `score.py` is plain
  Python over two small YAML files.

## Alternatives Considered

| Option | Reason Not Chosen |
|--------|-------------------|
| Run `score.py` and discard the output (strict minimum tier 1) | Satisfies the letter of "a workflow step invokes the harness" while being unable to fail on anything but a crash, because the harness is a pure function over committed inputs. SYS-017's own corollary — a gate that cannot fail is theater — argues against shipping it in that shape here. |
| Add the drift check but `continue-on-error` | An unenforced check reports green from a stale artifact, which is the failure mode this system keeps re-learning. A warning nobody is required to act on is the written human rule again, with more YAML. |
| Have CI regenerate `evals/results.md` and commit it | Launders a changed measurement into history with no review, and SYS-017 is explicit that CI never writes the baseline back. The point of the artifact is that a human looked at the number. |
| Diff without deleting the file first | Passes vacuously if `score.py` ever stops writing the artifact — the check would be asserting that git's checkout equals git's checkout. |
| Set a floor from the current κ (0.751 / 0.716) and gate on it | One measurement, no noise band. SYS-017 and `classifier/ADR-014` both refuse this, and CI cannot supply the missing sample because it recomputes the same deterministic function over the same bytes. |
| Add a second, scheduled leg for symmetry with the classifier | The classifier's split exists to manage paid, non-deterministic calls and fork-PR secret exposure. Nothing here is paid or non-deterministic, so a second lane would be ceremony with no referent (SYS-017 section 2). |
| Also assert `README.md`'s restated figures against `evals/results.md` | A real and worthwhile fix, and a different decision — `SYS-019` (what may be claimed) rather than `SYS-017` (whether it is enforced). One concern, one PR. |
| Re-run the judges in CI to get a second sample for a floor | Spends API budget per run, and `CLAUDE.md` forbids re-running the judges to double-check. SYS-017 puts paid legs on owner-triggered lanes or nowhere. |
