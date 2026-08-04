# PRECOMMIT — ERCOT-162: `ercot_storage_rt_offer_surface` arming test (the measured multi-tranche battery RT discharge-offer surface) + fresh same-HEAD control replay

**Date** 2026-08-04 · **ISO** ERCOT · pushed BEFORE any solve (rule-15 /
ercot145b protocol; the ERCOT-148/149/158 template). **Owner authorization:**
the ercot-162 session prompt is the owner's authorization the ercot-161 charter
(queue item 9b) required for this structural LP change (the ercot-159 item-9
precedent for a structural arm). Basis keeper `2026-08-03-ercot158-pool-arm`
(bundle `results/calibration/ercot158_poolarm_B`, determination NOT-YET, fail
set {C3a 2023-only −32.8%, C3b 2023-only, C3c, C7 2023-lignite cv-leg}, C1
16/16 all-class / 12/12 free-class, C6 ATTESTED+PASS). Charter:
`results/calibration/FINDING-ercot161-afternoon-wall-phase0-2026-08-04.md`
§4; mechanism-matrix §5.1 item 9/9b. Phase A (identification, this session):
`scripts/data/derive_ercot_storage_rt_offer_surface.py` →
`data/raw/_validation-source/ercot_storage_rt_offer_condbinned.json`.

## 0. Scope fence (DO-NOT-REDO, rule 28(a))

Per the ercot-162 prompt, this session does **NOT** re-open: ERCOT-159's
`energy_online_capability_cap` (R); the ercot41/43/106/108 envelope family;
`ercot_shoulder_online_span`; the West/Panhandle topology split;
`ercot_ordc_only_scarcity`; or the offer LEVEL program (the gas walls are
EXONERATED, not re-tunable — FINDING §2). The ERCOT-155 offer-dispersion
refusal (cold capacity) stands; this surface prices ONLINE telemetered
capability at its own submitted curve. The CT item-8(b) licensing blocker is
documented NOT binding on this successor (FINDING §1 Q3). The incumbent
`battery_dispatch_adder` = $10 stays on PS and every non-ERCOT ISO. Governance:
2023–2025 only (rule 22); ERCOT-scoped (rule 25). Solves need only the
committed condbinned JSON — never the raw NP3-965 shards (rule 23).

**The three ERCOT-154 DO-NOT-REDO items are honoured**: the arm is **NOT**
single-price (K=3 tranches per unit), **NOT** gas-multiple-based (absolute $ —
ERCOT-154 refuted the gas basis for storage), and **NO rung is selected on the
model's absorption** (K, the quantile set, and the widths are fixed A PRIORI in
the Phase-A derive, blind to any solve; §3 below).

## 1. The two runs (rule 16 full-span, rule 12 SEQUENTIAL invocations)

Both are `scripts/replay_keeper.py` replays of the keeper bundle's meta.json
recipe, full span `--year 2023 2024 2025`. **The box is 15 GB and each
plant-level ERCOT-year LP is ~10 GB RSS, so the rule-12 concurrency cap binds
at 1**: the two invocations run **SEQUENTIALLY** (control first, then arm),
years sequential within each (never in parallel). Both write to their own
`--out-dir`; both are NEW dated runs, never the keeper fixed in place.

* **Run A — control, fresh same-HEAD replay** (the ercot150-K2 lesson: the
  control is a fresh same-HEAD re-solve, **never the committed keeper bundle**,
  so the A/B is unconfounded by any regenerated-input drift — that drift
  cancels A→B):

  ```
  python scripts/replay_keeper.py results/calibration/ercot158_poolarm_B \
    --out-dir results/calibration/ercot162_control_A \
    --year 2023 2024 2025 \
    --note "ERCOT-162 Run A: fresh same-HEAD replay of the ercot158 keeper \
  config (UNCHANGED); A/B control for the storage RT offer surface arm."
  ```

* **Run B — the arm, single delta on the same config:**

  ```
  python scripts/replay_keeper.py results/calibration/ercot158_poolarm_B \
    --out-dir results/calibration/ercot162_stormarm_B \
    --year 2023 2024 2025 \
    --set ercot_storage_rt_offer_surface=true \
    --note "ERCOT-162 Run B: single delta off the ercot158 keeper config — \
  ercot_storage_rt_offer_surface=true (measured multi-tranche battery RT \
  discharge-offer surface); A/B vs ercot162_control_A."
  ```

  `--set ercot_storage_rt_offer_surface=true` routes through the generic
  prb_overrides ScenarioConfig channel (no solve kwarg of that name exists, so
  no kwarg-over-prb re-stomp exposure — the ERCOT-65 defect class does not
  apply). The wiring engages ERCOT + backcast only
  (`run_calibration.py::run_year`).

