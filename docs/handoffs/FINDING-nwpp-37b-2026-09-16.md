# FINDING — NWPP-37b: the pool members are screened before the sum (the follow-on to #6206)

Lane NWPP-37, second session (branch `claude/charming-cannon-q5hkxw`; carried as **NWPP-37b** so
the record does not collide with the lane that landed first) · model Fable (`claude-fable-5-1`) ·
original base `6d1a144d`, **rebased onto `origin/main` `e4e612ca`**, which already carries PR #6206
(`e1e8d809`, "Apply the EIA-930 NG: unit-slip screen at the frame constructor", FINDING / PRECOMMIT
`-nwpp-37-2026-09-16.md`). PRECOMMIT: `PRECOMMIT-nwpp-37b-2026-09-16.md` (written before any edit,
preserved verbatim with a status note). No solve, no shard, no ScenarioConfig field, no matrix row.

## 0. REPORT FIRST

1. **Two sessions ran the NWPP-37 charter in parallel and reached the same shape.** #6206 merged
   first: shape (A), the screen at the frame constructor (`_eia_hourly_frame` via
   `_eia_hourly_frame_raw`, `_eia_hourly_frame_filled`'s reindex branch, `_ercot_hourly_frame` after
   the long fill), the three `actuals` applications collapsed to one, the docstring repaired. This
   session's independent construction differed only in WHERE the single-BA seam sat
   (`_eia_hourly_frame_filled` rather than `_eia_hourly_frame`) and in **one substantive point**:
   the NWPP pool. On rebase this branch **adopts #6206's construction wholesale** and carries only
   the delta.
