# Prompt Pack Plan

Status: **planning**. A "prompt pack" is a self-contained build prompt that
can be handed to a fresh coding-agent session to implement one slice of the
multi-ISO expansion. Each pack states its goal, prerequisites, files, data
dependencies, tests, and acceptance criteria — and every pack carries the same
**ERCOT regression guard**: with all new toggles at default-off, ERCOT
backcast results must be unchanged.

Packs are designed so a session can finish one without timing out, then commit.
Lettering matches the cross-references in docs 01 (Pack E = hydro) and 02
(Pack F = fuel types).

## Dependency graph (build order)

```
A (topology+zones) ─┬─> B (data+calibration ref) ─> J (backcast & sign-off)
                    │
C (imports M4) ─────┤
D (capacity rev M1)─┤
E (hydro M3) ───────┤
F (fuel types) ─────┼─> G (fuel classes)
H (RPS/CES + carbon)┤
I (reserves M2) ────┘   (deepest LP change; do after first ISO calibrates)
```

A and B repeat per ISO. C–I are mostly build-once, reuse-everywhere. J repeats
per ISO. Recommended first vertical slice: **A→B→J for CAISO** (single zone +
existing import node) to prove the pipeline end-to-end, then layer modules.

---

## Pack A — Per-ISO topology, zone assignment & config foundation

**Goal:** Add/flesh out one ISO's `ISOConfig` (zones, load shares, links, TTC,
VOLL) and its plant→zone assignment so the fleet loads correctly.

**Prereqs:** doc 04 zone/TTC values for the ISO; eGRID/EIA-860 present.

**Files:**
- `src/market_sim/config/iso_configs.py` — add/replace `_<iso>_config()`,
  register in `_ISO_BUILDERS`. Replace PJM's placeholder TTC/shares with cited
  values. Add MISO and SPP builders from scratch.
- `src/market_sim/data/zone_assignment.py` — add to `_ISO_TO_BA_CODE`
  (MISO→`MISO`, SPP→`SWPP`); single-zone → `_SINGLE_ZONE`; multi-zone → a
  geographic splitter (lat/lon + FIPS) and `_LARGEST_ZONE` fallback (ERCOT's
  Houston-county logic is the template).
- `src/market_sim/config/constants.py` — per-ISO entries where keyed by ISO
  (`STATE_RPS_FLOORS`, `GAS_BASIS_DIFFERENTIAL`, `STORAGE_BASE_FLEET_MW`,
  `DEMAND_GROWTH_RATES`, `QUEUE_CAP_*`).

**Tests:** `tests/test_iso_config.py` (topology validates, shares sum to 1.0);
`tests/test_zone_assignment.py` (every BA plant resolves to a real zone, none
dropped; spot-check known plants land in expected zones).

**Acceptance:** `get_iso_config("<ISO>")` returns a valid config; fleet
assembled for the ISO has plant count & total capacity within a few % of the
ISO's published generation-fleet totals.

---

## Pack B — Per-ISO data ingestion & calibration reference

**Goal:** Make one ISO's backcast inputs load: EIA-930 hourly demand + CF
profiles, and the calibration-reference JSON/CSV entries.

**Prereqs:** Pack A; uploads from doc 01 (EIA-930 hourly parquet, missing CEMS
states, regional gas basis).

**Files:**
- `src/market_sim/data/renewables.py` — generalize CF derivation beyond ERCOT;
  use the EIA-930 per-fuel distribution (HSL path stays ERCOT-only until doc 04
  HSL data exists for the ISO).
- `scripts/data/build_calibration_reference.py` — extend the per-ISO-year emitter
  (demand stats, generation_twh by fuel, gas price, wind/solar capacity with
  zone_shares + monthly_ramp). Output `data/raw/_validation-source/{ISO}_{year}_*.csv`
  and append to `calibration_reference.json`.
- `scripts/data/derive_load_shares.py` — generalize to take an ISO + zonal-load file
  (multi-zone ISOs).

**Data deps:** doc 01 §2 (EIA-930), §3 (CEMS), §4 (gas basis), §5 (zonal load).

**Tests:** `tests/test_renewables.py` (CF profile mean ≈ annual-average CF for
the ISO); a calibration-reference schema test (all required keys present per
ISO-year).

**Acceptance:** `calibration_reference.json` has complete entries for the ISO
across target years; loaders read them without ERCOT-specific branches.

---

## Pack C — Import/export node module (M4)

**Goal:** Represent inter-ISO interchange faithfully (CAISO↔WECC,
NYISO↔HQ/PJM/NE/IESO, ISO-NE↔HQ/NYISO, PJM/MISO/SPP seams).

**Prereqs:** Pack A. CAISO's existing `WECC_import` node is the template.

**Files:**
- `src/market_sim/config/iso_configs.py` — generalize import nodes: a zone with
  `load_share=0` plus link(s) with TTC, and an associated **import offer price**
  (priced "generator" at the node) or a **fixed schedule** profile.
- `src/market_sim/model/dispatch.py` — import injection reuses existing flow
  variables; a priced import is a thermal-block generator at the node with an
  exogenous offer-cost series. No new variable class.

