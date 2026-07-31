# PREREG miso-112 — regulated-PRB committed-band SPLIT (hold-through + cycling)

Committed BEFORE the slice-size measurement is run (rule 23
[R-FROZEN-DERIVE] discipline: the measurement is source-data conduct
derivation, and this pre-registration is what keeps it blind to the
residual). Session miso-112, 2026-07-31, branch
`claude/miso-112-coal-prb-split-yn0al4`. Successor to miso-111
(`results/calibration/PREREG-miso111-prb-committed-flex-2026-07-31.md`,
`results/calibration/FINDING-miso111-prb-committed-dispatch-2026-07-31.md`);
mechanism-matrix §5.4 queue item 0, the live head.

## 1. Target

C7 `shape` FAIL on COAL_PRB — MISO's sole remaining determination blocker
(keeper `2026-07-31-miso-109b-hy-level`, D-1 cv_ratio 0.466 / 0.475 / 0.314
in 2023/2024/2025 against the 0.5 gate; profile_r 0.97-0.99, amplitude not
phase).

## 2. The measured fact this split rests on (miso-111, already committed)

Reality's regulated-PRB **within-run night level is ~0.62 × HSL** — BETWEEN
the model's mustrun band (~0.46 of nameplate, class cap-weighted) and its
full committed stack (~0.92). One band at one price cannot hold 0.62:

- discounted to `1 - contract_share` (the keeper), the band is
  inframarginal in all 8760 h and pins at ~0.92 — the C7 flatness;
- repriced whole to full SRMC (miso-111 arm B, matrix cell **R** — DO NOT
  RE-TEST that form), it drops to the mustrun band ~0.46 on every cheap
  night — shape passes 2023/24 (cv_ratio 0.466→0.828 / 0.475→1.028) but C1
  COAL_PRB flips −8.77 / −14.97 TWh vs ±8: the discount was carrying
  ~9-15 TWh/yr of REAL stay-online self-commitment energy.

The committed band therefore needs a **measured split**: a hold-through
slice (the fraction reality keeps loaded through cheap nights — keeps the
contract discount) and a cycling slice (bids full delivered cost). Both
sizes come from the same CAMPD within-run loading construction miso-111
built — source-data conduct, blind to the residual by construction of this
document.

## 3. The mechanism (exact construction, committed before measuring)

One new ScenarioConfig bool, **`coal_prb_committed_split`**, default False
(rule 24; matrix row added in the same PR per rule 26c). When armed:

- **Scope** (all conditions AND-ed): CAMPD-binned coal plant;
  `coal_supply ∈ {prb, subbituminous}` (the COAL_PRB class, the miso-111
  scope verbatim); plant ∈ `eia860_selfcommit_scope_plants()` (the
  regulated set whose committed band carries the
  `coal_committed_takeorpay_regulated` discount — merchant PRB already
  bids full cost, nothing to split); plant has a measured row in the
  split artifact (§4); coal-CHP plants (`coal_chp` map) excluded (their
  band floor basis is the steam host, not `_mustrun`); flat committed
  band only (`committed_ramp_spread == 0`, the keeper configuration — a
  ramp-rendered band skips the split, documented non-interaction).
- **Split rule** (formulaic, computed at bin assembly with the model's own
  per-plant tranche values — the same post-override `pct_mr` that sizes
  `_mustrun` and the same final `committed_cap`, so the stack is
  self-consistent):

  ```
  hold_cap = min(committed_cap, max(0, night_p50 − pct_mr/100) × nameplate)
  cyc_cap  = committed_cap − hold_cap
  ```

  (`committed_cap = nameplate × pct_mc/100` up to the existing peak-band
  clamp; `night_p50` is the measured within-run night level of §4.)
- **Hold-through slice**: keeps suffix `_committed`, hence the anchor tags
  (min_run / min_down / startup, `must_run_pct`, `bin_nameplate_mw`) and
  the regulated take-or-pay discount `1 − contract_share` — unchanged
  keeper pricing on a smaller band.
- **Cycling slice**: new suffix `_commitcyc`; min_run/min_down 0, startup
  0 (the same physical unit, already started — the `committed{i:02d}`
  ramp-slice precedent); bids **full delivered cost** under its supply
  passthrough; included in the `coal_econ_srmc_bound` ≥ 1.0 clamp (its
  marginal fuel is bought at market, exactly like econ/peak); never
  matched by any committed-band discount rule (suffix scoping);
  `_coal_tranche_rank` = 1.5 (physically between `_committed` 1.0 and
  `_econlo` 2.0).
- **`_mustrun` untouched everywhere.** No new floor of any kind (the
  miso-111 PREREG §8 inertness result stands: measured plant LSL p50
  0.182 sits far below the mustrun bands). Offer-side only ⇒ D-2 stays
  clean, G5.
- **`day_p50` sizes NOTHING.** The band top stays the tranche artifact's
  `committed_pct` (rules 19/23: this is a split of an existing band, not
  a resize — resizing would be a second mechanism and a re-derivation).
  `day_p50` is recorded as a consistency diagnostic only: predicted
  cycling-slice top `pct_mr/100 + (hold_cap + cyc_cap)/nameplate` is
  reported against it per plant.

