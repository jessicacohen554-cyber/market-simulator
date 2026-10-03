# PRECOMMIT — closeout-PJM-nuc: PJM full-span re-solve on the measured nuclear CF rows (2019–22)

Lane `claude/closeout-pjm-nuc`, 2026-10-03. Owner rulings **R-35** (*"Data PR now; re-solve with each ISO's
next solve"*) and **R-38** (*"PJM + SPP re-solves on the nuclear rows now"*). Desk: session_01ALecU5Wjde4tkbLrnMExT9.
Incumbent keeper `2026-10-02-w0-pjm-fix2` (`results/calibration/w0_pjm_span`; 2019–23 at `25da6022`, 2024–25 at
`ce8820dd`). **This file is committed before any solve exists.** The readings in §3 are fixed now.

## 1. What is solved

The keeper's recipe, replayed unchanged (`scripts/replay_keeper.py results/calibration/w0_pjm_span --years Y`,
no `--set`), one year per shard (rule 36). The pin is the first `origin/main` commit carrying PR #7109
(lane closeout-nuclear-rows: `NUCLEAR_MONTHLY_CF_BY_YEAR` PJM/NWPP/SPP 2019–22, SolveEpoch `2026-10-03b`). The full
SHA is recorded in §5 at launch. No offer band, multiplier or field moves. Zero free parameters are added, and the
`authorized_price_tuning` channel is not used ("none under the channel").

The only intended change is the input. For PJM 2019–22, nuclear availability now comes from the measured EIA-923
monthly CF rows instead of the year-invariant fallback (`NUCLEAR_MONTHLY_CF["PJM"] × (1 − EFORD)` = 0.951). Rule 14
[R-ACCURATE] governs: the measured input stays even if the fit worsens.

## 2. G-DRIFT (rule 29 (b), zero LP)

These are the hunks on the PJM backcast path between each leg's solve SHA and `origin/main` `93bce699`. The audit
read the diff hunk by hunk.

