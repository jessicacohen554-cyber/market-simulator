# CAISO CT-Drag D-8 Closure — Design (2026-07-06, Lane L-10, G-15)

**Status: EXECUTED 2026-07-06 (L-10 continuation) — the §4 A/B ran full-span at HEAD and
FAILED criterion (i); the drag stays, G-15 stays open. See §6 execution record. No drag
coefficient was changed, no keeper swapped, nothing tuned against a residual (rules
13/21/24).**

**Thread:** gap-register `docs/gap-register-2026-07.md` G-15. The CAISO CT net-load drag
(`ct_netload_drag`, the keeper's sole surviving CT commitment mechanism after the caiso-52
scrub) is LOYO-unstable — D-8 (`results/calibration/d8-coefficient-stability/summary.json`):
train (2023–24) slope 0.01064 vs full (2023–25) 0.00901 = **+18.1% out-of-training drift**
(> the ~15% calibration-complete gate, `forecast-validation-program-2026-07.md` §3.4 item 4),
2025 floor prediction 1.59 (train) vs 1.20 (full) TWh = +32.2% drift — and the floor it
drives is approximately the class it floors: the full-fit 2025 floor (1.20 TWh) is ≈88% of
measured 2025 CT_PEAKER energy (1.36 TWh), and in the HEAD replay of the keeper config
(caiso-55) the drag carries 59.4/66.3/69.4% of model class energy (2023/24/25) — a rule-20
peaker-budget FAIL (>10%) in every year.

## 1. The drag's rule-17 credentials (driver, window, forward story) — intact

Per its derivation (`scripts/derive_caiso_ct_reliability_floor.py`):

- **External driver:** CAISO local-RA commitment of fast-start simple-cycle peakers (LA
  Basin / Big-Creek-Ventura / Bay Area local capacity areas) during the duck-curve neck —
  measured CAMPD CT_PEAKER evening capacity factor regressed on EIA-930 system net-load
  (demand − wind − solar). `frac = clip(slope·netGW + intercept, 0, cap)` with slope
  0.00901/GW, intercept −0.1124, cap 0.36 — a measured net-load→commitment rule, not a fit
  to a generation/price residual.
- **Window:** h15–21 local (half-open 15–22), byte-for-byte the same window in derivation
  and application; D-4 off-window binding is 0.0% in every year at HEAD (caiso-55).
- **Forward story:** a forecast year has a load forecast and a VRE build, hence a net-load;
  the floor regenerates and responds to changed conditions (more solar → deeper neck →
  different drag). Rule-23 frozen: re-derives only on CAMPD/EIA-930 source updates.

So the drag is not an inadmissible floor — it is an admissible floor **carrying far too much
of the class**, which is what makes its coefficients unstable and D-8 red.

## 2. Rule-19 / D-2 enumeration — what floors CT_PEAKER at HEAD (no stacking)

| mechanism | status at HEAD | CT_PEAKER share |
|---|---|---|
| `ct_netload_drag` h15–21 | ON in keeper config (CAISO base default) | 59–69% of class energy (caiso-55 D-2) — the ONLY live CT floor |
| reliability-floor CT netload limbs (all-24h) | retired: `enabled=False` + windowed 15–21 in `reliability_floor_coeffs_CAISO.csv` (77c4f67, b3a9036); additionally rule-19-deduped in code — `drop_drag_owned_reliability_specs` drops every CT_PEAKER limb whenever the drag is active (`iso_configs.py`) | 0 |
| RA startup bridge (P2) | physics-gated: economic bridging requires `min_down ≥ RA_BRIDGE_ECON_MIN_DOWN_HOURS` (4 h, `constants.py`; 916e8cb) — fast-start CTs (min-down 1 h) never bridge | <0.4% all years |
| P2 RA must-offer min-load (`caiso_ra_mustoffer`, frac 0.26) | ON (CAISO default) | no CT_PEAKER attribution in D-2 at HEAD |

One mechanism per phenomenon holds. There is nothing to de-stack; the instability cannot be
blamed on floor interaction.

## 3. Why the D-8 instability is structural, not statistical