## 2. Mechanism statement (what `ercot_storage_rt_offer_surface=true` does)

Splits each ERCOT battery unit's single ENERGY-side discharge column into **K=3
priced tranches `Dis[s,k,t]`** sharing the unit's SOC pool and power cap, priced
at the measured per-net-load-bin absolute-$ SCED discharge-offer ladder:

* **Object**: the measured PWRSTR above-LSL, HASL-capped SCED2 discharge-offer
  segments (ONTEST excluded; ON/ONREG/ONFFRRRS in), MW-weighted absolute-$
  quantile ladder per net-load bin (Phase-A derive). The **HASL cap makes this
  rule-19 clean**: HASL is HSL net of the resource's AS responsibility, so the
  ladder prices ONLY the energy headroom the telemetered AS stack leaves to
  energy. Apply-time hours are binned by the SOLVE's own net-load percentile on
  the shared `NETLOAD_PCT_EDGES` — the RT/DAM wall convention, forward-native.
* **LP construction (a piecewise-cost decomposition on the base column)**: a new
  equality row `Dis[s,t] − Σ_k DisT[a,k,t] = 0` per armed battery-hour
  (`model/lp/rows.py::_build_dis_tranche_rows`) ties each armed battery's total
  discharge to its tranche columns. **The base `Dis[s,t]` column keeps its
  EXACT total-discharge meaning** — energy balance, SOC dynamics, the power cap,
  and the measured AS→energy deployment floor (`ercot_storage_as_deployment`,
  armed on the keeper) all ride the base column unchanged; the tranches only
  carry the rising price ladder. Each tranche `DisT[a,k,t]` is bounded above by
  `width_frac[k] × power_cap[s,t]` (fractions 0.10/0.20/0.70), and the LP fills
  cheapest-first, so the marginal cost of the last discharged MW follows the
  ladder. The reported `storage_discharge` output stays the base column = the
  TOTAL discharge (so the EIA-930 volume guard reads it correctly).
* **REPLACE (rule 19 [R-ONE-MECH])**: on an ARMED battery the measured tranche
  ladder REPLACES the flat `battery_dispatch_adder` ($10) — the armed base
  discharge column drops its $10 vom (keeping only the ε tiebreaker), and every
  tranche carries its own $/MWh rung. **PS + every other ISO untouched**
  (rule 25). The AS-side storage capability keeps its own co-opt owners
  (`storage_as_commitment` reserves the measured award from the power cap
  BEFORE the LP, so the tranche widths apply to the AS-net energy cap); this
  surface prices the ENERGY-side discharge only. Guarded
  mutually-exclusive with the endogenous storage-AS duration gate (off on the
  keeper).
* **The natural arbitrage dual**: at a battery-marginal hour the energy-balance
  price = the tranche offer + the battery's charge-energy replacement cost. In
  the real gap hours ERCOT batteries charge in cheap solar hours (~$0), so the
  clearing ≈ the tranche ≈ the p30 rung ($1,500 in 2023) — the FINDING's target
  λ $1,470. The tranche prices ($40+) exceed mid-band thermal, so the battery
  is NOT marginal in the mid-band and mid-band prices are untouched (the
  structural basis of the zero-spurious expectation; §4 gate 2).
* **An offer, NEVER a floor**: no `min_gen` is touched — the tranche columns are
  a cost decomposition, not a forced quantity — so **D-2/D-4 exposure is vacuous
  by construction** and the rule-17 floor hazard is structurally impossible.
* **Year-scoped, zero fitted scalars** (rules 13/23): no cross-year pooled
  fallback; each year uses its own measured ladder; a year absent gets NO
  surface (the flat adder is retained). The artifact is frozen against
  residuals.

## 3. Identification disclosure (Phase A, blind to any solve — rule 1 / the ercot-159 precommit discipline)

