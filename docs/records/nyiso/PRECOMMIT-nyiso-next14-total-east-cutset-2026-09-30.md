# PRECOMMIT — NYISO-NEXT-14: re-test the Total-East cutset envelope on the current keeper — 2026-09-30

- **Session:** NYISO-NEXT-14 (orchestrator; this container runs no LP, rule 32 (a)).
- **Owner ruling (this session, decision card):** "Re-test all 5 years". This re-opens cell **R** `nyiso_total_east_cutset_ttc` (nyiso-224 / nyiso-225, ruled "reject as constructed" 2026-09-10) on new evidence (rule 28).
- **Phase 0:** `docs/records/nyiso/FINDING-nyiso-next14-upstate-evacuation-phase0-2026-09-29.md`, probe `scripts/probes/nyisonext14_upstate_phase0.py` → `results/phase0/nyiso/_nyisonext14_phase0.json`.
- **Control (form 4):** keeper `2026-09-29-nyisonext13-recon-detach-span` (bundle `results/calibration/nyisonext13_span`, 2022–2025) + stamped `2026-09-29-nyisonext13-recon-detach-2021` (bundle `results/calibration/nyisonext13_2021`).
- **Arm:** the keeper recipe + `nyiso_total_east_cutset_ttc: true`. No code change. Nothing else moves.
- **Queue:** off-queue by the letter; it is the root cause of queue item 1 (FINDING §2).

## 1. The mechanism (unchanged since nyiso-224; zero free parameters)

The model's one `Upstate_West → Capital_Hudson` link is the A–E → east cutset (NYISO's TOTAL EAST). Today it is capped at the posted CENTRAL EAST DAM TTC, a sub-cutset. Armed, `pipeline.ttc.apply_iso_monthly_ttc` takes `constants.NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH` instead: the p90 of measured TOTAL EAST flow per calendar month, the construction armed for NYISO's border links (nyiso-125). The two tables replace each other on one seam; they never stack (rule 19). Basis: rule 14's misalignment exception, "a single GTC that is one of several parallel paths our reduced network collapses into one link".

## 2. What is new since the R

1. nyiso-224's G-5 fail (phantom COAL_PRB) cannot recur: the keeper fleet has no coal class in 2021–2025.
2. Under NEXT-13's detach, Upstate_West clears at the pooled node's price in 4,624–8,403 h and at ≤ $0 in 3,110 / 1,263 / 723 h (2021–2023). Measured A–E DA is never ≤ $0.
3. Upstate_West alone explains the 2021–2023 C3a miss (C3a with Upstate_West exact: +4.6 / −1.2 / +0.4 %).
4. The non-CE leg regresses on the external schedules with coefficients far from 1 (FINDING §3), so the cutset is not a double count of the seams.
5. nyiso-224's G-1 was a price proxy. The link's own binding is now read from `hourly/network_<y>.parquet`.

## 3. G-DRIFT (keeper `git_sha` 3145578d → pin)

Changed on the backcast path since `3145578d`:

- `a168680b` NWPP-NEXT-10 `unit_outage_exit_ym_from_eia860` (default off, not in the recipe; `fleet/arrays.py` and `outages.py` reached only when armed). **INERT.**
- `8f94addb`, `55ce8970`, `f1de7e7f` R-CAISO-15 (`renewables.py` HSL clock repair gated `iso == "CAISO"`; `model/storage.py` CAISO battery envelope; `paths.restore_eia860_dir` called only by that CAISO reader). **INERT.**
- `853ff96f` FR-22 registry row (governance, not the solve path). **INERT.**

All hunks inert for NYISO. Form 4 is valid; the keeper's committed bundles are the control.

## 4. Legs (rule 36)

Five year-isolated shards at the pinned `main` SHA:

`python3 scripts/replay_keeper.py results/calibration/nyisonext13_span --years <y> --out-dir results/calibration/nyisonext14_<y> --set nyiso_total_east_cutset_ttc=true` (2022–2025), and the same from `results/calibration/nyisonext13_2021` for 2021.

## 5. Gates (fixed before any solve)

- **G-1 leg acceptance.** `git rev-parse HEAD` = pin. The leg's `run_config.json` `scenario_config` equals the keeper's except (i) `nyiso_total_east_cutset_ttc: true` and (ii) keys absent from the keeper's config that sit at their `ScenarioConfig` dataclass default. The log carries `measured TOTAL EAST cutset p90 transfer`.
- **G-2 the link is a live constraint, neither saturated nor inert.** In P1, the `Upstate_West>Capital_Hudson` link sits at its forward bound (flow ≥ `limit_up` − 1 MW) in **≥ 1 % and ≤ 50 %** of hours, every year. Anchor: the market's CENTRAL EAST sits at ≥ 95 % of its posted limit in 19.2 / 10.0 / 4.4 / 2.5 / 3.6 % of hours (2021–2025). The keeper's price proxy (Upstate_West more than $5 below Capital_Hudson) is 97–100 % in 2021–2023.
- **G-3 the fabricated upstate pin clears.** Upstate_West P1 hours at ≤ $0 are **≤ 100** in every year (measured A–E DA: 0 h in every year; keeper 3,110 / 1,263 / 723 / 0 / 0).
- **G-4.** C6 PASS and C8 PASS, every year.

## 6. Promotion rule (fixed before any solve)

**Promote iff G-1, G-2, G-3 and G-4 hold in all five years.** This is a structural promotion (rule 1). C1, C3a, C3b, C3c, hydro vs EIA-923 and zonal prices are **reported, not gating**, in either direction. If any gate fails, the run is registered (rule 15) and not promoted, and the owner is asked.

## 7. Reported (not gates)

Per year: C1 key classes, C3a, C3b, C3c, price MAE; zonal load-weighted Δprice vs the keeper; model hydro vs EIA-923; pooled and NE-node TWh; the link's binding hours, and their hour-level coincidence with the market's CENTRAL EAST binding hours (lift, precision, recall — nyiso-225's caveat); the mean Capital_Hudson − Upstate_West spread in the link's binding hours vs the measured (F,G)−(A–E) DA basis in the market's; D-4 FAIL rows.
