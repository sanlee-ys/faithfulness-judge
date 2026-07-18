# Labeling guide — the human gold pass

You are labeling each claim in `data/claims.yaml` against **its context excerpt
only** — not the full article, not what's true in the world. For every claim, the
question is: *does this passage support this claim?* Your labels are the ground
truth the judge is validated against, so consistency matters more than speed.

## Workflow

```bash
uv run python src/labels.py export     # claims.yaml -> data/labeling.csv
# open data/labeling.csv in a spreadsheet, fill the `label` column
uv run python src/labels.py apply      # writes labels back into claims.yaml
git add data/claims.yaml && git commit -m "Gold labels" && git push
```

Each row shows the `question`, the `context_excerpt`, and the `claim_text`.
Put one letter in `label`:

| Letter | Label | Rule |
| --- | --- | --- |
| `s` | supported | Every part of the claim is stated in, or unambiguously entailed by, the excerpt. |
| `p` | partial | Mixed — part is grounded, part adds specifics the excerpt doesn't contain; or directionally right but overstated. |
| `u` | unsupported | Asserts something the excerpt doesn't support — fabricated fact, wrong value, or a claim built on a false premise. Contradictions count here. |
| `n` | na | Not a factual claim (filler, a meta-aside, an offer to help). Excluded from scoring. |

For the headline **binary** κ, `partial` collapses into `unsupported`; `na` is
dropped. So when unsure between `p` and `u`, it won't change the headline number —
label your honest read and move on.

## The three calls that keep you consistent

1. **A correct refusal is `supported`.** *"The passage doesn't state the cost"* —
   when the passage indeed doesn't — is a true statement about the passage → `s`.
   Only `u` if it claims something is absent that's actually in the excerpt.
2. **World-true but excerpt-absent → `unsupported`.** This is the whole thesis. A
   claim that's true in reality but not grounded in *this passage* is `u`. The
   model knowing the real answer doesn't make the answer grounded.
3. **Filler / meta → `na`.** *"I'd be happy to help,"* *"you may want to check the
   original source"* — no factual assertion, so `n`; excluded from κ.

## Worked examples, from this gold set

| Claim | Excerpt says | Label |
| --- | --- | --- |
| `asrt-q-06` "…points to **Fort Rucker, Alabama**" | excerpt says only "RTC", no location | `u` — invented a location |
| `asrt-q-19` "previous arrangement cost **~$880 million**" | no prior cost given | `u` — fabricated figure |
| `asrt-q-27` "the Army ordered **4** Robotic Combat Vehicles" | it's a feasibility experiment | `u` — accepted a false premise |
| `help-q-02-c3` "With IDIQ contracts, the government commits to a minimum order…" | not in excerpt | `u` — true-ish world knowledge, ungrounded |
| `asrt-q-40-c1` "the ceremony was a christening, not a commissioning" | excerpt describes a christening | `s` — correct, grounded |
| `asrt-q-31` "Between $2.2 billion and $2.5 billion per ship" | excerpt states this | `s` |
| `help-q-15-c3` "you would need to consult additional NATO reports" | — | `n` — meta-advice, not a claim |

## Tips

- Label by **row order** — claims from the same question sit together, so you
  hold one excerpt in your head at a time.
- The `variant` column tells you where a claim came from (`assertive` = blunt
  fabrications, `helpful` = subtler overreach). It's context, not a label input.
- You don't have to finish in one sitting — `apply` writes back only the rows you
  filled, and `export` again preserves labels already in `claims.yaml`.
