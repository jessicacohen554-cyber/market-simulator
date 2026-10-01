# PREREG nyiso-130 (Priority 2) — the NYISO solar CF LEVEL, identified and NOT armed this session

**Registered 2026-08-06, session nyiso-130.** Lever-queue item 2
(`docs/mechanism-testing-matrix.md` §5.5), named by nyiso-129 §5. Its own
object and its own pre-registration (rule 19 `[R-ONE-MECH]`), deliberately not
bundled with the session's Priority-1 A/B.

**Status: IDENTIFIED, RECONCILED, NOT ARMED.** The gating precondition
nyiso-129 set — reconcile 981.8 vs 1,081.8 GWh before sizing anything — is
**discharged** (§1). The identification is complete (§2) and turns out to be
*narrower* than nyiso-129's framing (§3). No solve is spent on it here: the
session's A/B is committed to Priority 1, and stacking a second lever on the
same arms would confound both. Everything below is reproducible from
`scripts/probes/_nyiso130_solar_gwh_reconciliation.py` →
`results/calibration/_nyiso130_solar_gwh_reconciliation.json`.

---

## 1. The GWh reconciliation — RESOLVED, and nyiso-128's figure is retired

Re-extracted Table III-2a from the committed 2026 Gold Book with a parser that
counts every `PV SUN` line and **reports** the ones it cannot match rather than
dropping them:

| | value |
|---|---|
| `PV SUN` lines on the page | 16 |
| rows matched (carry a Net Energy figure) | **15** |
| **reproduced total** | **981.8 GWh over 573.4 MW** |
| name-key collisions (the silent-overwrite failure mode) | **none** |
| capacity cross-check vs the independently-derived registry | **PASS** (573.4 MW, to 0.1 MW) |

