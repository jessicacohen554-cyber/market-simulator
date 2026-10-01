# RESULT — SPP-77: SPP gas CC is not self-committed at a scale that explains the crossover; the $147 fuel rows come from a bad EIA Missouri reference

**Zero LP. No solve, no shard, no bundle.** Nothing is owed under rule 15, and nothing is at risk
under rule 31. PRECOMMIT `PRECOMMIT-spp-77-cc-self-commitment-and-f923-outlier-2026-09-24.md` was
pushed at `cf8647e0a3075edac5f79c32b81a1e21fc62d4ca` before any new number was read.
Base `f68160020fa0799eff408e1bd4b80f0cd7f5a017`.
Probe `scripts/probes/_spp77_fuel_outlier.py`; its numbers are in `results/calibration/_spp77_fuel_outlier.json`.

**Verdict: neither A nor B names an admissible input. Nothing was built, no shard was launched, and
the SPP determination is untouched.**

---

## A. The fuel outlier: the reference is wrong; the fix is real but tiny, and not built here

**A1. Reproduced.** Source: the `fleet_only` rebuild of rung 2022 (gas $6.45 hard stop checked).
Jan-2022 CC offer fuel is $147.15 at Hawthorn (2079, 234.7 MW), $147.15 at State Line
(7296, 536.0 MW) and $47.94 at Dogwood (55178, 655.2 MW). That is 1,425.9 MW. Their February
prices are $4.35, $6.57 and $5.20.

**A2. Root cause: candidate (i), the state reference. Not a gap-fill, and not the plants' own prints.**

| item | value |
|---|---|
| Hawthorn's own F923 Jan-2022 print | **$5.41** (30,946 MMBtu) |
| State Line's own F923 Jan-2022 print | **$4.20** (694,427 MMBtu) |
| Dogwood's own F923 prints, 2022 | **none** (the IPP does not report cost) → filled from the nearby pool |
| EIA `N3045MO3` 2022-01 (screen reference) | $152.45/Mcf = **$147.01/MMBtu** |
| Volume-weighted mean of all 11 MO F923 gas prints, Jan 2022 | **$29.09** → reference ÷ own prints = **5.05×** |

- **Mechanism.** `screen_gas_plant_month_prices` checks each print against the reference but never
  checks the reference. A correct ~$5 print is "low" (< 0.5 × 147) and is *replaced by* $147. The
  pool is built from the screened frame, so Dogwood inherits a blend ($47.94). The log's "7 low"
  includes 2079 and 7296.
- **Why the reference is high.** Four MO plants did print $50–166 in Jan 2022, then returned to
  $1.6–4.0 in February:
  - Empire Energy Center (6223): $124.45
  - AECI St Francis (7604): $50.35 on 899 k MMBtu
  - AECI Holden (7848): $61.52
  - Ameren Peno Creek (7964): $166.08

  The same four spiked in Feb 2021 (Uri: $34.68 / $31.11 / $15.05 / $86.53). That pattern
  **fits** a lagged Uri cost true-up booked in Jan 2022 (candidate iii). It is **not proven**. Even
  with those prints, the public MO mean is $29, so the $147 reference is inconsistent with the
  published receipts of its own state.

**A3. Scan: plant-month offer fuel > 3× that month's capacity-weighted class median, 2019–2025.**

| year | flagged row-months | gas/oil MW flagged (excl. lignite) | max ratio |
|---|---:|---:|---:|
| 2019 | 0 | 0 | — |
| 2020 | 35 | 0 | — |
| 2021 | 75 | 1,350 (all **March**) | 4.4 |
| **2022** | **320** | **5,491 (all January)** | **27.1** |
| 2023 | 13 | 240 | 3.7 |
| 2024 | 37 | 1,882 | 5.1 |
| 2025 | 20 | 1,486 | 5.5 |

- **Uri (Feb 2021) is NOT flagged.** The whole class rose together: CC plants priced $17–68 that
  month, and the class median rose with them.
- **Jan 2022 is the one gross outlier**, 5× beyond anything else in seven years.
- The recurring COAL_LIGNITE flags are the same 5 rows / 650 MW at 3.0–4.6×, in 2020–22. That is
  class dispersion within lignite, not a gas-screen object. It is reported, not pursued.

