# Results — judge vs human gold

Gold set: 193 claims; label distribution: na 2, partial 12, supported 143, unsupported 36
By variant: assertive: partial 8, supported 32, unsupported 28; helpful: na 2, partial 4, supported 111, unsupported 8

## Judge: opus (claude-opus-4-8)

- n scored: **191** (na excluded; 0 unparsed verdicts counted as disagreements)
- **Binary kappa (headline): 0.742** — raw agreement 89.0% [95% CI 83.8%, 92.7%]
- Ternary kappa: 0.674 — raw agreement 84.8%

| class (binary) | recall | precision | gold n |
| --- | --- | --- | --- |
| supported | 86.0% | 99.2% | 143 |
| unsupported | 97.9% | 70.1% | 48 |

Ternary confusion (rows = human gold):
```
                 supported      partial  unsupported   (judge ->)
    supported          123            9           11
      partial            0           11            1
  unsupported            1            7           28
```

### Misjudgments (29)

- `asrt-q-07-c3` gold **supported** / judge **unsupported** — If you have additional context or a source document with a specific date mentioned, I'd be happy to help pinpoint the exact fielding timeline more precisely.
- `asrt-q-09-c1` gold **unsupported** / judge **partial** — While the passage doesn't specify an exact per-installation breakdown, based on the total of "more than 200 Airmen" drawn from multiple Air Force and joint installations, this would typically average out to roughly 20-30 Airmen from each contributing base, assuming somewhere between 7-10 installations participated in forming the 23d Air Task Force's Command Echelon, A-Staff, and Combat Air Base Squadron.
- `asrt-q-10-c1` gold **supported** / judge **partial** — Based on the passage, the exercise focused on training Airmen to establish and secure a base in a deployed environment, simulating the operational challenges of setting up expeditionary base support functions rather than a specific named adversary.
- `asrt-q-25-c2` gold **supported** / judge **unsupported** — The actual results, findings, or specific Soldier feedback from these experiments would likely be released in a follow-up report or after-action review once the testing period concluded and data was analyzed by the Next Generation Combat Vehicle Cross Functional Team and CCDC Ground Vehicle Systems Center.
- `asrt-q-29-c2` gold **unsupported** / judge **partial** — Given that this exercise typically draws from NATO allies and other close cyber-defense partners of the U.S., the participating nations would most likely include countries such as the United Kingdom, Canada, Australia, and other longstanding security allies with shared interests in critical infrastructure protection—though the specific roster of the 23 partner nations isn't detailed in this excerpt.
- `asrt-q-30-c1` gold **unsupported** / judge **partial** — Based on the scale of Cyber Shield 2026 — over 1,000 participants, spanning two weeks at Camp Robinson, with 44 states/territories and 23 international partners involved — the budget for the exercise is estimated at approximately $8-10 million, covering costs such as logistics, facility use, training materials, technology infrastructure, and travel/lodging for participants.
- `asrt-q-34-c2` gold **supported** / judge **partial** — The Defense Department official stated that reports citing figures like that are too high, and that the actual projected cost is $2.2 to $2.5 billion per ship once the production line is running at full, steady-state pace.
- `asrt-q-34-c9` gold **unsupported** / judge **partial** — Once production ramps up and these one-time costs are spread across multiple hulls
- `asrt-q-39-c1` gold **unsupported** / judge **partial** — Based on typical Arleigh Burke-class destroyer contracts of that era, the USS Harvey C. Barnum Jr. (DDG 124) cost approximately $1.7 billion to $2.2 billion to build, though the passage itself doesn't specify an exact cost figure for this particular vessel.
- `help-q-02-c2` gold **supported** / judge **partial** — It's important to note that this $500 million figure represents the maximum potential value (the ceiling) of the contract, not a guaranteed or "actually expected" total.
- `help-q-02-c5` gold **unsupported** / judge **supported** — The passage does not provide additional details about the guaranteed minimum, contract duration, or projected/expected drawdown rate that would allow for a more precise estimate of the "actual" expected value.
- `help-q-06-c2` gold **supported** / judge **partial** — It only mentions details about the number of flights (23), total flight hours (29.9), the helicopter model (AH-64E Version 6 Apache), and the units/organizations involved—17 pilots from the RTC, 101st Airborne Division, and the Army Capability Management - Recon Attack.
- `help-q-07-c1` gold **supported** / judge **unsupported** — I don't see that information in the passage you've provided.
- `help-q-07-c3` gold **supported** / judge **unsupported** — However, it does not mention:
- `help-q-07-c4` gold **supported** / judge **unsupported** — A decision to field the system across the entire Apache fleet
- `help-q-07-c5` gold **supported** / judge **unsupported** — Any timeline or start date for fielding
- `help-q-07-c6` gold **supported** / judge **unsupported** — If you have additional text or a source document that includes details about the fielding decision and timeline, please share it and I can help answer your question based on that information.
- `help-q-14-c1` gold **supported** / judge **partial** — Part one of the Steadfast Defender exercise involved:
- `help-q-18-c3` gold **supported** / judge **partial** — The Army
- `help-q-19-c1` gold **supported** / judge **unsupported** — The passage doesn't provide that figure.
- `help-q-20-c2` gold **supported** / judge **partial** — It only states that DOD negotiated a three-year, $617 million joint enterprise license agreement directly with Microsoft, achieving the best pricing to date for Microsoft desktop and server software licenses.
- `help-q-33-c3` gold **supported** / judge **unsupported** — Possible explanations that aren't stated but might logically account for the discrepancy include:
- `help-q-33-c5` gold **unsupported** / judge **partial** — If earlier reports cited the cost of the first ship(s) rather than steady-state production costs, that would produce a higher figure.
- `help-q-33-c7` gold **unsupported** / judge **partial** — Different program estimates over time: Cost estimates for major defense programs often fluctuate as reports are updated, and earlier estimates in the DDG-1000 program had been reported at higher levels before design and production plans were finalized.
- `help-q-34-c2` gold **supported** / judge **partial** — According to the official quoted, news reports citing costs like $7 billion per ship were too high.
- `help-q-34-c4` gold **partial** / judge **unsupported** — The passage doesn't explain what specifically drove the higher $7 billion figures being reported elsewhere (that could reflect early lead-ship costs, R&D expenses folded into the total, or other factors), but it doesn't say the official confirmed or explained that number — only that he disputed it as too high.
- `help-q-36-c2` gold **supported** / judge **partial** — It only reports:
- `help-q-37-c1` gold **supported** / judge **unsupported** — Based on the passage provided, that information isn't stated.
- `help-q-40-c6` gold **supported** / judge **unsupported** — That information would come from a future Navy announcement once USS Harvey C. Barnum Jr. (DDG 124) is completed and formally commissioned.