Zero fitted parameters. One measured input (`night_p50`) enters
formulaically. Rule-13 admissibility: a within-run night loading level is
plant conduct measurable from any year's CEMS record, year-static by
pooling (same status as `coal_takeorpay_share`), regenerates for a forward
year unchanged and responds to fleet changes via the plants it attaches
to; it is not an outcome pin (it does not touch prices, volumes or any
residual — the LP still chooses dispatch above/below the slice boundary
every hour by price).

## 4. Measurement protocol (exact, committed before running)

Source: CAMPD unit-level hourly gross load
(`data/raw/campd-unit-level/<STATE>_<year>.parquet`), 2023–2025, MISO
COAL_PRB plants (`class_plant_codes("MISO", ("COAL",))` filtered by
`_coal_class_for == "COAL_PRB"`), regulated vs merchant by
`eia860_selfcommit_scope_plants()`. PLANT basis; the WP-3 loading-when-on
construction verbatim (miso-111 §4: `HSL_proxy` = p99.5 of pooled plant
gross load, `online` = load ≥ max(10 MW, 2% × HSL)).

1. `night_p50` = p50 of plant load / HSL over ONLINE hours with
   hour-of-day ∈ h0–5, **pooled 2023–2025** (year-static parameter, like
   the contract shares; per-year values recorded for the record but the
   pooled value is the one the model consumes).
2. `day_p50` = p50 over ONLINE hours h13–18, pooled (diagnostic only, §3).
3. Artifact: `data/raw/_processed-legacy/coal_prb_committed_split_MISO.csv`
   (plant_code, leg, hsl_mw, night_p50, day_p50, n_night, n_day), written
   by `scripts/data/derive_prb_committed_split.py` (rule 23: re-derives
   only on CAMPD source updates). Session record with per-year values:
   `results/calibration/miso112_prb_conduct.csv`.

## 5. Kill rules (the split is DEAD and the session ends NO-LP if either fires)

Computed over regulated-PRB plants with the model's own artifact values
(`thermal_tranches_MISO.csv` `mustrun_pct`/`committed_pct`, the keeper's
`coal_mustrun_online_pmin=False` basis):

- **K1 — degenerate to the whole-band form (already R).** If the
  capacity-weighted hold share of the committed band,
  `Σ hold_cap / Σ committed_cap`, is **< 0.05**, the split reproduces
  miso-111 arm B, which is adjudicated R. Dead; write the finding, no
  solve.
- **K2 — degenerate to the keeper.** If the capacity-weighted cycling
  share `Σ cyc_cap / Σ committed_cap` is **< 0.05**, the split reproduces
  the discounted whole band. Dead; no solve.

(The miso-111 conduct kills K1–K3 — flat band, no headroom, merchant
artifact — already passed on this same construction and are not re-run.)

## 6. Phase-3 guards (pre-registered NOW; bind on the A/B)

Arms (each 2023+2024+2025 in ONE bundle, rule 16; years chained
sequentially per rule 12 via `scripts/probes/_miso112_chain.sh`):

- **A (control)**: the `miso109_hy_level_B` keeper recipe replayed at
  miso-112 HEAD, no delta (HEAD drift is real — miso-111 measured 0.030%
  L1 in 2025 from ~1 day of main).
- **B (arm)**: A + `coal_prb_committed_split=true`.

Guards (the miso-111 kills, inherited):

- **G1 (target).** COAL_PRB D-1 cv_ratio ≥ 0.5 AND profile_r ≥ 0.8 in
  **2023 AND 2024** in arm B. **2025 expectation, stated before solving:
  2025 will likely STAY under 0.5** (miso-111 arm B reached 0.411 with the
  whole band repriced; the residual is the overnight price-formation
  defect — model off-peak p10 $29.71 vs actual hub p10 $17.95 — the
  DATA-BLOCKED miso-78/79 congestion + sub-hourly-RT lane; no offer lever
  is stacked on it, rule 19).
- **G2 (C1, THE test the split exists to pass).** C1 fuel-mix 16/16 in
  every year — COAL_PRB back inside ±8 TWh. If the hold-through slice
  cannot hold volume while the cycling slice holds shape, the lane is
  closed BOTH WAYS (that finding is valuable — register it).
- **G3 (COAL_BIT untouched by construction).** COAL_BIT cv_ratio ≤ 2.0
  all years and profile_r within 0.05 of keeper.
- **G4 (prices).** C3a/C3b/C3c verdicts do not regress vs the keeper
  (ledgered CAVEATs may improve or hold, not widen).
- **G5 (forcing legitimacy).** No new floors; COAL_PRB D-2 forced rows
  stay zero in both arms (offer-side-only construction).
