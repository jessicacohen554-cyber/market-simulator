# PRECOMMIT — pjm-170: the PJM bituminous coal-sigmoid `ceil` is a dear-gas markup with no source

**Session:** pjm-170 · **Date:** 2026-09-07
**Branch:** `claude/pjm-coal-sigmoid-ceiling-pz4ckl`
**Keeper:** `2026-08-15-pjm-162-inputclock` (`pjm_debugb_inputclock_A`) — **UNCHANGED, not promoted**
**Control (G-CTRL form 4, committed, no control LP):** `results/calibration/pjm169_tp2022_2021_f2arm`, year 2022, F2-armed, git `f36cee6e`
**Predecessor evidence:** `docs/handoffs/PRECOMMIT-pjm169-f4-anchor-vintage-2026-09-06.md` §7.2 / §9.2–§9.3

Written **before any build and before any LP is solved**, per rule 29 `[R-SCREEN]`. Every
threshold, the screen-year selection rule, and every gate below are fixed here and are **not
revisable after a result is seen**.

---

## 1. The defect

PJM bituminous resolves `COAL_SIGMOID_DEFAULTS[("PJM","bituminous")]` overlaid by the keeper's
explicit field, giving the live effective curve

```
passthrough(gas) = floor + (ceil - floor) / (1 + exp(-gas_slope * (gas - gas_mid)))
                 = 0.65  + (1.32  - 0.65) / (1 + exp(-2.5 * (gas - 3.40)))
```

`floor = 0.65` is the keeper's explicit `coal_bit_passthrough_floor`; `ceil = 1.32`,
`gas_mid = 3.40`, `gas_slope = 2.5` come from the table.

`ceil = 1.32` means: **at dear gas a PJM bituminous tranche bids 32 % ABOVE its own full
delivered fuel cost.** pjm-169's zero-LP census measured where the curve actually sits:

| year | PJM bit passthrough mean | **hours ON the `ceil` asymptote** |
|---|---|---|
| 2021 | 1.1205 | 16.7 % |
| **2022** | **1.3188** | **91.5 %** |
| 2023 | 0.9166 | **0.0 %** |
| 2024 | 0.8140 | **0.0 %** |
| 2025 | 1.0565 | 8.5 % |

So **92 % of 2022's bituminous bid is priced by an asymptote the training window reaches in
0.0 % of hours in two of its three years**, and the table's own header says why that is a
defect: each asymptote "is pinned by a single gas regime — floor by the cheapest observed year,
ceil by the dearest", and the PJM entry is documented as bracketing the breakeven "across PJM
2023-2025". The parameter is identified on a window that never visits it.

**Its inline provenance is explicitly a residual.** `scenarios.py` records the value's history in
place: "Ceiling 1.25 -> 1.32 (PJM run 16): trims the dear-gas-2025 BIT over-run (+6.3 -> +3.3
TWh)". That is a number selected because a residual moved — which is exactly what rule 23
`[R-FROZEN-DERIVE]` freezes and rule 21 `[R-DOF]` calls an open root-cause issue rather than a
parameter.

## 2. Rule 23 `[R-FROZEN-DERIVE]` — the hard question, answered on SOURCE DATA

Rule 23 admits a re-derivation **only** when the parameter's *source data* updates, and the
commit must cite the data change. It is answered here **without reading any 2022 residual**, and
the answer predates this session.

### 2.1 The source-data trigger

The **#1803 intake** (`data/raw/coal-prices/`,
`docs/handoffs/coal-price-data-intake-2026-07.md`) landed the EIA **Annual Coal Report** region
f.o.b.-mine price by rank and the **BLS coal-mining PPI** — the series a real re-derivation of
this mechanism needs. `scripts/data/derive_coal_sigmoid.py` exists **for that trigger and states
so in its own docstring**: "A source-data update is the ONLY admissible re-derivation trigger, so
this re-derive is keyed to that intake, not to any moved residual (CLAUDE.md rules 10/11/23)."

