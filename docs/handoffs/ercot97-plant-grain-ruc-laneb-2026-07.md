# ERCOT-97 hand-off — plant-grain crosswalk + measured RUC conduct + Lane B (owner-directed 2026-07-22)

Owner direction (ERCOT-96 session, 2026-07-22): "I want the plant crosswalk,
fix reality RUC etc if we have measured and then lane B too in the next
prompt." This file carries the ready-to-paste ERCOT-97 charter and the
grounding facts the ERCOT-96 session verified for each lane.

## Verified grounding (this session)

1. **Crosswalk inputs exist and are sized.** DAM 2023 config-collapsed sites:
   58 CC_REGULAR (30.8 GW rating) / 189 CT_PEAKER (11.4 GW) / 46 ST_GAS
   (10.5 GW); model side `data/raw/reference/custom-bin-assignments.csv`
   (41 CC / 192 CT / 17 ST plants with Plant_Code, Plant_Name, Nameplate_MW,
   zone). Site mnemonics (DDPEC, CBECII, WHCCS2, FRNYPP…) do NOT token-match
   EIA names — evidence must be capacity (site p98 rating vs plant/class MW),
   Settlement Point Name, QSE, and the `ercot_noncampd_dam_crosswalk.csv`
   forensic style. The CAISO pattern (`build_caiso_resource_crosswalk.py` →
   reviewable CSV with match_score + accepted gating; loader consumes
   accepted rows ONLY) is the template — an unreviewed guess never enters a
   solve. The site×hour intermediate is already computed inside
   `derive_ercot_thermal_dam_availability.derive_year` (live_sh / rating).
2. **Measured RUC conduct data is ALREADY IN-REPO.** The 60-Day SCED
   disclosure corpus (`data/raw/ercot/SCED/`, full-year intake landed
   ERCOT-93) carries per-resource per-interval `Telemetered Resource Status`;
   `ONRUC` marks RUC-committed unit-hours — ERCOT capacity committed by the
   operator that economics would not have committed (the ERCOT-95 Finding 5
   "reality RUC/self-commits that capacity" conduct). ERCOT-93's ST_GAS
   telemetered-span derive is the read pattern. Admissibility: published,
   unit-resolved, regenerates for any year, responds to conditions (rule 13)
   — enters as commitment-STATE evidence (floors/held-out capacity), never a
   price.
3. **Lane B unchanged from ERCOT-95 Finding 4.** `ordc_lolp_params_path =
   data/raw/_validation-source/ercot_ordc_lolp_params.csv` (file present);
   `reserve_config.py` `resolve_lolp_params` collapses to annual mean →
   co-opt curve center mu 0→~915, σ 1400→1343. Predicted ~28 tail hours on
   the measured envelope — a rule-11 correctness item, NOT a C3c closer.
4. **Baseline for all A/Bs.** `2026-07-22-ercot96-dam-hourly-grain`
   (candidate, NOT-YET, keeper still ercot91): 2023 tail 51/181 (0.28×), C3a
   −27.8%, NRMSE 0.539, C7/C8 PASS. The byte-recipe base replay reproduces
   the ercot91 keeper exactly on the 4ff3118 tip tree.

## The prompt (paste as the ERCOT-97 session charter)