**K, the quantile set, and the widths were fixed A PRIORI**, before any 2024/25
block or any solve was seen: K=3 tranches, cumulative-power-fraction edges
0.10/0.30, widths 0.10/0.20/0.70, RIGHT-edge prices Q(0.10)/Q(0.30)/Q(0.99).
The LEFT-edge (lower-bound) variant is computed and DISCLOSED in the artifact
but NOT used. The derive reproduces the ercot-161 census to the cent (2023
gap-hours 0.711 GW offered / 0.556 GW ≥$500; status ON 56.4% / ONTEST 26.0% /
ONREG 16.0% / ONFFRRRS 1.56%).

**Year-pair rung stability, DISCLOSED (the live question):**

* **The p10 toe is STABLE across 2023/2024/2025** ($24–60 in every bin — the
  ERCOT-154 p30-toe stability precedent, here at p10).
* **p30/p50 are NOT year-stable, and this is a genuine finding, not a defect.**
  2023 (full delivery corpus) is HCAP-degenerate — p50=$5,000 in ALL SEVEN
  bins, the standing hockey stick the FINDING measured (the small ~1 GW 2023
  fleet held out at the cap). The 6×-larger 2024/2025 fleets (sample-day
  extracts) collapse to p50=$91–230 and p30=$60–81 — a **fleet-saturation
  regime shift**: as the BESS fleet grew ~6×, the median offer fell from the cap
  to competitive levels. **The top tranche Q(0.99)=$5,000 in ALL years.**
* **Year-scoping is exactly what handles this** (rule 13): each year's arm uses
  that year's own measured ladder, so 2023 gets the hot ladder (top tranche
  $5,000 over 70% of capability) and 2024/2025 get cold ladders (p30 ~$70, top
  $5,000). The forward-story caveat is honest: the "standing conduct" premise of
  the FINDING §4 holds ACROSS BINS within a year but NOT across years; the
  backcast is faithful per-year and the arm is backcast-only.
* **Named grain risk (stated before any solve)**: the RIGHT-edge top tranche
  Q(0.99)=$5,000 over 70% width is FAITHFUL for 2023 (the curve genuinely tops
  at the cap for p50–p99) but AGGRESSIVE for 2024/2025 (where the top 70% is
  really $80→$5,000 rising). The gates below (zero-spurious, new-tail-outside-
  actual, matched-hour C3c) are what adjudicate whether the 2024/2025 aggressive
  top tranche creates spurious tail (→ R) or stays inert because the crossing
  rarely reaches $5,000 in 2024/2025 mid-band (→ absorbed harmlessly).

## 4. Pre-declared gates (scored Run A → Run B, per year, no exceptions)

Standard analyzer: `scripts/probes/_ercot89_span_check.py`
(`--base results/calibration/ercot162_control_A --probe
results/calibration/ercot162_stormarm_B --years 2023 2024 2025`). Plus the
storage-specific scorer `scripts/probes/_ercot162_storage_ab.py` (written this
session, read-only over the two bundles' `system_<year>` / `storage_<year>`
sidecars + the committed gap-hour set + the EIA-930 series; solves nothing).

| gate | definition (per year, each of 2023/2024/2025) | kill condition |
|---|---|---|
| **C3a level guard** | annual demand-weighted resid: \|resid_B\| ≤ \|resid_A\| + 1.0 pp | any year DEGRADED |
| **Zero-spurious mid-band** | Δ(hours model ∈ [$150,$500] & actual < $150) ≤ 0 | any year TRIPPED |
| **Tail-not-away** | \|h>$200_B − h>$200_actual\| ≤ \|h>$200_A − h>$200_actual\| | any year moves AWAY |
| **NRMSE (C3b proxy)** | NRMSE_B ≤ NRMSE_A + 0.005 | any year DEGRADED |

Plus, pre-committed this session:

* **New-tail-outside-actual KILL** — scored on the 2023 matched-hour set: every
  NEW 2023 model >$300 hour under Run B (a model >$300 hour that was ≤$300 under
  Run A) MUST lie inside the actual >$300 set. Any fabricated tail hour on a
  quiet day (actual ≤$300) is a KILL regardless of the aggregate gates (the
  ercot-158 33-fabricated-tail-kill discipline).