That script was run on 2026-07-09 and its **MISO** rows were transcribed into the live literals.
Its PJM rows were computed at the same time and **deliberately left untranscribed** — the script
says so verbatim: "other ISOs' rows are delivered but their live literals are left unchanged
(their re-solves are separate owner lanes)." **This session is PJM's lane.** The re-derivation
was authorized by the intake and deferred for a solve, not refused.

### 2.2 The construction that fixes `ceil`, and why it is 1.0 for this basin

The derive script's `ceil` is not fitted to anything. It is a **cost-structure conclusion**:

> `ceil` — 1.0 for every supply: coal's delivered cost does not follow the gas index
> (mine-mouth/rail commodity), so at dear gas the bid is its full measured delivered cost, never
> a markup past it (rule-10 cost-tracking; retires the inconsistent `ceil>1.0` opportunity-cost
> story the D-8 audit flagged).

`COAL_SIGMOID_DEFAULTS`' own header states the same rule and names the inconsistency as an open
finding: cost-tracking basins "must carry ceil <= 1.0 — the sigmoid may only ever DISCOUNT the
bid toward sunk cost, never mark it up past full cost, since there is no gas-indexed contract
escalator to justify a markup"; the `ceil > 1.0` opportunity-cost story belongs to "ERCOT's
PRB-by-rail entries", and "the two stories being applied inconsistently by ISO, with no single
documented rule for which basin gets which, is itself part of the D-8 weak-identification
finding."

**Which story does PJM bituminous belong to? The measured supply chain decides, and it is
cost-tracking.** Reproduced at HEAD this session, `derive_coal_sigmoid.py --iso PJM`:

| iso | supply | n_priced | fob $/MMBtu | deliv $/MMBtu | hr_coal | regions |
|---|---|---|---|---|---|---|
| PJM | bituminous | **29 plants** | 3.661 | 4.307 | 11.02 | ESC, IN, KY, MD, OH, PA, VA, WV |

29 plants drawing **Appalachian / Interior-basin f.o.b. tonnage moved on short-haul rail**
(`COAL_DELIVERY_COMMODITY_SHARE["bituminous"] = 0.85`). There is no gas-indexed escalator
anywhere in that chain. **A bid above full delivered cost has no source in it.**

### 2.3 THE TWO TABLES, RECONCILED (handoff item 4)

The solve does **not** read `data/raw/_processed-legacy/coal_sigmoid_params.csv`. It reads
`COAL_SIGMOID_DEFAULTS[(iso, supply)]` overlaid entry-by-entry with explicit `ScenarioConfig`
fields (`fuel/trajectories.py::coal_sigmoid_params`). The three tables therefore read:

| parameter | table literal | keeper explicit field | **live effective** | derived CSV (source-grounded) |
|---|---|---|---|---|
| `floor` | 0.76 | **0.65** | **0.65** | 0.500 |
| `ceil` | **1.32** | — (None) | **1.32** | **1.000** |
| `gas_mid` | 3.40 | — | 3.40 | 7.080 |
| `gas_slope` | 2.5 | — | 2.5 | 1.000 |

**Two of the four derived values are at their guard clips, and this document says so before
proposing anything.** `COAL_SIGMOID_FLOOR_MIN = 0.50` and `COAL_SIGMOID_SLOPE_MIN = 1.0`
(`fuel_trajectories.py`), and the derived PJM row returns exactly those. The unclipped floor is
`gas_min / gas_mid = 2.86 / 7.08 = 0.404`, below the bound; the unclipped slope for an 8-region
group is below 1.0. So the derived PJM `floor` and `gas_slope` are **bounds, not measurements**,
and `gas_mid = 7.08` is a level whose companions are saturated.

**Consequence for scope — and it NARROWS the card rather than widening it.** Transcribing the
whole derived row would move three parameters, two of which are constants rather than
measurements, and would put in-window passthrough at ≈0.51 in every training year. **That is not
this card.** `ceil` is the one parameter of the four whose derived value is **neither a clip nor
a level estimate** — it is a structural conclusion about the contract form, identical in 2022 and
in 2023, and it is the parameter the measured defect names. **The arm changes `ceil` and nothing
else.** The remaining three stay at their incumbent (residual-tuned) values; that incompleteness
is stated at the gate, is not repaired here, and is not a new fit.

