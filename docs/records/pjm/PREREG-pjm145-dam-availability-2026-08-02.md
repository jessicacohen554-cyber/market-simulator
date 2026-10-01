# PREREG — pjm-145: `pjm_dam_availability` (measured PJM generation-outage availability), single-delta A/B off the pjm-143b keeper

**Session:** pjm-145, 2026-08-02. **Committed BEFORE any measurement and before
any code** (the miso-111/112/113 protocol). Direction prediction is stated in
§7 and will be scored honestly in the FINDING whatever it does.

## §0 — Queue provenance (rule 28a)

- **Queue item taken:** `docs/mechanism-testing-matrix.md` §5.3 **item 7** —
  "`pjm_dam_availability` (**U**) — intaken but untested." It is the live head
  of the PJM queue: items 1–2 are diagnosis notes that join item 5, item 3 is
  refused until a measured sub-zonal load basis exists, items 4–6 are watch
  notes, item 5 requires an owner-signed charter ("Do not arm anything on the
  price alone"), and items 9/11/12/13 are struck/closed. MISO (§5.4) has no
  live lever; ERCOT's (§5.1) remaining items 7–8 are data-intake-first; NEISO
  (§5.6) requires a new charter before any solve; CAISO's (§5.2) live items are
  a two-settlement charter (item 3) and a derive re-identification (item 9),
  neither an armed-lever A/B. PJM item 7 is the one queue head with committed
  data, built code, and no charter/data blocker.
- **Matrix cell:** `dam_availability_rebasis`, PJM column, currently `U`
  ("PJM: data intaken 2026-07-24, ships default-off — UNTESTED LEVER"). This
  session adjudicates that cell and updates it + §5.3 item 7 in the same
  session (rule 28b).
- **Rule 25:** ERCOT's verdicts on this family (envelope adopted as ERCOT
  backcast default at ercot137 owner ruling R2; event-window caps `K` at
  ERCOT-148/149; level rejections ERCOT-116/134) transfer NOTHING to PJM. PJM
  enters as `U`. Every parameter of the PJM mechanism (region, outage types,
  covered classes, denominator) is the intake's own cited default derived from
  PJM's published record — no ERCOT value is imported.
- **Parallel-session check:** `git log origin/main --oneline` at f58339b shows
  no pjm-145, no `pjm_dam_availability` arming, no competing branch.

## §1 — The mechanism (already built; this session arms and adjudicates it)

- **Field:** `ScenarioConfig.pjm_dam_availability` (default **off**,
  `src/market_sim/config/scenarios.py:6825`, registered in
  `_CACHE_KEY_OPTIONAL_FIELDS` — default key stays 603c2498bf71d21d; an armed
  run gets a distinct cache key, so no cache cross-contamination between arms).
- **Loader:** `src/market_sim/data/pjm_outages.py` — PJM Data Miner 2
  "Generation Outage for Seven Days by Type" (`gen_outages_by_type`),
  current-day actuals (`lead_days == 0`), region **"PJM RTO"**, outage types
  **forced + maintenance** (planned excluded — nuclear-refuel double-count
  avoidance vs the nuclear overlay). Committed CSVs:
  `data/raw/pjm-outages/by-year/gen_outages_by_type_{2023,2024,2025}.csv`.
- **Transform:** `avail(day) = 1 − outage_mw(day) / fossil_thermal_capacity`,
  one fleet-wide fraction, broadcast UNIFORMLY to the 7 covered classes (COAL,
  CC_REGULAR, CT_PEAKER, ST_GAS, CC_CHP, CT_CHP, ST_CHP).
- **Applier:** `src/market_sim/data/fleet/arrays.py` PJM block — per covered
  class, the cap-weighted class-day mean availability is water-filled
  (bidirectional, cap 1.0: RESTORE toward the ceiling where measured > model,
  REMOVE proportionally where measured < model), preserving each unit's
  intra-day shape. Uncovered (NaN) days keep the pre-overlay availability.
  Backcast mode only (mode-aware seam).
