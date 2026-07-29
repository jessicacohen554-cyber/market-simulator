# PRE-COMMIT — ERCOT-137: coal on the MEASURED NET-MARGIN offer form, on the ACCURATE availability envelope

**Date** 2026-07-29 · **ISO** ERCOT · **Lane** ercot137-coal-margin-offer ·
**Status** PRE-REGISTERED AND PUSHED **BEFORE ANY SOLVE.**
**OUTCOME (recorded post-solve, same session — the pre-registered text below
is unchanged):** run `2026-07-29-ercot137-coal-margin-measured`. Structural
gates PASS (P1 armed+bites; P6 impossible hours −83/−86/−91 %; P7 basis
16.00/14.54 vs 16.63/15.00, inside ±$1.00; P8 Martin Lake 1.451→1.059; (f)
DOF −1 residual scalar). FIT gates FAIL (P2 G1 3/21; P3 band-uniform; P4 C1
coal +6.2/+8.8/+8.6 TWh; P5 C3a −35.2/−14.5/−12.1; (d) C4 2024 coal flips
FAIL) — **the falsifier FIRED**: the residual is the dispatchable coal bands'
ranking vs gas (`FINDING-ercot117` §5.1), the named successor lane; no
mid-session re-scope. **PROMOTED KEEPER regardless, per the owner's
in-session sign-off on the rule-1 structural standard** (rulings R1/R2 made
both measured inputs the adopted representation; the fit residual is an open
root-cause lane, not a reason to revert — rule 14). Ledger:
`docs/calibration-log/ercot.md` 2026-07-29. ·
**Keeper / BASE** `2026-07-28-ercot116-regate-base` (bundle
`results/calibration/ercot116_regate_base`) — **the COMMITTED bundle is the
BASE; it is NOT re-solved** (owner ruling R3). ·
**Supersedes** `docs/PRECOMMIT-ercot136-coal-minload-reprice-2026-07-29.md`
(its single-scalar arm is replaced by the margin form per owner ruling R1;
its gate skeleton and falsifier are reused here). ·
**Phase-1 evidence** `docs/DIAGNOSIS-ercot136-coal-headroom-conduct-2026-07-29.md`
(§§3, 5, 6), `docs/DIAGNOSIS-ercot135-coal-merit-order-2026-07-28.md` (§§1, 4,
7.2), `docs/DIAGNOSIS-ercot134-coal-availability-pin-2026-07-28.md` (§§8–10).

---

## 0. Owner rulings (given 2026-07-29 — decided, not re-litigated here)

* **R1.** Coal offers move to a **NET-MARGIN-OFF-FUEL-COST form, calibrated
  from MEASURED data**, exactly how the gas fleet's
  `gas_offer_net_revenue_margin` does it. The $4.50 was a proxy for
  mine-mouth / effective take-or-pay behaviour; measured data replaces it.
* **R2.** **ERCOT-116 IS ADOPTED**: `ercot_thermal_dam_availability_coal=true`
  becomes the ERCOT backcast default. No more scoring against the made-up
  statistical availability estimate.
* **R3.** **NO ATTRIBUTION RUNS.** One combined arm. A decomposition can be
  run later if ever wanted. The committed keeper bundle is the BASE; the
  registered `2026-07-28-ercot116-regate-arm` numbers (G1 1/21, coal
  +6.5/+9.6/+11.4 TWh, C3a −35.3/−14.7/−13.2 %) are the availability-only
  reference — read from the record, never re-solved.

## 1. The arm — three changes, one bundle

**ARM = keeper recipe + `--coal-offer-margin`**, on a HEAD that carries:

