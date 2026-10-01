# PRECOMMIT — NWPP-NEXT-16: combined keeper (C), + captive-mine (D), + live-capacity WEFOR (E), 2019–2025, on pin

Written before any solve. Template: `PRECOMMIT-nwppnext14-clark-hr-bridger-vintage-2019-2025-2026-09-30.md`; procedure and
parent gotchas: `HANDOFF-nwppnext15-2026-09-30.md`. Owner cards (2026-10-01): "Run D too", "Solve [Task 2] now on top of
C", "No control".

## 1. Arms (all on keeper #19 `2026-09-30-nwppnext14-clark-hr-bridger`, bundle `nwppnext14_span`)

| arm | out-dir / branch | keys vs keeper #19 |
|---|---|---|
| **C** combined | `nwppnext16c_<Y>` / `claude/nwppnext16c-<Y>` | `campd_unit_fuel_split` True → **False**; `campd_per_unit_vintage_denominator` → **True** |
| **D** C + captive mine | `nwppnext16d_<Y>` / `claude/nwppnext16d-<Y>` | C + `coal_captive_marginal_fuel_price` → **True** |
| **E** C + live-capacity coal WEFOR | `nwppnext16e_<Y>` / `claude/nwppnext16e-<Y>` | C + `unit_outage_dispatched_bin_denominator`, `unit_outage_dispatched_bin_live_denominator`, `wefor_residual_short_screened_coal` → **True**; `wefor_residual` → **0.0**; `wefor_residual_groups` → **{COAL_BIT, COAL_LIGNITE, COAL_PRB, COAL_WC}** |

