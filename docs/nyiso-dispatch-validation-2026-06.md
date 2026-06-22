# NYISO dispatch validation — what actually mis-dispatches (2026-06)

Diagnostic solve `results/calibration/_diag_nyiso_baseline_2023` (keeper config:
`--iso NYISO --year 2023 --commitment --gas-monthly-actuals
--priced-interchange`). Throwaway single-year probe (rule #14) — **not** a
dashboard keeper; used only to localize the dispatch error before building
structure.

## Headline: the error is locational, and it is NOT a uniform "NYC under-runs"

Model vs **EIA-923** in-zone generation, 2023 (downstate thermal is fully
zone-mapped via `bin_assignments_NYISO.csv`; upstate's hydro+nuclear ~65 TWh is
not in the thermal map, so the upstate row is not comparable and is omitted):

| zone | model TWh | real TWh | model − real |
|---|---|---|---|
| Capital_Hudson | 19.54 | 20.75 | −1.21 |
| **NYC (J)** | **39.97** | **29.07** | **+10.90** |
| **Long_Island (K)** | **3.70** | **8.52** | **−4.82** |

So the downstate fleet is **mis-allocated**, not uniformly under-run:

- **NYC over-generates by ~11 TWh.** It self-supplies almost its entire load
  (~40 of ~41 TWh) because it cannot import enough cheap power — Central-East
  (1,750 MW, saturated by upstate hydro going east) bottlenecks the AC path and
  the priced node lands only ~1 GW into zone J (HTP + Linden DC cables). Real
  NYC imports ~12 TWh through Dunwoodie-South; the model imports ~1. **NYC needs
  *more delivered import / a looser internal path*, not an energy must-run** — a
  must-run floor would push it further over.
- **Long Island under-generates by ~4.8 TWh.** LI imports ~80 % of its load
  across the NYC→LI (1,650 MW) link + the ~1.2 GW external node; reality is
  ~52 % self-supply (cable-islanded + local-reliability rules force more in-zone
  running). The model freely floods cheap NYC gas into LI because nothing
  enforces LI's local-reliability self-supply. **LI is the in-city-floor
  target.**

## Price: the four downstate zones collapse to one LBMP

Model 2023 zonal LMP: Upstate_West / external **$27.57**; Capital_Hudson,
Lower_Hudson, NYC **$38.66**; Long_Island **$38.81** — i.e. everything east of
Central-East clears at one downstate gas price. Only **Central-East binds**;
the Lower_Hudson→NYC (Dunwoodie-South) and NYC→LI interfaces don't, so J/K/I/G
never separate. Recovering the LI premium requires LI to stop importing freely
(the LI floor) so its interface binds.

## NYC peakers are idle — a reserve/scarcity gap, not energy

NYC CT_PEAKER (1,664 MW, 21 plants) runs at **~0.2 % CF** (mean 3.7 MW), CT_CHP
~2 %. They are the EIA-923 −75 % / −44 % classes. They do not clear on energy
(downstate energy ~$38.66 < peaker MC) and there is no scarcity tail to call
them — this is **mechanism B (RCPF locational reserve scarcity)**, gated on NYC
headroom, *not* an energy must-run. (Confirms the residual-attribution doc.)

## Imports under-clear (16.56 vs 23.45 TWh measured)

Node clearing: HQ_hydro 900 MW firm-ish (always on, $13 < downstate price),
IESO_Ontario 780 MW avg, PJM_west 206 MW avg (~19 %), ISONE_tie ~0 (1.5 %),
import_scarcity 0. The deep blocks priced above the ~$38 downstate body never
clear; the gap is partly the documented EIA-930/EIA-923 basis floor (serving the
full wedge breaks the gas band). HQ/Ontario already clear ~fully in 2023, so a
firm-must-flow floor is **structurally correct but a minor 2023 lever** — its
value is cheap-overnight hours and lower-price years (2024) where the economic
node would otherwise back the baseload off.

## Validated fix list (revises the original three)

1. **LI in-city self-supply floor** — force Long_Island to generate ≥ a forward
   fraction of its own hourly load (cable + local-reliability rule). Recovers
   ~5 TWh LI gen, cuts LI over-import, separates the LI premium. **Clear win.**
2. **Firm imports (HQ + Ontario)** — mark the cheap baseload import as
   price-insensitive must-flow. Structurally correct; minor in 2023, matters in
   2024/low-price hours. Keep, don't oversell.
3. **NYC peaker recovery = RCPF reserve scarcity (mechanism B)**, re-gated on the
   corrected downstate headroom — NOT an energy must-run (NYC already
   over-generates by +11 TWh; an energy floor makes it worse).

The original "NYC in-city minimum-generation must-run" is **dropped**: the data
shows NYC over-, not under-generates. Imposing it would chase the peaker symptom
with the wrong (and non-physical-for-NYC) mechanism.

## Result of fixes #1 + #2 (2023 P2, both flags on)

`--nyiso-local-selfsupply --nyiso-firm-imports` on the keeper config, P2 (scored
pass; `min_gen` now preserved through commitment):

| zone | base TWh | + floors | real | verdict |
|---|---|---|---|---|
| Long_Island | 3.70 | **9.27** | 8.52 | **dispatch error fixed** (−4.8 → +0.75) |
| NYC | 39.97 | 38.37 | 29.07 | eased toward real (still over — import/peaker) |
| Capital_Hudson | 19.54 | 16.42 | 20.75 | drifted (floor pulled gen from Capital) |

LI fleet now runs its real mix — ST_GAS 0.4→2.5, CC 2.5→4.5, **oil 0→1.36 TWh**
(the dual-fuel LI units fire, as they do in reality). Firm imports were the
predicted near-no-op in 2023 (node 16.56→15.75 TWh).

**Honest trade-offs (rule #1 — the structural mechanism stays):**

- **Price MAE 7.90 → 8.16** (slightly worse). Forcing LI self-supply makes the
  system *longer*, pushing the already-under-priced downstate level down ~$3 (all
  four downstate zones 38.66 → 35.76). The **LI premium does not appear**: a
  `min_gen` floor makes the LI units *inframarginal*, so they set no price.
  Recovering the premium needs the LI cables to **bind** (local gas marginal),
  and the deeper under-pricing points straight at the **missing scarcity tail
  (fix #3 / RCPF)** — the floor sharpens, not solves, that need.
- **LI oil 1.36 TWh overshoots** the EIA-923 NYISO oil total (0.42); the 0.45
  fraction lands LI +9% over real. Both are second-order tunes (fraction /
  dual-fuel relabel), not reasons to revert the mechanism.

## Fix #3 status (NYC peaker / scarcity tail) — IMPLEMENTED 2026-06

In-LP **locational** reserve co-optimization is now wired for NYISO
(`energy_reserve_coopt` + `iso == "NYISO"`, default OFF). The existing
single-system reserve machinery (`model/dispatch._build_reserve_rows`) was
generalized to **multiple nested balance families**: the system NYCA tier
(`NYISO_RCPF_PRODUCTS`) plus the East ⊃ SENY ⊃ NYC regional tiers
(`NYISO_RCPF_LOCATIONAL`), each a balance row over its member zones, sourced
from the FERC ER21-502 / Rate-Schedule-4 anchors (`results.scarcity.
nyiso_reserve_coopt_inputs`; the per-zone `R_z` variables feed every family that
contains the zone, so a downstate shortage stacks the regional penalties into
the downstate LMP). ERCOT/PJM stay byte-identical (single all-zone family).

**Result (run `nyiso 19 locational-reserve-coopt`, 2023/24/25, registered
PROBE):** the reserve fires only in genuine summer scarcity (Jul/Aug/Sep;
reserve price $0 in winter), recovering the scarcity tail the NYCA-aggregate
curve and the post-solve RCPF adder cannot dispatch. The 2025 summer under-bias
eases markedly (Jun −30.7 → −14.6, Jul −22.1 → −15.8 vs the LI-floor probe);
2025 `price_shape` now PASSES (NRMSE 0.16) and 2024 price PASSES outright;
dispatch r 0.81–0.87 all years; 2023 body unchanged (BASE 12.31 → COOPT 12.27,
A/B-verified). It is **not** an energy must-run (NYC over-generates already).

**Why it is not yet a keeper — the residual moved to a NEW root cause.** The
aggregate is now gated by a **pre-existing winter/January downstate
over-pricing** (2023 `price_mean` +13 %, NRMSE 0.40; downstate zones ~$98 in
January vs upstate ~$40, actual NYCA RT $37.8). A BASE-vs-COOPT A/B with the
co-opt OFF reproduced the *identical* January price, so this is **not** caused
by fix #3 — it is a gas / dual-fuel marginal-unit residual (likely the winter
NYC delivered-gas basis or the dual-fuel oil-cap level). That is the next
investigation; the locational-reserve mechanism stays in (rule #1).
