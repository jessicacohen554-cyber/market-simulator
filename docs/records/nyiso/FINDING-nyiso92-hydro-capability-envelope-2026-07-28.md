# FINDING nyiso-92 — per-class hourly r decomposition, and the hydro capability envelope (2026-07-28)

**Session charter (owner, 2026-07-28):** "Scarcity hours are the issue for C3c
calibration but the hourly r for each asset class is pretty abysmal too… dig in
and figure out how to resolve NYISO with better dispatch matching."

**Keeper at session start:** `2026-07-27-nyiso-89-ctmeas-hrloaded` (C3c sole
blocking criterion, 3/0/7 h >$300 vs actual 10/12/42).

**Probe script (the characterization record):**
`scripts/probes/nyiso92_hourly_r_decomposition.py`.

---

## 1. Where the hourly r actually goes — the decomposition

Per class, per year, model-vs-CAMPD-bench correlation at four layers (hourly,
day-energy, hour-of-day profile, within-day residual), on the keeper's own
committed `hourly/` sidecars:

| class | 2023 r_hr | 2024 r_hr | 2025 r_hr | r_day (23/24/25) | profile r |
|---|---|---|---|---|---|
| CC_REGULAR | 0.705 | 0.583 | 0.536 | 0.742 / 0.566 / 0.534 | 0.95–0.98 |
| CC_CHP | 0.728 | 0.700 | 0.647 | 0.778 / 0.734 / 0.667 | 0.91–0.96 |
| ST_GAS | 0.831 | 0.876 | 0.827 | 0.834 / 0.896 / 0.846 | 0.95–0.96 |
| CT_PEAKER | 0.681 | 0.664 | 0.600 | 0.756 / 0.735 / 0.578 | 0.90–0.96 |
| CT_CHP | −0.070 | 0.293 | 0.251 | −0.11 / 0.33 / 0.30 | 0.16–0.24 |
| ST_CHP | 0.496 | 0.474 | 0.364 | 0.57 / 0.56 / 0.41 | 0.10–0.24 |
| **TOTAL fossil** | **0.861** | **0.836** | **0.788** | 0.878 / 0.840 / 0.787 | 0.96 |

Three structural facts fall out:

1. **The loss is day-to-day, not diurnal.** Every material class's
   hour-of-day profile r is ≥0.90 (the D-1 gate statistic — C7 passes), while
   the daily-energy layer carries the whole degradation. The model knows *what
   a day looks like*; it mis-picks *which days*.
2. **The driver is common, not merit-order shuffling.** Total-fossil hourly r
   (0.79–0.86) sits far above every class's own r, and the hourly residual
   cross-correlations between gas classes are predominantly POSITIVE
   (CC_REGULAR×CC_CHP +0.29/+0.32/+0.35) — the gas classes are wrong
   *together*, which indicts a common non-fossil component, not the offer
   stack. (CT_CHP/ST_CHP, the two sub-materiality CHP classes, are the known
   multi-class-plant bench-attribution lane — nyiso-88 §5 — and are excluded
   from conclusions here.)
3. **The day-picking failure is seasonal: winter.** DJF daily r collapses for
   every gas class (2024 CC_REGULAR 0.163, 2025 CC_CHP 0.025) while JJA holds
   0.70–0.93.

## 2. Component attribution — hydro is the largest mistracking input

Model components vs the measured EIA-930 series, daily-energy r:

| component | TWh (2023/24/25 model) | r_day 2023 | r_day 2024 | r_day 2025 |
|---|---|---|---|---|
| demand | 147.0 / 150.5 / 151.6 | 1.000 | 1.000 | 1.000 |
| wind | 4.6 / 6.0 / 7.0 | 1.000 | 0.999 | 1.000 |
| gas (total) | 57.8 / 63.2 / 68.6 | 0.887 | 0.842 | 0.788 |
| nuclear | 27.5 / 27.0 / 28.4 | 0.839 | 0.504 | 0.511 |
| import | 23.8 / 20.7 / 19.4 | 0.710 | 0.720 | 0.568 |
| **hydro** | 28.4 / 27.9 / 21.1 | **0.353** | **0.405** | **0.190** |

