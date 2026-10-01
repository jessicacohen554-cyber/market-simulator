# FINDING — NWPP-NEXT-14 phase 0 (ZERO LP): Jim Bridger in C4 coal 2023, and Clark's sub-physical CC heat rate

Everything here is read from committed artifacts or fleet-only rebuilds of keeper #18
(`results/calibration/nwppnext13pu_span`, `2026-09-30-nwppnext13-per-unit-attribution`). No LP.
Probes: `scripts/probes/_nwppnext14_{decomp,pile,arm0}.py`.

## 1. C4 coal 2023 (r 0.662 / NRMSE 0.317): Jim Bridger 8066, and why #18 deepened it

The C4 coal actual is the raw EIA-930 coal series (42.27 TWh, rebuilt with `run_calibration_full._eia930_frame`);
the model is the sum of the COAL_* class hourlies.

| series swapped into the fleet | r | NRMSE |
|---|---:|---:|
| keeper #17 as registered | 0.695 | 0.283 |
| keeper #18 as registered | **0.662** | 0.317 |
| #18 with Bridger ← its #17 series | 0.709 | 0.281 |
| #17 with Bridger ← its #18 series | 0.646 | 0.323 |
| #18 with Bridger ← CEMS | 0.849 | 0.239 |
| #18 with Bridger ← CEMS **Jan–May only** | 0.697 | 0.270 |
| #18 with Bridger ← CEMS **Jun–Oct only** | **0.821** | 0.287 |
| #18 rest-of-fleet (no Bridger) vs 930 − Bridger CEMS | 0.751 | — |

**Bridger alone accounts for more than the whole deepening.** Every other coal plant moved the other way in net
(the rest of the fleet is r 0.751 on its own). At #18 the decisive window is **Jun–Oct**, not the Feb–May
conservation that is closed (HANDOFF-nwppnext13).

Bridger monthly GWh, 2023:

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| #17 | 1398 | 1220 | 983 | 317 | 547 | 670 | 697 | 738 | 672 | 623 | 634 | 690 |
| #18 | 1398 | 1221 | 991 | 613 | 200 | 263 | 341 | 1381 | 295 | 225 | 795 | 796 |
| CEMS | 906 | 416 | 294 | 164 | 345 | 662 | 1155 | 1171 | 892 | 1267 | 879 | 960 |

Hourly: #18 is bimodal (P25 349 MW, median 861, P75 1,884); CEMS is steady (median 1,047).

**Mechanism (pile rows rebuilt past the fleet-only exit, `_nwppnext14_pile.py`).** Bridger's yard, 2023, cumulative
TBtu at each month-end:

| | Jan | Mar | Jun | Jul | Sep | Oct | Dec |
|---|---:|---:|---:|---:|---:|---:|---:|
| ceiling | 24.06 | 41.95 | 68.79 | 77.74 | 95.63 | 104.58 | 122.47 |
| soft take floor | 0.00 | 15.06 | 41.34 | 50.10 | 67.62 | 76.38 | 93.90 |
| #18 burn | 15.41 | 39.80 | 51.67 | 55.43 | 73.92 | **76.40** | **93.94** |
| CEMS burn | 9.98 | 17.81 | 30.72 | 43.45 | 66.19 | 80.17 | 100.43 |

- #18 burns **exactly its take floor** for the year (93.94 vs 93.90 TBtu) and touches it at Oct-end. Bridger is
  never economic above the floor: its economic tranches offer $38–51/MWh (F923 delivered coal $3.42/MMBtu at
  11.02 MMBtu/MWh + $4.50 VOM), the dearest coal in NWPP-EAST (Hunter $33.9, Huntington $30.0, Colstrip $29.4).
- NWPP-EAST model price by month, 2023: 163.4, 62.2, 45.1, 34.4, 25.4, 24.8, 32.6, 34.4, 31.3, 32.0, 42.3, 46.7.
  The share of hours above $42.19 is 0.97 / 0.86 / 0.94 in Jan–Mar and 0.00–0.02 in Apr–Oct.
- The measured WEIM ELAP prices (`data/raw/nwpp-weim`, May–Dec 2023) sit in the same range: PACE 19.8, 25.6, 52.9,
  38.4, 31.0, 40.3, 45.7, 39.6; IPCO 20.1, 26.6, 51.8, 39.2, 33.3, 56.0, 53.4, 45.2. Only July is clearly low in the
  model (32.6 vs ~52). So the summer under-run is **not mainly a price-level error**. Bridger's offer sits above
  most measured West imbalance prices too, and it ran baseload anyway.
- The LP therefore places the obligated take in the dearest hours (perfect foresight): Jan–Mar and August.
  Jan–Apr burn is 4.22 TWh against CEMS 1.78, and every MWh spent there is missing from Jun–Oct.
- Keeper #17 hid this. Its class-default take-or-pay must-run (953.5 MW) forced 101.3 TBtu of flat burn. #18's
  **measured** must-run (351.8 MW) removed an unmeasured floor, correctly under rule 14, and exposed the offer.

**What this says, and does not say.** The Feb–May conservation remains closed (no admissible identification).
The new, separable question is Bridger's **offer**. Bridger Coal Company is a captive mine (PacifiCorp 2/3,
Idaho Power 1/3), and its F923 delivered cost is an average that includes fixed mine cost. Whether a public filing
splits that into fixed and variable parts is an identification question for the next lane (owner card "Both",
2026-09-30). It is never a tuned passthrough (rules 1, 13).