`results/calibration/FINDING-caiso-evening-merit-2026-07-04.md`: in an energy-only,
ramp-free, 3-zone LP, CC (HR ~7.6) thermodynamically dominates CT (HR ~10.4) — CT's
*cheapest* band (~$59 at 2024 SoCal gas + CARB) exceeds the evening LMP in ~70% of evening
hours, so on pure merit the model clears only ~600 MW of evening CT vs ~1,000+ MW actual.
Reality commits the difference for **ramp** (fast net-load ramp → fast-start units) and
**locational** (LA-basin load pockets) reasons the LP cannot see. The drag is scaffolding
carrying that entire phenomenon: its regression is effectively fitting the whole class
trajectory of a small (7.6 GW), rapidly-changing fleet over three years of fast VRE growth —
so removing any year moves the slope materially (+18.1% without 2025, the deepest duck-curve
year). A coefficient family that IS the class it floors cannot be stabilized by more careful
regression; it stabilizes only when a structural mechanism takes the load off it.

**Non-remedies (prohibited):** re-fitting the slope/intercept/cap against any dispatch or
price residual (rules 13/21/24); re-widening the window (rule 17 — the h22 tail was dropped
from derivation AND application for cause); re-enabling the retired limbs or bridging
(rule 18/19); any per-plant or off-registry CT boost (rule 24).

## 4. Closure design

The closure vehicle already exists as a signed-off-pending design:
`docs/ramp-locational-design-2026-07.md` — two ISO-agnostic, zero-new-DOF mechanisms, both
**already implemented in the shared LP builder** as gated default-off flags
(`ramp_limits`, `local_capacity_constraints`; `model/dispatch.py`, threaded through
`run_calibration_full.py`):

1. **Plant-group hourly ramp-envelope rows** (`ramp_limits`) — CAMPD-measured p99.5 hourly
   trajectory envelopes (rule-13 admissible); slow-fleet friction lets fast-start CTs clear
   the evening ramp on merit.
2. **Local-capacity (LCR-area) min-gen rows** (`local_capacity_constraints`) — CAISO's
   published LCR study values (`data/raw/capacity-deliverability/caiso/caiso.csv`) on the
   LCR-area membership crosswalk; the load-pocket commitment the zonal topology cannot see.

That design's §"decision rule" (its lines ~267–282) is adopted verbatim as the D-8 closure
criterion, with the D-8 acceptance made explicit here:

- **A/B arm:** `ramp_limits + local_capacity_constraints` ON, `ct_netload_drag` OFF, full
  span 2023–2025, registered probe.
- **Pass ⇢ retire the drag:** the arm must show (i) CAISO CT evening (h15–21) energy at or
  above the drag arm's, or closer to CAMPD actual; (ii) D-1 diurnal shape held; (iii) CT
  forced share (then LCR-attributed only) within the rule-20 10% peaker budget. On pass,
  `ct_netload_drag` and the ST sibling are **removed from the CAISO wiring** (rule 26 —
  deleted means deleted, not zeroed), and the D-8 drag family drops out of the CAISO
  coefficient ledger entirely — closing G-15 by making the unstable family cease to exist.
- **Fail ⇢ the drag stays** (it is the most structurally faithful available mechanism,
  rule 1), G-15 stays open, and the failure evidence goes to the ramp-locational thread —
  never won back by re-tuning the drag.
- **D-8 acceptance on any surviving floor:** whatever floor remains after the A/B (LCR
  min-gen or a residual drag) must re-run `scripts/d8_coefficient_stability.py` and sit
  within the ±15% LOYO gate, or the calibration-complete checklist item 4 stays red for
  CAISO.

**Sequencing note (owner):** the ramp-locational design awaits sign-off; its A/B is a
solve-heavy CAISO wave. Per the merged L-8 memo (`emissions-co2-rate-plan-2026-07.md` §9.6),
any CAISO keeper re-solve that wave produces must carry `use_plant_emission_rates_v2=True`
(CAISO is carbon-priced — the flip is dispatch-affecting) with an optional v2-off ablation
twin for attribution, never a separate standalone re-solve wave for the flag alone.

## 5. Measurement arm run this session (the ONE permitted probe)

**`caiso-56-zero-drag` — zero-drag ablation, registered PROBE whatever the result (rules
15/16), never a keeper.** Byte-faithful `replay_keeper.py` of the caiso-51 keeper config at
HEAD (3b31193) with the single delta `ct_netload_drag=false`, all years 2023–2025
(`results/calibration/caiso56_zerodrag_ablation`). `use_plant_emission_rates_v2` stays OFF
exactly as the keeper ran. Purpose: the D-3-style attribution denominator for the drag's DOF
ledger entry — it measures exactly what the drag carries at HEAD with the limbs retired and
the bridge physics-gated (expected: CT collapses toward the ~30%-of-evening-hours merit
tail; CC absorbs; C3a/C4/price movement recorded, not judged). Environment note: like
caiso-55, the solve container lacks the capacity-deliverability clean partition, so the MIC
seam cap no-ops ("Returning no limits"); behaviourally inert — the per-hub corridor caps
(~5–7 GW) bind long before the keeper's 16 GW aggregate MIC cap — and it keeps the probe's
environment identical to its drag-ON baselines (caiso-55, caiso-r1-baseline).