**Link A: `25da6022` → `0d5f3e32` (PR #7069).** Already closed INERT for PJM in
`PRECOMMIT-pjm-closeout-r13-anchor-vintage-addendum-w0-2026-10-02.md` §G-DRIFT and re-checked against code:

| Commit | Scope | Verdict |
|---|---|---|
| 2f69901a | CAISO | INERT |
| 106d6bb7 | ERCOT coal pile | INERT |
| c463d503, 6c492459 | SOCO seams | INERT |
| 625420ff | SPP | INERT |
| b84878f3, 15c66030, c327931e | replay guard | INERT |
| 9402af20, 65d5f902 | STB reader, off the solve path | INERT |

**Link B: `0d5f3e32` → `93bce699`.**

| Commit / area | Verdict and reason |
|---|---|
| 8f359927 rubric v3.18 | INERT: scoring only; the C3c RT-window mask is live for CAISO only |
| 2ebc2f03, 556c3a96 NWPP seam limits | INERT: the field defaults off and is gated `iso == "NWPP"`; `NWPP_*` constants are token-scoped to NWPP in the surface |
| 3e9c0e3b forecast parity registry | INERT: forecast only |
| 5b9a5006 NWPP anchor CSV, epoch 03a | INERT: NWPP only |
| 0225b339 SPP MMU cut, epoch 02e | INERT: needs `spp_mmu_offer_unavailability`, False in every PJM year |
| 634506af, d57c02e7 replay overlay | INERT: replay resolution only; of the 21 flipped-default fields, only `capacity_screen_peak_measured_hindcast` differs from the record, and the overlay pins it to the recorded False |
| e86fc2c5 vectorisation (29 files) | INERT: byte-equivalent rewrite (spot checks: `outages._outage_hour_bounds`, `eia860`/`campd_bins` iterrows→zip, `kron_hours` vs `sp.kron`) |
| b767e519 LP float32 cast, cod_ramp `np.rint` | INERT: same values; half-to-even as `round()` |
| cd67797d, 3ad6a407 | INERT: docstring; census script |
| #7108 PJM-NEXT-31 | INERT: a probe and records only. It adds no field and no remap row. |

- **ScenarioConfig defaults:** none flipped. Two new fields, both default-off.
- **`pyproject.toml` / `uv.lock`:** unchanged.
- **Data:** no file a PJM solve reads changed.

**`ce8820dd` → `25da6022` (2024–25 legs).** INERT by `W0-phase3/KEPT-LEG-INERT-PROOF-2026-10-02.md` (code reading
plus a byte-identical availability/pmax/pmin/min_gen sweep).

**#7109 (the pin's own change).**
- **LIVE** for 2019–22: the nuclear rows.
- **INERT** for 2023–25: rows byte-identical under `--check`.
- TMI-1 (plant 8011) is unchanged (desk, 2026-10-03). The keeper already carries its Jan–Sep 2019 operation
  through the vintage-exit deferral. Expect no TMI effect in the 2019 leg beyond the uniform row CF.

**Why 2023–25 are re-solved anyway.** Every 2023–25 hunk is INERT, so their LP inputs are unchanged. But
`NUCLEAR_MONTHLY_CF_BY_YEAR` is a *declared* PJM solve-surface row, and its hash moves. Epoch `2026-10-03b` names PJM
with no year scope. A 2019–22 leg at the pin therefore records a different `solve_surface` fingerprint from the kept
legs' `23d4cbb5d30aefb0`. The composer's one-run check refuses mixed fingerprints, and this lane does not waive a
guard. **All seven years re-solve at one SHA** (7 shards, ~18 GiB each), which also gives a single-SHA bundle.

**Reproduction check.** The 2023–25 re-solves are, by the audit above, reproductions. §3 R4 turns that into a
reading.

## 3. Readings fixed before any number

Keeper baseline (calibration_verdict, rubric 3.18, run `2026-10-02-w0-pjm-fix2`):

| Criterion | Status | Values |
|---|---|---|
| C1 COAL_BIT | FAIL | +19.81 / +13.18 / +16.58 TWh (2019 / 2020 / 2021) |
| C1 CT_PEAKER 2021 | FAIL | −8.07 TWh |
| C3a | FAIL | −16.9 % (2022), −11.6 % (2025) |
| C3b | FAIL | 0.287 (2022), 0.222 (2025) |

Everything else PASS, CAVEAT (C3c 2019/21/22, model-class) or SKIPPED. Determination NOT-YET.

- **R1, nuclear.** First-order expected Δ model nuclear vs keeper (the FINDING §2 derived − fallback implied TWh):
  2019 −0.19, 2020 +1.75, 2021 −1.91, 2022 −2.10.
  - Expected after-gaps are ≈ −1.1 / −2.0 / −1.7 / −0.8 TWh. They are one-signed and clip-driven, the same sign as
    2023–25.
  - Pass band: each year's Δ has the predicted sign (2019 excepted, |Δ| ≤ 0.5) and lies within ±0.6 TWh of the
    prediction.
  - A miss is a FINDING, not a revert.
- **R2, displacement.** The displaced thermal energy (COAL_BIT + CC_REGULAR + other gas classes) moves opposite in
  sign to Δnuclear.
  - Σ|Δ thermal| ≤ |Δnuclear| + 0.5 TWh per year; net interchange absorbs the rest.
  - COAL_BIT 2019–21 and CC 2020 move in the direction this implies: 2020 down; 2021 up.
  - **2021 COAL_BIT (already FAIL at +16.58) is expected to worsen by ≤ ~1 TWh. That is not a flip.**
- **R3, price.**
  - C3a 2020 stays ≤ +10 % (keeper +9.6 %; more nuclear lowers the mean).
  - C3a and C3b in every year move by ≤ 1.5 pp and ≤ 0.02.
- **R4, reproduction 2023–25.**
  - Per class: |Δ| ≤ 0.05 TWh.
  - C3a: |Δ| ≤ 0.1 pp; C3b: |Δ| ≤ 0.002.
  - CO2: |Δ| ≤ 0.1 %.
  - A larger move is unexplained drift. It is attributed before any recommendation, and HOLD stands until it is.
- **R5, 2025 benchmark.** The LP output is held to R4. Any change in the 2025 *score* that comes from the EIA-923
  benchmark vintage the scorer reads today (not from the solve) is labelled "2025 EIA-923 data drift" and is not
  attributed to the re-solve.

**Decision rule.**
- **PROMOTE on structure (rule 14)** when no (criterion, year) flips PASS→FAIL and R4 holds.
- **HOLD** when any criterion flips PASS→FAIL, or R4 fails unattributed.
- A FAIL→PASS is reported but is not the objective (rule 1).
- Promotion happens only on the relayed owner ruling and in the desk's slot (after closeout-PJM-impl #7110). It
  carries `unit_marginal` for every year (rule 15), `fleet_census_<Y>.json`, the R-36/R-37 ledger entries carried
  forward verbatim, and an explicit `authorized_price_tuning` "none under the channel" block.

## 4. Mechanism matrix

No mechanism is tested; this is data coverage. No PJM.js cell moves. An evidence line goes on the nuclear-availability
cell only if one exists.

## 5. Shards

Recorded at launch: the pin SHA, one shard per year 2019–2025 (≤ 6 alive), env `env_016R8xUY4maDbppZ6TEns5V8`, and
prompts from `scripts/shard_prompt.py --iso PJM --all-years --sha <pin> --lane closeout-pjm-nuc --bundle
results/calibration/w0_pjm_span --note "closeout-pjm-nuc: nuclear CF rows 2019-22 (R-35/R-38)"`.