1. **Coal net-revenue margin form** (`coal_offer_net_revenue_margin` +
   `coal_offer_margin_anchor` + `coal_offer_margin_level`, ERCOT-137). The
   CAMPD coal `_mustrun` band moves from the fitted VOM-only sunk-fuel
   discount ($4.50/MWh) to

   ```
   bid(t) = HR_tranche × (fuel(t) − anchor) + emis(t) + level
   ```

   — full delivered-fuel tracking plus a fuel-invariant measured margin. THE
   MARGIN IS DERIVED, NOT FITTED (rule 13):
   `margin = level − HR × anchor`, applied per-tranche at its own heat rate,
   with both identification constants read from COMMITTED artifacts by
   `scripts/data/derive_coal_offer_margin_anchor.py`:
   * `level` = **15.8807 $/MWh** — measured RT curve bottom, 60-Day SCED
     `Submitted TPO-Price1` cap-wtd p50, 98.8–100 % coverage, res-hours-pooled
     over the four 2024–25 subsets (16.86 / 16.37 / 15.00 / 15.00;
     `results/calibration/ercot136_coal_headroom_conduct.json`
     `B1_curve_bottom` — THE identification. `Min Gen Cost` p25 $18.00 at
     28–31 % coverage is corroboration only, per ercot122 §1).
   * `anchor` = **1.7387 $/MMBtu** — training-window capacity-weighted mean
     of the model's own delivered coal price at the LP seam (1.8169 / 1.7556 /
     1.6436 by year; `results/calibration/ercot135_coal_merit_order.json`
     `A_model_offer`).
   RETIRED, not zeroed (rule 26): the fitted
   `coal_tranche_1_fuel_passthrough = 0.00` is no longer the operative ERCOT
   coal min-load pricing; whether its field and the legacy non-CAMPD tranche
   path are deleted outright or left inert is an **open owner ruling**
   (surfaced in §7). `coal_tranche_1_frac` and the CAMPD per-plant must-run
   shares STAY — measured min-load is 0.425–0.457, LARGER than the model's
   ~0.30, and moving share + price together would be two mechanisms on one
   phenomenon (rule 19). The committed/econ supply sigmoids above the block
   are untouched (rule 19).

2. **Accurate availability adopted** (owner ruling R2):
   `ercot_thermal_dam_availability_coal=true` wired as the ERCOT backcast
   default in `pipeline/backcast_config.py` (ERCOT-scoped; the other five
   ISOs stay False — rule 25). Measured-correct per ERCOT-134: impossible
   plant-hours 22,633/24,627/30,697 → 3,846/3,462/2,622 (−83/−86/−91 %).

3. **Water-fill / forced-derate collision FIXED** (correctness bug blocking
   (2); ERCOT-135 §7.2): the measured-DAM redistribution's restore ceiling is
   now `pmax × BIN_FORCED_DERATE_BY_YEAR`, never raw pmax — at the plant
   grain (`withholding._dam_waterfill` / `_ercot_dam_plant_hourly_apply`) and
   at both class grains. The measured plant fraction is live/rating over the
   disclosure's OWN (post-unit-loss) rating while model pmax still carries
   the destroyed unit, so a flat-1.0 ceiling resurrected Martin Lake to
   1.451× its COP-declared max (unit 1 destroyed — turbine fire + boiler
   explosion — before the 2025 vintage starts; the CAMPD outage derive can
   NEVER detect it, so `N_COAL4 {2025: 0.67}` is the only carrier). A mapped
   plant saturating at its ceiling does NOT push the destroyed MW onto other
   plants (the residual accounting is deliberately left on raw `pf`).
   Bit-identical wherever no forced-derate entry exists (unit-tested).

**Execution:** ONE bundle, full span `--year 2023 2024 2025`, years
sequential within the run (rules 12/16), solved in-session. Registered on the
backcast dashboard keeper-or-rejected (rule 15); the mechanism-matrix row
`coal_offer_net_revenue_margin` was added with the fields (rule 26c) and its
cell updates with this arm's verdict (rule 26b).

## 2. Ex-ante seam verification (run before the solve, no LP built)

The armed offer surface was captured at the exact LP seam
(`ercot135_coal_merit_order.capture_coal_offer_surface`, aborts pre-LP) to
verify arming and basis BEFORE burning solve time — an arming smoke check on
the mechanism, not a fit to any dispatch/price residual:

| year | `_mustrun` cap-wtd p50 | measured TPO-Price1 p50 | Δ | fleet p10/p25 (was 4.50/4.50) |
|---|---|---|---|---|
| 2024 | 16.00 | 16.63 (res-wtd of 16.86/16.37) | −0.63 | 15.61 / 16.02 |
| 2025 | 14.54 | 15.00 | −0.46 | 14.05 / 15.20 |

The per-year movement tracks delivered fuel the right way (2025 coal is
cheaper AND 2025 measured offers are lower). The $4.50 band is gone from the
armed surface; the model's share offered ≤$4.50 collapses from 0.30 to ~0
against the measured 0.058–0.084.

