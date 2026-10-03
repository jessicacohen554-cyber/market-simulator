# PRECOMMIT — closeout-SPP-nuc: SPP full-span re-solve carrying the 2019–22 nuclear monthly-CF rows, 2026-10-03

**Written and pushed BEFORE any solve number exists.** Readings, the expected direction, the regression
rule and the recommendation rule are fixed here and fail closed. Lane `closeout-spp-nuc` (branch
`claude/closeout-spp-nuc`), desk session_01ALecU5Wjde4tkbLrnMExT9. Owner rulings R-35 (*"Data PR now;
re-solve with each ISO's next solve"*) and R-38 (this re-solve, relayed by the desk charter).

- **Keeper (control, rule 29(b)):** `2026-10-02-w0-spp107r`, bundle `results/calibration/w0_sppr_span`
  (2019–2025, every leg solved at `15a351a1b61f187822e87b4dbbce99c7ac8c568d`).
- **Pin:** `8c3ea46192074cfd422fff6532acc035d37297bb` (main after #7109, merged 02:54Z) (main carrying the closeout-nuclear-rows PR: `NUCLEAR_MONTHLY_CF_BY_YEAR` SPP/PJM/NWPP
  2019–22 rows + SolveEpoch `2026-10-03b`, `tests/unit/config/test_nuclear_cf_coverage.py`).
- **Arm:** none. The recipe is the keeper's, replayed byte-for-byte (`replay_keeper results/calibration/w0_sppr_span
  --years Y`, no `--set`). The only intended change is data: SPP 2019–22 nuclear availability reads the measured
  EIA-923 monthly CF rows (frozen derive `scripts/data/derive_nuclear_monthly_cf.py`, rule 23: an initial
  derivation for years the table never carried) instead of the year-invariant fallback pattern × (1 − EFORD).
  No ScenarioConfig field, no offer band, no free parameter (rule 21 ledger unchanged).
- **Not a matrix re-test.** No mechanism cell is tested; the SPP-109 cells (`unit_outage_short_windows_gas`,
  `wefor_residual` carrier A) stay R and are not touched. `nuclear_unit_availability` (U) is a different
  mechanism (per-unit nuclear availability), not this table's row coverage; it stays U.

## 1. G-DRIFT (rule 29(b), zero LP) — keeper SHA `15a351a1` → pin

Two instruments, both recorded in `docs/records/spp/closeout-spp-nuc/`:

1. **Measurement** — `scripts/probes/_closeoutsppnuc_gdrift_identity.py` (adapted from
   `_soco92_gdrift_identity.py`): two `fleet_only` rebuilds per year of the keeper's own recipe, `market_sim`
   from a worktree at `15a351a1` vs the pin, one shared `data/` tree; sha256 over every LP-visible fleet array
   (unit_ids, mc_base, pmax, pmin, min_gen, availability, heat_rate, emission_rate, vom, plant_group,
   fuel_type_idx, zone_idx, plant_code, nox_rate), demand, and every numeric array the fleet build returns.
2. **Reading** — hunk-by-hunk classification of `git diff 15a351a1 <pin>` on the backcast path (src/, the
   runners, scripts/lib, data/raw, configs) for LP construction and solve, which instrument 1 cannot see.

**Result (zero LP, measured before any solve):**

- **Instrument 1 at the pin** (`closeout-spp-nuc/gdrift_pin.json`): mismatches are exactly
  `availability` and `min_gen` in 2019, 2020, 2021 and 2022. Every other array, demand and every
  fleet-build state array is bit-identical in all seven years. **2023, 2024 and 2025: ALL LP INPUTS
  BIT-IDENTICAL.** `min_gen` moves with availability because the nuclear must-run floor reads post-outage
  availability. Constants changed by value: `NUCLEAR_MONTHLY_CF_BY_YEAR` (the arm), plus
  `CAMPD_BINNING_ISOS`, `EIA930_PS_FOLDED_INTO_WAT`, `RGGI_MEMBER_STATES_BY_YEAR` and three new NWPP seam
  constants. The five `*_path` ScenarioConfig defaults changed spelling only (the arrays they feed are
  identical). New field `nwpp_seam_measured_limits` (default False, NWPP-gated).
- **Same probe at main before #7109** (`93bce699`, `closeout-spp-nuc/gdrift_main.json`): ALL LP INPUTS
  BIT-IDENTICAL in all seven years. So everything that landed between the keeper's solve and #7109 is inert
  on SPP's inputs, and #7109 is the only input change.
- **Instrument 2 (reading, 66 files, 15a351a1 → 8c3ea461)**: no LIVE hunk for the SPP backcast recipe
  outside the nuclear rows.
  - `kron_hours` (`model/lp/layout.py`, 23 call sites in `rows.py` / `reserve_rows.py`) sits on SPP's LP
    path and is byte-equivalent to `sp.kron`: data, indices, indptr and index dtype were checked over 300
    random blocks, T ≤ 8760, with NaN and −0.0.
  - `model.py` basis/float32 handling and the `outages.py` slice refactor are equivalent code.
  - The iterrows → zip refactors in campd / coal / eia923 / emission_rates / eia860 / fuel / renewables are
    equivalent code.
  - `hydro_cascade`, `committed_band_measured_basis`, the reserves and the NWPP/CAISO/NYISO/SOCO/ERCOT hunks
    are gated off in the recipe or ISO-scoped elsewhere.
  - The new `campd-unit-outages-shortgas-splitremap-SPP.csv` is read only under
    `unit_outage_short_windows_gas` (False). It changes the record-only `resolved_inputs` block, not a solve
    input.
  - Scoring: rubric 3.17 → 3.18 is a CAISO-only change, so SPP numbers do not move.
- SolveEpoch `2026-10-03b` re-keys every SPP backcast year (no year scoping). That moves `cache_key`, not
  the LP and not the `solve_surface` fingerprint.

**Classification:** 2019–22 **LIVE** (nuclear rows only) → re-solve. 2023–25 **INERT** (byte-identical LP
inputs plus INERT LP construction) → **KEPT legs** from `w0_sppr_span` under this inert proof. That saves 3
shards. The train tier 2023–25 is therefore unchanged by construction.

## 2. Readings and expected direction (fixed before any solve)

From the closeout-nuclear-rows FINDING table (model − measured nuclear TWh; LP pmax clip included):

| year | nuclear Δ TWh (new − keeper), expected | criteria to watch |
|---|---:|---|
| 2019 | −0.40 | C3a +12.4 % (FAIL): less nuclear → slightly higher price, FAIL stays FAIL, direction reported |
| 2020 | −0.97 | C3a +28.5 % / C3b 0.356 (FAIL): direction reported; COAL_PRB −2.73 TWh (PASS, ±8) |
| 2021 | +0.35 | C3a +7.4 % (PASS, 2.6 points of headroom): more nuclear → lower price, away from the edge; C1 CC −8.95 / PRB +10.95 (FAIL) |
| 2022 | +1.20 | C1 CC −9.35 / PRB +10.59 (FAIL); C4 gas NRMSE 0.32 (FAIL); C8 ST_GAS 34.6 % grounded conditional pass |

Per-plant moves (Wolf Creek 210, Cooper 8036) up to ±1.1 TWh; the displaced or added energy lands on gas/coal
at the margin. Readings, computed on the composed bundle vs `w0_sppr_span`:

- **R1** nuclear TWh per year and per plant (`hourly/class_hourly_<y>`), against the expected column above
  (tolerance: sign right and |Δ − expected| ≤ 0.3 TWh; a miss is reported, not gating).
- **R2** the per-(criterion, key, year) status and value diff from `calibration_verdict.py`, all criteria.
- **R3** where the nuclear Δ went: class TWh Δ (COAL_PRB, CC_REGULAR, CT_PEAKER, ST_GAS, wind curtailment),
  unserved and dump MWh per year (`hourly/system_<y>`).
- **R4** `legitimacy_diagnostics.json`: D-4 FAIL row set (keeper's rows) and C8 forced shares.

## 3. Regression rule and recommendation (fixed)

- **Pre-fix:** no criterion flips PASS → FAIL (or CAVEAT → FAIL) in any year. C1 COAL_PRB and CC_REGULAR
  2021/22 already FAIL; their direction is reported. If 2023–25 are kept legs (§1), the train tier is unchanged
  by construction; if they are re-solved, the same no-flip rule applies to them.
- **Also gating:** every leg Optimal; unserved energy not up > 500 MWh in any year vs the keeper; no new D-4
  FAIL row; C8 stays PASS.
- **Recommendation:** all hold → **RECOMMEND PROMOTE on structure** (rule 14 [R-ACCURATE]: measured data
  replaces an estimate; a worse fit would be a bug elsewhere, not a reason to keep the fallback). Any flip or
  gate failure → **HOLD to the desk** with the flip named. The determination is reported, not gating (SPP
  stays NOT-YET either way on the keeper's open rows).
- Promotion only on the owner ruling relayed by the desk, in the desk's slot. SPP's `config_partition` is
  re-keyed by hand at promotion (W0 phase-3 RESULT §5 item 5).

## 4. Solve plan

- **Four shards, 2019/2020/2021/2022**, one year each (rules 32/34/36). Each runs
  `replay_keeper results/calibration/w0_sppr_span --years Y` with no `--set`, pinned at `8c3ea46192074cfd422fff6532acc035d37297bb`, with
  the step-0 `git fetch origin <sha> && git checkout --detach <sha>` line. Prompts come from
  `scripts/shard_prompt.py --iso SPP --year Y --sha <pin> --lane closeout-spp-nuc --bundle
  results/calibration/w0_sppr_span`, plus `eval "$(python3 scripts/prepare_solve_container.py
  --emit-exports)"` before the solve and the `unit_marginal_<Y>` push check. Out-dir
  `results/calibration/closeout_spp_nuc_<Y>`, branch `claude/closeout-spp-nuc-<Y>`.
- **Compose:** `scripts/probes/_closeoutsppnuc_compose_span.py`, adapted from `_pjmnext26_compose_span.py`,
  because `_w0_compose_span.py` is not on main.
  - The recipe check is the keeper's recipe with **zero** differing fields. Provenance keys are excluded.
  - Legs 2019–22 use `--pinned-sha <pin>`.
  - 2023–25 are kept from `w0_sppr_span` at `15a351a1`, with `--inert-proof` pointing at this PRECOMMIT §1.
  - The composer refuses if the legs' `solve_surface` fingerprint differs from the keeper's.
  - Output: `results/calibration/closeout_spp_nuc_span`.
- **Scoring and registration:** `legitimacy_diagnostics.py`, then `dashboard_add_run.py` as a probe, then
  `calibration_verdict.py`. The RESULT gives the per-(criterion, year) diff vs `w0_sppr_span`.

## 5. DO NOT REDO

Everything in §5.7's DO-NOT-REDO; SPP-109 rows 1b/1c (both R cells stay R); offer-band retunes; any `--set`.
