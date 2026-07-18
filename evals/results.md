# Results — judge vs human gold

Gold set: 193 claims; label distribution: na 2, partial 12, supported 143, unsupported 36
By variant: assertive: partial 8, supported 32, unsupported 28; helpful: na 2, partial 4, supported 111, unsupported 8

## Judge: opus (claude-opus-4-8)

- n scored: **191** (na excluded; 0 unparsed verdicts counted as disagreements)
- **Binary kappa (headline): 0.699** — raw agreement 87.4% [95% CI 82.0%, 91.4%]
- Ternary kappa: 0.651 — raw agreement 84.3%

| class (binary) | recall | precision | gold n |
| --- | --- | --- | --- |
| supported | 86.0% | 96.9% | 143 |
| unsupported | 91.7% | 68.8% | 48 |

Ternary confusion (rows = human gold):
```
                 supported      partial  unsupported   (judge ->)
    supported          123            5           15
      partial            1            8            3
  unsupported            3            3           30
```

### Misjudgments (30)

- `asrt-q-07-c3` gold **supported** / judge **unsupported** — If you have additional context or a source document with a specific date mentioned, I'd be happy to help pinpoint the exact fielding timeline more precisely.
- `asrt-q-10-c1` gold **supported** / judge **partial** — Based on the passage, the exercise focused on training Airmen to establish and secure a base in a deployed environment, simulating the operational challenges of setting up expeditionary base support functions rather than a specific named adversary.
- `asrt-q-20-c1` gold **unsupported** / judge **supported** — The passage doesn't name a specific competing vendor, but based on the context of enterprise IT licensing at that scale, the most likely alternative DOD would have weighed against Microsoft is a competitor like Oracle or perhaps open-source alternatives (e.g., Linux-based solutions) for desktop and server software.
- `asrt-q-23-c2` gold **partial** / judge **unsupported** — The specific date for the second launch is not stated in the passage, but since QZS-6 was the first of two planned launches under this program, the second payload would be hosted on QZS-7, which is expected to follow at a later date—likely sometime in 2025 or subsequent to the first launch, based on typical satellite deployment schedules for this program.
- `asrt-q-25-c2` gold **supported** / judge **unsupported** — The actual results, findings, or specific Soldier feedback from these experiments would likely be released in a follow-up report or after-action review once the testing period concluded and data was analyzed by the Next Generation Combat Vehicle Cross Functional Team and CCDC Ground Vehicle Systems Center.
- `asrt-q-29-c2` gold **unsupported** / judge **supported** — Given that this exercise typically draws from NATO allies and other close cyber-defense partners of the U.S., the participating nations would most likely include countries such as the United Kingdom, Canada, Australia, and other longstanding security allies with shared interests in critical infrastructure protection—though the specific roster of the 23 partner nations isn't detailed in this excerpt.
- `asrt-q-33-c1` gold **partial** / judge **unsupported** — Some news reports likely cited the higher price tag for the first (lead) ships in the DDG-1000 program, which include substantial one-time research, design, and development costs, rather than the lower steady-state unit cost the Pentagon expects once the production line is fully established and building ships at a normal rate.
- `asrt-q-39-c1` gold **unsupported** / judge **partial** — Based on typical Arleigh Burke-class destroyer contracts of that era, the USS Harvey C. Barnum Jr. (DDG 124) cost approximately $1.7 billion to $2.2 billion to build, though the passage itself doesn't specify an exact cost figure for this particular vessel.
- `asrt-q-40-c4` gold **partial** / judge **supported** — Since the ship had not yet been commissioned at the time of this event, the passage does not contain information about a first deployment, as that would occur only after commissioning and subsequent workups/training.
- `help-q-02-c3` gold **unsupported** / judge **partial** — With IDIQ contracts, the government commits to a minimum order (often much smaller, though not specified in this passage) and then issues task or delivery orders as needed up to the ceiling amount.
- `help-q-02-c5` gold **unsupported** / judge **supported** — The passage does not provide additional details about the guaranteed minimum, contract duration, or projected/expected drawdown rate that would allow for a more precise estimate of the "actual" expected value.
- `help-q-06-c2` gold **supported** / judge **partial** — It only mentions details about the number of flights (23), total flight hours (29.9), the helicopter model (AH-64E Version 6 Apache), and the units/organizations involved—17 pilots from the RTC, 101st Airborne Division, and the Army Capability Management - Recon Attack.
- `help-q-07-c1` gold **supported** / judge **unsupported** — I don't see that information in the passage you've provided.
- `help-q-07-c3` gold **supported** / judge **unsupported** — However, it does not mention:
- `help-q-07-c4` gold **supported** / judge **unsupported** — A decision to field the system across the entire Apache fleet
- `help-q-07-c6` gold **supported** / judge **unsupported** — If you have additional text or a source document that includes details about the fielding decision and timeline, please share it and I can help answer your question based on that information.
- `help-q-14-c1` gold **supported** / judge **unsupported** — Part one of the Steadfast Defender exercise involved:
- `help-q-18-c1` gold **supported** / judge **partial** — According to the passage, the agreement was led by the Army Contracting Command, working in collaboration with:
- `help-q-18-c3` gold **supported** / judge **unsupported** — The Army
- `help-q-18-c4` gold **supported** / judge **unsupported** — The Air Force
- `help-q-19-c1` gold **supported** / judge **unsupported** — The passage doesn't provide that figure.
- `help-q-20-c2` gold **supported** / judge **partial** — It only states that DOD negotiated a three-year, $617 million joint enterprise license agreement directly with Microsoft, achieving the best pricing to date for Microsoft desktop and server software licenses.
- `help-q-30-c2` gold **supported** / judge **partial** — It only provides details about the exercise's scale and scope—including that over 1,000 participants from 44 states/territories and 23 international partners are taking part, that it runs from July 12–25, 2026, and that it's held at Camp Robinson with a focus on protecting critical infrastructure like water and power grids.
- `help-q-33-c3` gold **supported** / judge **unsupported** — Possible explanations that aren't stated but might logically account for the discrepancy include:
- `help-q-33-c6` gold **unsupported** / judge **partial** — Including R&D costs: Total program costs (including research and development) spread differently than per-unit procurement costs could make reported figures higher.
- `help-q-34-c2` gold **supported** / judge **unsupported** — According to the official quoted, news reports citing costs like $7 billion per ship were too high.
- `help-q-34-c4` gold **partial** / judge **unsupported** — The passage doesn't explain what specifically drove the higher $7 billion figures being reported elsewhere (that could reflect early lead-ship costs, R&D expenses folded into the total, or other factors), but it doesn't say the official confirmed or explained that number — only that he disputed it as too high.
- `help-q-36-c2` gold **supported** / judge **unsupported** — It only reports:
- `help-q-39-c2` gold **supported** / judge **unsupported** — It only covers details about the christening ceremony—where it took place, who gave the principal address, and who served as the ship's sponsor.
- `help-q-40-c6` gold **supported** / judge **unsupported** — That information would come from a future Navy announcement once USS Harvey C. Barnum Jr. (DDG 124) is completed and formally commissioned.