Results are registered on the dashboard sidecar/run payload for `2026-07-06-caiso-56-zero-drag`
and recorded in `docs/calibration-log.md` (same session).

## 6. Execution record (2026-07-06, L-10 continuation) — A/B RUN, VERDICT: FAIL, DRAG STAYS

The §4 A/B arm was solved full-span at HEAD and registered:
**`2026-07-06-caiso-57-ramp-lcr`** (bundle `results/calibration/caiso57_ramplcr_dragoff`),
a byte-faithful `replay_keeper.py` of the caiso-51 config with exactly the arm's deltas
(`ct_netload_drag=false`, `ramp_limits=true`, `local_capacity_constraints=true`; v2 OFF as
the keeper ran; environment matched to caiso-55/56 — capdel partition absent, MIC no-op
inert; shared-input hashes byte-identical to the chain). Note: the 2026-07-04 probe
(`FINDING-ramp-lcr-caiso-2026-07.md`, id `caiso-ramplcr-probe-rejected`) had already run
this A/B on the 07-04 code state but never reached the dashboard (git-relay 413) — this is
the registered, at-HEAD execution the §4 criterion required.

Decision rule scored on the P2 pass (matching every registered baseline):

| year | arm-Y eve CT (P1) | drag arm (recon) | CAMPD actual | arm-Y TWh | drag TWh | actual |
|---|---|---|---|---|---|---|
| 2023 | 309 (552) | ~690–860 | 850 | 1.73 | 2.04 | 3.05 |
| 2024 | 146 (236) | ~580–600 | 770 | 0.73 | 1.70 | 3.30 |
| 2025 | 106 (127) | ~425–445 | 303 | 0.68 | 1.30 | 1.65 |

(The drag arm's evening means are reconstructed from caiso-55's D-2 — the drag's forced
energy is 100% in-window (D-4=0), floor mean = forced TWh/2,555 h — plus the caiso-56 merit
tail's in-window share; the 07-04 probe measured the same recipe's drag arm at 857/599/425.)

- **(i) FAIL in all three years** — evening CT below the drag arm's AND farther from CAMPD
  actual (2025 included: |106−303| > |~435−303|).
- (ii) holds vs the no-mechanism baseline: 2023 CT D-1 r 0.803 / CV-ratio 0.883 is
  best-in-chain; 2024/25 r 0.740/0.613 fail <0.8 as every drag-off arm does (small noisy
  fleet); D-4 off-window 0%.
- (iii) PASSES decisively: D-2 CT forced share 0.4/1.0/0.03% (sole mechanism
  `ra_mustoffer_bridge`; the LCR row attributes NO CT forcing — its dual is uplift-like by
  design and never enters the zonal LMP).

**Disposition per the §4 fail branch: `ct_netload_drag` STAYS the CAISO default (most
structurally faithful available mechanism, rule 1); G-15 stays OPEN; the D-8 ±15% LOYO gate
(calibration-complete item 4) stays red for CAISO.** Nothing was re-tuned.

**Where the failure evidence points (the thread's next build).** At HEAD the mechanisms are
NOT inert-in-P1 as the 07-04 probe concluded: P1 evening CT reaches 552/236/127 MW
(+0.93/+0.18/+0.29 TWh class energy vs caiso-56) — the 2023 LA-Basin LCR (7,529 MW
requirement) plus the ~480 h of endogenous evening scarcity clear real CT on merit. The
suppressor has **moved into P2**: the UC decommit strips those runs (552→309, 236→146,
127→106) because the commitment hurdle sees only the energy margin — no credit for the LCR
row's shadow value, i.e. no bid-cost-recovery/uplift analogue, which is exactly how CAISO
pays locally-committed units in reality. The follow-up build is therefore **credit the LCR
dual (local-commitment value) in the P2 commitment margin** — the same pattern as the
existing AS-aware `as_value` term in `model/commitment.py` — not any floor and not a drag
re-tune (rules 1/19). Mean SP15 LMP is unchanged vs the drag arm (69.2/46.5/48.7 both arms)
— neither the drag nor ramp+LCR moves C3a; the body overprice is owned by the
midday/RUC-long and seam threads, and the 2024/25 tail deficit (0 h >$200 vs 35/8 actual)
by the missing scarcity/AS mechanism (issue #1492).