## 3. Predictions — fixed before the solve

Bands are ercot127's fixed edges (`<15, 15-20, 20-25, 25-30, 30-35, 35-50,
>=50`), G1 scored by `ercot128_coal_unit_grain.py --arm-bundle` (§H
fleet-aggregate loading-vs-price) against the same actuals. References:
KEEPER (= BASE) G1 **20/21**, C1 coal **+0.371/+0.797/−0.493 TWh**, C3a
**−27.2/−8.0/−8.2 %**; availability-only ARM (ercot134, committed record) G1
**1/21**, coal **+6.5/+9.6/+11.4 TWh**, C3a **−35.3/−14.7/−13.2 %**.

| # | prediction |
|---|---|
| **P1** | **Arming + bite.** `run_config.json` carries `coal_offer_net_revenue_margin=true` + the RESOLVED anchor (1.7387) and level (15.8807) + `ercot_thermal_dam_availability_coal=true`, all three years; coal energy moves materially vs the availability-only reference (falls ≥ 3 TWh/yr from 66.9/67.2/73.6). |
| **P2** | **G1 ≥ 8/21**, decisively above the availability-only 1/21. Direction is the load-bearing claim; approaching the keeper's 20/21 on the un-pinned fleet is the aspiration, ≥ 8/21 the gate. |
| **P3** | **The improvement over the availability-only reference is LOW/MID-band concentrated** (`<15`, `15-20`, `20-25`) — where a $4.50 block cleared and a ~$16 block does not. The `>=50` band moves least (< 3 pp): at scarcity prices both bids clear. |
| **P4** | **C1 coal within ±3.0 TWh in all three years** (back from +6.5/+9.6/+11.4). |
| **P5** | **C3a improves vs the availability-only reference by ≥ 8 pp in every year** (toward the keeper's −27.2/−8.0/−8.2; removing the cheap coal band lets gas set price in the hours the $4.50 block previously suppressed). |
| **P6** | **Impossible plant-hours DOWN vs the keeper BASE** by ≥ 80 % each year (~3,846/3,462/2,622, the ercot134 measurement; scored by `ercot134_coal_availability_pin.py --bundle`). This arm CHANGES availability — unlike the superseded ercot136 single-scalar arm, they are predicted to move, not to hold. |
| **P7** | **Basis check (the ercot132-leg-B failure mode).** The RESOLVED coal `_mustrun` band read back from `run_config.json` / the LP seam lands within **±$1.00** of the measured TPO-Price1 cap-wtd p50 per year (2024: 16.63; 2025: 15.00). Pre-verified at the seam (§2: −0.63 / −0.46); re-read from the solved bundle. A basis-mismatched transplant is REJECTED even if every other gate passes (leg B's measured $20.48 landed at $23.38 and that killed it). 2023 has no measured p50 — its application is the declared extrapolation, gated by (e) below. |
| **P8** | **Per-plant ARM/declared ≤ ~1.0 at every plant** (change 3 worked). Report the table against the ERCOT-135 §7.2 before-column (Martin Lake 1.451, J K Spruce 1.128, Major Oak 1.126, Limestone 1.096, Oak Grove 1.050, Sandy Creek 1.003, Coleto Creek 0.950). |

**Falsifier (fixed now).** If G1 does not beat the keeper's 20/21 AND the
low/mid bands do not carry the improvement over the availability-only
reference (P3), the residual defect is on the **GAS side of the ranking**
(`FINDING-ercot117` §5.1) — say so, register the rejection, do NOT re-scope
mid-session. A uniform-across-bands improvement is a level lever's signature,
which ercot132 leg B already refuted on this class.

## 4. The decision rule — fixed now

**Keeper-candidate recommendation requires ALL of:**

| # | criterion |
|---|---|
| (a) | **P1** holds — armed, resolved constants in `run_config.json`, biting. |
| (b) | **P2** holds — G1 ≥ 8/21 AND decisively above the availability-only 1/21. |
| (c) | **P3** holds — low/mid bands carry the improvement; `>=50` < 3 pp. |
| (d) | **No new C-gate FAIL vs the keeper BASE** (C1/C2/C4 stay PASS; C3a/b/c are already the ledgered FAIL frontier — they may not regress materially further than P5's floor). |
| (e) | **LOYO, per-year, 2-of-3 is FAIL** (the stricter ercot123 §7.2 gate, adopted verbatim). The level is identified on 2024–2025 SCED only; its 2023 application is an extrapolation — declared here, ex ante. The margin is fuel-invariant BY CONSTRUCTION, so a 2024-25-derived margin applied to 2023 is exactly what the form is designed for (the same training-window-anchor construction as the gas form). If 2023 regresses while 2024/2025 pass, that is ONE year (pass); any TWO failing years is FAIL. |
| (f) | **DOF ledger does not grow, and the residual-identified count FALLS by one** (rule 21): the operative $4.50 (fitted `coal_tranche_1_fuel_passthrough=0.00`) is retired; `anchor` and `level` are measured inputs with `lineage_solves 0`. |
| (g) | **P7** holds — the resolved band lands on the measured value (±$1.00, 2024 and 2025). |
| (h) | **P8** holds — no plant above ~1.0 of its own declaration. |

A C1 or price-MAE gain does NOT license the mechanism if (b)/(c)/(e)/(g)
fail (rule 1; the ercot132-leg-B precedent, where C1 improved and the arm was
still correctly rejected). Whatever the verdict, the run is registered and
the matrix cell stamped in this session (rules 15/26b). **The keeper file is
not touched without owner sign-off** — a passing arm is PROPOSED for
promotion, not self-promoted.

## 5. Composition and rule-19 enumeration (before the solve)

Mechanisms touching the coal min-load block in the ARM: the two floors
(`ercot_coal_min_config_floor`, `coal_mustrun_per_plant`) — UNCHANGED, they
represent "not price-responsive"; the margin form — the block's ONLY pricing
mechanism (replaces the $4.50); the supply sigmoids (PRB 0.76 / lignite
0.675 floors) — committed/econ bands only, untouched; `ercot_thermal_as_endogenous`
— AS pricing, untouched. No mechanism is stacked; one is replaced.

## 6. Honest limits, stated before it runs

* **It cannot fix a gas-side defect.** If the falsifier fires, the successor
  is the gas rebasis lane, not another coal probe — coal's enumeration is
  otherwise exhausted (ERCOT-122…136).
* **Even full adoption leaves C6 UNATTESTED** while residual-identified DOF
  entries persist elsewhere, and leaves the C3c scarcity tail where
  ERCOT-99/101/107/108 attributed it. A pass is not over-claimed.
* **The measured level is a p50 of a dispersed distribution** (p10 2.65–8.19,
  p25 10.32–13.00): the form prices the whole band at the p50's margin, so
  the model's ≤$4.50 share lands at ~0 against a measured 0.058–0.084 — a
  known, accepted flattening (the same class-median compression the gas
  committed bands carry).

## 7. Open owner rulings surfaced by this lane (NOT decided here)

1. Whether the retired `coal_tranche_1_fuel_passthrough` pricing path and the
   legacy non-CAMPD coal tranche path (`split_coal_tranches` `_t1/_t2/_t3`)
   should be **DELETED outright (rule 26 [R-DELETE]) or left inert**. The
   margin form makes the CAMPD path independent of them; the legacy path
   still consumes the fields for non-CAMPD fleets.
2. Promotion of this arm to ERCOT keeper, if the §4 rule passes.

## 8. Scope

Holdout years (2022 / 2019 / ≤2021 / H1-2026) untouched (rule 22). No new
GitHub Actions workflow. ERCOT-scoped only — no cross-ISO transfer of the
coal margin (rule 25; PJM/MISO enter the matrix row as `U`). CLOSED lanes
honoured: coal offer REACH (ercot123 §7.1), the self-scheduled fork
(ercot136), offer LEVEL rebasis (ercot132 leg B), F923 as a price question
(ercot135 §3), pooled econ_high (ercot122 §5.2), ramp trajectory (ercot127
§1), availability ENVELOPE layer (ercot126), min-config upper bound
(ercot130), plant-grain fractional min-load floor (ercot127 §3), unit-grain
commitment STATE (ercot128), age/temp derates (ercot121 §1a), EP-rebasis C3c
(ercot119), `ercot_zonal_gas_basis`, West/Panhandle topology split.