* **Matched-hour C3c on the control's own prices** — on the 100-hour gap set
  (`_ercot161_wall_phase0.json`, the FINDING top-100: control model mean
  **$441.27**, target λ **$1,470.16**) and the Phase-0 144 actual >$300 hours:
  report Run A → Run B model load-weighted mean/median at the gap set and the
  missed/hit split (re-derived on Run A's own prices for exactness). The
  headline object is the gap-hour lift toward λ; a K verdict wants the arm to
  move the gap-set mean UP toward $1,470 without tripping any kill.
* **2025 EIA-930 NG:BAT storage-volume guard** (the ERCOT-154 ground-(c)
  recurrence test; 2025 is the only full-series year): Run B's 2025 model
  battery discharge vs the measured EIA-930 `NG: BAT` annual volume (ERCOT-154
  measured 5,444.8 GWh, control model 4,483.3 GWh = −17.7%). The arm re-prices
  discharge (it does not add a floor), so **the guard KILLS only if Run B drives
  the 2025 discharge MATERIALLY FURTHER from the measured volume than Run A**
  (a withholding regression) — SOC re-optimisation moving the same energy toward
  the same scarce hours is admissible; a large volume collapse (the ERCOT-154
  ground-(c) failure mode, where the arm withholds ~90% of the fleet) is the
  kill. Threshold: Run B 2025 discharge must not fall below Run A's by more than
  5% of the measured 5,444.8 GWh (272 GWh).
* **Scorecard holds (vs Run A statuses)**: C1 16/16 (12/12 free), C2, C4, C8
  PASS held; C3b/C7 2024/2025 legs held; the standing 2023 fail set {C3a, C3b,
  C3c} may only improve or hold.
* **D-2/D-4 zero-forced-energy**: `legitimacy_diagnostics.json` for Run B must
  show NO new forcing mechanism id and forced-share rows unchanged vs Run A —
  the surface is an offer, never a floor; any forced energy attributed to it is
  a structural bug and a kill.
* **DOF/C6**: n_residual MUST NOT rise (zero fitted parameters added; the ladder
  and widths are measured/a-priori, rule-23 frozen).

**LOYO (rule 24):** zero fitted parameters ⇒ structurally LOYO-exempt per the
ercot145b/148/149/150/158 precedent, with the per-year guard table standing in:
all three years' gates must clear **independently** — a 2023 gain bought with a
2024/2025 guard trip (the aggressive-top-tranche risk of §3) is
overfitting-shaped and REJECTS the arm. No parameter exists to re-fit; the
frozen artifact is not re-swept against any residual of this A/B (rules 1/11/23).

## 5. Decision rule and registration (pre-declared)

* **K (keeper candidate)**: the 100-hour gap-set model mean moves materially UP
  toward λ $1,470.16 (the owner-priority residual), all §4 gates hold all three
  years, the 2025 volume guard holds → recommend and, under the owner's standing
  standard ("if structural integrity improves but gates regress that may still
  be a keeper"), promote via the keeper lane (`keepers/ERCOT.json` +
  `build_status.py --iso ERCOT` + `calibration-keeper-auditor --iso ERCOT` +
  matrix header re-stamp + §5.1 re-check). ERCOT holds no `complete` marker, so
  no `calibration-complete.json` re-key duty.
* **R (rejected)**: any §4 kill fires → mechanism stays merged default-off,
  matrix cell `R` with this doc + both bundles as evidence. The pre-declared R
  branch: **ordinary-hour lift** — if the arm lifts the 163 ordinary bin-6 hours
  ERCOT cleared at $76 p50, the standing-conduct premise mis-transfers into the
  LP and the arm is R on the zero-spurious gate.
* **I (inert)**: gates hold but the gap-set movement is not material → matrix
  cell `I`. The pre-declared I branch (FINDING §4): **the crossing never reaches
  the tranches** — if the thermal stack absorbs the withdrawn ~0.65 GW below
  $500 so the LP never crosses into the storage tranches, the arm is INERT and
  the residual object moves to the quantity side (the AS/energy split of storage
  capability at scarcity).
* **Either way**: BOTH runs are registered on the backcast dashboard in this
  session (rule 15 — bundle + sidecar + run payload committed and pushed via the
  `calibration-report` skill; retention top-15), the
  `ercot_storage_rt_offer_surface` matrix cell is stamped with the tested
  verdict + citation in the same session (rule 28(b)), and both runs are logged
  in `docs/calibration-log/ercot.md` as ercot-162.

## 6. Open owner rulings carried (surfaced, not decided)

Unchanged from the ercot158 keeper note: (9) the DAM deriver `_site()`
cross-train collapse + gas crosswalk partial acceptance; (10) the pin
remove-direction over-removal; the standing (8) rating-basis gap; the CC
econ-band under-dispatch (ERCOT-138/139) and the coal loading-conduct under-run
(ERCOT-126) — none of which this storage-energy arm touches.