```
ERCOT-97: three lanes on the 2023-summer C3c frontier, in order — (A) PLANT-GRAIN
crosswalk + plant×hour DAM availability, (B) MEASURED RUC-CONDUCT commitment state,
(C) Lane B published ORDC LOLP table. Baseline everything on the ERCOT-96 candidate
(2026-07-22-ercot96-dam-hourly-grain: 2023 tail 51/181 h, C3a -27.8%, C7/C8 PASS;
keeper ercot91 unchanged) — NOT on stale main.

READ FIRST (in order): CLAUDE.md in full (rule 26: this lane writes core infra →
Opus/Fable ONLY). docs/handoffs/ercot97-plant-grain-ruc-laneb-2026-07.md (this
charter's grounding facts). docs/handoffs/ercot96-thermal-dam-grain-2026-07.md +
docs/calibration-log/ercot.md §ERCOT-96 (what the hourly grain already banked and
how). docs/handoffs/ercot95-scarcity-tail-diagnosis-2026-07.md (Findings 4-6).
Use .venv/bin/python (bare python has no numpy).

WHERE WE ARE
- Keeper 2026-07-20-ercot91-seasonal-drag-fullspan, NOT-YET on C3c (2023 51 h vs RT
  181 after ERCOT-96's hourly grain; 2024 13/53; 2025 0/31). C3a/C3b ledgered; C3c
  2023 ledgered, 2024/2025 unledgered = the NOT-YET driver.
- ERCOT-96 candidate carries the class-HOUR DAM availability grain (zero fitted
  params, LOYO clean). Its bundle is the A/B base for every lane here; replay via
  scripts/replay_keeper.py on results/calibration/ercot96_hourly_grain_fullspan
  (--set routes dual-channel, kwarg + prb_overrides).
- ERCOT NOT in calibration-complete.json → rule 22: solve/score ONLY 2023-2025.
- Per-plant ERCOT LP ~8 GB, env ~15 GB → ONE year at a time, MALLOC_ARENA_MAX=2.

LANE A (PRIMARY) — DAM-site → EIA-plant crosswalk, then plant×hour availability
1. BUILD THE CROSSWALK the CAISO way (build_caiso_resource_crosswalk.py pattern):
   scripts/data/build_ercot_dam_resource_crosswalk.py emitting
   data/raw/reference/ercot-dam-plant-crosswalk.csv with per-row evidence
   (site, class, p98_rating_mw, settlement_points, qse, proposed plant_code,
   plant_name, capacity_ratio, match_method, match_score, accepted). Evidence
   basis: capacity corroboration (site p98 rating vs custom-bin-assignments
   class MW), settlement-point/substation tokens, QSE, county where known.
   AUTO-ACCEPT only unambiguous rows (capacity within tolerance AND
   name/SP corroboration); everything else accepted=0 → falls back to the
   class-hour envelope. Extend the ercot_noncampd_dam_crosswalk.csv 3-row
   forensic style for hard cases. The 58 CC sites are the priority (30.8 GW,
   fewest names, biggest units); CT's 189 small sites can stay largely
   unaccepted without hurting coverage.
2. APPLY plant×hour: extend derive_ercot_thermal_dam_availability.py to emit a
   site×hour parquet (the live_sh/rating intermediate it already computes);
   new ScenarioConfig flag ercot_thermal_dam_availability_plant (default off,
   requires _hourly): for ACCEPTED-mapped plants, cap the plant's tranches at
   its own measured site-hour fraction; rescale the unmapped remainder so the
   CLASS-hour total still lands on the measured class fraction (the ERCOT-96
   water-fill, applied to the residual set). Zero fitted parameters. The
   measured payoff is redistribution (~259 MW mean on tail hours) — expect
   merit-mix/zonal movement more than tail-count movement; judge by structure
   (rule 1), gates by C7/C8/zero-spurious/C3a as always.
3. A/B: 2023 rule-16 throwaway vs the ercot96 candidate base; then full-span
   2023-2025 ONE bundle if guards hold; LOYO before any promotion talk.

LANE B (SECOND) — measured RUC-conduct commitment state ("fix reality RUC")
1. MEASURE first (solve-free): from data/raw/ercot/SCED/ Telemetered Resource
   Status, count ONRUC unit-hours by class × hod × month for 2023-2025 (the
   ERCOT-93 telemetered-span derive is the read pattern; RESTYPE_TO_CLASS maps
   types). Size: how much RUC-committed capacity sits in the hod 13-19 window
   on the 56 tail days, which classes, which plants (composes with the Lane A
   crosswalk for plant grain). Compare against the model's committed state in
   the ercot96 candidate (its gas bridge floors ~50k unit-hours).
2. If material: derive a measured RUC commitment-state input (per class-hour,
   plant-hour where crosswalked) and thread it as min-gen/held-out commitment
   scaffolding through the EXISTING bridge/floor machinery — rule 12 (window +
   driver + forward story: RUC is the driver, the window is its measured
   firing pattern, forward years regenerate from the statistical RUC posture),
   rule 19 (reconcile with ercot_gas_commitment_bridge — REPLACE or gate, never
   stack on its residual), D-2 attribution id + D4_WINDOWS entry required.
   Rule 13 test: ONRUC is published operator conduct, regenerates any year,
   responds to conditions — admissible as commitment STATE, never as a price.
3. A/B same protocol. If RUC state and the bridge overlap, the bridge stands
   down where measured state exists (measured-over-derived, rule 14).

LANE C (LAST, quick) — the ERCOT-95 Finding-4 LOLP swap
replay ercot96 candidate meta 2023-only with
--set ordc_lolp_params_path='"data/raw/_validation-source/ercot_ordc_lolp_params.csv"'.
Adopt ONLY on correctness grounds if C7 + zero-spurious hold (predicted ~28 tail
hours at measured envelope, fewer at model reserves; NOT a C3c closer). Full-span
composition with whatever A/B survived from lanes A/B.

GATE (unchanged from ERCOT-96): C3c-2023 toward band AND C3a-2023 not worse,
WITHOUT breaking C7/C8/zero-spurious or 2024-25. If all three lanes land/exhaust
and C3c is still out of band, the ERCOT-95 disposition stands: recommend LEDGER
C3c 2024/2025 (3/3 MAX_LEDGERED_CAVEATS → CALIBRATED-WITH-CAVEATS via
calibration_verdict.determine) — OWNER SIGN-OFF, never unilateral. Do NOT flip
keepers/<ISO>.json without the owner's explicit promotion.

HARD GUARDRAILS (CLAUDE.md)
- Rules 1/11/13: no fitted availability/tightness knobs; every input measured +
  forward-regenerable; nothing tuned to the price residual. Crosswalk rows are
  identification metadata (accepted-gated), not tuning.
- Rule 22 quarantine: 2023-2025 only (CI-enforced).
- Rule 15/16: every completed run on the dashboard same-session (probe bundles
  gitignored by results/calibration/*probe*/ — name candidates without 'probe');
  all years in ONE bundle for any candidate.
- Rules 26/27: Opus/Fable only; push via mcp__github__push_files with per-blob
  SHA verification (this caught 2 real transcription defects in ERCOT-96 — verify
  EVERY blob); files >~80 KB never travel whole through a model response — patch
  or staging protocol (docs/handoffs/ercot96-thermal-dam-grain-2026-07.md
  "Transport manifest" has the working recipe); oversized run payloads go to the
  owner via the session file channel with sha256 manifest.
- No CI solves (private repo). Solve in-session, years sequential.

ENV GOTCHAS (from ERCOT-96, all verified)
- Base the tree on main ≥ a4a17c9 (or the ERCOT-96 branch
  claude/ercot-thermal-dam-grain-all6f0): it carries the hourly-grain code as
  docs/handoffs/ercot96-lane-a-core.patch — git apply + hash-verify + regenerate
  the hourly CSV (derive script, sha256 in the manifest) if the assembled files
  haven't landed on main yet. VERIFY before any solve:
  cd scripts && ../.venv/bin/python -c "import inspect,run_calibration_full as r;
  print('ercot_thermal_dam_availability_hourly' in
  inspect.signature(r.solve_and_persist).parameters)"  → must print True.
- Filtered fetch works when full fetch 413/504s:
  git fetch --filter=blob:limit=2m origin main, then sparse-exclude the missing
  off-lane blobs (rev-list --missing=print; ERCOT-96 excluded 1,586 — recipe in
  the session log). GIT_NO_LAZY_FETCH=1 everywhere after.
- ERCOT solve ~8-10 min/year; base+probe sequential, never concurrent.
- data/raw/ercot/2026-02.part0001-0009.parquet lack HASL (crash offer-wall
  derives on 2025) — not on these lanes' paths; quarantine if touched.

REFERENCE
- scripts/probes/_ercot96_phantom_measure.py (site-hour read + tail-day recipe)
- scripts/probes/_ercot96_ab_readout.py (the A/B comparator, bundle-vs-bundle)
- derive_ercot_thermal_dam_availability.py (site collapse, ratings, hourly emit)
- ERCOT-93 log entry + derive_ercot_stgas_* (SCED telemetered read pattern)
- build_caiso_resource_crosswalk.py + caiso-resource-eia-crosswalk.csv (template)
- data/raw/reference/ercot_noncampd_dam_crosswalk.csv (forensic row style)
```