- **Rule-17-analogue declaration** (this is an availability overlay, not a
  floor; the three legs are declared all the same): (a) **driver** — PJM's
  operator-published daily generation-outage record, a real physical
  availability quantity (rule 13's own example class); (b) **window** — the
  covered `lead_days == 0` dates of each solve year; outside the feed the
  statistical stack stands; (c) **forward story** — the same feed publishes a
  7-day forward outage forecast that regenerates for any future operating day
  and responds to conditions; forecast-mode years keep the statistical stack
  (the G4 mode-aware seam), exactly like the ERCOT analogue.
- **D-2 id / D4_WINDOWS: N/A by construction** — this mechanism is not a
  min-gen floor and forces nothing; it bounds availability. There is no floors
  npz entry to check. The fired/liveness checks that replace the miso-113
  floors-npz verification are pre-registered in §5 (K3/K4).
- **Disclosed basis approximation (known before any measurement):** the
  numerator is the WHOLE-fleet unplanned outage MW (PJM publishes no fuel
  split) while the denominator and application cover only the model's
  fossil-thermal classes; forced/maintenance outages of nuclear, hydro, wind
  etc. therefore inflate the fossil derate. This is the intake's documented
  first-order transform (rule 23: covered classes, outage-type default and
  region are **cited defaults, frozen against residuals** — this session tests
  the mechanism AS COMMITTED and does not retune any of them, whatever the
  residual does). If gates fail in a way attributable to this basis, the
  verdict is R with that attribution and the re-open condition is a per-fuel
  outage source — never an in-session denominator retune.

## §2 — A/B design

- **Keeper replayed:** `results/calibration/pjm143_hy_level_B`
  (`2026-07-31-pjm-143b-hy-level`, the current PJM keeper).
- **Control arm** (`results/calibration/pjm145_control_A`): byte-faithful
  replay at THIS session's HEAD, no overrides. A fresh control is solved
  (rather than reusing the committed `pjm144_control_A`) because 31 src files
  moved between that control's recorded HEAD (05b579d) and this session's
  (f58339b) — fh-2 + FFR-2B et al. — and their PJM-backcast inertness must be
  demonstrated, not assumed. The committed `pjm144_control_A` hourlies serve
  as a cross-check: control-vs-control max |class-hour Δ| is REPORTED; 0.0
  confirms the window was inert (the pjm-144 prereg pattern), a non-zero value
  is attributed to the window and the SAME-HEAD control remains the valid
  comparator.
- **Arm** (`results/calibration/pjm145_damavail_B`): identical replay plus
  exactly one override: `--set pjm_dam_availability=true` (the generic
  `prb_overrides` channel, recorded in `run_config.json`).
- **Years:** 2023 2024 2025, one bundle per arm (rule 16), solved as the
  per-year chain (rule 12; one fresh year per process, `--reuse-solved`
  byte-copies earlier years; swap active — the PJM per-plant + ramp-rows LP
  peaks ~15.6 GB, keeper note 14). ONE chain at a time (the miso-113 OOM
  lesson). Chain script committed before launch.
- **Holdout (rule 22):** years strictly {2023, 2024, 2025}. No out-of-training
  year is solved, scored, or read in this session.

## §3 — Ex-ante measurement (no-LP), run AFTER this PREREG commit

Instrument: `scripts/probes/_pjm145_damavail_exante.py` (committed before it
runs). Two halves, no LP anywhere:

1. **Loader-level:** per solve year — covered-day count (`lead_days == 0`,
   region "PJM RTO", non-leap clock), the measured unplanned-outage MW
   distribution, and the implied fleet-availability fraction distribution
   (p5/p25/p50/p75/p95).
2. **Fleet-level:** per solve year, build the keeper's fleet twice through the
   real path (`generators_to_fleet_arrays` with the keeper config vs the same
   config `with_overrides(pjm_dam_availability=True)`) and report, per covered
   class and pooled: cap-weighted day-mean availability delta in **MW**
   (restore/remove split, mean/p50/p95 of |Δ|), and the monthly profile of the
   pooled Δ.

## §4 — Ex-ante KILL rules (any one fires → register the finding, stamp the
matrix cell from the ex-ante evidence, and STOP — no LP is solved; that is a
complete session outcome)

- **KILL-COVER:** any solve year with **< 180 covered days**. (An availability
  overlay claiming a measured year on a minority of its days has no honest
  year-level story; the ALLYEARS bundle would mix bases within a year.)
- **KILL-INERT:** across ALL THREE years, pooled cap-weighted mean |Δ
  (availability × capacity)| **< 150 MW** AND p95 **< 400 MW**. Scale
  justification: pjm-144 measured 1.3–1.5 GW class-hour dispatch deltas that
  were price-inert (max zonal |Δλ| $0.034); an availability perturbation an
  order of magnitude below that floor cannot move any scored statistic — the
  miso-113 inert signature, killed ex ante instead of after two chains.
- **KILL-DEGENERATE:** the transform cannot represent the measured quantity
  against this fleet — the restore direction saturates (>30 % of covered
  class-days pinned at cap 1.0) or any covered class's water-fill target lands
  ≤ 0. Either means the measured aggregate and the model fleet basis are
  incompatible at first order; arming would exercise the clip, not the data.

## §5 — Construction gates (arm validity; all must hold or the A/B is void,
re-run after repair — the miso-113 two-lost-A/Bs lesson)

