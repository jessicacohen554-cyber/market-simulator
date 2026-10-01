# PREREG miso-111 — regulated PRB committed-band within-day flexibility

Committed BEFORE the Phase-2 measurement is run (rule 23 [R-FROZEN-DERIVE]
discipline: the measurement is source-data conduct derivation, and this
pre-registration is what keeps it blind to the residual). Session miso-111,
2026-07-31, branch `claude/miso-111-coal-amplitude-p1l29u`.

## 1. Target

C7 `shape` FAIL on COAL_PRB — MISO's sole remaining determination blocker
(keeper `2026-07-31-miso-109b-hy-level`, D-1 cv_ratio 0.466 / 0.475 / 0.314
in 2023/2024/2025 against the 0.5 gate; profile_r 0.97-0.99, so the defect is
amplitude, not phase). §5.4: C7 is NON-LEDGERABLE — it must be built or the
lane stays NOT-YET.

## 2. Phase-1 findings this PREREG rests on (no-LP, from committed artifacts)

Sources: the keeper's own committed bundle sidecars
(`results/calibration/miso109_hy_level_B/hourly/`), the committed run payload
(`frontend/data/backcast/runs/2026-07-31-miso-109b-hy-level.js`, per-plant
hourly model MW), the committed CAMPD bench
(`frontend/data/backcast/bench/MISO/<year>.json.gz`, per-plant hourly actual
MW), `eia860_selfcommit_scope_plants()`, and the keeper `run_config.json`.
No solve was run.

- **The 2025 collapse is a per-plant shape effect, not mix/census.**
  Counterfactual class off-peak CV (common 30 plants): 2023 shapes ×
  2023 weights = 0.0725; 2023 shapes × 2025 weights = 0.0815 (mix effect is
  *positive*); 2025 shapes × 2023 weights = 0.0193; 2025 shapes × 2025
  weights = 0.0230. The whole collapse is within-plant.
- **The within-plant driver is merit-order saturation on the 2025 fuel-price
  path.** Keeper gas prices: $2.54 (2023) / $2.19 (2024) / $3.52 (2025)
  /MMBtu. Model off-peak (h0-14) load-weighted LMP p10: $25.34 / $21.32 /
  $29.71. The PRB full-SRMC band (~$22-29/MWh) is *crossed* by the off-peak
  price distribution in 2023/2024 — the econ tranches back out overnight and
  supply the model's only within-day variability — and sits entirely *below*
  the 2025 off-peak price floor, so every tranche saturates flat at its
  availability ceiling. Near-flat plants (off-peak CV < 0.02): 9 plants /
  60.2 TWh / 51% of class energy (2023) → 13 plants / 89.3 TWh / 62% (2025).
  The five newly-flat plants include a MERCHANT plant (56456, CV 0.122 →
  0.011) whose committed band already bids full SRMC — price-driven
  saturation, not a take-or-pay artifact.
- **Take-or-pay shares are per-plant and year-static**
  (`coal_takeorpay_share` has no year argument), so "the contract share
  rose" is excluded as the 2025 driver. Census change is excluded above.
  `unit_outage_short_windows` operates at multi-day grain (level, not
  diurnal shape) and cannot produce an hour-of-day amplitude change.
- **The flexibility inversion persists in the keeper.** Energy-weighted
  per-plant off-peak CV of the mean diurnal profile, model: regulated
  0.062 / 0.056 / 0.018 vs merchant 0.330 / 0.184 / 0.143 (2023/24/25).
  Actual (CAMPD bench, same construction): regulated 0.160 / 0.126 / 0.083
  vs merchant 0.171 / 0.130 / 0.059. Reality's regulated PRB fleet is as
  within-day flexible as its merchant fleet (2025: *more* flexible); the
  model's regulated fleet is 5-8× stiffer than its merchant fleet.
