# Gold-set audit worksheet — ADR-002, Option D (phase 1)

**What this is.** A blind consistency audit of this repo's human gold labels.
The claims below were picked by a **structural** rule that was written and
committed *before* this file was generated: it reads each claim's text and
nothing else. It was applied to all 193 gold claims.

**This file deliberately tells you nothing about how any model labeled these
claims.** No verdicts, no agreement flags, no marking of which claims were
contested. That is the point: a gold set audited toward its judges stops being
ground truth, and the resulting number would be exactly the soft-number-dressed-
as-solid failure this project exists to catch. If you find yourself trying to
recall what the models said about a claim, that instinct is the thing the blind
design is protecting against.

**This is a correctness pass, not a tuning pass.** For each claim ask only:
*does the rubric, applied to this excerpt, give this label?* If it does, keep
the label. Changing a label because a different one "feels better" is drift.
Most rows should come back unchanged.

## How to fill it in

Replace the `?` on each `AUDIT` line with one letter. **Every line must be
filled**, including the ones you are confirming — a blank is indistinguishable
from a skip, so the re-score refuses to run until all of them carry a letter.

| Letter | Label | Rule |
| --- | --- | --- |
| `s` | supported | Every part of the claim is stated in, or unambiguously entailed by, the excerpt. |
| `p` | partial | Mixed — part grounded, part adds specifics the excerpt doesn't contain; or directionally right but overstated. |
| `u` | unsupported | Asserts something the excerpt doesn't support — fabricated fact, wrong value, false premise. Contradictions count here. |
| `n` | na | Not a factual claim (filler, meta-aside, an offer to help). Excluded from scoring. |

The three consistency calls, unchanged from
[docs/labeling-guide.md](../docs/labeling-guide.md):

1. **A correct refusal is `supported`.** *"The passage doesn't state the cost"* —
   when it indeed doesn't — is a true statement about the passage. Only `u` if
   it claims something is absent that is actually in the excerpt.
2. **World-true but excerpt-absent is `unsupported`.** The model knowing the
   real answer does not make the answer grounded.
3. **Filler / meta is `na`.** No factual assertion to grade.

Binary kappa collapses `partial` into `unsupported` and drops `na`, so a
`p`-vs-`u` coin flip does not move the headline. Label your honest read.

When every line is filled:

```
uv run python src/gold_audit.py rescore
```

That re-scores offline against the committed judgments — no API calls, no judge
re-runs — and reports the corrected numbers *both* ways, including the view
restricted to claims no judge got wrong, so any drift toward the judges is
visible rather than buried.

## The pre-registered selection rule

A claim is selected if it matches **at least one** of:

- **S1-short-fragment** — 8 words or fewer. The frozen splitter (SCOPE.md Decision 2) emits list items and sentence fragments as standalone claims; below this length a claim is often not self-contained, and a claim that cannot be evaluated in isolation is a decomposition artifact rather than a judgeable assertion.
- **S2-list-header** — Ends with a colon. A colon-terminated header introduces a list rather than asserting anything on its own, so the rubric's 'not a factual claim' test should resolve the same way for every instance of the shape.
- **S3-offer-to-help** — Offers further assistance or asks the reader for more input — the 'I'd be happy to help' shape docs/labeling-guide.md names as canonical `na`.
- **S4-external-referral** — Directs the reader to material outside the excerpt — the 'you may want to check the original source' shape docs/labeling-guide.md names as canonical `na`.

Applied to all 193 gold claims, this selected **30**. Rules firing: S1-short-fragment 20, S2-list-header 8, S3-offer-to-help 2, S4-external-referral 6 (a claim may match more than one).

---

## The 30 claims

### Context `ctx-02`

The event consisted of 23 flights on an AH-64E Version 6 Apache Attack Helicopter
totaling 29.9 flight hours. The flights were conducted by 17 pilots the RTC, 101st
Airborne Division, and the Army Capability Management - Recon Attack. The flights
included familiarization, evaluation, and survey flights with each pilot providing
positive feedback on the demonstrated capability.

**Q (q-07):** The demonstration led to a decision to field the system across the entire Apache fleet — when does fielding begin?

