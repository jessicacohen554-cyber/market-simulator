# PRECOMMIT — NYISO-NEXT-15: per-landing-link monthly import band — 2026-09-30

- **Session:** NYISO-NEXT-15, the orchestrator. This container runs no LP (rule 32 (a)).
- **Phase 0:** `docs/FINDING-nyiso-next15-landing-allocation-phase0-2026-09-30.md`.
- **Owner decision cards (this session):** "Build + test 5 yrs", then "P-32 per link".
- **Queue:** item 1 (the overshoot and the wrong-hours binding). Phase 0 traces it to the pooled node's landing allocation.
- **Control (form 4):** keeper `2026-09-30-nyisonext14-total-east-span` (bundle `results/calibration/nyisonext14_span`, 2022–2025) and stamped `2026-09-30-nyisonext14-total-east-2021` (bundle `results/calibration/nyisonext14_2021`).
- **Arm:** the keeper recipe plus `nyiso_import_landing_band: true`. Nothing else moves.

## 1. The mechanism (zero free parameters)

- `model/interchange/nyiso.py::build_nyiso_import_landing_band` gives each pooled border link (`NYISO_external` → Upstate_West, Capital_Hudson, NYC, Long_Island) one monthly band.
- The band sits on the link's own measured P-32 attributed net schedule. This is `attributed_zone_net`: the published PAR split, with the NE AC row excluded because it rides its own node. It is the series each link's hourly p90 envelope is already built from.
- Half-width is the existing `NYISO_IMPORT_RECON_BAND_FRAC` (2 %).
- `model/lp/rows.py::_build_import_link_rows` sums `Flow[l, t]` per month, in the node band's row slot.
- **Rule 19:** it replaces the pooled EIA-930 band, never stacks on it. The node's net import is the sum of these flows, and supplying both bands is refused.
- **Rule 14:** the pooled total moves from EIA-930 to the P-32 sum (−2 to +1 %), declared.
- **Rule 13:** backcast-only. The forecast band (the neighbour's forward position) is untouched, and a forecast config that arms the flag is refused.

## 2. G-DRIFT (keeper `git_sha` ac7d36d6 → pin)

- `2386952f` R-ERCOT-17 `ercot_south_texas_pooled_basis`: ERCOT fuel basis, default off, not in the recipe. **INERT.**
- This session's arm code: every hunk is reached only when `nyiso_import_landing_band` is true (default False). The keeper recipe's cache key is unchanged (`04d176acd9346c20` before and after). **INERT for the control.**

Form 4 is valid; the keeper's committed bundles are the control.

## 3. Legs (rule 36)

Five year-isolated shards at the pinned `main` SHA:

`python3 scripts/replay_keeper.py results/calibration/nyisonext14_span --years <y> --out-dir results/calibration/nyisonext15_<y> --set nyiso_import_landing_band=true` (2022–2025), and the same from `results/calibration/nyisonext14_2021` for 2021.

## 4. Gates (fixed before any solve)

- **G-1 leg acceptance.** `git rev-parse HEAD` equals the pin. The leg's `scenario_config` equals the keeper's except (i) `nyiso_import_landing_band: true` and (ii) keys absent from the keeper's config that sit at their dataclass default. The log carries `nyiso_import_landing_band — pooled node band`.
- **G-2 the allocation defect clears.** In P1, each pooled border link's annual mean flow is within max(3 % of |measured|, 25 MW) of its measured attributed P-32 mean, every year. Keeper misses: +35 to +246 MW downstate, −264 to −375 MW Upstate_West.
- **G-3 the cutset link stays live.** The `Upstate_West>Capital_Hudson` link sits at its forward bound in **≥ 1 % and ≤ 50 %** of P1 hours, every year.
- **G-4 no re-collapse upstate.** Upstate_West P1 hours at ≤ $0 are **≤ 100** in every year (measured 0; keeper 0).
- **G-5.** C6 PASS and C8 PASS, every year.
- **G-6 no infeasibility pressure.** P1 load-slack energy does not exceed the keeper's by more than 1 GWh in any year.

## 5. Promotion rule (fixed before any solve)

**Promote iff G-1 to G-6 hold in all five years.** This is a structural promotion (rule 1).

C1, C3a, C3b, C3c, price MAE, zonal prices, hydro, the link's binding-hour lift and spread, and the link flow in the market's CE-binding hours are **reported, not gating**, in either direction. If any gate fails, the run is registered (rule 15) and not promoted, and the owner is asked.

## 6. Prediction (recorded, not a gate)

- Upstate_West imports rise by about 260–375 MW and downstate imports fall by the same amount.
- The link's mean flow rises by a similar amount.
- The Upstate_West price falls toward measured in 2021–2022.
- Binding-hour lift improves but stays well short of the market's, because only about half of the binding-hour shortfall is imports (FINDING §2).