### 2.4 What is NOT the justification

No 2022 residual. No 2021 residual. No price or volume miss of any kind appears in §2, and no
gate below reads one (see §5's explicit exclusion of the target criterion). The statement is:
*a cost-tracking supply chain has no source for a bid above its own full delivered cost.* It
would read identically had 2022 never been solved.

## 3. The change (ONE mechanism, rule 19 `[R-ONE-MECH]`)

**One declared delta, no code change:**

```
coal_bit_passthrough_ceil : None (-> table 1.32)   ==>   1.00
```

applied through the **registered** `ScenarioConfig` field (rule 24 `[R-REGISTRY]`), the same
channel the keeper already uses for `coal_bit_passthrough_floor = 0.65`, so the value is recorded
in the arm's `run_config.json` as the number the LP solved with. `COAL_SIGMOID_DEFAULTS` is
**not** edited by the screen: a table edit would move the default for every consumer and every
ISO before the mechanism has been screened at all. Siting a promotion (config field vs.
transcribing the derived literal) is deferred and is not screened here.

### 3.1 Rule 19 — what else already prices this phenomenon (D-2 style enumeration)

Every other mechanism that could cap or mark a PJM bituminous bid, checked against the control's
recorded `scenario_config`:

| mechanism | state in the keeper | overlap |
|---|---|---|
| `coal_bit_committed_takeorpay` | `False` | none |
| `coal_committed_takeorpay_all` / `_regulated` / `_sunk_fixed` | `False` | none |
| `coal_takeorpay_from_data` | `False` | none |
| `coal_econ_srmc_bound` (clamps marginal coal to `>= 1.0`) | `False` | would *floor*, never *cap* |
| `coal_peak_offer_margin` / `coal_offer_net_revenue_margin` | `False` | none |
| `offer_curve_by_group["COAL_BIT"]` band multipliers | armed (0.548 / 0.6556 / 1.2664 / 1.044) | multiplies the **heat rate**, not the fuel passthrough — a different operand, and the authorized price-tuning channel of the rule 1 carve-out, untouched here |
| `coal_bit_passthrough_sigmoid` | `True` | **this mechanism** |

**No stacking.** The sigmoid `ceil` is the only fuel-side markup on a PJM bituminous tranche.

### 3.2 Where the mechanism can reach (the direct footprint, by construction)

`fuel/trajectories.py::coal_passthrough_by_supply` routes per supply tag, and
`fleet/legacy_bins.py::campd_tranche_fuel_frac` applies the result **only to coal tranches above
must-run** that carry the tag. So the mechanism's direct reach is exactly:

> PJM coal generators with `coal_supply == "bituminous"`, tranches `_committed` / `_econ*` /
> `_peak`. **Excluded by construction:** `_mustrun` (passes 0.0 — fuel sunk) and `_sync` (passes
> 1.0 — full SRMC), and every non-bituminous supply (`prb`, `subbituminous`, `lignite`, `waste`),
> whose own curves are untouched.

Gate **S4a** turns this into an exact, pre-solve, zero-LP measurement.

## 4. Screen year — the selection RULE, fixed before the census is read

Rule 29 `[R-SCREEN]` clause (1): the screen year is the year the mechanism's **own measured
footprint is largest**, never the year with the biggest residual.

**The footprint statistic is declared here, before it is computed:** the mean over 8,760 hours of
`|passthrough_arm(t) - passthrough_control(t)|` — i.e. `(1.32 - 1.00) x sigma(gas(t))` — evaluated
on the keeper's own resolved `_gas_series`, which is the series the offer path prices against.
Reported alongside it, and **not** a selector: the on-`ceil` occupancy of the table above.

**The declared screen year is 2022**, on pjm-169's already-measured occupancy (91.5 % on the
asymptote against 0.0 / 0.0 / 8.5 % in-window). **Pre-registered tie-break: if the census in §7
names a different year on the declared statistic, the census wins and the screen moves.** Only
one year is solved.