**A4. The pre-declared repair discriminator FAILS its own test, so nothing is built.** The declared
construction was: the reference ÷ the median of the other states in its Census division, with the
same (0.5, 2.0) band.
- It catches MO 2022-01 at **25.5×**.
- It also catches **real** events:
  - Uri Feb 2021: WY 10.2×, NM 5.2×, NE 5.0×, KS 4.9×
  - ID 2019-03: 5.1×
  - a long tail of AK, New England and producing-state cells

Screening Uri away is the one thing the PRECOMMIT forbade, so per its §A.3 the repair is **not built**.

*Post hoc, for routing only, not pre-registered:* the reference ÷ the volume-weighted mean of the
same state's own public F923 prints does separate the two cases.
- Across 2,663 state-months the median is 0.99.
- MO 2022-01 is **5.05×** and the next cell is 2.40× (IA 2019-02).
- Uri cells read 1.00–1.30 (KS 1.05, NE 1.02, WY 1.01, NM 1.00, TX 1.30).
- But with the (0.5, 2.0) band it flags **16** state-months across several ISOs (MT 2024, WV
  2023–24, IL, IA, MD). Several of those have only 1–3 public plants, because redacted IPP receipts
  are missing from the public mean.

That is a shared-seam change with cross-ISO reach (rule 25; MISO's 2022 keeper arms this screen
and carries MO plants). **Routed to a shared-data lane with its own PRECOMMIT.**

**Size, if it were fixed.** This is a diagnostic counterfactual only: MO 2022-01 repriced at the
US series by pre-seeding the reference cache, then a merit re-dispatch of the P1 served thermal
energy with SPP-76's instrument.
- 314 rows / 5,078 MW repriced.
- CC_REGULAR **+0.080 TWh**, COAL_PRB −0.011, CT_PEAKER −0.051, ST_GAS −0.012.
- Proxy fidelity: CC 29.04 / 28.42 P1 TWh, PRB 89.79 / 87.74.
- **C1 COAL_PRB 2022 stays +9.60 against ±8.00.** C4 was not re-scored: a 0.08 TWh one-month
  shift cannot move NRMSE 0.321 below 0.30.

## B. The missing driver: a published measure exists, and it is ~10× too small

**Sources.** SPP MMU Annual State of the Market reports for 2019–2025 (spp.org), plus the committed
`data/raw/spp-planning/transcriptions/ASOM_{2023,2024,2025}.txt` (calendar 2023 / 2024 / 2025).

**B1. What is published.** "Origin of start-up instructions for gas resources" gives CC separately
from simple-cycle CT and ST:

| calendar year | CC **self-commitment** share of start-up instructions | DA-market | RUC | source |
|---|---:|---:|---:|---|
| 2019 | 7 % | 89 % | 2 % | 2019 ASOM Fig 3-4 p.82 |
| 2020 | 9 % | 88 % | 2 % | 2021 ASOM Fig 3-3 p.93 |
| 2021 | 7 % | 88 % | 2 % | 2021/22/23 ASOM |
| 2022 | 7 % (2022 ASOM) / 8 % (2023 ASOM revision) | 89 % | 3 % | 2022 ASOM Fig 3-3 p.81 |
| 2023 | 9 % | 88 % | 2 % | 2023 ASOM Fig 3-3 p.73 |

- The measure is a **share of DA start instructions**. The MMU does not say whether it counts
  starts or started MW, and it is not energy or hours.
