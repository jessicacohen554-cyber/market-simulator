# PRECOMMIT closeout-ERCOT-w6: measured ERCOT CHP behind-the-meter share (2026-10-05)

**Charter** (desk, session_01ERkBTm23ZAP4CTZnJVD9Ss): arm `ercot_chp_btm_measured`, the transfer census's rank-1 lever,
as a single-arm span on the ERCOT keeper; score on three bench bases with the reconciled basis as the headline; do not
stack `chp_startup_covered` or `mustrun_chp_btm_holdout`; do not promote. Phase 0:
`FINDING-closeout-ercot-w6-chp-btm-phase0-2026-10-05.md` (this directory). Plan: `docs/backcast-closeout-plan-2026-10.md`
§3.ERCOT does not list this lever (it post-dates the plan); the desk charter is the stated reason for going off-plan.

## 1. Mechanism and identification

- **Field.** `ScenarioConfig.ercot_chp_btm_measured` (default off, ERCOT-only by `data.chp.chp_btm_measured_armed`,
  cache-key-optional at default). Armed per run (`--ercot-chp-btm-measured`, `replay_keeper --set`);
  `--no-ercot-chp-btm-measured` reaches the pre-arm posture. Not placed in `iso_configs._ercot_config`
  `default_scenario_overrides`: the calibration lane never applies those (the caiso-162 defect class, recorded in the
  matrix), so arming there would record the flag and change nothing; arming the ISO default is a promotion act.
- **Measured share.** Per plant, `100 × clip(1 − (resale + tolling + outgoing) / (gross − station use))`, pooled
  CY2022–24 from the plant's own EIA-923 Schedules 6/7 filing; retail counts as host supply. The CAISO-w6 derive,
  unchanged (`derive_caiso_chp_btm_share.derive`), ERCO-scoped (`scripts/data/derive_ercot_chp_btm_share.py`,
  rule 23). Rule 13: the filing regenerates yearly and responds to changed host contracts. Rule 14: the plants' own
  filings refute the 35/70 % sector default (Deer Park 2.9 %, Pasadena 0 %, Sweeny 84.9 %). Rule 25: ERCOT's own
  filings, not a transfer. Rule 21: zero fitted parameters.
- **Readers (rule 19).** One share, its existing readers: the `chp_steam_following` capacity carve, the
  `chp_export_floor_measured` grid floor (same `(1 − btm)` factor), the run-side BTM add-back
  (`run_calibration_full._btm_frame`, run column follows the flag) and the bench subtrahend (`btm_bench_twh`, reads
  the artifact whenever it exists, nyiso-149). No floor is added; the export floor's level moves with the share.

## 2. Recipe

**Arm A1** = `closeout_ercot_l1_span` replayed per year by `replay_keeper` with `--set ercot_chp_btm_measured=true`
and nothing else. Seven year-isolated shards (rule 36), pinned to the full SHA of the commit carrying this PRECOMMIT
(launch table, Addendum A). **Control:** the keeper's committed bundle (rule 29(b)); no control solve unless G-DRIFT
finds a LIVE hunk (§5).

## 3. Scoring bases

Every gate is read on three bench bases, arm vs keeper on the SAME basis, and also arm vs keeper-as-registered:

- **(a) original:** the committed ERCOT bench parts (sector-default subtrahend, fold deflation on).
- **(b) measured:** bench parts rendered with the measured subtrahend (what landing the artifact on `main` produces at
  the next ERCOT render, nyiso-149).
- **(c) reconciled (HEADLINE):** (b) plus ERCOT in `scripts/lib/benchmark_semantics.EIA930_GAS_FOLD_REFUTED`
  (the MISO-w3e route). Held as `_bench_basis_reconciled.patch` in this directory and **never landed on `main`**:
  it is owner decision #20.

## 4. Bars and kills (ex ante, before any solve)

**T1.** C1 CC_REGULAR 2019 PASS on basis (c): |model − actual| ≤ 8.00 TWh and |share| ≤ 3 pp (keeper +9.21 FAIL;
static A1r +7.51).

**Kills** (any one stops the lane at "record and stand down"):

| Kill | Condition |
|---|---|
| K1 | any C1 record PASS → FAIL on basis (c), all classes, all years |
| K2 | any C3a record PASS → FAIL on basis (c) |
| K3 | any C3b record PASS → FAIL on basis (c) |
| K4 | a new D-4 `chp_steam` row FAIL: a unit-conduct row for a plant-year that passes (or has no row) in the keeper, or a `chp_steam` window row FAIL. The named ex-ante risk is C R Wing 52176 2019 (floor ×1.50); it counts. |
| K5 | identification overrun: the model's P1 CHP grid energy (CC_CHP + CT_CHP + ST_CHP) rises by more than the static reach + 1.0 TWh in any year (reach +3.53 / +3.00 / +3.96 / +4.04 / +4.01 / +4.30 / +4.02, 2019–25) — the carve doing more than the filing allows; stop and diagnose |

K1–K3 are also reported on (a) and (b); a PASS → FAIL that appears only on (a) or (b) is reported, not a kill (the (b)
basis carries the refuted deflation, (a) the refuted default).

**Report, every year:** C1 CC_REGULAR / CC_CHP / CT_CHP / COAL_PRB / COAL_LIGNITE / ST_GAS / CT_PEAKER miss on each
basis; C3a, C3b, C4; P1 CHP grid TWh vs static reach; displacement by class (P1 unit sums, arm − keeper); the D-4
`chp_steam` floored TWh; C8; unserved energy.

