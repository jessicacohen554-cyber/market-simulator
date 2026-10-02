# PRECOMMIT — NWPP-NEXT-21: the priced interface (NWPP-56) on keeper #20, 2019–2025

Fixed before any solve. Owner cards 2026-10-02 (NEXT-20: "Fix both, then solve"; "Price only anchored years";
"Per-seam external zones"; "Schedule as residual"). Evidence: `FINDING-nwppnext20-seam-phase0-2026-10-02.md` (§A–§F).
Lane NWPP-NEXT-21, branch `claude/upbeat-bell-4p8c9c`, base main `0a28fedf`.

## 0. Parallel-lane check (done before this PRECOMMIT)

- No other live NWPP calibration session; NEXT-20 (`session_01GpoZnzVZBHaRnQ9TQH5Ztp`) is gone from the session list
  (`get_session`: not found), and its PR #7032 merged.
- `claude/w0-nwpp-2019…2025` belong to the close-out W0 governance lane (EIA-860 settlement re-solves), not to this
  lever. They are not salvaged here.
- Card N4 / R-a (Path 66's 4,800 MW on both sides): **still unruled by the CAISO lane.** It bears on a joint solve, not
  on NWPP's single-ISO solve, where CAISO is an exogenous price.

## 1. The arm

Keeper #20 (`2026-10-01-nwppnext16c-combined-vintage`), each year replayed from **its own leg bundle**, with exactly:
`--set reference_price_interface=true --set priced_interchange=true`.

**Why both keys (found at zero LP, this session).** `replay_keeper.py` routes each `--set` key to
`solve_and_persist` as its own kwarg. The "reference-price interface implies priced interchange" rule lives only in
the runner's CLI path (`run_calibration.py`, `run_calibration_full.py::main`). Keeper #20's `meta.json` records
`priced_interchange: false`. With only the first key, `run_year` builds no seam rows and serves the full schedule, so
the solve would be the keeper. The second key is the same arm, not a second lever: it is what the CLI flag implies.
In `run_config.json`, only `reference_price_interface` sits in `scenario_config`. `priced_interchange` is recorded in
`meta.json`.

| year | leg SHA (keeper #20) |
|---|---|
| 2019 | `1e4bd215c635aa876ab3ad75f8fb4657f4e47cec` |
| 2020 | `aa60aa43a9e27da9c7e14a8c7bcf09db1ad4dcc6` |
| 2021 | `3b38fefe402b5168c1557459a28978eb9274ed92` |
| 2022 | `11bb59fbf0d6a4b8716362f0e8c2f1899a601d11` |
| 2023 | `a54c7b97a9c588564bab90746f2dbbc44fd56838` |
| 2024 | `91f0bc2928bd348ac48f9d13c6fce7b3c8b460e8` |
| 2025 | `1a41ba5122095ef749302ddf2cb9d67f4fe89dfe` |

**Mechanism.** There are three priced seams, each in its own external zone (`IMPORT_SEAM_ZONES`) and each linked only
to its own border zone(s):

| seam | zone | limit | border | price |
|---|---|---|---|---|
| CAISO_COI | `NWPP_ext_COI` | 4,800 MW | NW, OR | MALIN anchor × CAISO net-load shape, hurdle 3 |
| CAISO_NEVP | `NWPP_ext_NEVP` | 1,933 MW | SNV | MALIN anchor × CAISO net-load shape, hurdle 3 |
| WECC_CAN | `NWPP_ext_BC` | 3,150 MW | NW | BCHA WEIM ELAP anchor (HR 37.64 / 20.60 / 10.51), priced 2023–2025 only |

Every unpriced counterparty is served at its measured flow: the served residual =
keeper schedule − the priced seams' measured legs.

**Zero-LP construction check at the pin (this session, `get_interchange_spec` / `build_interchange_fleet` /
`extend_with_import_node` / `load_demand`, keeper flags):**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| external zones | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| seam rows | 32 | 32 | 32 | 32 | 48 | 48 | 48 |
| served residual TWh | −1.96 | 4.27 | −10.39 | −9.28 | −22.12 | −19.06 | −6.15 |
| keeper demand frame TWh (native + schedule) | 279.581 | 292.940 | 289.358 | 298.960 | 280.261 | 290.216 | 302.532 |
| **arm demand frame TWh (native + residual)** | **272.855** | **274.573** | **268.646** | **277.900** | **262.091** | **271.477** | **287.331** |

`system.parquet` `demand` is the native load plus the export-positive served schedule. Native EIA-930 load is the
same in both runs; the frame moves by the priced legs (6.73 / 18.37 / 20.71 / 21.06 / 18.17 / 18.74 / 15.20 TWh).
The shard hard stop checks the arm frame over the five NWPP-* zones.

Stated, not fixed: `NWPP_ext_BC` is still built in 2019–2022, with no rows (the seam is unpriced there). Its link can
carry flow only into that zone's own slack or dump. Each shard reports that link's |flow|. A non-zero value is a
construction defect and is read before the run is used.

## 2. G-DRIFT (rule 29(b))

The pin is `86b73d6f910d4b3a179f6158727b5e31b5f8c265` (`claude/nwppnext20-pin`) = keeper code pin `33014efc` plus
`24a3dce7` (NEXT-19 wiring), `89b134af` (NEXT-20 code) and two ruff-format commits. Re-verified this session with
`git diff 33014efc 86b73d6f -- src scripts`: 11 files.

- `run_calibration.py` `require_priced_interchange_rows`: sits inside `elif priced_interchange:`. **INERT** for the
  keeper.
- `demand.py`: new `elif iso == "NWPP" and not include_interchange`. **INERT**, since the keeper serves the schedule.
- `iso_configs.py` and `registry.py`: docstrings and comments only. **INERT**.
- `spec.py`, `import_nodes.py`, `envelopes.py`, `__init__.py`: every new branch runs only under
  `reference_price_interface` / `priced_interchange`. **INERT**.
- The probes and `build_nwpp_weim_price_index.py` are off the solve path. **INERT**.

The **arm itself is the one LIVE change.** The libraries are 1.14.0 / 3.0.3 / 24.0.0 / 2.13.4.

## 3. Gates, declared ex ante

**(a) Structural STOP gate.** For each priced seam in every priced year:

- the annual net flow (export-positive, NWPP zone → external zone) has the measured SIGN, **and**
- the hourly r of the seam flow against the measured leg is > 0.

The measured legs, TWh export-positive:

| seam | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| COI | +7.0 | +15.3 | +12.1 | +12.5 | +1.1 | +2.2 | +3.0 |
| NEVP | −0.3 | +3.1 | +8.6 | +8.6 | +7.6 | +9.1 | +9.4 |
| BC (2023–25 only) | | | | | +9.5 | +7.5 | +2.8 |

Any failure means the arm is **not a promotion candidate** and the cell is recorded `R`.

Two magnitudes are too small for the sign gate to be meaningful. They are read but do not fail the gate on sign alone:

- NEVP 2019 (−0.3 TWh), whose measured leg is one-way export in 98–99.7 % of later-year hours;
- COI 2023 (+1.1 TWh).

Each is reported, with its r.

**(b) Load-bearing criteria.** No C1 / C2 / C3a / C3b / C4 record flips PASS → FAIL against keeper #20 without a stated
root cause. The comparison is `calibration_verdict --json` for both runs, diffed per (criterion, year, key).

**(c) Rule 20 forced energy and CT_PEAKER volume.** Both come from `legitimacy_diagnostics.json`. NEXT-19 §3 expects
CT_PEAKER at 2–2.7× under a West-shaped price. Any rule-20 trip means not a candidate.

**(d) The BC↔CA wheel.** Report the hours in which COI imports and BC exports at the same time (2023–25), with MWh.

## 4. Expected risk (stated so the result cannot reshape it)

At price-taker the priced seams export 20–62 TWh/yr against 10–19 TWh measured, because keeper #20's NW price sits
$2–35 below every seam (FINDING §D). The LP will close that gap by lifting NWPP's price and its thermal output.

- **Expect C1 gas and coal to rise.** They will be read at full magnitude.
- C4 coal 2023 (r 0.669 / NRMSE 0.313) may move either way. It does not decide the promotion (rule 1).
- Price stays UNSCORED in 2019–2022. 2023-06+ WEIM ELAP is report-only (R-9 / N2).

## 5. Hard stops per shard (any miss = STOP, no push)

1. `git rev-parse HEAD` = pin, and libraries 1.14.0 / 3.0.3 / 24.0.0 / 2.13.4.
2. sha256 of the four NEXT-16 inputs.
3. **Pre-solve construction:**
   - exactly three `NWPP_ext_*` zones;
   - seam rows 48 in 2023–25 and 32 in 2019–22;
   - served residual TWh equal to the §1 table ±0.01.
4. Diffs against the leg:
   - `scenario_config` differs only in `reference_price_interface` (False → True);
   - `meta.json` has `priced_interchange: true` and `reference_price_interface: true`.
5. Arm live: `flows.parquet` P1 carries links into all three `NWPP_ext_*` zones, and the COI link's Σ|mw| > 0.
6. P1 summed demand over the NWPP-* zones = the §1 arm frame ±0.05.
7. The keeper log lines are present.
8. The bundle is complete: `dispatch/<Y>_P1.parquet` and `hourly/{class_hourly,system,hydro_cascade,unit_hourly}_<Y>.parquet`.
9. The LP is feasible.

## 6. Composition and decision

1. Compose with `_nwpp42_compose_span.py --skip-diagnostics` (2023 leg first) into `nwppnext21_span`.
2. Run legitimacy diagnostics.
3. Write the attestation: NEXT-16 arm "c" plus this arm's keys.
4. Register with `dashboard_add_run --no-prune`.
5. Diff `calibration_verdict` per record against keeper #20.

**Decision rule (owner standing ruling).** Promote if structural integrity improves, even if a gate regresses. Report
every regression at full magnitude.

The arm replaces a served measured schedule with an endogenous priced exchange, against measured counterparty prices.
That is a structural gain if, and only if, gate (a) holds. If (a) fails, the seams are not following the spread, and
the arm is not structurally faithful.

The arm is not a candidate if any of these holds:

- gate (a) fails;
- rule 20 or C6 trips;
- a new failing record traces to the arm's own construction (for example, flow through the dangling 2019–22 BC zone).

Promotion and prune go on ONE owner card.