- CC **self-committed energy** is published only as a stacked chart ("Dispatch MWh by fuel/
  technology by commitment type"). Read from the vector geometry (a measurement, not a quoted
  number; the 2022/23 legend colours are swapped and were reconciled to the MMU's stated CC share):

| year | self-committed / total CC | share |
|---|---|---:|
| 2019 | ~0.9–1.0 / 46.6 TWh | ~2 % |
| 2020 | ~1.0 / 47.2 TWh | ~2 % |
| 2021 | ~1.23–1.33 / 35.7 TWh | ~3.5 % |
| 2022 | ~1.9–2.0 / 37.7 TWh | ~5 % |

**B2. Sizing against the gap.** Upper bound: all self-committed CC energy, as an average MW, is
placed entirely in RT≤0 hours.

| year | RT≤0 CC+ST gap (measured − model, MW) | self-committed CC, avg MW | coverage | vs C1 CC shortfall |
|---|---:|---:|---:|---:|
| 2020 | 3,229 − 1,767 = 1,462 | 114 | 7.8 % | — |
| 2021 | 2,070 − 426 = 1,644 | 140–152 | 8.5–9.2 % | 1.28 / 6.63 TWh = 19–20 % |
| 2022 | 2,176 − 277 = 1,899 | 217–228 | 11.4–12.0 % | 1.95 / 7.55 TWh = 25–26 % |

- The C1 column assumes the model gives self-committed CC zero energy. It does not (28.4 TWh CC in
  2022), so the true reach is lower still.
- Pass condition (c) was ≥ 50 % coverage. It **FAILS in every year.** Converting the start share
  to MW would also need a fitted scalar, because counts vs MW are unstated, so it fails there too.
- **The pattern is flat.** The start share runs 7 / 9 / 7 / 7–8 % while the model's CC+ST in RT≤0
  collapses 3,548 → 277 MW (12.8×).

**B3. What the measure does say.** **88–89 % of SPP CC starts are SPP's own day-ahead market
commitments**, not self-commitments. So the CC that stayed online in the real low-price hours was
mostly *market-committed*.
- The MMU's own explanation for that is the DA commitment's multi-hour constraints: "may continue
  to run a unit even when the marginal price falls below that unit's offer" (lead time, 2022/2023
  ASOM), plus the missing multi-configuration CC model (2021 ASOM rec. 2021.1).
- That is a **commitment-horizon / unit-commitment-physics** object: a MIP-DA behaviour the pure-LP
  P0/P1 design does not carry. Commitment reach is already on the dead list (SPP-73), and the
  gas-commitment family (SPP-44 R, SPP-66 R) **stays dead**: no measured driver sizes it.

**Plainly: no measured, forward-reproducible driver for SPP's CC self-commitment exists at the
scale of the gap.** The residual is best described as a model-class limitation of the LP commitment
relaxation against a MIP day-ahead market. That is routed, not built.

## Predictions (PRECOMMIT) scored

| # | prediction | outcome |
|---|---|---|
| A | root cause (i), the reference | **HIT** (own prints $5.41 / $4.20; reference 5.05× the state's own public mean) |
| A | fixed screen moves 2022 CC < 1 TWh | **HIT** (+0.080 TWh proxy) |
| A | C1 COAL_PRB 2022 stays out of band | **HIT** (−0.011 TWh) |
| A | C4 gas 2022 moves < 0.02 | not re-scored (0.08 TWh in one month; see §A) |
| B | a measure exists but fails (b) or (c) | **HIT on (c)**; **MISS on the form**: it IS gas-CC-specific, so (b) passes |
| B | gas measure flatter than the model's CC commitment | **HIT** (7–9 % flat vs 12.8× collapse) |
| B | no admissible driver → no shard | **HIT** |

## Failing rung rows and their owning objects

| row | owning object | this lane |
|---|---|---|
| C1 COAL_PRB 2022 +9.60 (±8.00) | crossover fuel-elasticity of CC commitment: DA market commitment physics (MIP horizon), not self-commitment, not heat rates, not fuel data | self-commit sized at ≤ 26 % upper bound; the MO fix reaches −0.01 TWh |
| C4 gas 2022 NRMSE 0.321 (0.30) | same object (CC decommitted in low hours), plus the Jan-2022 MO reference defect (tiny) | defect root-caused and routed |
| C3b 2020 / 21 / 22 (0.257 / 0.234 / 0.208) | price body and shape (SPP-74), gas low side (SPP-75); 2021 is Uri | not reached |
| C3a 2020 +15.5 % | price level: missing tail and congestion rent (SPP-70, SPP-74) | not reached |

## Routes

1. **Shared-data lane:** screen the F923 *reference* against its own state's public prints. Pre-
   register the band; enumerate the 16 cross-ISO cells; prove byte-identity elsewhere.
   MISO (MO plants, 2022) is the other exposed lane.
2. **SPP CC commitment:** the only unexplained object left is DA-market commitment physics. It has
   no admissible SPP lever on the dead list. The owner may choose to ledger C1 COAL_PRB / C4 gas
   2022 on the rung as a model-class limitation; rule 30(c) already keeps it from decertifying.
3. The secondary (SPP-75 §9.5 scoped CHP swap, a rule-28(c) PR, ~10–14 % reach) remains open.
