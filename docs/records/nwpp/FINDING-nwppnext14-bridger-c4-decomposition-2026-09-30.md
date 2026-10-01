# FINDING — NWPP-NEXT-14: why C4 coal 2023 deepened at keeper #18 (zero LP)

Keeper #18 `2026-09-30-nwppnext13-per-unit-attribution`, C4 coal 2023 r 0.662 / NRMSE 0.317 (floor 0.70 / 0.30).
Keeper #17 `2026-09-29-nwppnext12-boardman-membership`, r 0.695 / 0.283. Zero LP: every number below is computed
from committed sidecars (`hourly/class_hourly_2023.parquet` of both bundles; #17's from `8cc35a40`), the two run
payloads, the 2023 leg's `dispatch/2023_P1.parquet` (leg commit `e4f96c37`, provenance only — rule 33(d)), the
EIA-930 coal hourly the scorer uses (`run_calibration_full._eia930_frame`), and CAMPD unit-level hourly for 8066.

## 1. The deepening is Jim Bridger, and only Jim Bridger

Reproduced the scorer exactly: #17 0.695 / 0.283, #18 0.662 / 0.317 (930 coal 42.27 TWh).

| fleet coal series, 2023 | r | NRMSE |
|---|---|---|
| #18 as registered | 0.662 | 0.317 |
| #18 with Bridger's hourly swapped back to #17's | **0.709** | 0.281 |
| #17 with Bridger's hourly swapped to #18's | 0.645 | 0.323 |
| #18 with Bridger = CEMS × 0.92 (all year) | 0.844 | 0.227 |
| #18 with Bridger = CEMS **Feb–May only** (the closed conservation window) | 0.698 | 0.279 |
| #18 with Bridger = CEMS **outside Feb–May only** | **0.810** | 0.272 |

- The rest of the coal fleet moved slightly **toward** the benchmark at #18 (swap test: +0.014). The whole −0.033 is
  Bridger.
- **The deepening is not the closed conservation behaviour.** Correcting Bridger outside Feb–May alone clears the
  floor; correcting only Feb–May does not.
- Bridger plant r vs CEMS: 0.067 (#17), 0.045 (#18). Annual energy is right (model 8.52 TWh; CEMS gross 9.11).

## 2. What changed Bridger's shape

Bridger monthly, 2023 (GWh):

| | J | F | M | A | M | J | J | A | S | O | N | D |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CEMS gross | 906 | 416 | 294 | 164 | 345 | 661 | 1155 | 1170 | 892 | 1267 | 879 | 960 |
| #17 | 1398 | 1220 | 983 | 317 | 547 | 670 | 696 | 737 | 672 | 623 | 634 | 690 |
| #18 | 1393 | 1218 | 993 | 621 | 203 | 258 | 337 | 1384 | 290 | 232 | 795 | 795 |
| #18 econ tranches | 1161 | 1008 | 827 | 516 | 0 | 12 | 83 | 1130 | 45 | 0 | 570 | 562 |
| zone LMP, $/MWh | 163 | 62 | 45 | 34 | 25 | 25 | 33 | 34 | 31 | 32 | 42 | 47 |

1. At #18 the take-or-pay must-run fell from the class default 953.5 MW to the measured 351.8 MW (FINDING-nwppnext13
   §2.4). About 6 TWh of Bridger's energy moved onto the econ tranches.
2. **Those tranches are scheduled by the monthly pile, not by merit.** They run full in August at $34 and at zero in
   July ($33) and September ($31). The coal-yard identity is cumulative with flat ratable receipts
   (`coal_fuel_inventory_monthly_pile`). When the plant's offer sits above LMP, the LP burns only what each
   month-end floor forces, as late as it can: an August catch-up, then Nov–Dec.
3. **Why the offer sits above summer LMP:** the plant's own EIA-923 delivered coal cost, which
   `coal_plant_monthly_pricing` applies, rose from $2.29–2.89/MMBtu in 2022 to **$3.03–4.22/MMBtu in 2023**
   (October 4.22). At a ~10.5 heat rate that is $32–44/MWh of fuel against $25–34 LMP in May–October. Bridger's
   mine is captive, so this figure is an average booked cost that includes mine fixed cost. The marginal cost of an
   extra ton is lower. **That split is not identified in the model today.** It is a candidate structural question,
   not a lever: no offer multiplier moves (rules 1 and 13).

## 3. The "vintage-static tranche row" hypothesis: the defect is real, but it is not the cause

The per-unit deriver routes each unit by **that year's** CAMPD fuel label but divides by the **run-default (2025)**
EIA-860 bin nameplate. At a coal-to-gas conversion, a pre-conversion year's coal gross therefore lands on the
post-conversion coal bin. EIA-860 vintage census of bins that change inside the 2023–2025 window:

| plant | bin | default | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| Jim Bridger 8066 | COAL | 1,049 | **2,119** | 1,049 | 1,049 |
| North Valmy 8224 | COAL | 268 | **522** | **522** | 268 |
| Evander Andrews 7953 | CT_PEAKER | 227.3 | 287.5 | 262.2 | 227.3 |
| (minor) | CC/CT rows at 7605, 55179, 55733, 57028 | | | | |

In 2023, 46 % of Bridger's hourly samples sit above 100 % CF. Valmy's defect predates per-unit attribution: its
incumbent COAL row is byte-identical, with both 2023–24 units over one unit's nameplate.

The repair is `derive_thermal_tranches.py --per-unit-attribution --vintage-denominator` (this branch). Each year's
bins and nameplates, and the outage derate's plant capacity, come from that year's EIA-860 vintage. This is the
convention `_routed_family_rows` (miso-278) already applies. The row nameplate is the window's largest vintage
nameplate. The control (flag off) reproduces the committed `thermal_tranches-perunit-NWPP.csv` byte-for-byte. With
the flag on, 7 rows change:

| row | must-run % | committed % | p25 / median CF |
|---|---|---|---|
| Bridger COAL | 16.6 → **15.4** | 16.6 → 15.5 | 39.9 / 76.6 → 27.2 / 60.0 |
| North Valmy COAL | 40.7 → **24.5** | 40.7 → 24.5 | 50.4 / 57.5 → 26.6 / 42.3 |
| Evander Andrews CT | — | 42.2 → 34.0 | 69.1 / 76.5 → 57.2 / 68.2 |
| 7605, 55179, 55733, 57028 | — | ≤ 1.5 pt | ≤ 5 pt |

For COAL rows the LP reads must-run, committed and online_frac. p25 feeds ST_GAS floors only; median feeds CHP
only. So in solve terms:

- Bridger's forced floor moves −25 MW in 2023.
- Valmy's moves −84 MW on its 522 MW bin (2019–24) and −43 MW in 2025.

Bridger's measured must-run is ~15–17 % on either denominator. **The vintage defect does not explain the
deepening**, and repairing it will not restore the class default. It is a rule-14 repair justified on its own.

## 4. What this leaves

- C4 coal 2023 is bounded by Bridger's Jun–Oct timing (§1), which is set by offer-vs-LMP under the pile identity
  (§2). The Feb–May window is closed (outcome pin).
- Levers, for the owner:
  - (a) arm the vintage-denominator repair (zero DOF, structural; not expected to fix C4);
  - (b) identify captive-mine marginal vs average fuel cost from a public source (a new mechanism, design first);
  - (c) lever 2, the CT/CC widening;
  - (d) lever 3, coal WEFOR, which needs a live-capacity denominator variant.
- Never tune to r. `wefor_multiplier`, offer bands and the pile are untouched.

## 5. Lever 2 (CT under / CC over): Clark 2322's CC block is priced at an impossible heat rate

Zero LP, from the two payloads, the benchmark and a fleet-only rebuild of keeper #18
(`docs/records/nwpp/nwppnext14/ccfloor_census.json`).

- At #18, Clark's CC_REGULAR block (462 MW) dispatches 3.69 TWh in **every** year, at 70–75 % CF in every hour
  (min 70 %). EIA-923 CC net is 0.43–0.86 TWh. At #17 the same block was nearly unavailable, because its GT-peaker
  outage windows were misrouted onto it, so the defect was masked. Per-unit attribution (#18) restored its
  availability and exposed it.
- **Cause: its heat rate is 3.007 MMBtu/MWh** (3.394 in 2020, 3.703 in 2019): eGRID's plant `PLHTRT`. eGRID's plant
  heat input covers only the CEMS-reporting GT peakers, while its net generation also covers the non-CEMS combined
  cycle. No combined cycle beats `HEAT_RATE_BINS["gas_cc"]["h_class"]` = 6.3. NWPP's CC median is 7.3.
- Clark's own EIA-923 filing (Page 1, CT + CA prime movers) gives **9.00–9.59 MMBtu/MWh**, e.g. 2023: 4,100,891 MMBtu
  / 432,784 MWh = 9.476. At 3.0 the block offers at about a third of its fuel cost and runs baseload.
- No existing construction reaches it:
  - The eGRID CC-ceiling repair catches only values that are too high.
  - The SPP-49 simple-cycle floor covers only all-GT/IC plants, and Clark mixes CC and GT.
  - `egrid_family_heat_rates` does not cover Clark: eGRID publishes no unit heat input for its CC units, so its only
    live family is GT (derived here for NWPP, 6 plants covered, Clark absent).
- **Repair (owner card "Build + solve with vintage"): `cc_subfloor_eia923_heat_rates`.**
  - It is the CC mirror of SPP-49. A non-CHP CC-part row (CT/CA/CS/CC) whose plant rate is below the CC physical
    floor takes the plant's own EIA-923 CC prime-mover rate, or the floor where that rate is unusable.
  - Zero DOF. It is applied at the eGRID seam, so CAMPD-measured rates keep precedence.
  - Census: only Clark's three CC tranches move, in all seven years. Class availability is unchanged. Plant 55700
    also trips the floor (3.47 → 7.53) but a downstream measured rate overrides it, so it does not reach the LP.