#### `asrt-q-07-c3`

> If you have additional context or a source document with a specific date mentioned, I'd be happy to help pinpoint the exact fielding timeline more precisely.

- selected by: S3-offer-to-help, S4-external-referral
- current label: **na**

```
AUDIT asrt-q-07-c3 = ?
```

### Context `ctx-05`

Part one of a three-part Steadfast Defender exercise, ended near the coast of Portugal,
May 30. Part one was a dynamic maritime multi-domain collective defense exercise led by
the North Atlantic Treaty Organization, involving 19 ships from 11 allied nations and
including more than 5,000 participants.

**Q (q-15):** Which eleven allied nations contributed ships?

#### `asrt-q-15-c3`

> However, I cannot confirm this exact list without additional source material specifying the particular nations for this exercise.

- selected by: S4-external-referral
- current label: **supported**

```
AUDIT asrt-q-15-c3 = ?
```

### Context `ctx-10`

The projected unit cost of the next-generation U.S. Navy destroyer is much lower than
the figures being cited in some news reports, a senior Defense Department official said
here yesterday. The DDG-1000 is a high-tech, guided-missile destroyer that is envisioned
to eventually replace the Arleigh Burke class of warships developed 30 years ago. The
Pentagon would pay between $2.2 to $2.5 billion for each new DDG-1000 ship after the
regular production line is up and running.

**Q (q-31):** What per-ship unit cost does the official project for the DDG-1000 once production is running?

#### `asrt-q-31-c1`

> Between $2.2 billion and $2.5 billion per ship.

- selected by: S1-short-fragment
- current label: **supported**

```
AUDIT asrt-q-31-c1 = ?
```

**Q (q-34):** The official confirmed the $7 billion per-ship price — what drives a cost that high?

#### `asrt-q-34-c4`

> Lead ships in a new class typically carry much higher price tags because they include:

- selected by: S2-list-header
- current label: **unsupported**

```
AUDIT asrt-q-34-c4 = ?
```

**Q (q-34):** The official confirmed the $7 billion per-ship price — what drives a cost that high?

#### `asrt-q-34-c7`

> Learning-curve inefficiencies in the first units built

- selected by: S1-short-fragment
- current label: **unsupported**

```
AUDIT asrt-q-34-c7 = ?
```

### Context `ctx-02`

The event consisted of 23 flights on an AH-64E Version 6 Apache Attack Helicopter
totaling 29.9 flight hours. The flights were conducted by 17 pilots the RTC, 101st
Airborne Division, and the Army Capability Management - Recon Attack. The flights
included familiarization, evaluation, and survey flights with each pilot providing
positive feedback on the demonstrated capability.

**Q (q-07):** The demonstration led to a decision to field the system across the entire Apache fleet — when does fielding begin?

#### `help-q-07-c3`

> However, it does not mention:

- selected by: S1-short-fragment, S2-list-header
- current label: **supported**

```
AUDIT help-q-07-c3 = ?
```

**Q (q-07):** The demonstration led to a decision to field the system across the entire Apache fleet — when does fielding begin?

#### `help-q-07-c5`

> Any timeline or start date for fielding

- selected by: S1-short-fragment
- current label: **supported**

```
AUDIT help-q-07-c5 = ?
```

**Q (q-07):** The demonstration led to a decision to field the system across the entire Apache fleet — when does fielding begin?

#### `help-q-07-c6`

> If you have additional text or a source document that includes details about the fielding decision and timeline, please share it and I can help answer your question based on that information.

- selected by: S3-offer-to-help, S4-external-referral
- current label: **supported**

```
AUDIT help-q-07-c6 = ?
```

### Context `ctx-04`

The 101st Airborne Division (Air Assault) will deploy approximately 160 Soldiers to Fort
Knox, Kentucky, in support of an Emergency Deployment Readiness Exercise (EDRE) to be
held there. The Soldiers, from the division's 2nd Brigade Combat Team, are projected to
deploy Tuesday, Apr. 20.

**Q (q-13):** Why was the exercise moved from Fort Campbell to Fort Knox?

#### `help-q-13-c3`