2. **The delta: the pool is screened PER MEMBER, before the sum.** #6206 screens the POOLED series
   and its FINDING §5 measured why that is not enough — "pooled recovers 96 % of the 1.169 TWh
   artifact; per-member would recover all of it" — and routed it as a threshold question. This
   session's reading is that it is not one: the statistic, factor and anchor are untouched; only
   the population the two order statistics are computed over is the member's own series, which is
   the population `build_calibration_reference._pool_hourly_benchmark` already screens on (#6206
   §5 itself names that disagreement "the real finding") and the population the NWPP-10 demand
   dropout screen already runs on for the same reason ("a footprint sum can never read zero, so
   the screen has to run per member"). A flagged member hour is bridged by the member's own
   interpolation, so the pooled hour keeps the other sixteen members' real output.
3. **Measured against main (#6206) over all nine regions × 2019–2026: NWPP moves, nothing else
   does.** 648 reader outputs compared; 20 move, all NWPP; every other region reads 0 moved
   outputs and 0 moved columns, `bench` / `renewable_gen` controls identical. The rebased tree is
   **byte-identical to this session's original pre-rebase result** (0 movers between them), which
   also shows #6206's pooled pass is inert once the members are repaired (0 residual flags on NWPP
   2023–2025).
4. **What per-member changes for NWPP, at full magnitude (§3).** October 2025 pooled hydro repin
   target 7,120.0 (main) → **7,095.6 GWh**; December 2025 12,927.2 → 12,898.5; pooled `NG: WAT`
   peak 2025 **42,688 → 23,607 MW** (main's pooled pass leaves NWMT's 32,416 MW hour in — 1.83× the
   pooled anchor, 49× the member's); 2024 Aug / Oct **+8.8 / +7.9 GWh** — the pooled pass NaNs the
   whole pooled hour and `measured_monthly_hydro`'s nansum then drops sixteen members' real
   generation with it, while per-member keeps it and removes only the slip.
5. **Two flags #6206 §5 called "not obviously an artifact" are reported, not adjudicated:** PGE
   2023 `NG: OTH` h732 (119 MW vs a 33 MW p99.9, MW-scale) and NWMT 2024 `NG: WAT` h5556
   (1,782 MW vs 641 MW — roughly 4× NorthWestern's whole hydro nameplate, which reads as an
   artifact on the fleet, but the threshold is not this lane's to move). The G1 trip this
   session's PRECOMMIT pre-registered (SPP 2023 net-load probe, SOCO 2025 gas floor) now belongs
   to #6206's construction, not to this delta: against main both rows read 0.

## 1. Enumeration

PRECOMMIT-nwpp-37b §1 (25 rows, classified at `6d1a144d`) and #6206's PRECOMMIT §2 agree on
every reader: 19 direct `_eia_hourly_frame_filled` reads, six direct fuel-column readers, zero in
`demand.py`. This session additionally counted the pool constructor as the seventh fuel-column
reader (row 25) — the row this delta is about.

## 2. What this branch adds on top of main

`src/market_sim/data/eia930/frames.py` (+76): `_screen_pool_member_frame` (screen one member on
its own population; bridge flagged hours by that member's interpolation at the flagged positions
only, leaving `min_count=1` and not-yet-reporting storage semantics untouched); `_pool_member_frames`
applies it to every member; docstrings on `_pool_member_frames` and `_pool_hourly_frame`. #6206's
pooled pass at `_eia_hourly_frame` is left in place as the constructor's uniform guarantee — a
different series, measured inert once the members are repaired, so no series is screened twice.

`src/market_sim/data/eia930/envelopes.py` (+26, docstrings / comments only): rows 1, 2, 4, 5 say
their column arrives screened and what a flagged hour does in each reader.

`tests/unit/data/test_eia930_fuel_spike_screen.py` (+177, on top of #6206's file):
`TestScreenOnTheNeighbourAndSolarReaders` (the neighbour net-load driver, the CAISO solar
fraction, the reindexed short-year branch), `TestScreenOnThePoolMembers` (the pooled hour equals
16 × member + the slip member's interpolation, for `NG: WAT` and `NG: WND`; a member slip at 10×
the member's peak that sits UNDER 2.5× the pooled peak is still caught; no phantom monthly energy),
`TestNwppLivePins` (`fulldata`: pooled `NG: WAT` peak < 40 GW in 2024 and 2025; October 2025 =
7.0956 TWh). #6206's tests pass unchanged (32 passed in the file).

Not touched: `actuals.py` (main's), `demand.py`, `neighbor_price.py`, `virtual_bids.py`,
`zonal_shares.py`, any config, registry, verdict script, frontend, plan, ledger, matrix file.

## 3. Main (#6206) → this branch, measured

Method: `measure_seam.py` on main's tree and on the rebased tree, identical script (the same one
that produced this session's pre-rebase BEFORE / AFTER); every `NG:` column the seam hands out,
the screen's residual flags on it, every fuel-column reader's output and the two controls, per
region × 2019–2026.

| region | reader outputs compared | moved vs main | `NG:` columns moved vs main |
|---|---:|---:|---|
| ERCOT, CAISO, PJM, MISO, NEISO, NYISO, SPP, SOCO | 72 each (CAISO 80) | **0** | none |
| NWPP | 72 | **20** | 2023 `NG: OTH`; 2024 `NG: COL/NG/OIL/OTH/WAT`; 2025 `NG: COL/NG/OTH/WAT` |

| NWPP output | year | main (#6206) | this branch | Δ |
|---|---|---:|---:|---:|
| `measured_monthly_hydro`, October | 2025 | 7,120.0 GWh | **7,095.6 GWh** | −24.4 |
| same, December | 2025 | 12,927.2 | 12,898.5 | −28.8 |
| same, annual | 2025 | 110.3171 TWh | 110.2639 TWh | −0.0532 |
| same, Aug / Oct / Nov | 2024 | 8,685.4 / 6,511.3 / 8,620.0 | 8,694.2 / 6,519.2 / 8,614.4 | +8.8 / +7.9 / −5.6 |
| same, annual | 2024 | 105.0263 TWh | 105.0374 TWh | +0.0111 |
| same | 2023 | — | — | 0 |
| pooled `NG: WAT` peak | 2024 / 2025 | 20,302 / 42,688 MW | 19,981 / 23,607 MW | NWMT h5556 (1,782) and h6874 (32,416) caught |
| `measured_hydro_hourly_envelope` | 2024 / 2025 | — | 92 h ≤ 290 MW / 186 h ≤ 791 MW | bucket p95s |
| same, climatology fallback years | 2019–22, 2026 | — | moves with the 2023–25 pool | |
| `measured_hydro_min_flow_level` | 2024 / 2025 | — | 2 months ≤ 0.9 MW / Dec −66.7 MW | |
| `measured_gas_floor_profile` (NEVP `NG: NG`, no NWPP caller) | 2024 / 2025 | — | 30 h ≤ 240 MW / 91 h | |

Against the ORIGINAL base (`6d1a144d`, before either lane) the combined effect is this session's
pre-rebase table: October 2025 8,243.5 → 7,095.6 GWh (−1,148.0), pooled peak 817,202 → 23,607 MW,
and the rebased tree reproduces it to the byte.

The sign of the 2024 August / October rows is the construction argument in one number: on a
pooled-only pass a flagged pooled hour becomes NaN and `measured_monthly_hydro`'s `nansum` drops
the WHOLE footprint hour — ~19.5 GW of sixteen members' real hydro goes with the 65,891 MW slip —
whereas per member removes the slip and keeps the rest.

## 4. Gates

| gate | result |
|---|---|
| G1 byte-identity vs main, non-NWPP | **PASS** — 0 of 576 non-NWPP reader outputs move; 0 columns move |
| G2 controls | PASS — `bench` / `renewable_gen` identical in nine regions |
| G3 column set | PASS — NWPP only, the pre-registered member flags |
| G4 NWPP direction | PASS — the repin target falls where a slip was missed and rises where real members were dropped; 0 class-T movers |
| G5 tests | PASS — screen file 32/32 (#6206's 20 + 12); pool frame 6/6; full fast lane: §6 |
| G6 ruff | PASS — check + format clean |

## 5. Rules

13 / 14: a telemetry defect repaired by NaN + the member's own interpolation, on the member's own
population; no residual consulted. 19: one mechanism; the pooled pass and the member pass are
different series, and the pooled pass is measured inert once members are repaired. 23: the
NWPP hydro-budget derive (`build_nwpp_hydro_budget.py`) now reads repaired members — a source-data
change the owning lane re-derives on, not this one. 27: edited locally, pushed as bytes,
fetch-back verified. 28(c): no field, no row. 31 / 32 / 34: no solve.

## 6. Routed to NWPP-DESK

1. **Adjudicate the two member flags #6206 §5 named** (PGE 2023 `NG: OTH` 119 MW; NWMT 2024
   `NG: WAT` 1,782 MW) on the BAs' own fleet data. This branch screens them because the unchanged
   statistic does; it does not decide the threshold.
2. **#6206 §6 (SOCO 2024 `NG: OIL` cold-snap run) stands**; this session found the same hours
   independently (530 → 801 → 350 MW over h386–392) and changes nothing there.
3. **NWPP-40's `eia930_monthly` posture**: with the members repaired the first of NWPP-32 §3.2's
   two objections is closed; the 930-vs-923 population mismatch (NWPP-32 §7 item 2) still stands.

## Log entry

*(appended verbatim to `docs/calibration-log/nwpp.md` by the NWPP ADDITION DESK — plan §8.0 rule 1;
this lane did not write it into that file.)*

## nwpp-37b — 2026-09-16 — pool members screened before the sum (follow-on to #6206, zero-LP)

Second NWPP-37 session, Fable claude-fable-5-1, branch claude/charming-cannon-q5hkxw, rebased
onto e4e612ca (carries #6206). PRECOMMIT + FINDING `docs/handoffs/*-nwpp-37b-2026-09-16.md`.
No solve, no field, no matrix row.

Ran the NWPP-37 charter in parallel with the lane that merged as #6206 and reached the same
shape (A). On rebase adopts #6206's constructor seam and carries ONE delta: the NWPP pool is
screened PER MEMBER before the sum (`frames._screen_pool_member_frame`), the population the
reference builder and the NWPP-10 dropout screen already use — the item #6206 §5 measured (pooled
recovers 96 %) and routed. Statistic, factor, anchor unchanged. Measured vs main over nine
regions x 2019-2026: NWPP moves (20 outputs), nothing else; October 2025 pooled hydro 7,120.0 →
7,095.6 GWh, pooled NG: WAT peak 42,688 → 23,607 MW (NWMT 32,416 MW hour caught), 2024 Aug/Oct
+8.8/+7.9 GWh because a pooled-only pass NaNs the whole footprint hour and drops sixteen real
members with the slip. Adds neighbour / CAISO-solar / short-year / pool-member / NWPP live-pin
tests (+12). Routed: adjudicate PGE 2023 OTH 119 MW and NWMT 2024 WAT 1,782 MW member flags.
