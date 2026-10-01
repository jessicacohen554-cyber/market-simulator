# PREREG miso-113 — COAL_PRB night-level min-gen FLOOR on the P0-detected committed run

Committed **BEFORE any solve** and **BEFORE the Phase-2 binding measurement**
(the miso-111/112 discipline: the kill rules are written while still blind to
what the floor actually does to the keeper). Session miso-113, 2026-08-01,
branch `claude/coal-prb-night-floor-dxt1oa`, off `origin/main` at `6e98263`.

Lever: `docs/mechanism-testing-matrix.md` §5.4 item **0**, the MISO queue's live
head — the named successor in `FINDING-miso112-prb-committed-split` §5.

## 1. Target

C7 `shape` FAIL on COAL_PRB — MISO's **sole** failing criterion and the
determination blocker (keeper `2026-07-31-miso-109b-hy-level`, NOT-YET).
Keeper D-1 COAL_PRB, from its own committed `legitimacy_diagnostics.json`:

| year | profile_r | model off-peak CV | actual | cv_ratio | verdict |
|---|---|---|---|---|---|
| 2023 | 0.988 | 0.072 | 0.155 | 0.466 | FAIL |
| 2024 | 0.978 | 0.058 | 0.121 | 0.475 | FAIL |
| 2025 | 0.971 | 0.023 | 0.074 | 0.314 | FAIL |

Phase is right (profile_r 0.97–0.99); the defect is **amplitude**.

## 2. What is already spent (rule 28a DO-NOT-REDO — neither is re-tested here)

- `coal_prb_committed_dispatchable` — **R**, miso-111 (whole-band repricing).
- `coal_prb_committed_split` — **R**, miso-112 (measured per-plant SPLIT), on
  its own pre-registered G2: C1 2024 COAL_PRB −10.23 TWh vs ±8.

The offer-side family is closed. miso-112 §4's structural test is what licenses
this lane: per plant, online hours, cap-weighted over the 26 regulated PRB
plants, the **keeper's night level is already right** (0.437 model vs 0.434
measured, 2024) while the split arm drives it *below* the meter (0.374). A
discount-only hold slice has no floor. The named missing object is a **floor**.

## 3. The mechanism as it will be built (`miso_coal_night_floor`)

New `ScenarioConfig` bool, **default False**, MISO-only, P1-native, **no P2**.

Built on the repo's existing shared P0-detected-run → `min_gen` construction —
`model/commitment.py::caiso_ra_mustoffer_min_gen`, the same detector behind the
CAISO RA must-offer / ERCOT / NYISO gas bridges — injected at the P0→P1 seam
(`pipeline/solve.py::run_energy_solve` via a `p1_fleet_prep` hook), so MISO
keeps its commitment structure and is still scored on P1.

- **Detector call**: `fuel_types=("coal",)`, `floor_online_hours=True`
  (the ercot141 leg: floor every hour of each P0-detected run, not only the
  idle gaps), `startup_bridge=False` (no economic ≥min-down leg — the declared
  window is the detected run, not a next-day re-offer decision).
- **Level, per plant, measured, zero fitted parameters**:
  `frac_p = max(0, night_p50_p − mustrun_pct_p/100)`, where `night_p50` is the
  frozen artifact `data/raw/_processed-legacy/coal_prb_committed_split_MISO.csv`
  (p50 of plant load / HSL over ONLINE hours h0–5, pooled 2023–25, WP-3
  loading-when-on; frozen deriver `scripts/data/derive_prb_committed_split.py`,
  rule 23 [R-FROZEN-DERIVE]) and `mustrun_pct` is the plant's own
  `thermal_tranches_MISO.csv` band. This requires a new optional per-generator
  `min_load_frac_by_gen` argument on the shared detector (default `None` →
  byte-identical for CAISO/ERCOT/NYISO).
- **Scope**: the artifact's `REG` leg — the EIA-860 regulated self-commitment
  population (`eia860_selfcommit_scope_plants()`) — PRB/subbituminous CAMPD
  plants. This is the **driver's** population (who self-commits), not a physics
  gate. The **physics gate is the detector's own** `_ra_bridge_unit_params`
  (rule 18 [R-PHYSICS]): a tranche needs `min_down_hours > 0` and must not be a
  binned *incremental* tranche, so only the `_committed` band is ever floored —
  `_mustrun`, `_econ` and `_peak` all carry `min_run_hours = 0` and are
  rejected by parameter, never by class name.