**981.8 GWh is CONFIRMED. 1,081.8 GWh is RETIRED.** Two independent extractions
(nyiso-129's and this one) agree to 0.1 GWh, and the capacity total matches
`data/raw/reference/nyiso-market-solar-capacity.csv` — built from the same table
by a different script for a different purpose — exactly.

The error is **2025-only**. Extracting each Gold Book vintage's own reported
year:

| Gold Book vintage | reports | units | published Net Energy | nyiso-128 quoted |
|---|---|---:|---:|---|
| 2024 | 2023 | 10 | **229.9 GWh** | 0.23 TWh ✓ |
| 2025 | 2024 | 15 | **503.2 GWh** | 0.50 TWh ✓ |
| 2026 | 2025 | 15 | **981.8 GWh** | 1.08 TWh ✗ (+100.0 GWh) |

The third instrument nyiso-128's own prereg cited **corroborates the reproduced
figure, not the quoted one**: nyiso-106's independent MIS P-63 daylight-bulge
decomposition put 2025 at 0.994 TWh *as a lower bound*. The reproduced 981.8 GWh
sits **1.2 %** from it; 1,081.8 GWh sits **8.8 %** above it.

**Consequence, as nyiso-129 predicted:** the armed arm delivers 0.75 TWh of 2025
market solar, so the over-removal is **0.232 TWh**, not 0.332 — and the
"unearned" share of the C3a-2025 gain shrinks correspondingly. This does not
touch the promotion: the residual still runs in the tightening direction and is
still not a free parameter.

The 16th `PV SUN` row is **Shoreham Solar Commons (25.0 MW, Zone K)**, which
reports **0.0 across every capability column and no Net Energy at all**. It is
correctly excluded by both extractions and is likewise absent from the 573.4 MW
registry — not a missing unit.

## 2. The object

`RENEWABLE_AVG_CF["NYISO"]["solar"] = 0.15` — a **self-declared Tier-3
approximation**, sitting under a block comment that reads *"solar is the physical
utility-PV value for the latitude band. **needs-citation: verify against EIA-923
ISO totals before quoting a forecast**"* (`constants.py:3226-3233`). It is the
normalization target `renewables.derive_cf_profile` scales the NYISO solar shape
to, and the model realizes ~**0.133** after the nyiso-75 donor repair and
clipping.

## 3. The identification — and it is NARROWER than nyiso-129's framing

Measured CF = published Net Energy ÷ the registry's own **monthly** capacity
exposure (not year-end capacity — a plant commissioned in July is not exposed
for twelve months):

| year | published GWh | capacity exposure | **measured fleet CF** |
|---|---:|---:|---:|
| 2023 | 229.9 | 1,411,104 MW·h | **0.1629** |
| 2024 | 503.2 | 3,426,682 MW·h | **0.1468** |
| 2025 | 981.8 | 5,022,984 MW·h | **0.1955** |

**Reported against interest: the measured CF is NOT a stable 0.1955.** It swings
0.147 → 0.196, a 33 % range, so nyiso-129's "measured 0.1955" is a **2025-only**
statement and 2023/2024 do not support it on their face.

**The swing has a clean, non-fitted explanation, and it selects 2025:**
commissioning ramps. 2024 is the heavy build year (Capital_Hudson 80 → 300 MW,
Upstate_West 40 → 219 MW) and reads the *lowest* CF, because the monthly step
counts a plant as fully present from its in-service month while a commissioning
plant is not yet at full output. **2025 added no PV market generator at all** —
the 2026 Gold Book confirms the same 15 units — so **2025 is the only year in
which the measured number is a clean read of a mature fleet**, and it reads
**0.1955**.

So the identification is: **0.1955, from the one mature-fleet year**, with
2023/2024 explicitly excluded as commissioning-contaminated rather than averaged
in. Rule 13 `[R-MEASURED]` admissible — it is the registry's own published output
over its own published capacity, regenerates from each Gold Book vintage, and
responds to changed conditions (fleet mix, new entries). **Identified from the
registry, never from the price residual** (rule 13); the price direction is not
consulted at any point in §1–§3.

## 4. What must be pre-registered BEFORE it is armed

Handed forward deliberately unfinished, so the arming session states them ex
ante rather than after seeing a number:

1. **Which quantity moves.** `RENEWABLE_AVG_CF["NYISO"]["solar"]` is an
   **ISO-wide** normalization consumed by `derive_cf_profile`, while 0.1955 was
   measured on the **registered market fleet**. Post-`nyiso_solar_market_generator_basis`
   those are the same population — which is exactly why this lever only became
   well-posed after that arm landed — but the arming session must show that,
   not assume it.
2. **The 0.15 → 0.133 gap is a SECOND, separate defect.** The constant says
   0.15 and the model realizes 0.133; clipping and the donor profile eat ~11 %
   before any re-level. Raising the constant without explaining that gap moves
   the wrong knob. Enumerate it (rule 19) before choosing between re-levelling
   the constant and repairing the realization.
3. **Direction and adverse case.** More NYISO solar is more zero-marginal-cost
   afternoon energy: it pushes C3a **down** and the C3c tail **down**, i.e. the
   same direction as this session's Priority-1 arm. If both land, the combined
   C3a effect must be re-checked against the ±10 % band — **the two levers are
   not independent and must not be scored as if they were.**
4. **Rule 25 `[R-ISO-SCOPE]`.** NEISO carries the identical Tier-3 0.15 with the
   identical `needs-citation`. It is NOT covered by this identification and must
   derive its own from its own market's data.

## 5. Why it is not armed here

The session's solve budget is committed to Priority 1, whose adverse case (§7 of
`PREREG-nyiso130-li-transfer-security-limit-2026-08-06.md`) already puts the C3c
tail in play in all three years. Arming a second lever that pushes the same gate
the same way, on the same arms, would make neither attributable — rule 19's
point exactly. The reconciliation is the deliverable nyiso-129 asked for; the
lever is left **identified, sized and ready**, with its open questions named.