`eia923_cc_family_heat_rates` stays True in every arm (Clark, settled at #19).

- **C** is the rule-19 debt from HANDOFF-nwppnext15 lever 0: the per-unit fuel split and the vintage denominator repair
  the same defect (the per-unit tranche artifact divides by the head-vintage nameplate); the selector refuses both. The
  vintage denominator is broader: it also repairs North Valmy 8224's must-run (212.45 → 127.89 MW). Artifact
  `thermal_tranches-perunit-vintage-NWPP.csv` sha `6fe20358…be65ab9`. **DOF +0.** If C is promoted, the per-unit
  fuel-split composition is deleted (rule 26).
- **D** — `PHASE0-nwppnext15-captive-mine-2026-09-30.md`: at mixed-source coal plants the econ/peak tranches take the
  EIA-923 Page-5 non-captive delivered price (measured, per plant-month, forward-regenerable from the then-current
  Page 5 — rule 13). Census: Bridger econ −$9.1/MWh 2023, −$2–5 2019–21/2024, +$1.0 2022; Hunter 2022 +$6.2, Huntington
  2019 −$7.6 on <1 % of volume; 2025 untouched (no Page-5 file). **DOF +0** (owner "no threshold").
- **E** — Task 2. The parent `unit_outage_dispatched_bin_denominator` NWPP cell is **R** (NEXT-12/13), given before the
  live sub-gate existed; the live sub-gate is the new evidence (rule 28(a)): Centralia 1,340 → 670 MW and Colstrip
  2,094 → 1,480 MW in 2021, 2022 and 2025 (`nwppnext15/live_denominator_census.json`). `wefor_residual = 0.0` is the
  caiso-187 residual `max(0, W − X)` construction already ledgered for NWPP (FINDING-nwppnext13 §1.3); groups naming
  only coal scope it to screened coal. It does **not** reach Bridger, so it cannot by construction move the one failing
  record's Bridger cause. **DOF +0** (wefor_residual is identified, not tuned).

## 2. Prediction (zero LP), and what would NOT be a reason

- **C** ≈ NEXT-15's solved vintage-denominator run: 0 status changes vs #19, C4 within ±0.01, C4 coal 2023 r ≈ 0.67.
- **D** lowers Bridger's 2023 econ offer ~$9/MWh → more Bridger Jun–Oct energy → C4 coal 2023 r up (direction only).
  Inventory take floor still binds annual burn, so the effect is a monthly re-shape, not an annual-level move.
- **E** raises screened-coal availability (Centralia/Colstrip in 2021/22/25) → coal TWh up in those years, gas down.
- Owner standing ruling: promote if structural integrity improves, even if a gate regresses; every regression reported at
  full magnitude. The decision is structure (rules 14/19), never the residual. Arms are not selected by which one clears
  C4 coal 2023 (rule 1).

## 3. G-DRIFT (rule 29(b)) vs keeper #19's pin `54edd9e324913a2c915199ca2af8e46abfed582b`

Code: `git diff 54edd9e3 94f36436 -- src/market_sim scripts/run_calibration*.py scripts/lib scripts/replay_keeper.py
data/raw/_validation-source data/raw/reference` — 31 files, 22 commits, every hunk classified:

| commits | what | class |
|---|---|---|
| 450c1b33 miso-294 | `actual_lmp.json` MISO rows | INERT (another ISO's scorer data) |
| 41e0f242 R-ERCOT-19 | prior-year commitment profile (`floors.py`, `offer_curves.py`, `commitment_profile.py`, ERCOT artifact) | INERT (default-off flags, ERCOT artifact; `floors.py` targets refactor is identical arithmetic) |
| bf7c1228 R-ERCOT-20 | custom-bin / master-registry / `eia860.py` / `outages.py` CC-site splits | INERT (ERCOT plant codes 3469/7900/56350, `ba_code=ERCO`) |
| 3a7d8006, 71c1dfbf, 32e0c185, 444cbdd4 PJM-NEXT-16 | `ISO_BA_JOINS` OVEC, PJM gas bridge, `_joining_ba_generators` | INERT (PJM-only; NWPP join set is `()`) |
| 91a525f3 soco-96 | `dual_fuel_measured_oil_burn` | INERT (default off, SOCO artifact) |
| cd589798 R-CAISO-20 | CAISO interchange unprinted arm | INERT (CAISO-only, default off) |
| 1d83b224 (via 58c7b3fd) | `campd_per_unit_vintage_denominator` selector | ARM (C/D/E) |
| c361efe0 | `coal_captive_marginal_fuel_price` | ARM (D only) |
| 10b20574 | `unit_outage_dispatched_bin_live_denominator` (+ screened-coal-first WEFOR) | ARM (E only) |
| various | CLI plumbing, `scenarios.py` fields at frozen drop values, `solve_surface_declared.py` | INERT (no key move) |

**Code: ALL INERT** outside the arms. **Libraries: LIVE.** Keeper #19 solved off-pin (highspy 1.15.1 / pandas 3.0.6 /
pyarrow 25.0.1 / pydantic 2.13.5); these arms solve on `requirements.txt` (1.14.0 / 3.0.3 / 24.0.0 / 2.13.4). Owner card
"No control": the library effect is **not measured** and is confounded with the arm in every C-vs-#19 difference. D-vs-C
and E-vs-C are clean (same pin, same libraries).

## 4. Recipe (per shard, arm A ∈ {c,d,e}, year Y)

```
pip install --ignore-installed pyyaml==6.0.3 && pip install -r requirements.txt && pip install -e . --no-deps
mkdir -p /tmp/n49 && git fetch --depth=1 origin 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 \
  && git archive 909cdd30bfdd8a398b10a4255b1340d0d9ef1943 results/calibration/nwpp49_ror_span | tar -x -C /tmp/n49
python3 scripts/data/curate_hydro_plant_modes.py --iso NWPP
python3 scripts/data/curate_coal_receipts.py && python3 scripts/data/curate_coal_stocks.py
python3 scripts/replay_keeper.py /tmp/n49/results/calibration/nwpp49_ror_span \
  --out-dir results/calibration/nwppnext16<A>_<Y> --years <Y> \
  <keeper #19 --set list, PRECOMMIT-nwppnext14 §4, with campd_unit_fuel_split=false> \
  --set campd_per_unit_vintage_denominator=true \
  [D:] --set coal_captive_marginal_fuel_price=true \
  [E:] --set unit_outage_dispatched_bin_denominator=true --set unit_outage_dispatched_bin_live_denominator=true \
       --set wefor_residual_short_screened_coal=true --set wefor_residual=0.0 \
       --set 'wefor_residual_groups=["COAL_BIT","COAL_LIGNITE","COAL_PRB","COAL_WC"]' \
  [Y in 2019–2022:] --set hydro_backfill_year=null
```

Exact per-shard prompts: `docs/records/nwpp/nwppnext16/shards/shard_<A>_<Y>.txt`.

## 5. Hard stops (any miss = STOP, no push)

1. `git rev-parse HEAD` = the pin; highspy/pandas/pyarrow/pydantic = 1.14.0 / 3.0.3 / 24.0.0 / 2.13.4.
2. sha256: `campd_ct_heat_rates_NWPP.csv` 29baa2f1…; `campd-unit-outages-perunit-NWPP.csv` ff5b0644…;
   `thermal_tranches-perunit-vintage-NWPP.csv` 6fe20358…; `eia923_cc_family_heat_rates_NWPP.csv` cc9ac299….
3. `scenario_config` diff vs `nwppnext14_span/run_config_<Y>.json` = exactly the arm's §1 keys.
4. Arm-live: thermal_tranches path `-perunit-vintage-`; D: log `coal_captive_marginal_fuel_price (NWPP <Y>)`;
   E: solve does not raise the fail-closed `wefor_residual_short_screened_coal requires` error.
5. P1 summed demand = 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 / 302.532 TWh ±0.05.
6. Keeper log lines: `coal per-yard budget`, `coal take floor`, `coal monthly pile`, `NWPP Path 76 (Alturas)`.
7. Bundle has `dispatch/<Y>_P1.parquet` + `hourly/{class_hourly,system,hydro_cascade}_<Y>.parquet`.
8. Feasible LP.

## 6. Decision

Per arm: compose with `scripts/probes/_nwpp42_compose_span.py --skip-diagnostics` (2023 leg first) into
`nwppnext16<A>_span`; legitimacy diagnostics; attestation; `dashboard_add_run --no-prune`; `calibration_verdict` diffed
per (criterion, year, key) vs keeper #19 and vs C. One owner card carries promotion + prune (rule 35).

## Addendum (post-solve, 2026-10-01) — §3 library line corrected

Keeper #19's own `run_config_<Y>.json` record highspy 1.14.0 / pandas 3.0.3 / pyarrow 24.0.0 / pydantic 2.13.4 (runtime
`importlib.metadata`). #19 was on pin; the off-pin solve was NEXT-15's unmerged run. The "Libraries: LIVE" line in §3 is
withdrawn: C vs #19 is a clean A/B. Results: `RESULT-nwppnext16-combined-captive-live-2026-10-01.md`.