### 1.1 The vintage-static tranche row: real, but not the cause

The per-unit tranche artifact divides each bin's pooled 2023–2025 CAMPD conduct by one nameplate, the head fleet's.
Bridger's coal bin is 2,119 MW in 2023 (four units on coal) and 1,049 MW in 2024–25 (units 1–2 converted to gas).

| derive | nameplate | committed | must-run | p25 CF | median CF |
|---|---:|---:|---:|---:|---:|
| per-unit, 2023 only | 1049 | 30.5 | 30.5 | 65.1 | **113.8** |
| per-unit, 2024–25 | 1049 | 16.4 | 16.4 | 29.7 | 67.2 |
| per-unit, 2023–25 (keeper #18) | 1049 | 16.6 | 16.6 | 39.9 | 76.6 |
| fuel-split on each year's own vintage bin | 2119 | 16.3 | 16.2 | 30.8 | 62.3 |

The 2023-only row reads a median CF of 113.8 %, which is physically impossible (rule 14). The miso-278 unit-fuel-split
construction (`unit_fuel_split_rows`) already derives on each window year's own EIA-860 vintage bin. Composed with the
per-unit family, it moves only that one line, and in the LP only Bridger's must-run: 351.8 → 343.3 MW (2023), 174.1 →
169.9 MW (2024), plus a 2.1 / 1.0 MW committed sliver. It is a structural repair, not the C4 lever.

## 2. Clark 2322: a sub-physical CC heat rate, and the CC over / CT under drift

At keeper #18, Clark CC_REGULAR (462 MW) dispatches **3.69 TWh every year**, which is its full availability, against
EIA-923 CC net of 0.43–0.86 TWh: **+2.8 to +3.3 TWh/yr**. That alone exceeds the whole CC_REGULAR over-dispatch of
2024–25, and CT_PEAKER under-dispatch is its substitute.

- Every Clark generator loads eGRID's plant-grain rate: **3.007 MMBtu/MWh** (3.703 at the 2019 vintage). CAMPD
  meters Clark's 24 GT peakers (units 11A…22B), not its combined cycle, so eGRID's `PLHTIAN` covers the peakers while
  `PLNGENAN` covers the whole plant. The CT_PEAKER bins are overridden by `measured_ct_heat_rates` (10.633); the CC
  bins have no measured row and keep 3.007, which gives an $11/MWh offer in 2024.
- EIA-923 measures the CC block (CT fuel ÷ CT + CA net) at **9.38 / 9.27 / 9.00 / 9.30 / 9.48 / 9.04 / 9.59** in
  2019–2025.
- Before #18, Clark CC was 0.002–0.68 TWh available, so the rate did not matter. Per-unit attribution (correctly)
  made it available and exposed it.
- No existing flag reaches it. `egrid_family_heat_rates` needs eGRID unit heat input for the CC family, which Clark
  lacks (its derived NWPP family artifact has no Clark row). The boundary repair only fixes rates that are too high.
  SPP-49's floor is for simple-cycle-only plants.
- Census of the NWPP fleet, 2019 / 2023 / 2025: the only other CC row below 6.3 is Oregon State University 57653
  (CC_CHP, 5 MW), which is steam-credited and belongs to the CHP chain. Clark is the only instance.

## 3. The arm (owner cards, 2026-09-30)

1. **`eia923_cc_family_heat_rates`** (new, default off; card "EIA-923 CC-family HR"). A non-CHP plant's
   CT/CA/CS/CC rows whose loaded rate is below the CC physical floor (`HEAT_RATE_BINS["gas_cc"]["h_class"]`, 6.3)
   take the plant's own EIA-923 CC-family rate for the eGRID vintage the join reads, accepted only inside
   [6.3, 11.5]. It is a population rule, zero DOF. Artifact: `eia923_cc_family_heat_rates_NWPP.csv`. On NWPP it
   moves Clark's six CC rows only (3.007 → 9.038 at the 2024 vintage, 9.476 at 2023, 9.376 at 2019).
2. **`campd_unit_fuel_split` composed with `campd_per_unit_attribution`** (card "Both"). The selector now returns
   the per-unit family's own `-perunit-fuelsplit-` companion. It is derived with
   `derive_thermal_tranches.py --per-unit-attribution --unit-fuel-split` against the per-unit outage extract, and it
   moves Bridger's COAL row only (§1.1).

LP-array delta of both together, fleet-only on keeper #18's recipe (`_nwppnext14_arm0.py`): only Clark's three CC
bins (heat rate, offer) and Bridger's four coal bins (must-run split) move, in 2023 and 2024.

**Prediction.** Clark CC falls from ~3.7 TWh toward its 0.4–0.9 TWh history in every year, and CT_PEAKER plus other
CCs pick up the difference. C1 CC_REGULAR over-dispatch in 2024–25 should shrink by up to ~3 TWh and CT_PEAKER
under-dispatch should shrink. C4 coal 2023 should barely move: the Bridger floor falls by 8 MW, and Clark is a gas
plant, so coal moves only through prices. The decision rests on rule 14, not on those records.

## 4. Lever 3 (coal WEFOR relief): owner card "New sub-gate, default off"

The owner ruled that the live-capacity denominator becomes a **new** default-off field, so miso-266's shared flag and
MISO's keeper stay byte-identical. It is not built in this session. It is routed to the next lane with the WEFOR relief.
