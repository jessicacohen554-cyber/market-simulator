# FINDING — R-ERCOT-5: the 2019 scarcity tail, and the rest of the measured-availability stack (zero LP)

**Session:** R-ERCOT-5, 2026-09-25.
**Keeper:** `2026-09-25-r-4-day-guard` (bundle `results/calibration/r_ercot4_dayguard_span`, 2019–2025). Precondition checked on `main`: `keepers/ERCOT.json` names it.
**LP spent in this finding:** none. Every number comes from the keeper's committed hourly sidecars, instrumented `fleet_only` rebuilds of the keeper recipe, CAMPD unit-level CEMS (`data/raw/campd-unit-level/TX_<y>.parquet`), EIA-860 and the committed RT hub series (`actual_lmp_hourly_ERCOT.parquet`).

## Headline

- ERCOT stays **CALIBRATED** on the train tier. Nothing here touches it.
- **2019's C3a +99 % is two objects.** The >$1,000 tail carries **75 %** of the load-weighted gap ($46.96 of model LW vs $10.24 RT). The sub-$1,000 body carries the rest (+37 % even with both series capped at $1,000) — FINDING-r-ercot-3's coal-behind-gas merit order.
- **The tail is part real, mostly phantom.** 21 of the model's 72 hours above $1,000 coincide with real RT hours above $1,000 (Aug 12–16). 12 model hours above $1,000 had RT below $200. March (5 h) and July (9 h) are pure phantoms (RT 0 h above $1,000).
- **A construction defect sits under the phantoms, and it is in every year.** The CAMPD full-stop unit windows — the standard (≥ 5 d), short-coal and short-gas families — are stored as DATES and re-expanded to 00:00–23:00. **~99 % of ERCOT windows are contradicted by CEMS for the very unit they declare out**, on their first or last day. In 2019 those "out" units generated **4.5 TWh inside their own windows**.
- The repair already exists in the codebase (caiso-183 carriage, nyiso-229 **K**). It never reached ERCOT: its selector is predicated on the NYISO per-unit/merit extract family, which ERCOT does not arm. **Armed for test in this session** (PRECOMMIT-r-ercot-5).
- **2020 is data-blocked, with one bounded availability component** (§4).

## 1. 2019, month by month: real vs phantom

Keeper payload, P1, load-weighted over zones; RT = `HB_HUBAVG`.

| month | model mean | RT mean | model h > $1k | RT h > $1k | P1 slack MWh | model tail $/MWh (eq-hr) | RT tail |
|---|---|---|---|---|---|---|---|
| Mar | 68.7 | 26.0 | 5 | 0 | 244 | 38.2 | 0.0 |
| Jul | 76.1 | 30.1 | 9 | 0 | 0 | 38.9 | 0.0 |
| **Aug** | **327.7** | **131.1** | **39** | **17** | **6,401** | **276.3** | **88.2** |
| Sep | 121.0 | 50.1 | 14 | 6 | 22 | 79.8 | 16.1 |
| Oct | 45.9 | 28.0 | 5 | 2 | 0 | 20.2 | 4.9 |
| other 7 | 20–28 | 17–25 | 0 | 1 | 0 | 0 | ≤ 1.6 |

- **Real:** Aug 12–16, 2019. RT hit the $9,000 cap on Aug 13 and 15, and the model's slack peaks (1,117 / 1,599 MWh) sit on exactly those afternoons.
- **Phantom:** Mar 4–5 (RT $55–790), Jul 9–10 and 30, Aug 2/5/6/14/21/22, Sep 3/23/25–26, Oct 2. The model sets $2,400–$7,800 there against RT $70–$900.

## 2. Model capability vs each plant's own same-hour CEMS output, in the 72 scarcity hours

Probe `scripts/probes/_r_ercot5_availability_census.py`. It rebuilds the keeper fleet (`fleet_only`), snapshots availability before the DAM pin, after the DAM pin, and final (after the ERCOT-148/149 precedence cap), and compares each plant's `Σ pmax × availability` with its CEMS net output that hour, at **unit grain**. W A Parish's gas-steam units route to 34702, and Barney Davis unit 1 to 49392. Measured output is capped at the plant's `pmax`.

Mean MW of available capability below the plant's own measured output, over the 72 hours:

| binding stage | MW |
|---|---|
| precedence cap, a single short (< 5 d) window below CEMS | 300 |
| precedence cap, a single standard window below CEMS | 194 |
| precedence cap, window × partial product only (the ercot-173/174 double count) | 101 |
| DAM COP fraction itself below CEMS | 107 |
| DAM pin / class-hour water-fill (gas, unmapped plants) | 530 |
| **total** | **1,231** |