- **G6 (registration).** BOTH arms registered on the dashboard this
  session (rule 15); the new field gets its OWN matrix row with the
  verdict; the `coal_prb_committed_dispatchable` cell is touched ONLY if
  new evidence changes its R adjudication (none is expected — the
  whole-band form is not re-tested).

**Pre-registered promotion rule.** If G1 passes in 2023+2024, 2025
*improves* vs control, and G2–G5 pass, the arm is a rule-1 keeper
candidate ON STRUCTURAL FIDELITY even with C7-2025 still failing — the
owner's 2026-07-31 grant (structural integrity may outrank gate
regression; on record in the miso-111 session) is cited in the promotion
note if used; any promotion re-stamps the matrix header and runs
`calibration-keeper-auditor --iso MISO`.

## 7. Sharpened predictions (stated before measuring or solving)

- **P-A (slice sizes).** From miso-111's class aggregates
  (night 0.62, mustrun ~0.46, stack ~0.92): hold share ≈
  (0.62 − 0.46)/0.46 ≈ **0.35** of the band, cycling ≈ 0.65. Neither
  kill rule fires.
- **P-B (G2, volume).** The hold slice pins the model's night level at
  `mustrun + hold = night_p50` — the measured night level itself — so the
  arm's overnight shed should approximate the REAL fleet's night
  backdown, and C1 should return inside ±8 (control +2.02/+1.86 TWh of
  headroom). Honest risk, sized in advance: naive linear scaling of the
  miso-111 shed by the cycling share (≈0.65 × −10.8/−16.8 TWh delta)
  puts 2024 at ≈ −9 TWh, marginally outside — the pass depends on the
  hold slice genuinely holding through cheap nights, which is precisely
  the mechanism under test. If 2024 C1 fails, G2 kills the arm and the
  lane closes both ways.
- **P-C (G1, shape 2023/24).** cv_ratio lands between control and
  miso-111 B; at ~0.65 cycling share the interpolation gives ≈0.70
  (2023) and ≈0.83 (2024) — both clear 0.5.
- **P-D (2025).** Improves over control 0.314 but ≤ miso-111 B's 0.411
  (the split holds MORE at night than the whole-band form), so C7-2025
  stays FAIL; the residual is the price-formation lane, not reopened.
- **P-E.** COAL_BIT stays in its keeper band (offers untouched;
  second-order price feedback only).

## 8. What this session will NOT do (DO-NOT-REDO, restated)

Whole-band committed repricing (miso-111, R — the split is the ONLY open
form); blunt `sunk_fixed` removal (miso-102); tonnage RHS in any form
(miso-103/104); offer steepening / PRB price levers (miso-102); DA
virtuals (miso-105); CT heat-rate levers (miso-106/107); MOM outages
(miso-85/87); topology (miso-78/79); hydro lanes (miso-108/109/110,
closed both directions); any NEW floor below the mustrun band (provably
inert — measured LSL p50 0.182 < mustrun 0.30-0.52); no holdout year in
any form (rule 22 — MISO holds NO tier marker; `--year` strictly
{2023, 2024, 2025}); no re-derivation of any parameter against a residual
(the §4 measurement is source-data conduct, blind to the model's residual
by construction of this document).

## 9. Post-measurement refinement slot

Appended AFTER the §4 measurement runs and BEFORE any solve (the miso-111
§8 pattern): kill-rule readout, measured slice sizes, and any
measurement-forced design refinement. Refinements may only narrow scope or
report diagnostics — the split rule of §3 is frozen as written.

**Measurement ran (this commit; §1–§8 committed first at f9d5d61). No kill
rule fired; no design refinement — the §3 rule stands verbatim.**

- Census: 30 MISO COAL_PRB plants measured (26 REG, 4 MER), every REG
  plant carrying a `thermal_tranches_MISO.csv` COAL row, so the readout
  basis is exactly the runtime basis (`COAL_MUSTRUN_BY_PLANT` holds no
  MISO plant — verified, 10 ERCOT entries only).
- **K1 NOT fired**: cap-weighted hold share of the committed band =
  **0.286** (≥ 0.05).
- **K2 NOT fired**: cap-weighted cycling share = **0.714** (≥ 0.05).
- P-A was 0.35/0.65 from the class aggregates; the plant-resolved answer
  is 0.29/0.71 — same neighbourhood, and now per-plant: **8 plants**
  (Sherco 6090, Labadie 6009 among them) measure `night_p50 ≤ pct_mr/100`
  → hold slice floored at 0, their whole band cycles (the miso-111 form
  is CORRECT at those plants per their own meter); **12 plants** measure
  `night_p50` at/above the band top → whole band holds through (keeper
  form persists there); **6 plants** genuinely split (1710, 1733, 2103,
  4050, 8023, 56068). The heterogeneity is the mechanism: miso-111
  applied one answer to all 26 and both uniform answers are refuted.
- Consistency diagnostic (`day_p50`, sizes nothing): recorded per plant
  in `results/calibration/miso112_prb_conduct.csv`; band tops generally
  sit at-or-above day_p50 (the econ tranches above the band carry the
  measured day peak), no anomaly requiring narrowing.