**Decision rule.** T1 met and K1–K5 clear → report the scored flips and the promotion cost to the desk (no promotion
in this lane). T1 missed or any kill → record, set the ERCOT `chp_btm_measured` cell, stand down.

## 5. G-DRIFT (keeper legs `106d6bb7` → the pinned build)

Measured by `scripts/probes/_closeout_ercot_w6_gdrift_identity.py` (two `fleet_only` rebuilds per year on the keeper's
own per-year recipe, keeper sha vs build, one shared data tree, every LP-visible array hashed). Result in Addendum B.
The lane's own hunks (flag default off): `data/chp.py` (new function + ERCOT branch of the armed/for-iso routers) INERT
off; `config/scenarios.py` (field, cache-key optional at default) INERT; `run_calibration_full` (`_btm_frame` ERCOT
branch, CLI, generic-channel key) LP-INERT, scoring-LIVE for ERCOT through the bench subtrahend (basis (b), handled by
§3); `build_bench_part_zero_lp.py` and the derive INERT for the solve.

## 6. Declared side effects

1. **Bench subtrahend (ERCOT), on `main` with the artifact.** Every ERCOT render from the merge forward subtracts the
   measured CHP BTM (≈ 10.7–12.5 TWh/yr instead of ≈ 14.9–17.7): the CC_CHP actual rises ≈ 4.6–5.5 TWh/yr, and on the
   deflated basis the family reconcile newly fires in 2020–25 (×0.956–0.970 on every ERCOT fossil class). Static, this
   moves no keeper C1 status (FINDING §3, arm M). Same family as CAISO-w6's declared subtrahend change. The desk can
   hold the artifact off `main` until #20 is ruled if it prefers; the lane's PR will say so.
2. **Render leg not touched.** Per-plant BTM fields stay on the sector default (payload-source edit = cross-ISO bench
   re-stamp, the CAISO-w6 held leg). C1/C2 read `btm.parquet`.
3. **Merge order with MISO-w3e.** The MISO branch edits the same routers (`chp.py`, `_btm_frame`); this lane already
   uses the per-ISO dict form MISO-w3e introduced, so the conflict is mechanical.

## Addendum A — launch table

Pin: **`60e11319cc500262ef3bb21290a377777c6bfe7e`** (the commit carrying this PRECOMMIT). Prompts from
`scripts/shard_prompt.py` plus step 0 `git fetch origin <sha> && git checkout --detach <sha>` and the zstd-9 size rule.
Environment `env_016R8xUY4maDbppZ6TEns5V8`, auto mode, ≤ 6 alive. Launched 2026-10-05 10:01Z.

| Year | Shard session | Out-dir / branch |
|---|---|---|
| 2019 | session_011SAy94Yi6RjnsEcPWeUdyP | `closeout_ercot_w6_2019` / `claude/closeout-ercot-w6-2019` |
| 2020 | session_013MGxDWDh4sGT3iHQAVWNQz | `closeout_ercot_w6_2020` / `claude/closeout-ercot-w6-2020` |
| 2021 | session_01EW9gwCshbjfUR17vuCMFM6 | `closeout_ercot_w6_2021` / `claude/closeout-ercot-w6-2021` |
| 2022 | session_01AcpPc6UXFm9geLhjJmrsC9 | `closeout_ercot_w6_2022` / `claude/closeout-ercot-w6-2022` |
| 2023 | session_01YFbfAwtrGDAceomqqVGThi | `closeout_ercot_w6_2023` / `claude/closeout-ercot-w6-2023` |
| 2024 | session_015y1vfKBm8n62jWpSawzZQr | `closeout_ercot_w6_2024` / `claude/closeout-ercot-w6-2024` |
| 2025 | launched when a slot frees (≤ 6 alive) | `closeout_ercot_w6_2025` / `claude/closeout-ercot-w6-2025` |

## Addendum B — G-DRIFT result (keeper `106d6bb7` → build working tree = `60e11319`, flag off)

`results/phase0/ercot/_closeout_ercot_w6_gdrift_identity.json`. Completed ≈ 10:01Z, as the shards were being created and
before any shard reached its LP (the arm solve does not depend on it; it decides only whether the keeper is a valid
control).

- **Instrument 3 (every LP-visible fleet array + demand + every numeric state array, all seven years, on the keeper's
  own per-year recipe): ALL LP INPUTS BIT-IDENTICAL.**
- ScenarioConfig defaults changed: five `*_path` fields only (absolute-path strings of the two trees). Constants
  changed: `CAMPD_BINNING_ISOS`, `NUCLEAR_MONTHLY_CF_BY_YEAR`, `RGGI_MEMBER_STATES_BY_YEAR` — none reaches an ERCOT
  array (instrument 3).
- LP construction / solve, by reading: `lp/layout.kron_hours` replaces `sp.kron(eye(T), block)` with a documented
  byte-identical CSR construction; basis-status and reduced-cost copies are dtype-identical vectorisations; the UC
  package is gated on `unit_commitment_milp` (absent from the recipe, default off); `run_calibration`'s live-roster
  change runs only under `reliability_floor_layup_window_mask` (off in every ERCOT leg) and `iso != "ERCOT"`; the coal
  take-floor and NWPP seam hunks are ISO-gated away from ERCOT. **No LIVE hunk → no control solve** (rule 29(b)); the
  keeper's committed bundle is the control.