- **Mechanism enumeration (rule 19), everything acting on MISO coal
  commitment/offers in the keeper:** `coal_takeorpay_from_data` (K —
  `_mustrun` band fuel discount), `coal_committed_takeorpay_regulated` (K —
  `_committed` band of `eia860_selfcommit_scope_plants()` discounted to
  `1 - share`, the band this session targets), `coal_mustrun_per_plant` (K),
  `coal_econ_srmc_bound` (K — econ/peak tranches clamped ≥ full SRMC),
  `coal_plant_monthly_pricing` (K), `coal_warm_committed` (K),
  `commitment_screen_coal` (K), `unit_outage_short_windows` /
  `unit_outage_maxgen_events` (K — availability, not diurnal shape),
  `miso_rpe_pricing` (K), temp derate (daily-grain for coal; no hour-of-day
  signal). No reliability_floor rows bind on COAL_PRB (D-2: zero forced
  rows). Nothing else floors or reprices this class.

## 3. The hypothesis Phase 2 tests

The regulated self-commitment is real (SOM Table 7: regulated utilities
self-commit 53-56% of coal starts); its representation — a committed band
priced at `1 - takeorpay_share` ≈ VOM in all 8760 h — is the category error
(miso-96/miso-102 lineage). A real self-committed unit stays ON but follows
load down toward min-load overnight. If that is what MISO's own regulated
PRB fleet measurably does, the correct representation is the repo's existing
commitment-bridge construction (P0-detected run pattern → min-gen floor at a
MEASURED min-load fraction, committed band repriced to full SRMC in P1), not
a price discount.

Note the saturation finding above sharpens WHY the bridge form can pass 2025
where the miso-102 blunt-removal arm left cv_ratio at 0.364: with ~62% of
class energy repriced from ~VOM to full SRMC, the marginal unit overnight
becomes coal itself (PRB SRMC $22-29 vs 2025 gas-CC SRMC ≈ $27.6), so the
class re-enters the price-responsive band instead of sitting under it — and
the floor (not the discount) carries the self-commitment, which is what
protects C1 volume in the cheap-gas years.

## 4. Phase-2 measurement protocol (exact, committed before running)

Source: CAMPD unit-level hourly gross load (`data/raw/campd-unit-level/
<STATE>_<year>.parquet`), 2023-2025, MISO COAL_PRB plants only
(`class_plant_codes(iso='MISO', classes=('COAL_PRB',))` from
`scripts/data/derive_campd_gas_commitment_params.py`), split regulated vs
merchant by `eia860_selfcommit_scope_plants()`. PLANT basis throughout
(caiso-135: the consuming basis is what must be measured — the floor
multiplies plant pmax):

1. Per plant: `HSL_proxy` = p99.5 of plant gross load (summed units);
   `online` = plant load ≥ max(10 MW, 2% × HSL_proxy); `LSL_proxy` = p5 of
   online hours; `lsl_frac = LSL_proxy / HSL_proxy` — the WP-3
   loading-when-on construction verbatim.
2. Committed-window within-day profile: over ONLINE hours only, the mean
   hour-of-day profile of plant load / HSL_proxy, per plant per year; class
   profile = capacity-weighted mean over plants, regulated and merchant
   separately. Report off-peak (h0-14) CV and (max−min) amplitude of that
   profile.
3. Class statistic: capacity-weighted p50 of `lsl_frac` (regulated PRB,
   plant basis) — the candidate `min_load_frac` identification, reported
   per year and pooled.

## 5. Kill rules (the hypothesis is DEAD and the session ends NO-LP if any
fires)

- **K1 — flat committed band.** If the regulated-PRB capacity-weighted
  ONLINE-hours hour-of-day profile has off-peak CV < 0.04 in ALL of
  2023/2024/2025 (i.e. even conditioned on being ON, reality's regulated
  fleet holds a near-constant level and the observed class CV is start/stop
  edges, not within-run load-following), the min-load-with-headroom
  representation cannot produce the missing amplitude. Dead; write the
  finding, no solve. (0.04 is ~half the smallest failing-year actual class
  CV, 0.074 — a within-run signal weaker than that cannot close a cv_ratio
  gate that needs ≥0.5.)
- **K2 — no headroom.** If the regulated-PRB plant-basis `lsl_frac`
  capacity-weighted p50 ≥ 0.85 pooled 2023-2025, the measured band between
  min-load and max is too thin for the LP to express the observed amplitude
  (actual off-peak profile swings 8-16% of mean). Dead; no solve.