**Data deps:** interface TTCs (doc 04); historical net interchange from EIA-930
(`Total interchange`) for calibration; HQ/import offer proxy price.

**Tests:** `tests/test_transmission.py` extension (import node injects within
TTC, priced into LMP); ERCOT (no import nodes) unchanged.

**Acceptance:** modeled net interchange sign/magnitude tracks EIA-930 actuals
for the ISO within tolerance.

---

## Pack D — Capacity / resource-adequacy revenue module (M1)

**Goal:** Add exogenous capacity-market revenue to retirement/entry economics
so capacity-market ISOs don't over-retire thermal. **No LP change.**

**Prereqs:** Pack A. Reference: `capacity.py::apply_economic_retirements`,
`estimate_expected_revenue`, and the existing EAC-revenue addition pattern
(`compute_attribute_revenue`).

**Files:**
- `src/market_sim/config/iso_configs.py` — add `capacity_mechanism`
  (type: RPM/ICAP/FCM/PRA/RA-obligation/none; price $/MW-day or $/kW-yr;
  season: annual/seasonal; UCAP derating).
- `src/market_sim/model/capacity.py` — add `capacity_revenue` to `net_revenue`
  and to expected new-entry revenue; gate on `capacity_mechanism` (off = ERCOT
  behaviour exactly).
- `src/market_sim/config/constants.py` — per-ISO capacity-price series with
  citations (BRA/FCA/PRA clearing prices; CONE proxy for SPP/CAISO).

**Tests:** `tests/test_capacity.py` — a unit with negative energy margin but
positive capacity revenue survives in an RPM ISO and retires in ERCOT;
seasonal-MISO accounting (M8) splits the year into 4 seasons.

**Acceptance:** PJM/NYISO/NEISO/MISO thermal retirement trajectories are
materially less aggressive than energy-only; ERCOT unchanged.

---

## Pack E — Hydro energy-budget module (M3)

**Goal:** Give hydro (fuel code 6) an inter-temporal energy budget + min/max MW
instead of a flat thermal block. Material for NYISO, CAISO, ISO-NE, MISO.

**Prereqs:** Pack A/B. EIA-923 monthly hydro generation (present) → energy
budget; EIA-860 nameplate → max MW.

**Files:**
- `src/market_sim/data/hydro.py` (new) — load monthly hydro energy budgets and
  min/max MW per ISO-zone.
- `src/market_sim/model/dispatch.py` — add a constraint family over the hydro
  generator subset: `Σ_{t∈month} P_hydro[g,t] ≤ monthly_energy[g,month]`, plus
  min-flow lower bounds. Reuses existing P variables; vectorized (no hour loop)
  via a month-incidence sparse matrix. Guard so zero hydro budget = current
  behaviour.

**Tests:** `tests/test_dispatch.py` — hydro respects monthly budget; shifts
generation to high-price hours within the budget; ERCOT (negligible hydro)
unchanged.

**Acceptance:** modeled hydro monthly energy matches EIA-923 actuals; hydro
price-following behaviour is sane.

---

## Pack F — New fuel types: oil & biomass

**Goal:** Register oil and biomass as dispatchable thermal generators (per
methodology §1.5: data/parameter extension, no LP change).

**Prereqs:** none structural. Reference the existing `gas_st` entry — it is the
closest template (legacy steam, full parameter set across every dict).

**Files (add an entry for each new fuel to every keyed dict):**
- `src/market_sim/data/fleet.py` — add to `FUEL_TYPE_MAP` (use the reserved
  code 11 and the next free codes); extend the EIA energy-source classifier
  (`_classify_fuel`-style logic, ~line 900) so EIA fuel codes
  (`DFO`/`RFO`/`PC`→oil, `WDS`/`AB`/`MSW`/`LFG`→biomass) map correctly.
- `src/market_sim/config/constants.py` — add entries to `HEAT_RATE_BINS`,
  `CO2_RATES`, `NOX_RATES`, `FUEL_CO2_FACTOR_PER_MMBTU`, `VOM`, `EFORD`,
  `THERMAL_AVAILABILITY`, and a fuel-price source (oil → distillate/residual
  price series; biomass → fuel cost). Each with a citation comment.
- Fuel price plumbing in `src/market_sim/data/fuel.py` for the new fuels.

**Data deps:** oil price (EIA distillate/residual $/MMBtu), biomass fuel cost;
emission factors (EPA). Oil is critical for NYISO/ISO-NE peakers; biomass for
PJM/MISO/NEISO.

**Tests:** `tests/test_fuel.py` / `test_fleet.py` — oil & biomass units classify,
get correct MC, emit correctly; a fleet with oil dispatches it only at high
prices (peaker behaviour).

**Acceptance:** Northeast oil/dual-fuel units appear and dispatch in scarcity;
biomass shows up in PJM/MISO fuel mix; ERCOT unchanged (no such units).

---

## Pack G — New fuel classes (granular subtypes & dual-fuel)