> If you encountered information elsewhere suggesting the location was changed, that detail isn't included in this excerpt—you may want to check the original source for additional context that might explain the choice of Fort Knox as the exercise location.

- selected by: S4-external-referral
- current label: **na**

```
AUDIT help-q-13-c3 = ?
```

### Context `ctx-05`

Part one of a three-part Steadfast Defender exercise, ended near the coast of Portugal,
May 30. Part one was a dynamic maritime multi-domain collective defense exercise led by
the North Atlantic Treaty Organization, involving 19 ships from 11 allied nations and
including more than 5,000 participants.

**Q (q-14):** How many ships, nations, and participants took part in part one of Steadfast Defender?

#### `help-q-14-c1`

> Part one of the Steadfast Defender exercise involved:

- selected by: S1-short-fragment, S2-list-header
- current label: **supported**

```
AUDIT help-q-14-c1 = ?
```

**Q (q-14):** How many ships, nations, and participants took part in part one of Steadfast Defender?

#### `help-q-14-c2`

> 19 ships

- selected by: S1-short-fragment
- current label: **supported**

```
AUDIT help-q-14-c2 = ?
```

**Q (q-14):** How many ships, nations, and participants took part in part one of Steadfast Defender?

#### `help-q-14-c3`

> 11 allied nations

- selected by: S1-short-fragment
- current label: **supported**

```
AUDIT help-q-14-c3 = ?
```

**Q (q-14):** How many ships, nations, and participants took part in part one of Steadfast Defender?

#### `help-q-14-c4`

> More than 5,000 participants

- selected by: S1-short-fragment
- current label: **supported**

```
AUDIT help-q-14-c4 = ?
```

**Q (q-15):** Which eleven allied nations contributed ships?

#### `help-q-15-c3`

> To find out which specific nations participated, you would need to consult additional NATO or Steadfast Defender exercise reports that provide a detailed breakdown of participating countries.

- selected by: S4-external-referral
- current label: **supported**

```
AUDIT help-q-15-c3 = ?
```

### Context `ctx-06`

The Defense Department has leveraged the buying power of more than two million
information technology users to award a three-year, $617 million joint enterprise
license agreement for Microsoft products, defense officials announced. The deal, led by
the Army Contracting Command in collaboration with the Defense Information Systems
Agency, the Army and the Air Force, demonstrates the best pricing DOD has received to
date for Microsoft desktop and server software licenses, officials said.

**Q (q-18):** Which organization led the agreement, and with whom?

#### `help-q-18-c1`

> According to the passage, the agreement was led by the Army Contracting Command, working in collaboration with:

- selected by: S2-list-header
- current label: **supported**

```
AUDIT help-q-18-c1 = ?
```

**Q (q-18):** Which organization led the agreement, and with whom?

#### `help-q-18-c2`

> The Defense Information Systems Agency (DISA)

- selected by: S1-short-fragment
- current label: **supported**

```
AUDIT help-q-18-c2 = ?
```

**Q (q-18):** Which organization led the agreement, and with whom?

#### `help-q-18-c3`

> The Army

- selected by: S1-short-fragment
- current label: **supported**

```
AUDIT help-q-18-c3 = ?
```

**Q (q-18):** Which organization led the agreement, and with whom?

#### `help-q-18-c4`

> The Air Force

- selected by: S1-short-fragment
- current label: **supported**

```
AUDIT help-q-18-c4 = ?
```

**Q (q-19):** In absolute dollars, how much did DOD pay for the same licenses before this agreement?

#### `help-q-19-c1`

> The passage doesn't provide that figure.

- selected by: S1-short-fragment
- current label: **supported**

```
AUDIT help-q-19-c1 = ?
```

### Context `ctx-07`

A U.S. space domain awareness payload hosted on Japan's Quasi-Zenith Satellite 6 (QZS-6)
successfully launched on a Japanese H-3 launch vehicle from the Yoshinobu Launch Complex
at the Japan Aerospace Exploration Agency's (JAXA) Tanegashima Space Center (TNSC) in
Japan on February 2, 2025. This is the first bilateral U.S. Japan cooperative space
effort focused on national security, and the first of two launches as part of the JAXA
Quasi-Zenith Satellite System Hosted Payload (QZSS-HP) program.

