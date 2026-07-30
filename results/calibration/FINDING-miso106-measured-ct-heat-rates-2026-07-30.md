# FINDING — miso-106: measured CT loaded heat rates, MISO's own artifact

> **Verdict: KEEPER.** `2026-07-30-miso-106b-ct-heatrate` replaces
> `2026-07-28-miso-101b-tempgrain` as the MISO keeper, promoted 2026-07-30 on
> owner authorization ("*if structural integrity improves but gates regress that
> may still be a keeper… if so plz promote*") and on rule 1 `[R-STRUCT]`.
> Determination **NOT-YET**, the SAME determination and the SAME criterion
> profile as the keeper it replaces (9 scored / 6 target-grade / 2 ledgered /
> 1 fail), decided by the same C7 COAL_PRB shape issue this delta does not touch.
> Ledgered-caveat budget **unchanged at 3/3**.

* **Pre-registration:** `PREREG-miso106-measured-ct-heat-rates-2026-07-30.md`,
  committed **before either arm was solved** (`166339f`).
* **Arms:** `2026-07-30-miso-106a-ct-hr` (control) /
  `2026-07-30-miso-106b-ct-heatrate` (treatment). Both registered.
* **Lever:** mechanism matrix §5.4 **item 4**, MISO cell `U` → `K`.

---

## 1. What was wrong with the input

MISO's non-ERCOT fleet loader gives every combustion turbine eGRID's
**plant-average annual** heat rate. Two things are wrong with that for a peaker,
and MISO's own data shows both.

**(1) An annual average is not a loaded rate.** *South Fond Du Lac* (7203,
326.5 MW, 4 turbines) carried **26.544 MMBtu/MWh** — above the physical
simple-cycle ceiling of 25.0, and roughly 2× any operating turbine. CAMPD says
why: the units produced 2.2–3.7 GWh each in 2024, a capacity factor near
**0.5 %**, so the annual mean is overwhelmingly start and part-load fuel. Their
loaded rate is 13.79–13.93 gross, **14.014 net**. It is one of **5** MISO
CT_PEAKER plants (445 MW) the model priced outside `[6, 25]`.

**(2) At a mixed facility it is not even the right technology's rate.** eGRID
keys one heat rate per PLANT, so **19 MISO CT_PEAKER plants / 1,651 MW (7.4 % of
class MW)** carried an eGRID rate **below 9.0** — a *combined-cycle* number on a
peaker. CAMPD's own `unitType` tag separates them decisively:

| plant | CAMPD unit tags | model (eGRID) | measured |
|---|---|---|---|
| Perryville 55620 | 1-1/1-2 `Combined cycle`, **2-1 `Combustion turbine`** | **6.890** | **10.774** |
| Zeeland 55087 | **CC1/CC2 `Combustion turbine`**, CC3/CC4 `Combined cycle` | **8.587** | **10.922** |
| Black Dog 1904 | CT unit 6 | 8.517 | 10.491 |
| Moselle 2070 | CT units 4, 5 | 8.892 | 12.144 |

At Zeeland the CAMPD `Combustion turbine` units sum to the model's 318.2 MW of
CT_PEAKER exactly, and the `Combined cycle` units to its CC_REGULAR — the
attribution is not inferred, it is read off the tag.

## 2. The artifact — MISO-derived, zero transferred, zero fitted

`data/raw/_processed-legacy/campd_ct_heat_rates_MISO.csv` (86 plant rows) +
`_units.csv` (250 unit rows), from
`scripts/data/derive_campd_ct_heat_rates.py --iso MISO --detail`. Method frozen
since nyiso-89 and **unchanged here**.

| | |
|---|---|
| coverage | **86 / 168** plants, **19,121 / 22,289 MW (85.8 %)**, ≈92–96 % of the class's real energy |
| excluded by the physical band | **0** |
| two-signed | **56 cheaper / 30 dearer**; 51 moved > 0.5, 32 > 1.0, 16 > 2.0 MMBtu/MWh |
| capacity-weighted | 12.290 → **11.868** (−3.4 %) |
| generation-weighted | 11.436 → **11.427** (−0.1 %) |

**Rule 25 `[R-ISO-SCOPE]`.** The same flag is a keeper in NYISO (nyiso-89) and
PJM (pjm-137). **Neither ISO's rates, coverage, or predicted direction crossed
the boundary.** MISO's artifact is built from MISO's CAMPD over MISO's 14 states
against MISO's own model fleet, and §3's prediction was built only from MISO's
numbers — which is what made it falsifiable, and what let it be falsified.

**Rule 21 `[R-DOF]`.** Ledger 26 entries, **2 residual — the same two as the
outgoing keeper.** Every derive threshold (loaded window 0.80 × p95, ≥ 50
qualifying hours, band `[6, 25]`) is frozen and none was chosen against a MISO
residual.

**Rule 19 `[R-ONE-MECH]`.** The only mechanism touching CT_PEAKER is the h14-21
`reliability_floor` — a *quantity* floor. This is a *cost* input on the same
class: nothing stacked, no floor added or widened, no window declared.

## 3. The mechanical prediction, and where it was wrong

PREREG §3 predicted the change is a **curve compression, not a level shift**,
and that held exactly:

* bottom-12 of the model's CT curve (1,982 MW, dispatched first) —
  capacity-weighted **+1.280 MMBtu/MWh, dearer**;
* top-8 (1,454 MW, real CF 0.064) — **−4.510, much cheaper**;
* roster p100 (2023) **$67.42 → $53.53**, p50 −$0.10.

**What the pre-registration got right:** CT_PEAKER volume falls in all three
years (15.325 → 14.140, 19.549 → 18.595, 18.929 → 17.746 TWh); D-1 cv_ratio
rises in all three; D-4 stays exactly 0.000; C3c unchanged; C3b worsens in 2025;
D-2 CT_PEAKER share rises; C3a moves less than 1.0 pp.

**What it got wrong, recorded as wrong.** PREREG §5 predicted C1 CT_PEAKER would
**improve** in 2024 and 2025, both of which sat *above* actual. The direction of
the volume change was right but the **magnitude was larger than assumed**, so
both **overshot past zero**:

| year | actual | arm A | arm B | |
|---|---|---|---|---|
| 2023 | 19.199 | 15.325 (−20.18 %) | 14.140 (**−26.35 %**) | worse — predicted |
| 2024 | 19.296 | 19.549 (+1.31 %) | 18.595 (**−3.63 %**) | worse — **predicted improvement** |
| 2025 | 18.425 | 18.929 (+2.73 %) | 17.746 (**−3.69 %**) | worse — **predicted improvement** |

All three stay far inside the ±8 TWh band, so C1 holds **PASS**. This is the
**second** ISO running of this flag whose pre-registration was refuted in
direction, after pjm-137's.

## 4. Result against every pre-registered gate

Against a same-HEAD flag-off control, **every criterion verdict is identical** —
9 scored / 6 target-grade / 2 ledgered / 1 fail in both arms.

| gate | arm A | arm B | vs PREREG |
|---|---|---|---|
| **C3b price shape (KILL GUARD, veto 0.20)** | 0.075 / 0.116 / 0.190 | 0.075 / 0.116 / **0.192** | direction predicted; **+0.002 only, PASS holds** with 0.008 headroom. Failure mode 1 did **not** fire |
| **C3a mean LMP** | −1.4 / −6.7 / −14.3 % | **−1.2 / −6.6 / −14.2 %** | improves in all 3; sign was explicitly *not* predicted, magnitude 0.2/0.1/0.1 pp inside the ≤1.0 pp bound |
| **C3c price tail** | 1 / 6 / 0 h | 1 / 6 / 0 h | **bit-identical**, as predicted |
| **C1 fuelmix** | PASS | PASS | no flip, as predicted (but see §3) |
| **C4 dispatch corr** | PASS | PASS | as predicted |
| **D-1 CT_PEAKER** | r 0.971/0.971/0.985, cv 0.979/0.848/0.805 | r 0.973/0.971/0.985, cv **1.222/0.931/1.046** | cv_ratio rises in all 3 as predicted; **toward 1.0 in 2024 and 2025**, overshoots in 2023 |
| **D-1 COAL_PRB** | FAIL 0.467/0.476/0.318 | FAIL 0.462/0.475/0.313 | **unchanged**, as predicted — MISO's blocker is independent of CT heat rates |
| **D-2 CT_PEAKER (cap 15 %)** | 11.77 / 8.39 / 8.78 % | **14.21 / 10.14 / 10.51 %** | rises as predicted; **stays under cap.** Failure mode 2 did **not** fire — 0.79 pp headroom in 2023 |
| **D-4 off-window** | 0.000 | **0.000** | exactly as predicted |
| **G1 flag fidelity** | `false` | `true` | PASS |
| **G2 liveness** | — | 766 / 920 / 1,354 MW class-hour | PASS |
| **G4 slack/dump** | — | no new load shed | PASS |

## 5. Four things move the wrong way, and it is promoted anyway

Per rules 1 and 14, an accurate input stays in even when the fit worsens, and a
worse fit is a discovered-bug signal — never something to offset with a tuned
adder.

1. **C1 CT_PEAKER |err| degrades in all three years** (§3), against a
   pre-registration that predicted two improvements.
2. **D-2 CT_PEAKER forced share rises 11.77 → 14.21 %**, and the forced
   **energy** rises **1.188 → 1.743 TWh (+47 %)**. This is the most interesting
   result in the session and it is *not* a denominator artifact: correctly-priced
   peakers want to run **less**, so the h14-21 `reliability_floor` binds
   **harder** — it is now holding up capacity the corrected economics would shut
   off. **Recorded as an open item.** It must not be closed by relaxing the
   floor or by reverting the input; it is evidence about the floor, which is
   exactly what rule 14 says a worse number after an accurate input means.
3. **C3b-2025 worsens 0.190 → 0.192.** Pre-registered as the mechanism's
   expected cost (it removes the top of the CT curve, and MISO's diagnosed
   defect is diurnal spread compression, miso-89). The gate holds.
4. **Zeeland's CTs genuinely run hard** — 4.45 TWh of CAMPD gross over
   2023–2025, CF 0.532 — and pricing them ~$6–8/MWh dearer cuts their model run
   hours against an actual that says they run. Rule 14's named scenario; the
   accurate input stays and the root cause is left open.

## 6. The control is a bounded noise floor, not a bit-equality — G3 FAILED

**G3 as pre-registered failed and is recorded as a fail.** The PREREG required
arm A to reproduce the committed keeper at `max |Δ| < 1e-6 MW` on every
class-hour; it lands at **912.5 MW**, on 2.4–2.7 % of class-hours.

**The threshold was mis-specified, not the run.** It was written without first
checking main's drift from the keeper's code basis, and main has moved **21
files / 1,312 insertions under `src/market_sim/`** since `8501baa`
(`model/lp/costs.py`, `model/lp/model.py`, `pipeline/year.py`, `runner.py`,
`data/loss_surface.py` among them). Bit-identity to a bundle built on older code
was never obtainable by this session.

What the control **does** establish, measured rather than asserted:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| total generation vs keeper | **+0.000000 %** | **+0.000000 %** | **+0.000000 %** |
| load-weighted mean LMP | $32.4081 vs $32.4083 | $30.1016 vs $30.1015 | $38.9151 vs $38.9151 |
| worst per-class **annual** divergence | 0.00381 % | **0.00630 %** | 0.00000 % |

The 912.5 MW maxima are alternate-optima reallocation: 2025 nets to ±0.01 MWh on
**every** class across the whole year, hydro nets to exactly 0.00 in all three
years over 1,536–1,770 hours (energy-budgeted, so intra-budget shuffling is
costless), and the largest delta sits on `import`, served by 32 equally-priced
tranches.

**Consequence, stated as a limit:** the A/B attribution carries a **0.00630 %
per-class-year noise floor** rather than zero. Every movement claimed in §4 is
orders of magnitude above it (class-hour max |Δ| between arms 766/920/1,354 MW;
annual class moves ~1 TWh). **Lesson for successors: check `git diff <keeper
basis>..HEAD -- src/market_sim/` before pre-registering a bit-equality control.**

## 7. Execution notes

* **A single-process three-year solve was OOM-killed** at 15.9 GB anon-rss on a
  15 GB box, after 2023 and 2024 had both solved. Both arms were rebuilt **one
  fresh year per process**, chained with `--reuse-solved` into one 2023–2025
  bundle (rules 12/16) — the same remedy miso-96 and miso-98 used. Every year in
  both bundles was freshly solved in this session.
* `--reuse-solved` carries `dispatch/` forward but **not** the derived
  `hourly/class_hourly_*.parquet` sidecars. Those were regenerated for the
  reused years by the same groupby the solver uses, **verified first by
  reproducing the solver's own 2025 sidecar exactly** (148,920 rows, max |Δ|
  0.0). *This is a real gap in the reuse path and a candidate fix: the reuse
  branch should regenerate the sidecars itself.*
* Rule 22: 2023–2025 only, no holdout year solved, scored or registered; MISO
  carries no calibration-complete marker.

## 8. What this leaves open for MISO

1. **The reliability-floor signal (§5.2)** — new, and the best-identified item
   this session produced. The h14-21 CT_PEAKER floor now forces 1.743 TWh. Its
   driver and window are D-4 clean, so this is not a legitimacy failure; it is a
   question about whether the floor's *level* was implicitly absorbing a
   mispriced fleet.
2. Queue items **5** (`dual_fuel_switching`) and **6**
   (`hydro_budget_nameplate_aware` + the `NG: PS` pin audit) are untouched.
3. C7 COAL_PRB remains MISO's determination blocker, confirmed independent of CT
   heat rates.