- **K3 — merchant artifact.** If the merchant-PRB within-run profile shows
  ≥2× the regulated amplitude in every year (i.e. the within-run
  flexibility is a merchant phenomenon and the regulated flatness is real),
  the mechanism must NOT be scoped to the regulated band. Dead in the
  proposed form; finding documents what was measured.

Honesty note on prior exposure: the CLASS-level actual off-peak CVs
(0.155/0.121/0.074) were already published in the keeper's committed
`legitimacy_diagnostics.json`, the regulated-vs-merchant ORDERING was
published by miso-102, and §2 above computed plant-level actual CVs
(unconditional, all hours) as part of the Phase-1 diagnosis. What has NOT
been measured anywhere is the ONLINE-conditioned (committed-window)
within-day profile and the plant-basis `lsl_frac` for this fleet — K1/K2/K3
bind on exactly those, and they are being committed before that measurement
exists.

## 6. Phase-3 guards (pre-registered NOW; a Phase-3 solve is licensed only if
§5 passes, and these bind on the A/B)

Arms: same-HEAD control (A) reproducing the keeper recipe at HEAD
(the miso-106 G3 lesson), and arm (B) = A + the mechanism under test. Years
2023 2024 2025 in ONE bundle each (rule 16), sequential solves (rule 12).

- **G1 (target).** COAL_PRB D-1: cv_ratio ≥ 0.5 AND profile_r ≥ 0.8 in all
  three years in arm B (the C7 gate itself). 2025 explicitly included — a
  2023/2024-only improvement reproduces miso-102 and fails.
- **G2 (the miso-102 kill, C1).** C1 fuel-mix stays 16/16 in every year.
  Any class flipping out of band kills the arm.
