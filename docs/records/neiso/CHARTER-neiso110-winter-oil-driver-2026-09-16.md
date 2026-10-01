# CHARTER — neiso-110: what actually drives ISO-NE's winter oil burn

**Opened by** neiso-109, 2026-09-16, on the owner's ruling *"3"* (promote the gas repair **and**
open the oil root cause immediately).
**Evidence that opens it:** `docs/RESULT-neiso109-gas-repair-2026-09-16.md` §6.
**Status:** charter only. **No mechanism is proposed here, nothing is armed, no lever is picked.**

---

## 1. WHY THIS EXISTS

neiso-109 repaired `algonquin_citygate_daily.csv`, which carried **82 rows of other trading hubs'
prices** — 69 through an extremum pattern with no Algonquin anchor, 13 through the main sentence's
character-bounded window. The repair is not in question: Sumas, PG&E, SoCal, Waha, FGT, Chicago
Citygate, Henry Hub and Transco Z6 NY quotes have no business in a Boston citygate series.

**What the repair exposed is the finding.** The model had been burning oil in February 2023 because
it believed Boston gas reached **$30.13/MMBtu**. Boston peaked at **$15.77**. The $28–30 print was
**Transco Z6 NY's** — and it is the very print `data.fuel.hubs.iso_hub_daily_gas_prices`'s docstring
cites as the worked example of the daily overlay succeeding ("the $28/MMBtu 2023-02-02 arctic print
lands on its true calendar day").

Strip it, and **2023 has no hour above oil parity at all**.

## 2. THE GAP, MEASURED

Model oil against NEISO's measured actual (`frontend/data/backcast/bench/NEISO/<year>.json.gz`,
`classFull`), TWh:

| year | **actual** | pre-repair keeper | post-repair keeper | model short by |
|---|---:|---:|---:|---:|
| 2020 | 0.149 | 0.000 | 0.001 | **−0.148** |
| 2021 | 0.239 | 0.020 | 0.021 | **−0.218** |
| **2022** | **1.852** | 0.150 | 0.131 | **−1.721** |
| 2023 | 0.390 | 0.310 | 0.003 | **−0.386** |
| 2024 | 0.312 | 0.250 | 0.048 | **−0.263** |
| 2025 | 0.909 | 1.627 | 2.396 | **+1.487** |

Two facts organize the whole question:

1. **The model is short oil in five of six years, and by 1.7 TWh in 2022 — both before and after the
   repair.** Winter Storm Elliott is the largest oil-burn event in the window and the model never
   reproduced it. The repair did not cause this and does not fix it.
2. **2025 is the one year the model OVERSHOOTS**, and it overshoots by more after the repair. So the
   defect is not a uniform "too little oil" — it is that the *allocation between gas and oil is being
   made by the wrong mechanism*, which lands high in one year and low in five.

The combined gas+oil pair barely moves (RESULT §6): in 2025 the repair shifts 0.77 TWh from gas to
oil and the pair stays 2.37 TWh over actual either way. **The repair changed the label, not the
quantity.**

## 3. THE HYPOTHESIS TO TEST — STATED SO IT CAN FAIL

> **ISO-NE's winter oil burn is not produced by hourly gas/oil price parity. It is produced by
> fuel-security obligations — and the model is currently pricing it as an economic switch.**

The real drivers are institutional and physical, not marginal-cost:

* **ISO-NE's Winter Reliability Program / Inventoried Energy Program** pay for *stored* winter energy,
  so dual-fuel units burn oil to satisfy an obligation and to cycle inventory, not because oil is
  cheaper that hour.
* **Gas-pipeline nomination and interruptible-transport limits** force oil when gas is *unavailable*
  at any price — a quantity constraint the parity test cannot see.
* **Periodic dual-fuel firing/testing requirements** put oil in the stack in hours where parity is
  nowhere close.

If the hypothesis is right, the parity channel should be a *bound* on oil burn, not its generator,
and the missing volume should be reconstructible from the obligation side.