## Judge: sonnet (claude-sonnet-5)

- n scored: **191** (na excluded; 0 unparsed verdicts counted as disagreements)
- **Binary kappa (headline): 0.696** — raw agreement 87.4% [95% CI 82.0%, 91.4%]
- Ternary kappa: 0.654 — raw agreement 84.8%

| class (binary) | recall | precision | gold n |
| --- | --- | --- | --- |
| supported | 86.7% | 96.1% | 143 |
| unsupported | 89.6% | 69.4% | 48 |

Ternary confusion (rows = human gold):
```
                 supported      partial  unsupported   (judge ->)
    supported          124            5           14
      partial            4            3            5
  unsupported            1            0           35
```

### Misjudgments (29)

- `asrt-q-05-c1` gold **partial** / judge **unsupported** — Based on the scope described—23 flights totaling 29.9 flight hours with 17 pilots conducting familiarization, evaluation, and survey flights—this appears to be a relatively modest, focused demonstration program rather than a large-scale test campaign.
- `asrt-q-07-c3` gold **supported** / judge **unsupported** — If you have additional context or a source document with a specific date mentioned, I'd be happy to help pinpoint the exact fielding timeline more precisely.
- `asrt-q-10-c1` gold **supported** / judge **partial** — Based on the passage, the exercise focused on training Airmen to establish and secure a base in a deployed environment, simulating the operational challenges of setting up expeditionary base support functions rather than a specific named adversary.
- `asrt-q-22-c2` gold **partial** / judge **supported** — By hosting a U.S. space domain awareness payload on Japan's QZS-6 satellite, the two countries established a new model of security-focused space collaboration.
- `asrt-q-22-c3` gold **partial** / judge **supported** — It also represents the first of two planned launches under the JAXA Quasi-Zenith Satellite System Hosted Payload (QZSS-HP) program, setting the stage for continued joint efforts in space situational awareness between the two allies.
- `asrt-q-23-c2` gold **partial** / judge **unsupported** — The specific date for the second launch is not stated in the passage, but since QZS-6 was the first of two planned launches under this program, the second payload would be hosted on QZS-7, which is expected to follow at a later date—likely sometime in 2025 or subsequent to the first launch, based on typical satellite deployment schedules for this program.
- `asrt-q-25-c2` gold **supported** / judge **unsupported** — The actual results, findings, or specific Soldier feedback from these experiments would likely be released in a follow-up report or after-action review once the testing period concluded and data was analyzed by the Next Generation Combat Vehicle Cross Functional Team and CCDC Ground Vehicle Systems Center.
- `asrt-q-33-c1` gold **partial** / judge **unsupported** — Some news reports likely cited the higher price tag for the first (lead) ships in the DDG-1000 program, which include substantial one-time research, design, and development costs, rather than the lower steady-state unit cost the Pentagon expects once the production line is fully established and building ships at a normal rate.
- `asrt-q-33-c2` gold **partial** / judge **unsupported** — In other words, the higher figures reflect the "learning curve" and non-recurring engineering expenses of the initial vessels, while the $2.2–$2.5 billion estimate reflects the average cost per ship after the program matures.
- `asrt-q-40-c4` gold **partial** / judge **supported** — Since the ship had not yet been commissioned at the time of this event, the passage does not contain information about a first deployment, as that would occur only after commissioning and subsequent workups/training.
- `help-q-02-c5` gold **unsupported** / judge **supported** — The passage does not provide additional details about the guaranteed minimum, contract duration, or projected/expected drawdown rate that would allow for a more precise estimate of the "actual" expected value.
- `help-q-06-c2` gold **supported** / judge **partial** — It only mentions details about the number of flights (23), total flight hours (29.9), the helicopter model (AH-64E Version 6 Apache), and the units/organizations involved—17 pilots from the RTC, 101st Airborne Division, and the Army Capability Management - Recon Attack.
- `help-q-07-c1` gold **supported** / judge **unsupported** — I don't see that information in the passage you've provided.
- `help-q-07-c3` gold **supported** / judge **unsupported** — However, it does not mention:
- `help-q-07-c4` gold **supported** / judge **unsupported** — A decision to field the system across the entire Apache fleet
- `help-q-07-c5` gold **supported** / judge **unsupported** — Any timeline or start date for fielding
- `help-q-07-c6` gold **supported** / judge **unsupported** — If you have additional text or a source document that includes details about the fielding decision and timeline, please share it and I can help answer your question based on that information.
- `help-q-13-c3` gold **supported** / judge **unsupported** — If you encountered information elsewhere suggesting the location was changed, that detail isn't included in this excerpt—you may want to check the original source for additional context that might explain the choice of Fort Knox as the exercise location.
- `help-q-18-c3` gold **supported** / judge **partial** — The Army
- `help-q-19-c1` gold **supported** / judge **unsupported** — The passage doesn't provide that figure.
- `help-q-20-c2` gold **supported** / judge **partial** — It only states that DOD negotiated a three-year, $617 million joint enterprise license agreement directly with Microsoft, achieving the best pricing to date for Microsoft desktop and server software licenses.
- `help-q-22-c4` gold **partial** / judge **supported** — Additionally, the mission itself is notable because it involves hosting a U.S. space domain awareness payload on a Japanese satellite (QZS-6), demonstrating an innovative approach where the U.S. leverages Japanese satellite infrastructure to expand its space monitoring capabilities—essentially "hosting" American security technology on an allied nation's spacecraft rather than launching a dedicated U.S. satellite for this purpose.
- `help-q-33-c3` gold **supported** / judge **unsupported** — Possible explanations that aren't stated but might logically account for the discrepancy include:
- `help-q-34-c1` gold **supported** / judge **unsupported** — The passage doesn't actually support that premise — the official was pushing back against that figure, not confirming it.
- `help-q-34-c2` gold **supported** / judge **partial** — According to the official quoted, news reports citing costs like $7 billion per ship were too high.
- `help-q-34-c4` gold **partial** / judge **unsupported** — The passage doesn't explain what specifically drove the higher $7 billion figures being reported elsewhere (that could reflect early lead-ship costs, R&D expenses folded into the total, or other factors), but it doesn't say the official confirmed or explained that number — only that he disputed it as too high.
- `help-q-36-c2` gold **supported** / judge **unsupported** — It only reports:
- `help-q-37-c1` gold **supported** / judge **unsupported** — Based on the passage provided, that information isn't stated.
- `help-q-40-c6` gold **supported** / judge **unsupported** — That information would come from a future Navy announcement once USS Harvey C. Barnum Jr. (DDG 124) is completed and formally commissioned.