**Goal:** Where one fuel type is too coarse, add fuel *classes*: distillate vs
residual oil, oil_ct vs oil_st, biomass subtypes, and **dual-fuel** (gas units
that switch to oil when gas basis spikes — central to NYISO/ISO-NE winters).

**Prereqs:** Pack F.

**Files:**
- `src/market_sim/config/constants.py` — finer keys in the fuel dicts (e.g.
  `oil_distillate` vs `oil_residual`, with distinct heat rates/emission rates).
- `src/market_sim/data/fleet.py` — dual-fuel handling: a unit carries a primary
  and backup fuel; marginal cost takes `min(gas_mc, oil_mc)` per hour when the
  unit is dual-fuel capable and gas basis is provided. This is an
  `assemble_mc` extension (objective-only), not an LP structural change.

**Data deps:** EIA-860 dual-fuel flags / multiple-energy-source fields; regional
gas basis (already partly in `GAS_BASIS_DIFFERENTIAL`) and oil price series.

**Tests:** `tests/test_fuel.py` — dual-fuel unit switches to oil when gas basis
exceeds the oil-parity threshold; ERCOT (no dual-fuel) unchanged.

**Acceptance:** NYISO/ISO-NE winter price spikes are reproduced via fuel
switching rather than pure scarcity slack.

---

## Pack H — State/zonal RPS-CES + carbon programs (M5/M6)

**Goal:** Faithful clean-energy and carbon policy: multi-state RPS within an
ISO, NYISO CES / CAISO 60% RPS, and RGGI / CA cap-and-trade as ISO-default
carbon prices.

**Prereqs:** Pack A. Reference `policy/rps.py`, `STATE_RPS_FLOORS`,
`policy/constraints.py` (the constraint extension point), `policy/carbon.py`.

**Files:**
- `src/market_sim/config/iso_configs.py` — `rps_scheme` (single annual vs
  zonal/multi-target) and `carbon_program` (RGGI / CA-CAT default price).
- `src/market_sim/policy/constraints.py` / `rps.py` — emit per-scheme RPS rows
  (reuse `_build_rps_row` pattern; one row per target).
- `src/market_sim/policy/carbon.py` — apply ISO-default carbon price when a
  carbon program is active and the scenario doesn't override.
- `src/market_sim/config/constants.py` — RGGI and CA-CAT allowance price series
  with citations.

**Tests:** `tests/test_config.py` / policy tests — RGGI carbon price flows into
MC for NYISO/ISO-NE/(partial PJM); multiple RPS targets each get a dual; ERCOT
unchanged.

**Acceptance:** carbon-program ISOs show the expected MC uplift on emitting
units; clean shares track the RPS/CES trajectories.

---

## Pack I — Operating-reserve co-optimization (M2)

**Goal:** Co-optimize energy + operating reserves (Reg-Up/Dn, Spin, Non-Spin).
The **only deep LP change**; do it after the first ISO calibrates on energy
alone, so it's an additive refinement.

**Prereqs:** a calibrated energy-only ISO; deep familiarity with `dispatch.py`
`VariableLayout` and the vectorized constraint builder.

**Files:**
- `src/market_sim/model/reserves.py` (new) — reserve product definitions,
  per-ISO requirement curves.
- `src/market_sim/model/dispatch.py` — extend `VariableLayout` with an optional
  reserve block (zero-width when off, so existing column math is byte-identical
  for ERCOT); add reserve-procurement constraints and headroom coupling
  `P[g,t] + Σ_r Reserve[g,r,t] ≤ pmax·avail`. Must stay vectorized (kron over
  hours), struct-of-arrays.

**Data deps:** per-ISO reserve requirements (MW or % of load); reserve-product
definitions; ancillary clearing prices for validation.

**Tests:** `tests/test_dispatch.py` — reserve requirement met, headroom
respected, reserve shadow prices sane; **critical:** with reserves off, the LP
column count, objective, and duals are identical to today for ERCOT.

**Acceptance:** modeled reserve prices and energy-reserve interaction are
plausible; no regression in energy-only runs.

---

## Pack J — Per-ISO backcast calibration & sign-off

**Goal:** Run the ERCOT backcast harness for the ISO and calibrate to actuals.

**Prereqs:** Packs A, B, plus whichever module packs the ISO's profile
(doc 02 §3) requires.

**Files:** mostly config/parameter tuning + `scripts/run_calibration_full.py`
generalization; append results to `docs/calibration-log.md` and citations to
`docs/parameter-citations.md`.

**Acceptance (mirrors ERCOT sign-off):** price duration curve, fuel-mix
generation shares, emissions, curtailment, and net interchange all within the
documented tolerance vs EIA/eGRID actuals across target years; per-ISO status
table in `00-iso-addition-protocol.md` marked complete.

---

## How to run a pack

1. Open a fresh session on branch `claude/multi-iso-expansion-plan-*` (or a
   per-ISO sub-branch).
2. Paste the pack body as the task; it is self-contained.
3. Implement, run the named tests **plus** the full suite, confirm the ERCOT
   regression guard, commit at the pack boundary.
4. Update the status table and check off the Section-2 checklist items in
   doc 00.