Named cases:
- **Martin Lake, Aug 6 afternoon:** 1,586 MW available vs 2,357 MW CEMS. U3's short window is dated Aug 2 → **Aug 6**, and U3 was back by the morning of Aug 6.
- **Limestone, Jul 9:** 893 vs 1,402. LIM2's window ends Jul 9, the day it restarted.
- **Oak Grove and Cedar Bayou, Sep 3:** windows end Sep 3.
- **Lake Hubbard, Jul 10:** 134 vs 585 MW.
- **Mar 4–5:** 0.8–2.0 GW of standard-window caps on units CEMS shows running.

## 3. The defect: day-granular window edges

`outages.unit_outage_event_window` reconstructs a window with no hour columns as `[outage_start 00:00, outage_end + 1 day)`. The detector finds windows in HOURS (`derive_campd_unit_outages.py`). So the extract asserts up to 23 h at each edge that the detector never detected — exactly where the event contract guarantees the neighbouring hour was running.

Unit-grain census, probe `scripts/probes/_r_ercot5_window_edge_census.py` → `docs/handoffs/r-ercot/r_ercot5_window_edge.json`. It counts hours inside a window at which CAMPD shows the SAME unit (same facility id, same unit id) with gross load > 0:

| year | std windows contradicted | std GWh inside | short-coal | GWh | short-gas | GWh | unit-h on first/last day (all families) |
|---|---|---|---|---|---|---|---|
| 2019 | 824 / 825 | 2,888 | 24 / 24 | 261 | 506 / 506 | 1,388 | 98.3 % |
| 2020 | 966 / 972 | 3,363 | 21 / 21 | 217 | 460 / 460 | 1,231 | 98.7 % |
| 2021 | 992 / 998 | 3,306 | 20 / 20 | 189 | 461 / 461 | 1,243 | 98.5 % |
| 2022 | 741 / 744 | 2,338 | 30 / 30 | 309 | 451 / 452 | 1,087 | 98.9 % |
| 2023 | 598 / 601 | 2,026 | 15 / 15 | 163 | 378 / 382 | 958 | 99.1 % |
| 2024 | 731 / 734 | 2,431 | 27 / 27 | 256 | 395 / 397 | 843 | 98.6 % |
| 2025 | 647 / 655 | 2,062 | 40 / 40 | 365 | 427 / 428 | 969 | 97.5 % |

- Interior contradictions are 1–2.5 % of the unit-hours and 0.2–2.3 % of the energy (all three families). The detector's placement is right; the SCHEMA's rounding is wrong.
- This is NYISO's nyiso-229 measurement reproduced on ERCOT's own CAMPD (its steps 1 and 3; rule 25 — no number crosses).
- It is the same lesson R-ERCOT-4 drew from the shaped partial layer, one grain finer: a layer capping hours its own source shows running.

**Why the repair never reached ERCOT.**
- `unit_outage_window_hour_grain` (nyiso-229, **K** on NYISO) selects the `-perunitmerithour-` extract, and only when `campd_per_unit_attribution` AND `campd_outage_merit_order_guard` are armed.
- ERCOT routes through its bin sheet and arms neither. ERCOT's cell was **U** ("reads the field as n/a in practice").

**Seam, zero LP.** Field ON vs the keeper, fleet-only, TWh of capability per year. `gap` is the capability below own-hour CEMS; `scar` is the mean MW restored in that year's P1 > $1k / slack hours. Full table: `docs/handoffs/r-ercot/r_ercot5_hourgrain_seam.txt`.

| year | coal lift | CC lift / cut | ST lift / cut | coal gap A→B | CC gap A→B | scar MW (coal/CC/ST) |
|---|---|---|---|---|---|---|
| 2019 | 0.73 | 4.29 / 0.94 | 1.60 / 0.60 | 4.15 → 3.81 | 3.77 → 2.17 | 148 / 277 / 269 |
| 2020 | 0.72 | 4.64 / 0.71 | 1.70 / 0.46 | 2.52 → 2.18 | 4.09 → 2.34 | 522 / 69 / 139 |
| 2021 | 0.71 | 4.78 / 0.85 | 1.68 / 0.47 | 5.01 → 4.63 | 3.71 → 1.85 | 116 / 498 / 251 |
| 2022 | 0.77 | 3.02 / 1.15 | 1.35 / 0.47 | 3.69 → 3.28 | 4.07 → 3.01 | 164 / 580 / 223 |
| 2023 | 0.63 | 2.95 / 0.65 | 0.53 / 0.23 | 2.03 → 1.73 | 4.11 → 2.93 | 12 / 31 / 48 |
| 2024 | 0.80 | 2.93 / 1.10 | 0.93 / 0.38 | 3.14 → 2.75 | 4.89 → 3.96 | 0 / 1,013 / 122 |
| 2025 | 0.83 | 2.48 / 0.83 | 0.66 / 0.37 | 3.31 → 2.86 | 4.52 → 3.57 | — (no P1 scarcity) |