**A control solve is NOT spent** (rule 29 clause (b)): the control is the committed
`pjm169_tp2022_2021_f2arm` 2022, differenced as G-CTRL **form 4**, valid on the G-DRIFT code
audit in §8.

## 5. The gates — STOP gates only, fixed here

**The target of this card is C1 fuel-mix in 2022. C1 IS EXCLUDED FROM EVERY GATE BELOW.** A
screen that read "did C1 improve" would be the fitted-mechanism selection rule 1 `[R-STRUCT]`
forbids, done one year at a time. No gate reads any residual, in either direction.

**The screen may KILL the arm; it may never PROMOTE one**, it contributes to no determination,
and its bundle is never registered (rule 29 clause (2)).

| # | gate | pass condition |
|---|---|---|
| **S1** | scoping identity | the arm's `run_config.json` records `coal_bit_passthrough_ceil = 1.0`; `floor` / `gas_mid` / `gas_slope` unchanged at 0.65 / 3.40 / 2.5; the resolved passthrough arrays for `prb`, `subbituminous`, `lignite`, `waste` are **byte-identical** to the control's; `COAL_SIGMOID_DEFAULTS` is untouched on disk (rule 25 `[R-ISO-SCOPE]`: no other ISO can move) |
| **S2** | the identity the mechanism asserts | over all 8,760 hours of the screen year, `max(passthrough_arm) <= 1.0 + 1e-9` (a cost-tracking tranche never bids above full delivered fuel cost) **and** `passthrough_arm(t) <= passthrough_control(t)` for every `t` with equality only as `sigma -> 0` (the cheap-gas floor is untouched at 0.65) |
| **S3** | plumbing: the flag reaches the LP as computed | the arm's assembled offer array on the directly-priced tranches differs from the control's by the §7 pre-registered mean `ΔMC`, within **±2 %** of that value, and the sign is **negative** (coal marked DOWN) |
| **S4** | **displacement-aware footprint** (three clauses, §5.1) | S4a **and** S4b **and** S4c |
| **S5** | no non-target load-bearing or protective flip | of the control's 2022 PASSes — **C2, C3a, C4, C6, C8** — none reads FAIL in the arm. (C1 is the target, excluded. C3b is already FAIL and cannot flip. C3c is a ledgered caveat on a holdout year, rubric v3.6.) |

### 5.1 S4 — the displacement-aware footprint gate (handoff item 2)

pjm-169's S4 read "every non-gas class < 1.0 % annual energy" and its own §9.2 records the
defect: **raising a gas offer by $10.57/MWh MUST re-allocate dispatch through the merit order,
and in PJM the next unit up is coal — so the gate could not separate the confound it targeted
from the mechanism working correctly, and it killed an arm for behaving correctly.**

The repair is to bound **what the mechanism directly prices** and to **stop reading
re-allocation as a defect at all**. Three clauses; **no clause of S4 treats a non-target class's
energy change as a failure, of any size.**

- **S4a — DIRECT PRICING CONFINEMENT (pre-solve, zero LP, exact).** Build the assembled P0 offer
  array `mc_base` for the screen year twice through `run_calibration.run_year(fleet_only=True)` —
  control recipe and arm recipe — and diff them cell by cell.
  1. **Every** changed `(generator, hour)` cell belongs to the §3.2 set: a PJM coal generator
     tagged `bituminous`, tranche `_committed` / `_econ*` / `_peak`.
  2. **Zero** cells change outside that set. Tolerance is exactly zero — this is an offer array,
     not a solve.
  3. Each changed cell equals `Δpassthrough(t) x fuel_price(g,t) x heat_rate(g)` to within
     `1e-6` relative.
  **FAIL if any cell outside the set moves.** This is the bound on the direct effect, and it is
  the clause that would actually have caught the confound pjm-169's S4 was written for.
- **S4b — DIRECT-EFFECT MAGNITUDE BOUND (post-solve).** The target class's energy gain must be
  carriable by the tranches the mechanism actually repriced:
  `ΔE(COAL_BIT) <= headroom`, where `headroom = Σ over directly-priced tranches of
  (pmax x availability, summed over 8,760 h) − their control energy`. A gain above the physical
  headroom of the repriced rows would be a plumbing error, not a market response. **No other
  class appears in this clause.**