- **K1 recorded:** the arm's `run_config.json` carries
  `scenario_config.pjm_dam_availability == true`; the control's carries
  `false`.
- **K2 control integrity:** the fresh control reproduces the committed keeper
  on the scorecard basis (determination CALIBRATED, 9/9 target grade, C1
  16/16 all / 12/12 free, every criterion status equal). The strict byte basis
  vs `pjm143_hy_level_B` hourlies is REPORTED (pjm-144 achieved 0.0 MW; a
  non-zero here is attributed to the 05b579d→f58339b window and does not void
  the A/B — the arm is scored against the same-HEAD control, which is the
  point of solving one).
- **K3 fired:** every arm year's solve log carries the applier's
  "PJM measured generation-outage availability (year): CLASS set to measured
  fleet level on N day(s)" line for ≥ 1 covered class, and N matches the
  ex-ante covered-day count. (The floors-npz check is N/A — §1.)
- **K4 liveness:** arm vs control max class-hour |Δ MW| **> 50 MW** in every
  year (the pjm-144 MW leg). A mechanism that fires (K3) but moves nothing
  scored is verdict **I** — checked on `class_hourly` BEFORE any narrative is
  written (the miso-113 discipline).

## §6 — Kill gates (non-degradation; every number from
`scripts/calibration_verdict.py`'s own `metrics.json`, never re-derived)

- **P1 (criterion flips):** any scored criterion PASS→FAIL flip vs the control
  in any year kills promotion → verdict **R**, keeper unchanged, flip named.
  **C3c is reported explicitly in every outcome** (queue item 6: the 2024/2025
  margins are ~1 h / ~2.5 h over the 0.5× floor — the thinnest margins in the
  keeper).
- **P2 (C1):** all-class and free-class C1 counts do not regress (16/16,
  12/12).
- **P3 (C8):** no covered class's forced share loses its GROUNDED status
  (CT_PEAKER is the standing watch item).
- **P4 (determination):** the arm's determination is not worse than the
  control's (CALIBRATED, 9/9) in any year.
- **P5 (DOF):** the DOF ledger is byte-unchanged (18 entries / 6
  residual-identified) — this lever adds ZERO free parameters; every loader
  constant is a cited intake default.

## §7 — Direction prediction (stated before any measurement; scored honestly
in the FINDING, right or wrong)

**NET REMOVE, prices UP.** Predicted: the measured unplanned availability sits
BELOW the model's statistical+CAMPD availability on most covered days — the
aggregate numerator includes non-fossil forced MW over a fossil-only
denominator (§1), and CAMPD-inferred unit outages systematically undercount
fleet-wide unplanned derates. Consequences if right: load-weighted LMP up in
all three years; C3a-2023 (control +2.99 %) moves AWAY from zero, C3a-2024
(−1.28 %) and C3a-2025 (−9.04 %) move TOWARD zero; C3c model tail-hour counts
rise toward the actual (control 3/10/32 h vs actual 6/18/59). The ERCOT family
precedent (measured-correct, rejected twice on level because the statistical
estimate was silently load-bearing) is the named risk: if the PJM fit degrades
the same way, the honest outcome is **R with the compensating-error diagnosis
recorded** — adoption of a fit-degrading accurate input is an owner ruling
(the ercot137 R2 pattern), not a session's.

## §8 — Verdict rules (pre-registered)

1. Ex-ante kill fires → cell verdict from the ex-ante evidence (`I` for
   KILL-INERT, `R` with reason for COVER/DEGENERATE), FINDING registered,
   stop. Complete session outcome; no LP spent.
2. K4 fails (fires but moves nothing scored) → **I**, both arms registered,
   cell stamped, keeper unchanged.
3. Any P-gate fires → **R**, both arms registered, cell stamped, keeper
   unchanged, C3c effect reported.
4. All construction gates pass, no kill fires, AND ≥ 1 criterion strictly
   improves with zero degradations anywhere → the arm is a **keeper
   candidate** registered as such (the nyiso-109 "prereg's own verdict"
   pattern applies only at that bar); anything short of it leaves the keeper
   unchanged and the cell records the measured verdict. No self-promotion on
   any weaker outcome.

## §9 — Registration duties (rule 15 + 28b)

Both arms on the backcast dashboard (rejections and inert results included);
matrix cell `dam_availability_rebasis` PJM + §5.3 item 7 adjudicated in the
same session; FINDING-pjm145 committed; `docs/calibration-log/pjm.md` entry;
`check_registry_payload_parity.py` before every push; payloads over `git push`
(457 KB `push_files` cap); blob-verify every pushed file ≥ 300 lines
(rule 27).
