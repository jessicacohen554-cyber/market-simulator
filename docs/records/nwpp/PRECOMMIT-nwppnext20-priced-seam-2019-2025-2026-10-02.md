# PRECOMMIT — NWPP-NEXT-20 lever B: the priced seam (`reference_price_interface`) on keeper #20, 2019–2025

Fixed before any solve. Lane closeout-NWPP (plan §3.9 step 3). Owner card 2026-10-02 "Fix both, then solve". Evidence:
`FINDING-nwppnext20-seam-fixes-and-censuses-phase0-2026-10-02.md` (§1 the fixes and the price-taker bound). **SOLVES HOLD**
until the W0 lane (`claude/closeout-b-w0-foundation`) merges and the desk releases this lane. Lever C failed its census (FINDING §2)
and has no PRECOMMIT. R-3 is not queued ahead of B (FINDING §3).

## 1. The arm (one key)

Keeper #20 (`2026-10-01-nwppnext16c-combined-vintage`). Each year is replayed from **its own leg bundle**
(`replay_keeper.py <leg> --set reference_price_interface=true`), legs:

| year | leg SHA (keeper #20) |
|---|---|
| 2019 | `1e4bd215c635aa876ab3ad75f8fb4657f4e47cec` |
| 2020 | `aa60aa43a9e27da9c7e14a8c7bcf09db1ad4dcc6` |
| 2021 | `3b38fefe402b5168c1557459a28978eb9274ed92` |
| 2022 | `11bb59fbf0d6a4b8716362f0e8c2f1899a601d11` |
| 2023 | `a54c7b97a9c588564bab90746f2dbbc44fd56838` |
| 2024 | `91f0bc2928bd348ac48f9d13c6fce7b3c8b460e8` |
| 2025 | `1a41ba5122095ef749302ddf2cb9d67f4fe89dfe` |

**What arming does (wired at NEXT-19, fixed at NEXT-20).**
- The measured EIA-930 schedule (`nwpp_net_interchange`) is dropped from the energy balance. Rule 19: replaced, never
  stacked.
- Three priced seams land in `NWPP_external`, 8 export + 8 import tranches each:
  - CAISO @ MALIN on CISO **net** load, 6,733 MW, hurdle 3.0;
  - WECC_SW @ PALOVRDE on the NEVP proxy, 6,049 MW, hurdle 2.0;
  - WECC_CAN @ **BCHA ELAP**, 3,475 MW, hurdle 2.0.
- HR by year 2023–25 is measured; 2019–22 take the flat means 11.05 / 14.43 / 22.38.
- The node links to the border zones at the summed seam limits.
- An empty priced build is refused.

**Rule checks.**
- Rule 13: the anchors are counterparty prices on the far side of each seam (MALIN, PALOVRDE, BCHA), never the
  footprint's own price, and forward-reproducible as gas × HR × neighbour load shape.
- Rule 14: the misalignments are declared — PALOVRDE stands in for the Desert-SW, and AESO's 325 MW is unpriced.
- Rule 19: one interchange mechanism.
- Rule 24: a registered key, nothing else.
- Rule 25: no other ISO's fitted value; card N4's CAISO `WECC_import` double count stays routed (NWPP is solved alone;
  CAISO's keeper is untouched).

## 2. G-DRIFT (rule 29(b)) — decided at release, not now

Main has moved since pin `33014efc`, including this PR and, before release, the W0 EIA-860 settlement. At release the
parent:
1. pins a full 40-char SHA on main that carries this PR and W0;
2. classifies every hunk between `33014efc` and that SHA on the NWPP backcast path as INERT-with-reason or LIVE.

- **If every hunk is INERT:** the keeper #20 bundle is the control, and 7 arm shards run.
- **If any hunk is LIVE** (W0 re-vintages the fleet, which is expected to be LIVE): a 7-shard **control span** (keeper
  recipe at the new pin, no `--set`) runs alongside the 7 arm shards. The arm is scored against that control. Keeper #20's
  numbers are reported only as context.

NEXT-20's own code hunks are INERT for the keeper recipe: all of them sit on the default-off seam path or in docs. This is
asserted by `test_nwpp_default_config_builds_no_seam_rows`.

## 3. Gates (pre-fixed; the owner charter's reading)

- **Target:** C4 coal 2023 r ≥ 0.70 **and** NRMSE ≤ 0.30, with C4 coal 2022 / 2024 / 2025 still passing (r ≥ 0.70,
  NRMSE ≤ 0.30).
- **Watch, reported at full magnitude, any year:**
  - C4 gas r / NRMSE;
  - CT_PEAKER energy (NEXT-19 §3: a West-shaped price lifts CT 2–2.7× at price-taker);
  - rule 20 forced-energy shares from `legitimacy_diagnostics.json`;
  - C1 fuelmix;
  - C2 system volume.
- **Structural check (pre-fixed):** model annual net export vs measured Σ(NG−D) = −6.63 / −3.12 / +5.43 TWh (2023–25).
  A year off by **more than 10 TWh** (≈ 3.5 % of footprint load) means the seams over- or under-trade. The arm is then
  **not a promotion candidate on structure**, whatever C4 reads.
  - The price-taker upper bound is +39.9 / +52.1 / +18.3 TWh (FINDING §1c). The bar is set before any solve and is
    never moved.
- **2019–2022 watch:** the WECC_CAN flat HR prices the Canada seam at $53 / $41 / $83 / $139. FINDING §1b gives the
  likely upward bias. Each year's WECC_CAN net export is reported, and if any year exports > 2,500 MW in more than half
  its hours, that is called out explicitly.

## 4. Expectation (ex ante)

- Price shape: the NW price gains CAISO's within-day shape and a higher Jul–Oct level. Direction on C4 coal 2023 is +.
- Magnitude: NEXT-17 §4 shows that even at measured prices about half of Bridger's Jun–Oct gap survives, and Feb–May
  is untouched. **Clearing C4 coal 2023 is not expected; P ≈ low–med.**
- Risk: C4 gas and CT_PEAKER regress as the seams pull NWPP's price up (arm G showed gas fragility between days).
- A clear would be checked for its mechanism before it is believed.

## 5. Hard stops per shard (any miss = STOP, no push)

1. `git rev-parse HEAD` equals the pin. Library versions are 1.14.0 / 3.0.3 / 24.0.0 / 2.13.4 (or the pin's
   `requirements.txt`, stated).
2. The `scenario_config` diff against the leg's own `run_config.json` is exactly `reference_price_interface` False → True
   (arm). For a control shard it is empty, apart from fields the G-DRIFT audit names.
3. Arm live: the log shows NWPP priced rows built (48 rows = 2 × 8 × 3), `NWPP_external` in the zone list, and the
   measured schedule NOT applied.
4. P1 summed demand: 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 / 302.532 TWh, ± 0.05. Demand excludes
   the external node.
5. Keeper log lines are present: `coal per-yard budget`, `coal take floor`, `coal monthly pile`, `NWPP Path 76 (Alturas)`.
6. The bundle has `dispatch/<Y>_P1.parquet`, `hourly/{class_hourly,system,hydro_cascade,unit_hourly,unit_marginal}_<Y>.parquet`
   (rule 15: `unit_marginal` every year).
7. The LP is feasible. No scorer is run in a shard; each shard pushes its full bundle (rule 34).

## 6. Composition and decision

- **Compose.** Run `_nwpp42_compose_span.py --skip-diagnostics` (2023 leg first). Then run legitimacy diagnostics, the
  attestation (arm keys added to `_ARMED`/`_SOURCES`), `dashboard_add_run --no-prune`, and `calibration_verdict --json`
  for the arm and its control. Diff per (criterion, year, key).
- **Decision rule** (owner standing ruling): promote if structural integrity improves, even if a gate regresses. Every
  regression is reported at full magnitude.
  - It is not a candidate if it trips the §3 structural check, rule 20 or C6, or if it opens a failing record that traces
    to the seam construction itself (e.g. the 2019–22 Canada fallback).
  - Promotion and prune go on ONE owner card.
  - The decision is never chosen by C4 coal 2023 alone (rule 1).
- **If B lands but 2023 still fails:** run plan §3.9 step 5 (`coal_captive_marginal_fuel_price` in composition). If the
  residual is then Feb–May, run step 6, the ledger row. R-3's cumulative ceiling is the composition partner named in
  FINDING §3.