**It can fail**, and here is how: if a corrected parity construction (a per-plant delivered oil price,
a burner-tip gas adder, or a daily rather than annual oil price) reproduces the 2022 1.85 TWh without
touching an obligation mechanism, the hypothesis is wrong and the defect is in the price construction.
**Test that first** — it is cheaper and it is the null.

## 4. WHAT NEISO ALREADY CARRIES — AND A MATRIX GAP THAT HAS TO BE CLOSED FIRST

Armed on the keeper today:

| field | keeper value |
|---|---|
| `dual_fuel_switching` | `True` |
| `dual_fuel_oil_reattribution` | `True` |
| **`dual_fuel_oil_daily_parity`** | **`False`** ← the parity price is ANNUAL, not daily |
| `neiso_winter_fuel_mustrun` | `True` |
| `neiso_winter_fuel_inventory` | `True` |
| `neiso_oil_burn_budget` | `True` |
| `neiso_gas_coldsnap_derate` | `True` |
| `neiso_winter_fuelsec_commit_frac` / `_min_stable_pct` / `_tmin_c` | `1.0` / `0.4` / `−7.0` |

**`dual_fuel_oil_daily_parity = False` is the first thing to look at**, because it means the oil side
of the comparison is a *year* constant (`resolve_annual_oil_price` → 18.00 in 2023/2024, 20.64 in
2025) while the gas side is now a properly daily series. A daily gas price tested against an annual
oil price is a grain mismatch, and it is exactly the null in §3.

**BLOCKER, and it is rule 28 `[R-MECH-MATRIX]` work that must happen before any lever is picked:**
six of the eight mechanisms above **have a row in `docs/codebase-site/data/mechanism-matrix.js` but
NO CELL in `docs/codebase-site/data/mechanism-matrix/NEISO.js`** —
`neiso_winter_fuel_mustrun`, `neiso_winter_fuel_inventory`, `neiso_oil_burn_budget`,
`dual_fuel_oil_daily_parity`, `dual_fuel_oil_reattribution`, `neiso_gas_coldsnap_derate`.
They are **armed on NEISO's own keeper and unrecorded in NEISO's own column.** Rule 28(a) says never
re-test an adjudicated cell — but these cells do not exist, so the lane cannot tell what has been
tried. **Reconstruct them from the calibration log before proposing anything**, and do not fill them
speculatively.

## 5. THE SHAPE OF THE SESSION

1. **Phase 0, zero LP.** Measure the 2022 oil gap against the obligation side: how much oil burn do
   ISO-NE's published winter programs and the CAMPD unit record actually account for, and in which
   hours? Compare to the 292 GWh the model produces. A gap that the obligation side cannot explain
   kills the hypothesis before a solve.
2. **Close the matrix gap** (§4) so the lane knows what is already adjudicated.
3. **Test the null first**: `dual_fuel_oil_daily_parity` and the oil-price grain. Cheap, and if it
   closes the gap the charter is over.
4. Only then consider an obligation mechanism — and it enters under rule 17 `[R-FLOOR-WINDOW]`
   (driver, window, forward story) and rule 19 `[R-ONE-MECH]` (enumerate what already floors oil
   before adding anything; four mechanisms already touch it).

## 6. WHAT THIS CHARTER DOES NOT AUTHORIZE

* **No fitted oil adder, haircut or offset.** Rule 13 `[R-MEASURED]`: the 1.7 TWh 2022 gap is a
  residual, and closing it with a tuned value is the forbidden move, not the fix.
* **No reverting the gas repair.** Rule 14 `[R-ACCURATE]` is explicit that a worse fit from accurate
  data is a discovered bug, not a reason to restore the inaccurate input. The contaminated file is
  not coming back.
* **No claim that the current keeper's oil is right.** It is ledgered as a known miss on the
  promoted keeper, reported at full magnitude.