- **S4c — RE-ALLOCATION IS CONSERVATIVE, NOT CREATIVE (post-solve).** `|Δ(total served energy)| /
  total < 0.5 %`, and no class carrying **zero** energy in the control acquires **> 1 %** of ISO
  load in the arm. **Displacement of any magnitude into any class the market already has is
  explicitly ALLOWED and is never a failure.**

### 5.2 Reported, NEVER gated — declared in advance so it cannot become a pass condition

Coal marked DOWN is expected to raise coal dispatch and displace gas CC, and the control's live
C1 2022 failure is a `CC_REGULAR` **over**-run of +22.02 TWh — so the arm points the helpful way.
**That is not a pass condition, no gate reads it, and saying so here in advance is what stops it
becoming one** (rule 1 `[R-STRUCT]`). C1's 2022 magnitudes, C3a, C3b NRMSE and C5a are recorded
in §9.1 at full magnitude and contribute to no verdict.

**And the converse binds equally:** if C1 degrades, the arm is **not** killed for it. An arm
killed on structure is not revived by a target improving; an arm that clears every structural
gate is not killed by a target worsening.

## 6. KILL RULE

**Any of S1, S2, S3, S4a, S4b, S4c, S5 failing ⇒ the arm is DEAD.** The remaining years are
**never** spent, nothing is promoted, the keeper is untouched, and the session's result is the
kill. Only if **every** gate passes does the full span (`--year 2023 2024 2025`, one invocation,
one bundle, rule 16 `[R-ALLYEARS]`) become the next step — and the screen year is re-solved
inside that bundle.

**Rule 29 clause (c):** the screen bundle (and any control bundle a LIVE hunk would have earned)
is **deleted from `results/calibration/` before this PR merges**. This document carries every
number the session will ever cite from it. Git history is the record.

## 7. Phase-0 census and the pre-solve prediction

Run before the screen and before any LP, per §4 and rule 29 clause (0). Artifacts:
`results/calibration/_pjm170_census.json` and `_pjm170_offer_delta.json`; probe
`scripts/probes/_pjm170_bitceil_census.py`. Measured on the keeper's own resolved config
through `run_calibration.run_year(fleet_only=True)`.

### 7.1 Part A — the footprint census, and the screen year it selects

**The declared statistic is `mean |passthrough_arm(t) - passthrough_control(t)|`** (§4, fixed
before measurement). `×in-win` normalises to the largest TRAINING-window year.

| year | gas mean | `pt` control | `pt` arm | **FOOTPRINT** | ×in-win | on-`ceil` (1e-3) | on-`ceil` (pjm-169 conv.) |
|---|---|---|---|---|---|---|---|
| 2021 | 4.109 | 1.1205 | 0.8958 | 0.2247 | 1.16 | 0.0 % | 16.7 % |
| **2022** | **7.121** | **1.3188** | **0.9994** | **0.3194** | **1.65** | **74.8 %** | **91.5 %** |
| 2023 | 3.255 | 0.9166 | 0.7892 | 0.1273 | 0.66 | 0.0 % | 0.0 % |
| 2024 | 2.856 | 0.8140 | 0.7357 | 0.0783 | 0.40 | 0.0 % | 0.0 % |
| 2025 | 3.934 | 1.0565 | 0.8624 | 0.1942 | 1.00 | 8.5 % | 8.5 % |

**THE SCREEN YEAR IS 2022, on the statistic declared before it was computed** — footprint
0.3194, **1.65×** the largest in-window year. The §4 pre-registered tie-break did not need to
fire.

