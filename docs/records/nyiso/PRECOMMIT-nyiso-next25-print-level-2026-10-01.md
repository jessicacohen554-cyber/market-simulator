# PRECOMMIT — NYISO-NEXT-25: price NYISO's daily gas at each day's own Transco Z6 NY print — 2026-10-01

Phase 0: `docs/records/nyiso/FINDING-nyiso-next25-offcap-winter-gap-phase0-2026-10-01.md`. Fixed before any solve.

**The arm.** One new field, default off, zero free parameters: `nyiso_gas_daily_print_level`.
In `_nyiso_hub_daily_gas_prices` (both branches), a priced day = `hub_level × print / trade-day print mean`.
The calendar-day renormalisation is skipped. The case is rule 14 (the measured print is that day's price)
and rule 19 (the downstate CTs already price the same commodity at the raw print). It is not the residual:
Feb 2023 moves the other way, and that is pre-registered (rule 1). This is a first test; no cell has been
adjudicated (`nyiso-248` was level-free).

**Pin.** The `main` commit carrying this PRECOMMIT and the field (recorded in every shard prompt and in the RESULT).

## 1. G-DRIFT (form 4: committed bundles are the control; no control solve)

| span | solve-path hunks | class |
|---|---|---|
| keeper `fdc41f36` → `f2b83ef2` | classified by NEXT-23 PRECOMMIT §1 (130 comment/docstring-only, 11 string-literal-only, the rest ISO-gated or default-off incl. `nyiso_gas_flow_date`) | INERT |
| `f2b83ef2` → main `5033ad9a` | `scripts/lib/bench_stamp.py` (a bench-stamp alias row), `scripts/lib/forecast_provenance.py` (docstring) | INERT: neither is read by `replay_keeper` / `run_year` |
| this PR | the new field (hash-dropped at False), the hubs.py branch | INERT off (unit test `test_off_is_byte_identical_default`) |

Solve surface, `surface_rows("NYISO")`: 228 = 228 rows with the same hash at main and with this PR.

## 2. Footprint (zero LP; fleet rebuilt with the flag off and on, cap on)

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| gas rows whose fuel price moves | 448 | 337 | 328 | 330 | 342 |
| max \|Δ cell\| ($/MMBtu) | 1.0 | 3.5 | 8.8 | 6.0 | 28.3 |
| NYC CC Jan gas ratio on / off | 0.97 | 0.98 | 1.00 | 1.15 | **1.17** |

pmax, availability and demand are untouched (only `fuel_prices` moves).

## 3. Legs (rule 36: one year-isolated shard per year)

- **Arm A** (vs the keeper): `replay_keeper.py results/calibration/nyisonext21_span --years <y> --out-dir results/calibration/nyisonext25_<y> --set nyiso_gas_daily_print_level=true`. Use `nyisonext21_2021` for 2021.
- **Arm B** (composite, vs the NEXT-23 arm): the same command with `--set nyiso_gas_flow_date=true --set nyiso_gas_daily_print_level=true`, out-dir `nyisonext25f_<y>`.

B isolates the flag on the flow-dated build (Jan-2025 `c` = 0.65). Its control is the NEXT-23 bundles on
PR #6984's branch. B is promotable only with the owner's ruling on #6984.

## 4. Gates (each arm vs its control's committed bundles, all five years)

- **G-1 leg acceptance.** `git rev-parse HEAD` = the pin. The leg's `scenario_config` equals the control's
  except the arm's flag(s) and keys born since, at their dataclass default.
- **G-2 the repair is live.** 2025: the NYC P1 mean price over the January days on which the cap does not
  bind (FINDING population) is **higher** than the control's.
- **G-3 conservation.** Per year and zone, P1 demand equals the control's within 0.1 GWh. P1 load-slack
  exceeds the control's by ≤ 1 GWh.
- **G-4 protective.** C6 and C8 PASS, every year.
- **G-5 conduct.** The composed `legitimacy_diagnostics.json` has no D-4 FAIL row, keyed
  (year, mechanism, plant), that is absent from the control **and carries ≥ 5 GWh**. New FAIL rows under
  5 GWh are listed in the RESULT and do not block on their own. The threshold is set here, ex ante: NEXT-23's
  unrelated fuel-date perturbation produced 0.2–2.9 GWh bridge rows in four years.

## 5. Promotion rule

**Arm A: promote iff G-1 to G-5 hold in all five years and no year's determination downgrades vs the
keeper.** The basis is structural (rules 14 and 19). If any gate fails or any year downgrades, the run
is registered (rule 15), not promoted, and the owner is asked.

**Arm B:** reported as an owner card. It is promoted only if the owner promotes NEXT-23 (#6984) and B
passes G-1 to G-5 vs the NEXT-23 bundles.

Reported, not gating: C1, C2, C3a, C3b, C3c per year; zone prices; the winter vs non-winter split.

## 6. Prediction (recorded, not a gate)

- C3a 2025 improves by 2–5 pts. Bracket NYC −9.1 % → −6.7…−5.0 %; Capital_Hudson −11.1 → −6.5 %.
- 2024 improves by about 1–2 pts. 2021–2022 move < 1 pt.
- 2023 winter worsens (Feb `c` = 1.14). Upstate_West rises in 2024–2025.
- B moves 2025 further than A, because flow-dated Jan `c` is 0.65 vs 0.78.
- The Central East congestion deficit remains (ledgered).