- **G3 (the miso-102 kill, COAL_BIT overshoot).** COAL_BIT D-1 cv_ratio
  stays ≤ 2.0 in every year (miso-102's arm hit 2.6-2.8×), and COAL_BIT
  profile_r does not drop below its keeper value by more than 0.05.
- **G4 (price criteria).** C3a/C3b/C3c verdicts do not regress vs the
  keeper (PASS stays PASS; the two ledgered CAVEATs may improve or hold,
  not widen past their ledger bands). Directional expectation, stated
  before solving: repricing the committed band UP should move mean LMP
  toward actuals (C3a is an under-prediction in all years) — but this is an
  expectation, not a license; if C3a worsens the arm is reported as-is.
- **G5 (forcing legitimacy).** The bridge floor is declared as mechanism id
  `miso_coal_commitment_bridge` with window = the P0-detected committed-run
  pattern (rule 17: driver = SOM Table 7 regulated self-commitment; the
  floor may bind only during detected runs; forward story = regenerates
  from any year's P0 pattern + the frozen measured `min_load_frac`). If
  COAL_PRB forced share exceeds the 30% budget, the rule-20 conditional
  pass path applies: a `D4_WINDOWS` entry must exist and D-1 must clear —
  no exemption is claimed in advance.
- **G6 (registration).** BOTH arms are registered on the dashboard in this
  session whatever the outcome (rule 15), and the mechanism-matrix MISO
  cell is stamped with the verdict (rule 26), rejection included.

## 7. What this session will NOT do (DO-NOT-REDO, restated)

No coal minimum-take/tonnage RHS (miso-103/104); no blunt `sunk_fixed`
removal (miso-102); no offer steepening or PRB-scoped price levers
(miso-102: model coal is already 0.9-2.8× real price-responsiveness); no DA
virtual depth (miso-105); no CT heat-rate or CT floor levers (miso-106/107);
no MOM outage attribution (miso-85/87); no topology work (miso-78/79); no
hydro reopening (miso-108/109/110); no holdout year in any form (rule 22 —
MISO holds neither tier marker; --year ∈ {2023, 2024, 2025} only); no
re-derivation of any min-stable parameter against a residual (the §4
measurement is source-data conduct, blind to the model's residual by
construction of this document).

## 8. Post-measurement design refinement (committed BEFORE any solve)

Phase 2 ran after §1-§7 were committed (da5ab19). No kill rule fired:

- K1: regulated-PRB ONLINE-conditioned off-peak CV = 0.159 / 0.126 / 0.076
  (2023/24/25) — not flat; trough h2, peak h17-18, amplitude 18-25% of HSL.
- K2: plant-basis `lsl_frac` cap-weighted p50 = 0.182 — ample headroom.
- K3: merchant amplitude 1.1-1.6× regulated, not ≥2× — not a merchant
  artifact.
- Discriminating conduct test (beyond the PREREG, reported for completeness):
  regulated-PRB overnight de-load vs day max is 0.488/0.452 on cheap nights
  (hub overnight min < $22) vs 0.189/0.221 on dear nights (> $28), 2023/2025
  — the within-day cycling is PRICE-RESPONSIVE conduct, not blind
  load-following. Only the COMMITMENT (staying online) is self-determined.

**Design refinement forced by the measurement.** The §3 floor half of the
hypothesis is ALREADY REPRESENTED, more strongly than measured: the
per-plant CAMPD `_mustrun` bands (thermal_tranches_MISO.csv: 30-52% of
nameplate for the large regulated PRB plants) sit far ABOVE the measured
plant LSL (p50 0.182), are always-on at sunk-contract fuel (share 1.0 →
fuel-free bid), and are what carries the self-commitment once (rule 19). A
new bridge floor at 0.182 × pmax would bind BELOW the existing mustrun band
— provably inert. What is missing is the HEADROOM half only: the
`_committed` band (a further ~22-52% of nameplate) is pinned inframarginal
in all 8760 h by the regulated take-or-pay discount, so ~92% of the large
regulated plants' capacity cannot respond to price while the meter shows
that same band cycling nightly.

**The Phase-3 arm is therefore a single offer-side delta, no new floor:**
`coal_prb_committed_dispatchable` (new ScenarioConfig bool, default False) —
when armed alongside `coal_committed_takeorpay_regulated`, a PRB-supplied
plant's `_committed` tranche is EXCLUDED from the regulated sunk-contract
discount and bids full delivered cost under its supply passthrough
(identical to a merchant committed band). BIT/lignite keep the discount (the
G3 protection is by construction — miso-102's COAL_BIT 2.6-2.8× overshoot
came from repricing BIT). The `_mustrun` band is untouched in every arm.

**Sharpened predictions, stated before the solve:**
- P-A: 2023/2024 COAL_PRB cv_ratio rises to the neighbourhood of miso-102b's
  0.727/0.931 (possibly somewhat less: BIT keeps its discount here, so the
  overnight price feedback differs).
- P-B: 2025 improves but clearing 0.5 is GENUINELY UNCERTAIN — miso-102b
  reached only 0.364 with ALL coal repriced, and the model's overnight price
  floor (~$29.7 p10 off-peak vs actual $17.95) leaves most of the PRB band
  inframarginal at night. The live question is whether the expensive top of
  the measured per-plant delivered-price spread (Michigan rail PRB, e.g.
  Monroe ~3.3 GW) straddles the model's 2025 night prices and cycles. If
  2025 stays < 0.5, G1 fails and the arm is registered REJECTED per §6 —
  with the residual attributed to the overnight price-formation defect
  (model night HE0-3 $27.8-35.3 vs actual $19.4-26.9, present in BOTH
  miso-102 arms), which is a SEPARATE lane this session does not open.
- P-C: C1 stays 16/16 (PRB has +2.02/+1.86 TWh of ±8 headroom and the
  scoped repricing sheds far less than miso-102b's all-coal −18.5/−27.2
  TWh; the displaced energy lands on CC_REGULAR, which is UNDER by 4-5 TWh,
  so both move toward actuals). If PRB flips C1, the arm dies (G2).
- P-D: COAL_BIT D-1 stays in its keeper band (G3) — its offers are
  untouched; only second-order price feedback reaches it.
- P-E: C3a improves or holds in all years (repricing raises inframarginal
  bids; the model's mean LMP is under in all three years). Night-hour price
  fit worsens (the miso-102 P5 result) — reported, not hidden; C3b verdict
  must not flip (G4).