**Hydro is the worst-tracking material component in the model, on 21–28 TWh
(~18 % of load), and it carries the exact CAISO parks-at-zero signature** the
caiso-124/126 keepers closed:

* model hours <100 MW: **349 / 405 / 1,098** vs measured **0 / 15 / 15**;
* model hourly p5: **274 / 151 / 0 MW** vs measured **2,072 / 1,969 / 1,526**;
* model day-to-day energy std: **21–23 GWh** vs measured **6–8 GWh** (the
  budget LP's perfect-foresight hoarding swings the fleet ~3× harder day to
  day than water physically allows).

Nuclear day-tracking (0.50 in 2024–25, refuel/outage timing;
`nuclear_unit_availability` matrix cell N=U) and the import hourly shape
(r_hr 0.40–0.49, the nyiso-86 §3 open item) are the next two components; both
are named follow-ups, not this session's arm.

### The cold-snap gas↔oil swaps are a recording artifact, not dispatch

The worst single days (2023-02-02, 2024-01-15/16, 2025-01-17/19/12-12) show
model gas −110…−220 GWh/day with model oil +90…+150 — but this is the
dual-fuel parity switch **relabeling** capped gas unit-hours as oil
(`dual_fuel_oil_reattribution`, armed in the keeper lineage) against a
measured feed (NYIS) that does NOT track switching (Jan-2025: 0.80 TWh
relabelled vs 0.031 TWh measured `NG: OIL`). The calibration CLI has since
pinned the re-attribution NEISO-only, so a fresh NYISO solve no longer
carries the mismatch; the keeper-lineage meta.json (and hence both nyiso-92
bundles, which replay it) still records it. Net dispatch distortion on those
days is far smaller than the labels suggested. The 2023 measured 2.17 TWh
`NG: OIL` (Jan–Jun, vs 0.42 TWh EIA-923 oil class) is a static
plant-primary-fuel attribution artifact of the feed — do not chase it.

## 3. C3c re-anchored: the tail is mostly SUMMER, not the cold snaps

Dated actual RT hours >$300 (`actual_lmp_hourly_NYISO.parquet`, the committed
tail basis):

* **2023 (10 h):** scattered singles — Jan 11, Feb 3, Jun 1, Aug 11, Sep 5–7
  (4 h), Oct 10/26.
* **2024 (12 h):** Apr 28 (2), then **summer** — Jun 17, Jul 6/7/14/15/29/31
  (7 h), Dec 1/26. Winter Storm Gerri (Jan 2024): **zero** hours >$300.
* **2025 (42 h):** Jan 6/21/22 + Feb 19 (5 h winter); **Jun 23–25 = 18 h**
  (the heat emergency), July 15 h, Aug 10 2 h, Oct 2 h.

Model max-zonal price in exactly those hours: 2024 median $119 / max $202
(never above $300); 2025 median $208 / p90 $366. The blocked mass is
summer-evening RT scarcity, which the queue's lever #1 (DA
virtual depth, `pjm_da_virtual_bids` form) targets — consistent with the
nyiso-85 §7d roof diagnosis. The winter-fuel lane is NOT the C3c unlock;
at most ~4–5 h/yr (2025) are winter hours.

## 4. The nyiso-92 arm — measured two-sided hydro capability envelope

**Mechanisms (one family, zero new DOF):** `hydro_dispatch_envelope` (p95
month×hour-of-day ceiling, measured EIA-930 NYIS `NG: WAT`) +
`hydro_min_flow_floor` (Q95 month-constant floor, the ceiling percentile's
mirror — constants.HYDRO_MIN_FLOW_PERCENTILE). Both are the CAISO keeper's
engines (caiso-72/124), ISO-generic, matrix cells N=U (untested transfer,
rule 25: the NYISO levels derive from NYISO's own measured series at solve
time — nothing crosses the boundary).

* Driver (rule 17a): run-of-river inflow + FERC/treaty minimum releases
  below; head/flow/scheduling deliverability above. NYISO's fleet is
  *dominated* by two RoR-class projects (Robert Moses Niagara 2,429 MW +
  St-Lawrence 912 MW = 72 % of fleet MW), so the pure budget LP's freedom to
  park at 0 and hoard into peaks is maximally wrong here.