- The gas "cut" column is the DAM class-hour water-fill conserving the measured class total, so it redistributes rather than adds.
- **A/A null:** with the field off, the rebuild at the edited HEAD is byte-identical to the pre-edit build (all 251 stage arrays, 2019).

## 4. 2020 (Step 2)

- 2020 has **0 MWh** of P1 slack and 5 hours above $1,000 (RT 2).
- Its LW gap is +7.31 $/MWh. The sub-$1,000 body carries **+5.65 (77 %)**, and the tail only +1.66.
- The body is the coal-behind-gas merit order of FINDING-r-ercot-3 (Jun +6, Jul +9, Apr–May +4 $/MWh; COAL_PRB −13.56 TWh).

**The availability stack does contribute, but boundedly:**
- Coal capability below its own same-hour CEMS output totals **2.52 TWh** in 2020 (all causes). That is an upper bound of ~19 % of the coal energy gap, even if every MWh of it were dispatched.
- The hour-grain arm removes 0.34 TWh of it.
- The rest is the window × partial double count, already adjudicated R (§5).

**2020 is recorded as data-blocked on the coal offer-conduct object.** The owner declined the 2019–2022 SCED procurement. No multiplier is tuned per year, and the 2023 curves are not reused (rule 1(b)/(c)).

## 5. The other layers, censused and not armed

**The window × partial PRODUCT (ercot-173/174 double count)** is still the largest single below-CEMS object:
- It holds coal below its own same-hour output by 2.0–5.0 TWh/yr, e.g. 2019 4.15 TWh.
- The existing unit-scoped composition (`ercot_dam_availability_event_cap_unit_scoped`, matrix **R**) would remove ~70 % of that: 2019 4.15 → 1.39 TWh; coal capability lift 3.7–6.4 TWh/yr.
- In the 2019 scarcity hours it lifts coal only ~87 MW, so it is **not** the 2019-tail object.

This is new evidence for the R cell, and it is **surfaced, not armed**:
- The R was decided on 2026-08-06 against the pre-ercot-185 partial layer. That layer has since been repaired twice (shaped K, day-guard K).
- ercot-185's own log names exactly this re-test ("removing the double-count against a REPAIRED partial layer may no longer flood").
- ercot-173's G-COAL148 gate scored the flood against the product ceiling itself. It never scored against the plant's own CEMS output.
- Coal is now SHORT of actual in every year (2023 −4.3, 2024 −4.9 TWh PRB), where the 2026-08 flood concern was over-dispatch.
- Unit-scoped zero-LP table: `docs/handoffs/r-ercot/r_ercot5_unitscoped_seam.txt`.

**DAM COP below CEMS (107 MW in the 2019 tail):**
- The pin's measured fraction sits below the plant's same-hour output (e.g. Lost Pines 55154). This is the COP's day-ahead declaration versus RT reality.
- Rule 14 decided it: the COP is the chosen instrument, so this is not a defect.

**The coal min-config floor** is a floor (`min_gen`), not a cap. It cannot hold a plant below its own output, so this census has nothing to count for it.

## 6. Small items found (proposed, not done)

- **Fleet coverage, ERCOT (TRE/ERCO) plants that CEMS shows running but the model does not carry** (2019, CEMS p99 net minus model pmax). Two are material:
  - **Decker Creek** steam units 1 & 2: −565 MW (0.68 TWh in 2019; they retired 2020 / 2022). The bin sheet carries only the 206 MW of CTs.
  - **Brazos Valley / Jack Fusco (EIA 55357)**: −558 MW, running every year at 3.4–3.8 TWh gross from the CTs alone. EIA-860 lists its BA as **MISO** while its NERC region is **TRE**, so its ERCOT membership needs a cited crosswalk before any action.
  - Also the known **Hidalgo** code mismatch: 7762 vs bin 55545.
  - Cogeneration shortfalls (Channelview, Deer Park, Pasadena, …) are behind-the-meter netting, not omissions.
- **The unit-outage deriver lost every coal window to COAL-SUB.** It read the bin sheet's `Plant_Group` raw. It is repaired here through `artifact_class`, the same repair R-ERCOT-4 made to the partial deriver. With it, the committed ERCOT std / layup / short / shortgas extracts reproduce **line-for-line (2019+)**.
  - The **non-ERCOT branch of the same deriver has the same break** (it reads `g.plant_group`), so coal windows cannot be re-derived for other ISOs until that is fixed. It is left to those lanes (rule 25).
- The **measured PRB proxy** for 2019/2020 stays unbundled. It is immaterial alone (−$2.4/MWh on 5 `_mustrun` tranches), and bundling it would confound this arm's attribution.