## Judge: sonnet (claude-sonnet-5)

- n scored: **191** (na excluded; 39 unparsed verdicts counted as disagreements)
- **Binary kappa (headline): 0.425** — raw agreement 72.3% [95% CI 65.5%, 78.1%]
- Ternary kappa: 0.436 — raw agreement 72.3%

| class (binary) | recall | precision | gold n |
| --- | --- | --- | --- |
| supported | 81.1% | 95.1% | 143 |
| unsupported | 45.8% | 73.3% | 48 |

Ternary confusion (rows = human gold):
```
                 supported      partial  unsupported   (judge ->)
    supported          116            0            8
      partial            4            0            0
  unsupported            2            0           22
```

### Misjudgments (53)

- `asrt-q-02-c1` gold **supported** / judge **__unparsed__** — Based on the passage, the contract has a $500 million ceiling, which represents the maximum value the Indefinite Delivery/Indefinite Quantity (IDIQ) contract is expected to reach.
- `asrt-q-05-c1` gold **partial** / judge **supported** — Based on the scope described—23 flights totaling 29.9 flight hours with 17 pilots conducting familiarization, evaluation, and survey flights—this appears to be a relatively modest, focused demonstration program rather than a large-scale test campaign.
- `asrt-q-06-c1` gold **unsupported** / judge **__unparsed__** — Based on the passage, the demonstration flights were conducted at the RTC (Rucker Training Center) in coordination with the 101st Airborne Division and the Army Capability Management - Recon Attack office, which points to Fort Rucker, Alabama, as the location for these Apache helicopter flights.
- `asrt-q-07-c3` gold **supported** / judge **unsupported** — If you have additional context or a source document with a specific date mentioned, I'd be happy to help pinpoint the exact fielding timeline more precisely.
- `asrt-q-10-c2` gold **partial** / judge **__unparsed__** — The scenario emphasized building foundational skills across Air Force specialties—such as base security, logistics, and infrastructure support—needed to operate in a contested or deployed setting, reflecting a generic expeditionary/deployed threat environment rather than a specific nation-state or named opposing force scenario.
- `asrt-q-22-c2` gold **partial** / judge **supported** — By hosting a U.S. space domain awareness payload on Japan's QZS-6 satellite, the two countries established a new model of security-focused space collaboration.
- `asrt-q-22-c3` gold **partial** / judge **supported** — It also represents the first of two planned launches under the JAXA Quasi-Zenith Satellite System Hosted Payload (QZSS-HP) program, setting the stage for continued joint efforts in space situational awareness between the two allies.
- `asrt-q-23-c1` gold **supported** / judge **__unparsed__** — Based on the passage, only the first QZSS-HP payload launch date (February 2, 2025) is provided.
- `asrt-q-23-c2` gold **partial** / judge **__unparsed__** — The specific date for the second launch is not stated in the passage, but since QZS-6 was the first of two planned launches under this program, the second payload would be hosted on QZS-7, which is expected to follow at a later date—likely sometime in 2025 or subsequent to the first launch, based on typical satellite deployment schedules for this program.
- `asrt-q-25-c2` gold **supported** / judge **unsupported** — The actual results, findings, or specific Soldier feedback from these experiments would likely be released in a follow-up report or after-action review once the testing period concluded and data was analyzed by the Next Generation Combat Vehicle Cross Functional Team and CCDC Ground Vehicle Systems Center.
- `asrt-q-33-c1` gold **partial** / judge **__unparsed__** — Some news reports likely cited the higher price tag for the first (lead) ships in the DDG-1000 program, which include substantial one-time research, design, and development costs, rather than the lower steady-state unit cost the Pentagon expects once the production line is fully established and building ships at a normal rate.
- `asrt-q-33-c2` gold **partial** / judge **__unparsed__** — In other words, the higher figures reflect the "learning curve" and non-recurring engineering expenses of the initial vessels, while the $2.2–$2.5 billion estimate reflects the average cost per ship after the program matures.
- `asrt-q-34-c1` gold **supported** / judge **__unparsed__** — The passage doesn't confirm a $7 billion price — in fact, it says the opposite.
- `asrt-q-34-c2` gold **supported** / judge **__unparsed__** — The Defense Department official stated that reports citing figures like that are too high, and that the actual projected cost is $2.2 to $2.5 billion per ship once the production line is running at full, steady-state pace.
- `asrt-q-34-c3` gold **unsupported** / judge **__unparsed__** — The $7 billion figure likely reflects early lead-ship costs rather than the steady-state unit price.
- `asrt-q-34-c7` gold **unsupported** / judge **__unparsed__** — Learning-curve inefficiencies in the first units built
- `asrt-q-34-c8` gold **unsupported** / judge **__unparsed__** — Amortized R&D expenses for new technologies (like the integrated power system and advanced gun systems) folded into the first ship's price
- `asrt-q-34-c9` gold **unsupported** / judge **__unparsed__** — Once production ramps up and these one-time costs are spread across multiple hulls
- `asrt-q-36-c2` gold **unsupported** / judge **__unparsed__** — In short, the Navy judged that team's technical solution and program management approach to be superior to
- `asrt-q-39-c1` gold **unsupported** / judge **supported** — Based on typical Arleigh Burke-class destroyer contracts of that era, the USS Harvey C. Barnum Jr. (DDG 124) cost approximately $1.7 billion to $2.2 billion to build, though the passage itself doesn't specify an exact cost figure for this particular vessel.
- `asrt-q-40-c4` gold **partial** / judge **__unparsed__** — Since the ship had not yet been commissioned at the time of this event, the passage does not contain information about a first deployment, as that would occur only after commissioning and subsequent workups/training.
- `help-q-02-c3` gold **unsupported** / judge **__unparsed__** — With IDIQ contracts, the government commits to a minimum order (often much smaller, though not specified in this passage) and then issues task or delivery orders as needed up to the ceiling amount.
- `help-q-02-c4` gold **unsupported** / judge **__unparsed__** — The actual total value realized will depend on how many orders are placed against the contract over its duration, and could end up being significantly less than $500 million if not all potential orders are exercised.
- `help-q-02-c5` gold **unsupported** / judge **supported** — The passage does not provide additional details about the guaranteed minimum, contract duration, or projected/expected drawdown rate that would allow for a more precise estimate of the "actual" expected value.
- `help-q-06-c2` gold **supported** / judge **__unparsed__** — It only mentions details about the number of flights (23), total flight hours (29.9), the helicopter model (AH-64E Version 6 Apache), and the units/organizations involved—17 pilots from the RTC, 101st Airborne Division, and the Army Capability Management - Recon Attack.
- `help-q-07-c3` gold **supported** / judge **__unparsed__** — However, it does not mention:
- `help-q-07-c4` gold **supported** / judge **unsupported** — A decision to field the system across the entire Apache fleet
- `help-q-07-c5` gold **supported** / judge **unsupported** — Any timeline or start date for fielding
- `help-q-07-c6` gold **supported** / judge **unsupported** — If you have additional text or a source document that includes details about the fielding decision and timeline, please share it and I can help answer your question based on that information.
- `help-q-09-c2` gold **supported** / judge **__unparsed__** — It only states that more than 200 Airmen total converged from multiple Air Force and joint military installations to form the 23d Air Task Force.
- `help-q-14-c1` gold **supported** / judge **__unparsed__** — Part one of the Steadfast Defender exercise involved:
- `help-q-18-c1` gold **supported** / judge **__unparsed__** — According to the passage, the agreement was led by the Army Contracting Command, working in collaboration with:
- `help-q-18-c3` gold **supported** / judge **__unparsed__** — The Army
- `help-q-18-c4` gold **supported** / judge **unsupported** — The Air Force
- `help-q-19-c1` gold **supported** / judge **__unparsed__** — The passage doesn't provide that figure.
- `help-q-20-c2` gold **supported** / judge **__unparsed__** — It only states that DOD negotiated a three-year, $617 million joint enterprise license agreement directly with Microsoft, achieving the best pricing to date for Microsoft desktop and server software licenses.
- `help-q-21-c2` gold **partial** / judge **__unparsed__** — Payload type: A U.S. space domain awareness payload (a sensor package designed to help track and monitor objects in space)
- `help-q-22-c4` gold **partial** / judge **supported** — Additionally, the mission itself is notable because it involves hosting a U.S. space domain awareness payload on a Japanese satellite (QZS-6), demonstrating an innovative approach where the U.S. leverages Japanese satellite infrastructure to expand its space monitoring capabilities—essentially "hosting" American security technology on an allied nation's spacecraft rather than launching a dedicated U.S. satellite for this purpose.
- `help-q-26-c2` gold **supported** / judge **__unparsed__** — It only mentions that the Next Generation Combat Vehicle – Cross Functional Team and CCDC Ground Vehicle Systems Center are collaborating to conduct soldier operational experiments at Fort Carson, Colorado, running from June 15 to August 14, 2020, to assess the feasibility of integrating unmanned vehicles into ground combat formations.
- `help-q-28-c2` gold **supported** / judge **__unparsed__** — The exercise takes place at Camp Robinson and runs for two weeks, from July 12 to July 25, 2026.
- `help-q-33-c3` gold **supported** / judge **unsupported** — Possible explanations that aren't stated but might logically account for the discrepancy include:
- `help-q-33-c4` gold **unsupported** / judge **__unparsed__** — Including lead-ship costs: Early ships in a class often cost significantly more than later production units due to non-recurring engineering, design, and startup costs.
- `help-q-33-c5` gold **unsupported** / judge **__unparsed__** — If earlier reports cited the cost of the first ship(s) rather than steady-state production costs, that would produce a higher figure.
- `help-q-33-c6` gold **unsupported** / judge **__unparsed__** — Including R&D costs: Total program costs (including research and development) spread differently than per-unit procurement costs could make reported figures higher.
- `help-q-34-c1` gold **supported** / judge **__unparsed__** — The passage doesn't actually support that premise — the official was pushing back against that figure, not confirming it.
- `help-q-34-c2` gold **supported** / judge **__unparsed__** — According to the official quoted, news reports citing costs like $7 billion per ship were too high.
- `help-q-34-c4` gold **partial** / judge **__unparsed__** — The passage doesn't explain what specifically drove the higher $7 billion figures being reported elsewhere (that could reflect early lead-ship costs, R&D expenses folded into the total, or other factors), but it doesn't say the official confirmed or explained that number — only that he disputed it as too high.
- `help-q-36-c2` gold **supported** / judge **unsupported** — It only reports:
- `help-q-36-c3` gold **supported** / judge **__unparsed__** — Who won: Ingalls Shipbuilding and Northrop-Grumman Ship Systems
- `help-q-37-c2` gold **supported** / judge **__unparsed__** — The text only mentions a $2.9 billion, three-year contract awarded to Ingalls Shipbuilding and Northrop-Grumman Ship Systems for the design, building, and testing phase of the DD(X) destroyer and its associated family of surface ships.
- `help-q-40-c3` gold **partial** / judge **__unparsed__** — Christening is an earlier milestone in a Navy ship's life: it involves formally naming the vessel and having its sponsor break a bottle across the bow, but the ship is still under construction at this point.
- `help-q-40-c4` gold **unsupported** / judge **__unparsed__** — Commissioning — when a ship officially enters active service in the fleet — happens later, after construction is completed and the ship is turned over to the Navy.
- `help-q-40-c6` gold **supported** / judge **__unparsed__** — That information would come from a future Navy announcement once USS Harvey C. Barnum Jr. (DDG 124) is completed and formally commissioned.