* Window (rule 17b): all 24 h (inflow is around-the-clock); the floor is
  month-constant so no diurnal shape is pinned; the ceiling binds only where
  the LP would exceed measured deliverability.
* Forward story (rule 17c): both levels re-derive from the same EIA-930
  history (solve-year series in backcast, pooled climatology forward) and
  scale with the water year through the budget.
* Levels measured at solve time: floor 1,844–2,496 (2023) / 1,733–2,537
  (2024) / 1,315–2,292 (2025) MW by month — 66 % of the 28.4 TWh 2023 budget
  (vs CAISO's 36–46 %: a mostly-RoR fleet keeps most of its energy in the
  sustained base, which is the point); ceiling evening p95 ~4.4 GW.
* **Rule 19 reconciliation:** `NYISO_HYDRO_TREATY_MIN_FLOW` (constants.py,
  Niagara 0.25 / St-Lawrence 0.50 nameplate fractions) is DEAD in the
  production path — only tests pass it to `load_hydro_budget`
  (`per_plant_min_flow`); no orchestrator does. The Q95 floor becomes the
  single live floor on conventional hydro; the treaty registry remains the
  audit cross-check (fleet Q95 1.8–2.5 GW comfortably covers the ~1.06 GW
  treaty-implied minimum on the two plants, so the licence evidence is
  subsumed, not contradicted).

**Deliberately NOT armed: `hydro_ror_split`.** The classifier's completion
rule was reviewed on CAISO only, and its rule-1 hybrid mapping
("Run-of-river/Peaking" → NOT shapeable → flat at monthly water) would bind
Robert Moses Niagara — 52 % of NYISO hydro MW — whose real diurnal pattern is
*treaty-structured* (the 1950 Niagara Treaty scenic-flow schedule concentrates
divertible water in nights/off-season), i.e. neither flat nor price-chasing.
Flattening it would erase a real, externally-driven diurnal shape. The
measured month×hod envelope already carries that treaty structure (it is in
the measured series). NYISO's `hydro_ror_split` therefore stays U pending its
own classifier review with the Niagara hybrid question answered from the
treaty schedule; this is a named follow-up.

**Bundles (both replay the keeper-lineage recipe, same HEAD, years
2023–2025 sequential, one delta):**

* control `results/calibration/nyiso92_ctrl_zerodelta` — zero-delta.
* arm `results/calibration/nyiso92_hydro_envfloor` — + the two hydro fields.

**Pre-registered judgment frame (written before the solves returned):**

* Success is STRUCTURAL: hydro parks-at-zero hours → ~0, day-to-day std
  toward measured, hydro r up; the gas classes' daily/hourly r should move up
  as the common driver shrinks. The arm is NOT judged on C3c or MAE (rule 1).
* Watch honestly: the C1 2023 CC_REGULAR knife edge (−2.784 of ±2.94, 0.156
  TWh headroom) — hydro re-timing can move it either way; C5a 2025 CO2
  (+7.6 % caveat) — if the envelope's feasibility guard sheds hydro energy to
  gas, CO2 moves; report both regardless of direction.
* Exact-equality check first (nyiso-89 §4a lesson): the arm must NOT be
  byte-identical to the control.

## 5. Results

**Exact-equality check:** the arm is NOT byte-identical to the control (class
energies move up to 0.44 TWh; the control reproduces nyiso-91's control
exactly — 2023 CC_REGULAR 32.513, CT_PEAKER 0.443/0.394/1.407 — so no HEAD
drift entered the A/B).

**The hydro pathology is eliminated** (arm, per year 2023/2024/2025):

| statistic | control | arm | measured |
|---|---|---|---|
| hours <100 MW | 349 / 405 / 1,098 | **0 / 0 / 0** | 0 / 15 / 15 |
| hourly p5 (MW) | 274 / 151 / 0 | **2,100 / 1,852 / 1,376** | 2,072 / 1,969 / 1,526 |
| day-to-day std (GWh) | 20.9 / 23.4 / 22.8 | **8.4 / 11.3 / 11.5** | 6.2 / 8.4 / 7.9 |
| hydro r_day | 0.353 / 0.405 / 0.190 | **0.517 / 0.701 / 0.328** | — |
| hydro r_hr | 0.594 / 0.549 / 0.381 | **0.741 / 0.778 / 0.552** | — |

