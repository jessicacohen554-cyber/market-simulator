# PRECOMMIT — PJM RUBRIC-RESIDUAL: the E&AS operand is zero because the forecast lane solves PJM **without PJM's reserve co-optimization**

**Lane:** PJM RUBRIC-RESIDUAL (composition half of the post-Q56 residual).
**Branch:** `claude/pjm-rubric-residual-composition-xhw1kj`, off `origin/main` `2b9606bd`.
**DATA PROFILE: pjm.**
**Pushed BEFORE any LP** (rule 29 `[R-SCREEN]`). Nothing is armed by this commit; the
only code it adds is a read-only phase-0 instrument.

Instrument: `docs/handoffs/pjmeas/phase0-eas-operand-2026-09-07.py` (+ `.json`). It reads
committed artifacts only — no solve, no config change.

---

## 0. What this lane found, in one paragraph

The named successor is real and it is **narrower and more specific than "the E&AS operand
is zero"**. The operand is zero because the T1-H / forecast lane solves PJM with
`energy_reserve_coopt=False`, `pjm_reserve_pergen=False`, `pjm_reserve_supply_cap=False`,
while **PJM's own calibrated backcast keeper solves with all three True**. Without the
reserve co-optimization the PJM screen price signal is a bare merit-order dual surface
whose **annual maximum is $52.7715/MWh in every zone that carries a decided unit** —
below the marginal cost of most of the gas-steam fleet ($51.2–58.2/MWh), so
`max(0, price − mc)` is identically zero for 8,760 hours and the fleet offers its full
gross bar into the D57 clearing. Measured: the 2022 decided cohort (103 units,
8,693.3 MW, the year that carries the ENTIRE gas_st over-exit) earns **$122,869 of E&AS
against a $304,263,925 going-forward cost — a ratio of 0.000404**, with
`reserve_uplift_usd` and `reserve_signal_mean_usd_mwh` exactly 0.0. The same 103 units,
on their own marginal costs, priced against a **committed PJM 2021 solve that carries the
co-optimization**, earn a MW-weighted **$40.66 per accredited MW-day** — four orders of
magnitude more. And the harness's own stated reason for withholding scarcity from PJM's
screens (`run_capacity_hindcast._build_config` docstring: *"for PJM the capacity-market
footing (no ORDC overlay; RPM net-CONE × UCAP already enters the screens via
`capacity_revenue_per_mw_yr`, so the master flag is a harmless no-op there)"*) was
**voided by D57**, which replaced that exogenous payment with an endogenous clearing whose
input IS the E&AS margin. The screen now has neither the scarcity rent in its prices nor
the capacity payment that stood in for it.

---

## 1. Phase 0 (zero LP) — four measurements

### A. The operand, as the T1-H screen saw it

From `results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm` (key
`fb16fda2ddb0a94a`), `pipeline_events` `event="decided"` rows:

| decision year | fuel | n | MW | GFC | energy margin | reserve uplift | E&AS/GFC | reserve signal | screen price mean / max | mc_mean range |
|---|---|---|---|---|---|---|---|---|---|---|
| **2022** | gas_st | 103 | 8,693.3 | $304,263,925 | **$122,869** | **$0** | **0.000404** | **0.0 $/MWh** | 36.9592 / **52.7715** | 51.16 – 58.24 |
| 2023 | gas_cc | 4 | 55.7 | $1,670,250 | **$0** | **$0** | **0.0** | 0.0 $/MWh | 36.9592 / **52.7715** | 52.79 – 56.23 |

2021, 2024 and 2025 carry **no decided rows at all**. The screen-price columns are
identical across 2022 and 2023 because 2022 is a **bridged** year, so both decisions read
the 2021 solve's `prior_results`.

**The mechanism is exactly visible here:** `screen_price_max` (52.7715) is *below*
`mc_mean` for most of the cohort, so the pro-forma `Σ_t max(0, price − mc, reserve) × cap`
is structurally zero, not small. For contrast, the committed PJM **backcast** 2021 solve
(`results/calibration/pjm169_tp2022_2021_f2arm/hourly/system_2021.parquet`, P1) prices the
same ISO at mean $40.58, p99 $91.67, **max $213.46** across its eight internal zones.

### B. The committed clearing, reproduced offline (identity gate)

The instrument re-clears each year's committed `offer_stack` against the shipped
`capacity_supply_curve` + `clear_capacity_supply_stack` at the committed
`price_takers_mw` / `requirement_mw`.

Tolerance is **the ledger's own serialization**, not a chosen slack: `offer_stack` writes
`round(o, 4)` $/MW-day and `round(a_mw, 3)` MW, so a reproduction *from* the ledger cannot
beat 1e-4 on price. Position is required EXACT.

| year | committed price | repro | Δprice | Δposition | uncleared MW by fuel |
|---|---|---|---|---|---|
| 2022 | 90.411052 | 90.411100 | 4.8e-05 | **0.0** | coal 1172.069→1172.068 · gas_st 9536.643→**9536.637** |
| 2023 | 86.517664 | 86.517700 | 3.6e-05 | **0.0** | coal ✓ · gas_st ✓ · gas_cc 61.382→69.386 |
| 2024 | 165.968925 | 165.968900 | 2.5e-05 | **0.0** | coal 5878.449→5878.448 |
| 2025 | 213.056369 | 213.055869 | 5.0e-04 | **0.0** | (none) |

**One exception, named rather than absorbed:** 2023 gas_cc, 8.004 MW. Diagnosed —
**41 gas_cc units are all serialized to the SAME offer 86.5177**, straddling the marginal
price; the serialization collapses their true distinct offers onto one value and the
`(offer, unit_id)` tie-break lands one 8.004 MW unit the other way. It is a serialization
tie at the marginal step, confined to 2023, and it does not touch the screen year.
**The screen year 2022 reproduces clean** (0.006 MW on gas_st, 0.001 MW on coal, position
exact), which is the gate this lane actually needs.

### C. The counterfactual, swept — 2022, uplift applied to the zero-margin classes only

Stated in **$/MW-day of accredited capacity**, the unit the offer is already in: an E&AS
increment of Δ lowers `max(0, GFC − EAS)/(A·365)` by exactly Δ, so nothing about `pmax` or
the bar is assumed. Uplift on `gas_ct` / `gas_st` / `oil`; `coal` and `gas_cc` offers are
**not touched**.

| Δ $/MW-day | Δ $/kW-yr | price | position | uncleared MW by fuel |
|---|---|---|---|---|
| 0 | 0.00 | 90.411 | 1.04260 | coal 1,172.1 · **gas_st 9,536.6** |
| 5 | 1.82 | 90.411 | 1.04260 | *unchanged* |
| 10 | 3.65 | 90.411 | 1.04260 | *unchanged* |
| 15 | 5.47 | 88.046 | 1.04320 | coal 2,076.2 · gas_st 8,725.3 |
| 20 | 7.30 | 83.046 | 1.04447 | coal 2,076.2 · gas_cc 2,140.9 · gas_st 6,195.3 |
| 25 | 9.12 | 78.108 | 1.04572 | **coal 6,574.6** · gas_cc 2,145.2 · gas_st 1,821.1 |
| 30 | 10.95 | 73.108 | 1.04699 | coal 6,639.4 · gas_cc 2,145.2 · gas_st 1,532.1 |
| **40** | **14.60** | **67.760** | **1.04835** | **coal 6,647.8 · gas_cc 3,605.2 · gas_st 0** |
| 50 / 75 / 100 | — | 67.760 | 1.04835 | *saturated, identical to Δ=40* |

Two structural readings, neither of which is a residual:

1. **There is a hard threshold at ≈$12.7/MW-day.** Below it the uncleared set is
   *exactly* unchanged — the gas_st plateau offers at $103.04–103.11/MW-day against a
   $90.41 clearing price, so a smaller uplift provably cannot reach the failing set. That
   threshold is the natural STOP for the screen (gate G3 below).
2. **The composition rotates monotonically**, out of gas_st and into coal, purely from the
   stack's own arithmetic — the uplift class and the displaced class are different classes.

### D. The supply side — the SAME 103 units on a reserve-co-optimized PJM price surface

Same units, same `mc_mean`, same `availability_mean`, same accredited MW; only the hourly
price/reserve series change, from the hindcast lane's co-opt-less duals to the committed
PJM 2021 backcast solve that carries the co-optimization. 103 of 103 units zone-mapped, 0
unmapped.

| | hindcast (control) | co-opt-armed backcast 2021 surface |
|---|---|---|
| total E&AS on the cohort | **$122,869** | **$119,972,990** |
| per accredited MW-day, MW-weighted mean | ~$0.004 | **$40.656** |
| per accredited MW-day, min / p25 / median / p75 / max | — | 25.567 / 33.416 / 38.953 / 51.766 / 64.845 |

`bc_joint == bc_energy` **exactly**: the reserve *price* term never binds above the energy
margin. So the E&AS does not come from PJM paying peakers a reserve price — it comes from
the co-optimized LP's **energy duals carrying the reserve opportunity cost**, which is
`FINDING-pjm138`'s title verbatim ("system energy IS reserve opportunity cost") and lifts
the price tail from $52.77 to $213.46 so a unit with mc $51–58 is in-merit in the top hours.

**Honest limits of D**, stated before it is used: this is a BACKCAST 2021 solve on the
backcast fleet, demand and offer curves, so it bounds the **order of magnitude**, not the
value the armed hindcast would produce. It is used only as an order-of-magnitude gate.

---

## 2. Rule 29(b) — G-DRIFT: form 4 is VALID, no control solve is earned

The registered `pjm-t1h` (`pjm-2021-2025-realized-t1h-d75rarm`, key `fb16fda2ddb0a94a`,
`git_sha` `10cda1fa`) **is** this lane's control. Audit at `origin/main` `2b9606bd`:

Three code-level instruments, all clean:

1. **The PJM solve-surface fingerprint is unmoved.** Recomputed at HEAD from the control's
   own recorded config: `0f749d17202c32d9`, **211 rows, `moved: {}`, `epochs: []`** —
   byte-identical to the bundle's `solve_surface.json`.
2. **The control's recorded config re-keys to `fb16fda2ddb0a94a` at HEAD**, with **zero**
   recorded fields absent from HEAD's dataclass.
3. **Every changed hunk classifies INERT for PJM**, with its reason:

| file | change | verdict |
|---|---|---|
| `config/iso_configs.py` | both hunks inside `_spp_config` (N↔S limit 48,711.8 → 3,400 MW + docstring) | INERT — another ISO's branch (verified: no non-SPP line changed) |
| `config/paths.py` | `SPP_HSL_DIR`, `SPP_WIND_SHAPE_DIR`, one `"SPP"` registry entry | INERT — another ISO's artifact |
| `config/scenarios.py` | two NEW fields `ercot_ep_gas_basis_monthly`, `cc_summer_derate_reconciled_basis`, both `bool = False` + cache-key registration | INERT — default-off flags absent from the control's recipe (key unmoved, item 2) |
| `data/fleet/arrays.py` | `_reconciled_summer_ratios` helper | INERT — hard-gated at `arrays.py:744` under `getattr(config, "cc_summer_derate_reconciled_basis", False)` |
| `data/fuel/__init__.py`, `data/fuel/basis/{__init__,ercot,meanzero}.py` | ERCOT EP gas basis + SPP hub path | INERT — another ISO + a default-off flag |
| `data/renewables.py` | SPP added to `_UNCURTAILED_FALLBACK_ISOS` and `_WIND_ZONE_SHAPE_ISOS` + an SPP curtailment reader | INERT — **PJM is in neither set before or after** |
| `data/transmission_expansion.py` | `TRANSMISSION_BASE_STATIC_VINTAGE["SPP"]` 2025→2026 | INERT — SPP key only |
| `pipeline/backcast_config.py` | `_SPP_OFFER_CURVE` under `if iso.upper() == "SPP"` | INERT — ISO-gated, **and a `mode="forecast"` hindcast never enters the backcast config path** |
| `scripts/run_calibration_full.py` | `--cc-summer-derate-reconciled-basis` passthrough | INERT — a different script; this lane runs `run_capacity_hindcast.py` |
| `scripts/lib/transmission_expansion/spp.py` | docstring only | INERT |
| `data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet` | CAISO artifact | INERT — another ISO |

**All hunks INERT ⇒ form 4 holds; the keeper's committed numbers are the control and no
control solve is spent.**

---

## 3. Rule 28 — the matrix, checked before proposing

| PJM cell | verdict | what it means here |
|---|---|---|
| `ordc_scarcity_overlay` | **G** | **NOT re-opened.** Its own citation is the reason: *"the in-LP co-opt already owns the phenomenon with PJM's published two-step ORDC curve loaded, so an adder would still be a rule-19 stack."* This lane arms **the co-opt the G-refusal defers to**, never the overlay. `scarcity_price_overlay` stays False. |
| `energy_reserve_coopt` | **K** (fc omitted ⇒ K) | PJM's keeper mechanism, in both declared lanes — yet the T1-H run carries it **False**. That gap is the object. |
| `reserve_pergen` | **K** | same |
| `dynamic_reserve_requirements` | **K** | same family, not touched by this arm |
| `capacity_screen_scarcity_restoration` | **U** | **Not the lever, and not testable here:** its own field docstring requires `iso == "ERCOT"` ("the committed-capability tables are ERCOT-identified; rule 25 — other ISOs enter the matrix as U"). |
| `economic_retirement_screen` | **R** | not re-tested |
| `retirement_sector_gate`, `capacity_market_supply_clearing`, `capacity_adequacy_requirement_published`, `pjm_vre_accreditation_vintage` | K (fc) | Q55/Q56 **not re-opened** |

No cell adjudicated R/I/G is re-tested. The mechanism this lane proposes is already **K**
for PJM in both declared lanes; what is new is measuring it **in the lane that lost it**.

---

## 4. THE ARM, declared before the solve

Three fields, PJM's own backcast-keeper reserve footing, brought into the hindcast harness:

```
energy_reserve_coopt   = True
pjm_reserve_pergen     = True
pjm_reserve_supply_cap = True
```

All three are rule-13 clean by their own docstrings — no measured series, no fitted
parameter: the co-opt installs PJM's **published two-step ORDC** as reserve balance rows;
`pjm_reserve_supply_cap` is "a physical deliverability definition (ramp × cap), never
fitted to the LMP residual" (`RAMP10_FRAC_BY_GROUP × pmax`, availability-scaled);
`pjm_reserve_pergen` is a supply layout. Reachability in forecast mode is structural, not
assumed: `runner.py:3527` calls `apply_reserve_coopt` unconditionally inside the shared
year loop with `sim_year=year`, and the wrapper's only gate is
`if not config.energy_reserve_coopt: return None` — there is no `mode == "backcast"` test
on the path.

**Cache keys, pre-declared and to be matched before any arm output is read:**

| leg | key |
|---|---|
| control (registered `pjm-t1h`) | `fb16fda2ddb0a94a` |
| **ARM (all three)** | **`cf9b7dc1ca285c35`** |
| solo `energy_reserve_coopt` | `d821af43aebd8f74` |
| solo `pjm_reserve_pergen` | `274dd5cf1f354e06` |
| solo `pjm_reserve_supply_cap` | `a1b09c86130e0ba3` |

---

## 5. THE SCREEN YEAR — **2022** — named here, before the screen runs

**Chosen on the mechanism's own measured footprint (rule 29(1)), never on the residual.**
The zero-E&AS operand's entire decided cohort is 2022: **103 units / 8,693.3 MW**, against
2023's 4 units / 55.7 MW and **zero decided rows in 2021, 2024 and 2025**; and 2022 carries
**9,536.6 MW of the window's uncleared gas_st**. No year-by-year band error was consulted
in making this choice.

2022 is a **bridged** year decided off the **2021** solve, so the screen is
`--start-year 2021 --end-year 2022`: **one solved year (2021)**, which is the minimum that
can exercise the mechanism at its footprint. Rule 16 `[R-ALLYEARS]` is untouched — the
screen bundle is a throwaway diagnostic probe, **never registered, never a keeper, never
quoted as a keeper number**, and deleted before merge per rule 29(c); every number this
lane will ever cite from it lands in the FINDING.

### The gates — STRUCTURAL, STOP-only, and none of them reads a band

**G1 — REACHABILITY.** The armed 2021 solve installs a non-degenerate PJM reserve
co-optimization: reserve balance rows present, and a reserve price non-zero in ≥1 hour.
**STOP if the armed 2021 price surface is identical to the control's** — the arm is then
structurally inert in the forecast lane and dies here.

**G2 — PRICE-SURFACE DIRECTION AND ORDER.** Pre-registered direction **UP**: a reserve
opportunity cost added to the energy dual can raise or hold it, never lower it. Control
`screen_price_max` = **52.7715 $/MWh**. **STOP if the armed per-zone max is below
$60/MWh** — under 15 % of the phase-0-measured move, i.e. the mechanism did not move the
object it claims to move.

**G3 — THE OPERAND MOVES BY THE ORDER PHASE 0 PREDICTS.** The 2022 decided cohort's
E&AS per accredited MW-day, read from the armed ledger. Control ≈ **$0.004**. Predicted
band from D: **$25–65**, MW-weighted ≈ **$40.7**. **STOP below $12.7/MW-day** — phase-0 C's
*measured* threshold under which the 2022 uncleared set is exactly unchanged, so the arm
provably cannot reach the failing set. This compares E&AS supplied against E&AS the stack
needs; it is not a band.

**G4 — FOOTPRINT CONFINEMENT.** Every unit whose `capacity_offer_usd_per_mw_day` moves has
a non-zero E&AS change, and no unit's offer moves without one. Asserted from the armed
ledger.

**G5 — I2 HOLDS.** D57's invariant — the screen's failing set IS the auction's uncleared
set — holds in the armed 2022 screen, as it does in all eight D57 screens and in the
control.

**G6 — NO NON-TARGET LOAD-BEARING FLIP.** No forecast invariant PASSing in the control may
FAIL in the arm other than through the retirement bands the mechanism targets.

### Reported at full magnitude, and GATING IN NEITHER DIRECTION

`retire.total_gw`, `unit_recall_gt300`, `false_retire`, coal exits, gas_st exits. Phase-0 C
already says which way they would move; making that the screen's pass condition would be
precisely the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids, done one year at a
time. They are reported, never gating.

### The falsifiable point prediction, and a COST pre-registered before it appears

At phase-0 D's supplied level (Δ ≈ $40.7/MW-day) the phase-0 C sweep's Δ=40 row predicts
the armed 2022 clearing at **price $67.76/MW-day, position 1.04835, uncleared: gas_st 0 ·
coal 6,647.8 MW · gas_cc 3,605.2 MW**.

**The cost, stated at the gate:** from Δ≈$20 the sweep pulls **gas_cc** into the uncleared
set (2,140.9 MW, rising to 3,605.2 MW at Δ≥40) even though the uplift never touches a
gas_cc offer — it happens because the clearing price *falls* (90.41 → 67.76) as displaced
cheaper supply enters. PJM's actual window gas_cc exits are ~0.075 GW (announced only), so
the arm is predicted to open a **new false-exit channel in gas_cc**. Per rule 14
`[R-ACCURATE]`, if it materialises that is a discovered bug to root-cause, **not** a reason
to revert the arm.

---

## 6. Pre-existing RED on `main`, verified rather than assumed

Verified at `origin/main` `2b9606bd`; `git diff HEAD origin/main -- src/market_sim scripts
tests` is **empty**, so this tree is the clean-main baseline for all four.

1. **FR-22 parity — CONFIRMED.** `scripts/check_forecast_parity.py`: 3 FAILs, exactly
   `miso_seam_neighbour_{anchored_ladder,hourly_ladder,hourly_spp}`. Not this lane's.
2. **Rule-22 S1 status staleness — CONFIRMED, with a correction to the brief.**
   `scripts/audit_keepers.py` fails S1 on `status/ERCOT.js` **and `status/PJM.js`**.
   `status/shared.js` `iso_order` **already carries SPP** — that half is repaired on main.
   PJM.js is in this lane's ISO but the staleness is pre-existing; not repaired here.
3. **`test_cache_solve_surface` — CONFIRMED.** 2 failures,
   `{'NUCLEAR_MONTHLY_CF_BY_YEAR': '00a8e8726fd0edd6'} != {}`. Not this lane's.
4. **`test_caiso_st_gas_peak_measured` — CONFIRMED.** `1.154 != 1.166`. Not this lane's.

Two incidental observations, recorded and **not repaired**: `run_capacity_hindcast.py
--help` raises `ValueError: unsupported format character ','` from an unescaped `%` in a
help string; and `pipeline/year.py::run_year_solve` has no caller in `src/market_sim/`
(the live call site is `runner.py:3527`).

## 7. The owed cherry-pick — ALREADY LANDED, nothing to do

`FINDING-capx-d78arm-2026-09-06.md` §9.1 **is** on `main`: commit `4ad49fe3`
("capx D78-ARM: record the CI test reading and baseline the three failures the local
selection did not cover") is an ancestor of `origin/main`, and the section is present in
`origin/main`'s blob. No cherry-pick is owed.

## 8. Not re-opened

Q55, Q56, the sector gate, `ordc_scarcity_overlay`'s G, `economic_retirement_screen`'s R.