**A CORRECTION TO THE OCCUPANCY COLUMN, recorded rather than quietly adopted.** pjm-169 §7.2
reported 2022 at **91.5 %** on-`ceil` and 2021 at 16.7 %; this probe's own convention
(`pt >= ceil - 1e-3`) measures **74.8 %** and 0.0 %. The gap is **entirely the threshold
convention and not the curve**: pjm-169 used `pt >= ceil - 0.01 x (ceil - floor)`, i.e. within
1 % of the curve's RANGE (threshold 1.3133), while this probe used a stricter absolute
tolerance (threshold 1.3190). The curve itself reproduces **exactly** — the control mean
passthrough matches pjm-169 to four decimals in all five years (1.1205 / 1.3188 / 0.9166 /
0.8140 / 1.0565). Both columns are reported above; **neither is the selector** (§4), and both
say the same thing qualitatively: 2022 sits on the asymptote for most of the year and two of
the three training years never reach it at all.

**A structural confirmation, reported not gated:** under the arm, 2022's mean passthrough is
**0.9994** — the dear-gas year lands at essentially exactly full delivered fuel cost, which is
precisely what §2.2's cost-tracking construction says the dear-gas asymptote should be. The arm
does not introduce a discount; it removes a markup.

### 7.2 Gates S1 and S2, satisfied pre-solve

| gate | measured | verdict |
|---|---|---|
| **S1** other coal supplies untouched | `prb`, `subbituminous`, `lignite`, `waste` passthrough arrays **byte-identical** (`np.array_equal`) control vs arm, in all five years | **PASS** (pre-solve leg) |
| **S2** `max(passthrough_arm) <= 1.0 + 1e-9` | True in all five years | **PASS** |
| **S2** `passthrough_arm(t) <= passthrough_control(t)` ∀ t | True in all five years | **PASS** |

S1's remaining leg (the arm's `run_config.json` records `ceil = 1.0` with `floor`/`gas_mid`/
`gas_slope` unmoved) is read off the solved bundle in §9.

### 7.3 Part B — S4a, and the S3 prediction fixed before the solve

Offer-array (`mc_base`) diff for 2022, control vs arm, both assembled through the same
`fleet_only` path the solve uses:

| quantity | measured |
|---|---|
| generator rows in the PJM LP | 3,405 |
| rows the mechanism may reach by construction (§3.2) | **243** (25,504.28 MW) |
| rows that changed | **243** |
| **rows that changed OUTSIDE the set** | **0** |
| cells that changed | **2,128,680** = 243 × 8,760 exactly |
| **cells that changed OUTSIDE the set** | **0** |

> **S4a PASSES exactly, at zero tolerance, before any LP.** The mechanism reprices the 243
> bituminous above-must-run tranches and *nothing else* — not a single one of the other 3,162
> rows moves by any amount. This is the measurement pjm-169's S4 was reaching for and could not
> express: it bounds the DIRECT effect exactly while leaving merit-order re-allocation entirely
> free.

**THE S3 PREDICTION, FIXED HERE BEFORE THE SOLVE:**

> **mean ΔMC over the directly-priced tranche-hours = −$9.2267/MWh** (min −$43.9126, max
> −$2.1066). **S3 passes iff the solved arm's mean ΔMC on those tranches is NEGATIVE and within
> ±2 % of −9.2267, i.e. in [−9.4113, −9.0422] $/MWh.**

Independent arithmetic cross-check: Δpassthrough ≈ −0.3194 (§7.1) × PJM bituminous delivered
fuel × heat rate ≈ $28.9/MWh ⇒ ≈ −$9.2/MWh. The sign is the operative part — the arm **removes**
a dear-gas markup rather than adding a discount.

## 8. G-DRIFT audit — the keeper's committed bundle IS the control (rule 29 clause (b))