- **Composition**: `_bridge_floored_fleet(..., MECH_MISO_COAL_NIGHT_FLOOR,
  preserve_absorption=True)` — **maximum**-composition onto `min_gen`, never
  additive, with the `pmin < 0` priced export-sink rows exempt (caiso-138 §D:
  a zeros-init floor otherwise collapses every sink's lower bound to zero and
  deletes MISO's seam export outlet in the scored P1).

### 3.1 Rule 17 [R-FLOOR-WINDOW] — driver, window, forward story

- **Driver**: regulated **self-commitment**. MISO SOM Table 7 — 53–56 % of coal
  starts in the training window are self-committed, not market-committed.
- **Window**: the plant's **own P0-detected committed run** (the `_committed`
  tranche's run pattern at the 5 % run threshold), plus any idle gap shorter
  than the unit's own `min_down_hours` — a physical restart bar, not a
  commitment choice. No clock-hour rule, no calendar boxcar: a plant the model
  has offline is never floored.
- **Forward story**: regenerates in any forecast year from that year's own P0
  run pattern plus the frozen measured `night_p50` — no measured outcome, no
  same-year pin. Rule 13 [R-MEASURED] admissible on the same footing as the
  ERCOT 0.574 LSL and the NYISO 0.523/0.239 min-loads.

### 3.2 Rule 19 [R-ONE-MECH] — what already floors COAL_PRB, and the reconciliation

D-2 attribution on the keeper's committed `legitimacy_diagnostics.json`:
COAL_PRB carries **zero** forced rows. At the bare `COAL` class the only D-2
mechanism is `reliability_floor` at **0.5453 TWh / 176.978 TWh = 0.31 %**
(2023). Nothing else min-gen-floors this class.

What *does* hold the class up today is **offer-side**, not a floor: the
`_mustrun` band bids fuel-free and the `_committed` band carries the regulated
take-or-pay discount (`coal_committed_takeorpay_regulated=True`), so both sit
inframarginal. The new floor is therefore **not stacked on an existing floor**;
it is reconciled two ways:

1. **Against the mustrun band** — by subtracting it from the level
   (`night_p50 − mustrun_pct/100`), so the plant's **total** floor is exactly
   `night_p50 × nameplate`, never `mustrun + night`. Merit order inside a plant
   (mustrun fuel-free < committed discounted < econ < peak) makes this exact.
2. **Against `reliability_floor`** — by maximum-composition in
   `_bridge_floored_fleet`: on any unit-hour both write, the higher floor wins
   and only one D-2 mechanism id is tagged. They can never sum.

### 3.3 Phase-1 design facts (committed artifacts, no LP, blind to any residual)

Where the floor can physically reach, from `thermal_tranches_MISO.csv` +
the frozen night artifact, over the 26 REG PRB plants:

- cap-weighted `night_p50` **0.4446**; cap-weighted mustrun band **0.3013**;
  cap-weighted mustrun+committed **0.7172**.
- **8 / 26 plants (30.8 % of REG PRB capacity) have `night_p50 ≤` their own
  mustrun band** → floor target is **identically zero** there.
- **14 / 26 plants (67.7 % of capacity) have `night_p50 ≤` mustrun+committed**
  → the floor lies entirely *inside* the existing inframarginal block.
- The remaining 12 plants need more than mustrun+committed; the detector caps
  `target_mw` at the `_committed` tranche's own capacity, so the floor never
  reaches an `_econ`/`_peak` tranche and can never force more than the plant's
  measured night level.

This is stated **before** the Phase-2 measurement so §5's kill rule is not
written to a known answer.

## 4. Re-reading miso-111 PREREG §8 — does the inertness argument survive?

miso-111 §8 retired the bridge form as *"provably inert"* on this reasoning:
the measured plant-basis **LSL** (`loading-when-on p5`) is **0.182**
cap-weighted, which sits *below* the per-plant `_mustrun` bands (0.30–0.52), so
"a new bridge floor at 0.182 × pmax would bind BELOW the existing mustrun band
— provably inert."

**That specific argument does not transfer to this level.** The level here is
the within-run **night p50**, 0.4446 cap-weighted (0.434 on miso-112 §4's
online-hours basis; 0.62 × HSL on miso-111's class basis) — 2.4× the LSL, and
**above** the mustrun band at 18 of 26 REG plants (69.2 % of capacity, §3.3).
So the *level* leg of the inertness argument is refuted: the floor does reach
above the band it was said to sit under.

**What §3.3 shows instead is a DIFFERENT and stronger inertness risk, on the
COMMITTED band rather than the mustrun band**: at 14 of 26 plants (67.7 % of
capacity) the night level sits inside `mustrun + committed`, and that whole
block is already pinned inframarginal by the take-or-pay discount. A floor
placed under a block the LP already dispatches in full binds nothing. Whether
that risk is real is exactly what Phase 2 measures against the keeper's own
hourly dispatch — it is **not** assumed here, and the mechanism is built
either way.

**Stated plainly, before measuring**: this session's answer to "does miso-111's
inertness verdict survive at the night level?" is **no on its stated grounds
(the LSL-vs-mustrun comparison) — but the question is re-opened on new grounds
(the committed band's offer-side pin), and Phase 2 decides it.**

## 5. Kill rule — decided BEFORE any solve

**K1 — INERTNESS.** From the keeper's own committed per-plant hourly model MW
(`frontend/data/backcast/runs/2026-07-31-miso-109b-hy-level.js`, decoded via
`_decode_cf_bytes`) — **no LP** — compute the floor's binding volume per year:

```
bind_twh = Σ_plants Σ_{h: online}  max(0, floor_mw_p − model_mw_p[h])
floor_mw_p = min(night_p50_p, mustrun_pct_p/100 + committed_pct_p/100) × nameplate_p
online     = model_mw_p[h] > 0.05 × nameplate_p     (the detector's own run threshold)
```

**If `bind_twh` is < 0.5 % of the keeper's COAL_PRB annual energy in EVERY
year (2023, 2024, 2025), the mechanism is adjudicated `I` — provably INERT —
and NO solve is spent.** The precedent is miso-109/110 (`hydro_budget_
nameplate_aware`, adjudicated `I` without a solve on an L1 = 0 measurement).

Threshold rationale, fixed now: closing C7 requires the model's off-peak CV to
roughly **double** (0.072 → 0.155 in 2023). A mechanism that touches under
0.5 % of class energy cannot move a class CV by that magnitude, in either
direction; below that line the honest verdict is inert, not "small effect".

**K1 does not fire ⇒ Phase 3 runs the A/B.** A binding volume above the line is
a live mechanism whatever its sign, and it gets solved.

## 6. Guards — pre-registered, and G2 is the one that killed both predecessors

| id | guard | disposition if missed |
|---|---|---|
| **G2** | **C1 fuel-mix 16/16 every year** — COAL_PRB inside ±8 TWh in 2023, 2024 **and** 2025, and no other class flips | **arm NOT promoted** |
| G1 | C7 COAL_PRB `cv_ratio ≥ 0.5` in **2023 and 2024**, `profile_r ≥ 0.8` | not promoted |
| G3 | COAL_BIT untouched: `cv_ratio ≤ 2.0` and `profile_r` within 0.05 of control | not promoted |
| G4 | C3a / C3b / C3c: no verdict flip vs control | not promoted |
| G5 | **C8 forced-share budget (rule 20 [R-FORCED-BUDGET])**: COAL_PRB is a material class (≥ 2 % of MISO load), so the floor's forced share of COAL_PRB energy must be ≤ **30 %**, and D-4 off-window share ≤ **0.05** | over budget ⇒ conditional pass ONLY on D-4 clean + D-1 gates cleared; D-4 miss ⇒ not promoted |
| G6 | rule 15 dashboard registration of **every** run this session (control and arm, keeper or rejected) + rule 28 matrix cell update | binding regardless of outcome |

**2025 is explicitly NOT a G1 target.** The residual there is the overnight
price-formation defect (model off-peak p10 $29.71 vs actual hub $17.95),
data-blocked at miso-78/79, and rule 19 forbids stacking a lever on it. 2025
C7 is expected to stay under 0.5 and that is pre-registered as a **pass**, not
a surprise.

## 7. Predictions, stated before the measurement and before any solve

- **P-A — direction.** A `min_gen` floor can only **raise** dispatch in hours
  it binds, and those are by construction the *low* hours. Its first-order
  effect on within-day CV is therefore **negative** (a floor flattens a
  profile), not positive. If this arm improves C7 it must be through a
  **second-order price-formation channel**: pinning the cheap committed band
  removes it from the margin (the ercot141 premise — a pinned variable cannot
  price), which re-prices the overnight stack and lets other classes cycle.
  That channel is real but indirect, and I am **not** confident of its sign.
- **P-B — G2 risk.** The keeper is already **over** on 2023 COAL_PRB volume
  (miso-112's control shed 8.12 TWh to come back inside the ±8 band). A floor
  adds energy. So the G2 risk here runs in the **opposite** direction from
  miso-111/112's: over, not under. If K1 does not fire, 2023 C1 is the most
  likely G2 casualty.
- **P-C — the most likely single outcome** is that **K1 fires** and the
  mechanism is adjudicated `I` on §3.3's committed-band reasoning, closing the
  floor lane the same way the offer lane closed — with a measurement rather
  than a preference.
- **P-D** — COAL_BIT is untouched by construction (the floor is PRB/REG-scoped
  and BIT plants are not in the artifact's REG PRB set), so G3 should pass
  trivially; a G3 miss would indicate a scoping bug, not a mechanism effect.

## 8. Post-measurement readout — committed BEFORE any solve

Phase 2 ran after §1–§7 were committed and pushed. **K1 did NOT fire.** Probe
`scripts/probes/_miso113_floor_binding_audit.py`, no LP, on the keeper's own
committed per-plant hourly payload:

| year | COAL_PRB class energy | floor volume WRITTEN | floor volume that BINDS | binding share | K1 line |
|---|---|---|---|---|---|
| 2023 | 123.689 TWh | 70.500 TWh | **6.1957 TWh** | **5.01 %** | 0.5 % |
| 2024 | 118.327 TWh | 72.284 TWh | **6.1893 TWh** | **5.23 %** | 0.5 % |
| 2025 | 147.133 TWh | 75.974 TWh | **2.2705 TWh** | **1.54 %** | 0.5 % |

Ten times the inertness line in both cheap-gas years. **So the answer to §4's
open question is settled, and it settles it against the inertness reading:**
the committed band is *not* pinned inframarginal in every hour. miso-111
Phase-1's "the `_committed` band is pinned inframarginal in all 8760 h" does
not hold on the keeper's own dispatch — the band backs out, and the measured
night level is exactly what it backs out below. **miso-111 PREREG §8's
"provably inert" verdict fails on BOTH of its legs at this level**: on the
level leg (§4: the night level sits above the mustrun band at 18 of 26 plants,
69.2 % of REG PRB capacity) and now on the reachability leg as well.

Concentration, 2023: 4 plants carry 5.0 of the 6.2 TWh — 1733 (1.92), 1710
(1.23), 56068 (1.10), 1893 (0.73). All four are large regulated PRB plants
whose measured night level sits above their own mustrun band, which is the
population the mechanism was designed for.

**The A/B is therefore licensed and Phase 3 runs.** Nothing in §6's guards or
§7's predictions is revised — in particular P-B (2023 C1 is the most likely G2
casualty, in the OVER direction) is left exactly as written, and 6.20 TWh of
binding volume against a class already over by >8 TWh is now a quantified
statement of that risk rather than a hunch.

## 9. Rule duties this session commits to

- **Rule 15 [R-DASHBOARD]** — every run produced is registered on the backcast
  dashboard in THIS session, keeper or rejected probe. If K1 fires, **no run is
  produced** and there is nothing to register (the miso-109/110 precedent); the
  adjudication lands in the matrix and the findings doc instead.
- **Rule 16 [R-ALLYEARS]** — any A/B is `--year 2023 2024 2025` in ONE
  invocation per arm, years sequential within the run; the two arms are
  separate invocations that may run concurrently (rule 12, cap 2 for MISO's
  per-plant multi-zone LP).
- **Rule 22 [R-HOLDOUT]** — `--year` strictly {2023, 2024, 2025}. MISO holds no
  holdout marker and none is touched. Leave-one-year-out scoring within
  2023–2025 before any promotion is proposed.
- **Rule 20 / D-4** — `D4_WINDOWS` entry for the new mechanism added in the
  **same PR** as the field, so the D-4 row exists for a material class.
- **Rule 26 [R-MECH-MATRIX]** — the new mechanism carries its own matrix row in
  the same PR as the `ScenarioConfig` field (duty c), and the tested cell is
  stamped with its verdict this session (duty b), rejection included.
- **Rule 21 [R-DOF]** — no free parameter is added. The level is one measured
  conduct input consumed formulaically; the arm is not proposed as a keeper
  unless every guard above passes, in which case a DOF ledger entry is written.
