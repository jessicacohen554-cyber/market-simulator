# PRECOMMIT — NYISO-NEXT-18: the mid-vintage retiree carry (Indian Point 3) — 2026-09-30

- **Session:** NYISO-NEXT-18, the orchestrator. This container runs no LP (rule 32 (a)).
- **Phase 0:** `docs/FINDING-nyiso-next18-upstate-price-phase0-2026-09-30.md`.
- **Queue:** item 1 (2021 C3a +11.1 %, the owner's block on `complete`).
  - Phase 0 answers the queued question: the link, not the upstate stack (FINDING §1). No new transport lever is proposed there.
  - This arm is the defect phase 0 found on the way: Indian Point 3 missing from Jan–Apr 2021 (FINDING §2). It is **not** a CENTRAL EAST lever.
- **Rule 28:** all three flags are cell **U** in the NYISO shard. No adjudicated cell (R / I / G) is re-tested.
- **Control (form 4):**
  - Keeper `2026-09-30-nyisonext16-winter-spread-span` (bundle `results/calibration/nyisonext16_span`, 2022–2025).
  - Stamped `2026-09-30-nyisonext16-winter-spread-2021` (bundle `results/calibration/nyisonext16_2021`).
- **Arm:** the keeper recipe plus three existing flags set true. Nothing else moves.
  - `mid_vintage_exit_carry`
  - `fleet_zone_vintage_coords`
  - `retiree_vintage_status_scope`

## 1. G-DRIFT (keeper `git_sha` 38ea5423 → pin)

Every commit touching the backcast solve path since the keeper (`git log 38ea5423..origin/main -- src/market_sim scripts/run_calibration*.py scripts/replay_keeper.py scripts/lib data/raw/_validation-source data/raw/reference`):

| commit | change | class |
|---|---|---|
| `ca84177c` R-CAISO-17 | CAISO EIA-930 clock windows under `caiso_eia930_clock_repair` | INERT: another ISO's branch (audited by NEXT-17) |
| `41e0f242` R-ERCOT-19 | commitment-profile sub-gates, `floors.py` / `offer_curves.py` | INERT: default-off flag absent from the keeper recipe |
| `13b721ea` miso-292 | `actual_lmp.json` MISO 2019/2022 rows | INERT: no NYISO row touched |
| `d757b216` R-CAISO-18 | `caiso_intertie_unprinted_year_measured_gas` | INERT: default off, CAISO |
| `1f4793ae`, `4ddb0ae4` NEXT-17 | `nyiso_fg_split` | INERT: default off, byte-identical off (`tests/iso/nyiso/test_nyiso_fg_split.py`) |
| `7105f162`, `400d7bd6` SPP-105 | `spp_gas_crow_residual_outage` + path | INERT: default off, SPP |
| `1d83b224` NWPP-NEXT-14 | `campd_per_unit_vintage_denominator` | INERT: default off, absent from the keeper recipe |
| `dd40dac5` NWPP-NEXT-14 | `cc_subfloor_eia923_heat_rates` | INERT: default off, absent from the keeper recipe |
| `cd589798` R-CAISO-20 | overnight clean rung | INERT: default off, CAISO |

All hunks are INERT. Form 4 is valid; the keeper's committed bundles are the control.

**Zero-LP pre-flight** (`scripts/probes/nyisonext18_fleet_census.py`, all five years; FINDING §3.1):

- Demand is identical to the keeper in every year.
- The fleet changes are exactly: IP3 into Lower_Hudson, Jan–Apr 2021 (2,894.7 GWh available); NYC and Capital retiree CTs (2022: 199.1 GWh; 2023: 1,304.4; 2024: 41.4); Nassau Energy and Hilton re-zoned out of the Upstate_West fallback; and 2025's zero-availability phantom rows removed.

## 2. Legs (rule 36: one year-isolated shard per year, all five registered years)

At the pinned `main` SHA:

- 2022–2025: `python3 scripts/replay_keeper.py results/calibration/nyisonext16_span --years <y> --out-dir results/calibration/nyisonext18_<y> --set mid_vintage_exit_carry=true --set fleet_zone_vintage_coords=true --set retiree_vintage_status_scope=true`
- 2021: the same from `results/calibration/nyisonext16_2021`.

## 3. Gates (fixed before any solve; every value anchored to the keeper or to measured data)

- **G-1 leg acceptance.**
  - `git rev-parse HEAD` equals the pin.
  - The leg's `scenario_config` equals the keeper's except (i) the three flags true and (ii) keys absent from the keeper at their dataclass default.
- **G-2 conservation.** Per year and per zone, P1 demand equals the keeper's within 0.1 GWh.
- **G-3 the repair is live.**
  - 2021: NYCA nuclear P1 energy Jan–Apr is within ±5 % of the NYISO fuel-mix nuclear energy for Jan–Apr (keeper: −25 %).
  - 2021 May–Dec and every month of 2022–2025: NYCA nuclear P1 energy equals the keeper's within 1 GWh per month.
- **G-4 no infeasibility pressure.** P1 load-slack energy does not exceed the keeper's by more than 1 GWh in any year.
- **G-5.** C6 PASS and C8 PASS, every year.
- **G-6 conduct.** No D-4 failure row keyed (year, mechanism, plant) appears in the arm's composed `legitimacy_diagnostics.json` that is absent from the keeper's, in any year. Rows are keyed by the regex `(\d{4}) (.+?): plant (\S+)` (the NEXT-16 `_d4_fail_keys` pattern).

## 4. Promotion rule (fixed before any solve)

**Promote iff G-1 to G-6 hold in all five years.** This is a structural promotion (rule 1; rule 14): it restores a measured plant, in its measured zone, for its measured operating months, and it drops a unit EIA itself marks out of service. Zero free parameters.

The following are **reported, not gating**, in either direction:

- C1, C3a, C3b, C3c and price MAE;
- zone-month errors;
- the CE-regime Capital − Upstate spread against measured;
- Astoria GT (55243) and Hudson Avenue dispatch against CAMPD.

If any gate fails, the run is registered (rule 15), not promoted, and the owner is asked.

## 5. Prediction (recorded, not a gate)

- **2021:** Jan–Apr prices fall system-wide. About 1 GW of zero-cost supply displaces marginal gas. 2021 C3a moves down from +11.1 %. Whether it crosses the ±10 % band is not predicted with confidence.
- **2022–2025:** the footprint is ≤ 1.3 TWh of mostly NYC CT availability. Every criterion should move by ≤ 0.3 points.
- **The CENTRAL EAST spread is not expected to move** (FINDING §1). IP3 is downstate.