`git diff f36cee6e HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
= **55 files, +3,639 / −59**. Every hunk on the backcast path classified below; **no control
solve is spent.**

**Independent corroboration, computed first:** PJM's **solve-surface fingerprint at HEAD is
`0f749d17202c32d9`, 211 rows, `moved: {}` — byte-identical to the fingerprint the control bundle
recorded.** The capx-D79 surface covers `constants.py`, `capacity_market.py`,
`fuel_trajectories.py`, `ercot_envelopes.py`, `plant_taxonomy.py`, `entry_config.py` and
`pipeline/offer_curve_base/generic.py` projected onto PJM, so those seven modules are discharged
at the registry-value level by measurement rather than by reading.

| changed path(s) | classification | reason |
|---|---|---|
| `config/constants.py`, `config/capacity_market.py`, `config/fuel_trajectories.py` | **INERT** | in the D79 solve surface; PJM projection byte-identical (fingerprint above). Additions are SPP rows + `ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR` |
| `config/solve_surface.py`, `solve_surface_declared.py` | **INERT** | SPP appended LAST to `SURFACE_ISOS`; one new ERCOT declaration. PJM rows unmoved (measured) |
| `config/iso_configs.py` | **INERT** | `_spp_config` (new ISO) + `"retirement_sector_gate": True` in `_pjm_config` `default_scenario_overrides` — the **forecast** front end. `run_calibration*.py` never calls `apply_iso_scenario_defaults` (pjm-169 §2.1, verified three ways); a backcast never reads it |
| `config/scenarios.py` | **INERT** | three new fields, all `bool = False` and absent from the PJM recipe: `miso_seam_neighbour_hourly_spp`, `ercot_ep_gas_basis_monthly`, `cc_summer_derate_reconciled_basis` |
| `config/paths.py` | **INERT** | two new SPP directory constants |
| `pipeline/backcast_config.py` | **INERT** | both hunks ISO-gated: `_SPP_OFFER_CURVE` under `if iso.upper() == "SPP"`, and `_ordc_order` under `if iso.upper() == "ERCOT"` (empty dict ⇒ no-op for PJM) |
| `model/reserves/spec.py` | **INERT** | the one changed call sits inside `_ercot_multiproduct_design` |
| `results/scarcity.py` | **INERT** | new `ercot_as_measured_requirement_mw` + its ERCOT callers |
| `results/cache.py` | **INERT** | docstring/epoch ledger for the D78 PJM **forecast** arm; its own record states a PJM plain backcast keeps key `3a566deac3a85682` unmoved |
| `data/fleet/arrays.py` | **INERT** | new `_reconciled_summer_ratios`, gated on `getattr(config, "cc_summer_derate_reconciled_basis", False)` — default-off, absent from the PJM recipe |
| `data/campd.py`, `data/fleet/models.py`, `data/zone_assignment.py`, `data/renewables.py`, `data/eia930/{__init__,frames,demand}.py`, `data/fuel/basis/meanzero.py`, `data/transmission_expansion.py`, `model/interchange/{spec,registry}.py`, `scripts/lib/*` | **INERT** | SPP registration only — new ISO keys, a new `"SPP"` registry entry, and new SPP-keyed loaders. No shared code path altered |
| `data/eia930/envelopes.py` | **INERT** | new `measured_miso_spp_hub_prices`; MISO's SPP seam only |
| `model/interchange/miso.py` | **INERT** | `neighbour_hourly_spp` sub-gate; MISO only |
| `data/fuel/basis/{__init__,ercot}.py`, `data/fuel/__init__.py` | **INERT** | new `ercot_electric_power_gas_basis_monthly` + re-exports; ERCOT only |
| `data/neighbor_price.py` | **INERT** | a new import-time uniqueness assertion over `_HR_GAS_ELASTIC`; no value changes |
| `scripts/run_calibration.py` | **INERT** | `_renewable_bound_is_delivered_pinned` is read only inside the `ercot_gtc_limits_measured` / `ercot_wtx_curtailment_driver` branches; plus the MISO/SPP sub-gate validation |
| `scripts/run_calibration_full.py` | **INERT** | three new optional kwargs, all defaulting to `None` ⇒ no-op when unset |
| `data/raw/_validation-source/*`, `data/raw/reference/*` | **INERT** | SPP additions + a CAISO WECC intertie parquet; PJM's actuals rows are `calibration_reference.json` / `actual_lmp.json` **additions**, and the control and arm are scored by the SAME HEAD scorer, so any actuals movement is common-mode and differences out |

**ALL HUNKS INERT ⇒ G-CTRL form 4 is valid and the keeper's committed 2022 IS the control.**
No LIVE hunk, so no control solve is earned. Recorded here before the arm is solved.

## 9. RESULT

*(Appended after the screen.)*