**Every material gas class's hourly r improves in every year:**

| class (r_hr 23/24/25) | control | arm |
|---|---|---|
| CC_REGULAR | 0.705 / 0.583 / 0.536 | **0.770 / 0.652 / 0.573** |
| CC_CHP | 0.728 / 0.700 / 0.647 | **0.790 / 0.781 / 0.676** |
| ST_GAS | 0.831 / 0.876 / 0.827 | **0.852 / 0.893 / 0.839** |
| CT_PEAKER | 0.681 / 0.664 / 0.600 | 0.688 / 0.644 / 0.612 |
| TOTAL fossil | 0.861 / 0.836 / 0.788 | **0.915 / 0.896 / 0.819** |

Winter day-picking recovers where the collapse was measured (2023 CC_CHP DJF
daily r 0.557 → 0.701; 2024 CC_REGULAR MAM 0.533 → 0.704; 2025 CC_REGULAR JJA
0.874 → 0.905), and the measured import series' hourly r rises
0.477/0.493/0.396 → 0.587/0.612/0.454 under a mechanism that touches no seam
wiring — the import defect was partly hydro-shape leaking through the
interchange reconciliation. Honest adverse cells: CT_PEAKER 2024 r_hr
0.664 → 0.644 (r_day 0.735 → 0.668); C7 CT_PEAKER 2025 off-peak cv_ratio
0.934 → 0.797 (ungated — class under the 2 % materiality floor). Class
energies move <0.5 TWh: this is a re-timing, not a level change.

**Gates (arm vs control, `calibration_verdict.py`):**

* C2 / C3a / C3b / C4 / C7 / C8 PASS both; C8 2024 ST_GAS forced share
  IMPROVES 32.0 % → 30.9 % (still grounded above budget). C6 PASS on the
  UNION'd 20-entry DOF ledger (nyiso-89's 19 + `hydro_capability_envelope`,
  measured, zero fitted scalars — n_residual stays 6).
* **C1 regresses exactly where pre-registered:** 2023 CC_REGULAR
  −2.784 → −3.045 TWh of ±2.94, FAIL by 0.105 TWh (13/14, free 9/10). The
  control's PASS rested on ~0.26 TWh of phantom overnight CC dispatch that
  existed only because hydro could park at 0 MW — dispatch the measured
  fleet never produces. Rule 14: the accurate input reveals the true
  downstate CC deficit (CC_REGULAR −3.0 + pinned CC_CHP −4.6 TWh vs bench in
  2023, the nyiso-81 "downstate ST/CC mix boundary" item); re-burying it
  under the false hydro structure is forbidden.
* **C3c UNCHANGED at 3/0/7 h vs 10/12/42** — the sole prior blocker is not
  degraded, and §3 dates the missing mass to summer RT scarcity (the DA
  virtual-depth lane), not to anything hydro touches.

**Verdict: KEEPER (promoted in-session on the owner's standing rule —
"if structural integrity improves but gates regress that may still be a
keeper").** `2026-07-28-nyiso-92-hydro-envelope` replaces
`2026-07-27-nyiso-89-ctmeas-hrloaded`; determination NOT-YET, same class and
same sole blocker (C3c). LOYO (rule 22): the mechanism carries no parameter
fitted to any year — each year's bounds derive from that year's own measured
series and the one percentile is the pre-existing cross-ISO constant; all
three years scored in this bundle, direction consistent in each. Keeper
auditor: 0 failures. Matrix: `hydro_dispatch_envelope` /
`hydro_min_flow_floor` N → K; `hydro_ror_split` N stays U behind the Niagara
classifier review.

**Named follow-ups (queued, matrix §5.5):** `nuclear_unit_availability`
NYISO derivation (r_day 0.50 in 2024–25 on 26–28 TWh); the `hydro_ror_split`
NYISO classifier review (Niagara hybrid label vs the treaty schedule); the
import hourly shape (nyiso-86 §3, improved but ungated); dropping
`dual_fuel_oil_reattribution` from the NYISO keeper-lineage metas (recording
basis, zero dispatch delta); and the C3c DA-virtual-depth build, now the only
queue item aimed at where the measured tail actually lives.