**Q (q-21):** What kind of U.S. payload launched, on what vehicle, and from where and when?

#### `help-q-21-c1`

> Based on the passage:

- selected by: S1-short-fragment, S2-list-header
- current label: **na**

```
AUDIT help-q-21-c1 = ?
```

**Q (q-21):** What kind of U.S. payload launched, on what vehicle, and from where and when?

#### `help-q-21-c3`

> Host satellite: Japan's Quasi-Zenith Satellite 6 (QZS-6)

- selected by: S1-short-fragment
- current label: **supported**

```
AUDIT help-q-21-c3 = ?
```

**Q (q-21):** What kind of U.S. payload launched, on what vehicle, and from where and when?

#### `help-q-21-c4`

> Launch vehicle: A Japanese H-3 rocket

- selected by: S1-short-fragment
- current label: **supported**

```
AUDIT help-q-21-c4 = ?
```

**Q (q-21):** What kind of U.S. payload launched, on what vehicle, and from where and when?

#### `help-q-21-c6`

> Date: February 2, 2025

- selected by: S1-short-fragment
- current label: **supported**

```
AUDIT help-q-21-c6 = ?
```

**Q (q-22):** What makes this launch significant?

#### `help-q-22-c1`

> Based on the passage, this launch is significant for two main reasons:

- selected by: S2-list-header
- current label: **na**

```
AUDIT help-q-22-c1 = ?
```

### Context `ctx-10`

The projected unit cost of the next-generation U.S. Navy destroyer is much lower than
the figures being cited in some news reports, a senior Defense Department official said
here yesterday. The DDG-1000 is a high-tech, guided-missile destroyer that is envisioned
to eventually replace the Arleigh Burke class of warships developed 30 years ago. The
Pentagon would pay between $2.2 to $2.5 billion for each new DDG-1000 ship after the
regular production line is up and running.

**Q (q-33):** Why did some news reports cite higher cost figures for the ship?

#### `help-q-33-c3`

> Possible explanations that aren't stated but might logically account for the discrepancy include:

- selected by: S2-list-header
- current label: **supported**

```
AUDIT help-q-33-c3 = ?
```

**Q (q-33):** Why did some news reports cite higher cost figures for the ship?

#### `help-q-33-c8`

> If you're looking for the specific reason given in the original reporting, the passage as provided doesn't include that detail—you may need to consult the full article for the official's

- selected by: S4-external-referral
- current label: **supported**

```
AUDIT help-q-33-c8 = ?
```

### Context `ctx-11`

The Navy has selected Ingalls Shipbuilding and Northrop-Grumman Ship Systems to design
the next-generation DD(X) family of ships. Assistant Navy Secretary John Young announced
the $2.9 billion three-year contract April 29. The money goes to designing, building and
testing the DD(X) destroyer and a "family" of surface ships. Navy officials see the
DD(X) family at the core of surface warfare in the 21st century.

**Q (q-36):** Why did the Navy choose that team over the competing bidder?

#### `help-q-36-c2`

> It only reports:

- selected by: S1-short-fragment, S2-list-header
- current label: **supported**

```
AUDIT help-q-36-c2 = ?
```

**Q (q-36):** Why did the Navy choose that team over the competing bidder?

#### `help-q-36-c3`

> Who won: Ingalls Shipbuilding and Northrop-Grumman Ship Systems

- selected by: S1-short-fragment
- current label: **supported**

```
AUDIT help-q-36-c3 = ?
```

**Q (q-36):** Why did the Navy choose that team over the competing bidder?

#### `help-q-36-c4`

> Who announced it: Assistant Navy Secretary John Young

- selected by: S1-short-fragment
- current label: **supported**

```
AUDIT help-q-36-c4 = ?
```

**Q (q-36):** Why did the Navy choose that team over the competing bidder?

#### `help-q-36-c5`

> When: April 29

- selected by: S1-short-fragment
- current label: **supported**

```
AUDIT help-q-36-c5 = ?
```
