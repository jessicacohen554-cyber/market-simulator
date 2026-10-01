# RESULT — SPP-95: SPP's own 2020/2021 wind curtailment rows, solved and PROMOTED.

**Lane** SPP-95 (solves SPP-94's plan) · keeper `2026-09-26-spp-86-coal-extract` (bundle `spp86_arm_span`) is the
control (rule 29(b) form 4, no control solve) · PRECOMMIT `docs/records/spp/PRECOMMIT-spp-94-curtail-rows-2026-09-27.md`,
merged at `020bb1c5cb38b73da686dc4e83d1620c415b1437` before any shard launched · registered run
**`2026-09-28-spp-94-curtail-rows`**, bundle `results/calibration/spp94_arm_span` (2019–2025) · owner ruling on
promotion: **PROMOTE** (decision card "Promote (Recommended)", 2026-09-28).

## 1. What was solved

Seven shards, one per year (rule 36), each pinned to `020bb1c5`. Each replayed the keeper's recipe unchanged with
`replay_keeper.py`. The only delta is **data**: the 2020 (244 MW) and 2021 (725 MW) rows in
`data/raw/spp-hsl/spp_wind_curtailment_annual.csv` (sha256 `dd6c2898…`). With them, the armed year-own seam applies
2.55 % / 6.37 % instead of the 9.65 % 2023–25 mean. The parent solved nothing (rule 32(a)).

| year | leg SHA (provenance only, rule 33(d)) | shard check |
|---|---|---|
| 2019 | `8b376a816b6e65e2d54de560f4e987979b6e72e3` | PASS |
| 2020 | `ef6d12223ba317a59e9d577d32683e19e6b4be57` | PASS |
| 2021 | `19b2ad12eff577795b5dd1217bd160920fd1b00a` | PASS |
| 2022 | `1b514f2e3dad85c85308b29ec36cb5795e0d2cb3` | PASS |
| 2023 | `e8f7fcc0a1b8ed258c4174a4dfac3f4dfe749a51` | PASS |
| 2024 | `611fabed9e6a3f5afba2ec793cb0d354024f3957` | PASS |
| 2025 | `9436bee5fa999e7720b78aac2a7f2feccd695c9d` | PASS |

The parent re-ran `scripts/probes/_spp94_shard_check.py` locally on every leg. It then composed them with
`_rspp_compose.py --side arm --require unit_outage_netload_mask_repair=true --require
unit_outage_coal_extract_basis_share=true`, attested with `scripts/gen_spp94_attestation.py`, and registered the
composite with `--no-prune`.

## 2. Expectations E1–E6 (declared in PRECOMMIT §4)

| # | expectation | result | holds? |
|---|---|---|---|
| E1 | shard check PASS on all 7 legs | 7 / 7 PASS (recipe identical to the keeper, gas price, input sha256s, extract, N/S topology, `dispatch/<Y>_P1.parquet`) | **yes** |
| E2 | 2019, 2022–25 reproduce the keeper (≤1e-4 TWh per class; max hourly \|Δprice\| ≤1e-6) | every class 0.0000 TWh; max \|Δprice\| 0.000000 in all five years | **yes** |
| E3 | 2020/2021 wind falls, by ≤6.62 / ≤3.60 TWh | **−6.0218 / −2.8163 TWh** | **yes** |
| E4 | thermal absorbs ~1:1; demand-weighted price up or flat | 2020: thermal+solar +6.006 TWh, price_dw 19.426 → 21.113 (**+$1.69**). 2021: +2.808 TWh, 38.477 → 39.901 (**+$1.42**) | **yes** |
| E5 | 2020/2021 slack does not rise (keeper 0) | 0.0 / 0.0 MWh | **yes** |
| E6 | declared costs (not criteria) | see §3 | as declared |

The 2020 wind drop moves mostly into gas and coal: CC_REGULAR +3.204, COAL_PRB +1.905, CT_PEAKER +0.377,
COAL_LIGNITE +0.364 and ST_GAS +0.111 TWh. In 2021 it moves mostly into coal: COAL_PRB +2.097, CC_REGULAR +0.376 and
COAL_LIGNITE +0.208 TWh. Max hourly |Δprice| is $45.95 in 2020 and $47.25 in 2021.

## 3. Gate moves, at full magnitude. None is a criterion in either direction (rules 1, 14).

| tier / year | keeper `spp-86` | arm `spp-94` |
|---|---|---|
| **train 2023–25** | CALIBRATED (lone ledgered C3c) | **CALIBRATED (lone ledgered C3c), byte-identical** |
| 2019 | NOT-YET: C3a +11.5 % | identical |
| 2020 | NOT-YET: C3a **+17.6 %**, C3b NRMSE **0.259** | NOT-YET: C3a **+27.8 %**, C3b NRMSE **0.348**, i.e. **worse**, as E6 declared |
| 2021 | NOT-YET: C1 CC_REGULAR −9.54 TWh, COAL_PRB +11.43 TWh; gas NRMSE 0.326 | NOT-YET: CC_REGULAR **−9.16** (better), COAL_PRB **+13.52** (worse), gas NRMSE **0.317** (better) |
| 2022 | NOT-YET: C1 CC_REGULAR −10.31, COAL_PRB +13.49 TWh | identical |

**Run level:** NOT-YET, with failing set `{fuelmix, price_mean, price_shape, price_tail, dispatch_corr}`.

**Reading.** The correction removes wind that SPP says was not curtailed, so the input is now right. This exposes the
2020 price over-forecast more fully: the old 9.65 % gross-up had been hiding part of it with extra zero-cost wind.
By rule 14, a worse fit after an accuracy fix points to a miscalibration elsewhere, not to a reason to revert.
In 2020 that is the price body, which SPP-72/74 found is not the tail. In 2021–22 it is the coal/CC split
(SPP-89/90/91).

## 4. §5 recommendation rule, applied mechanically

| condition | result |
|---|---|
| (a) E1 on every leg | PASS |
| (b) E2 on all five untouched years | PASS |
| (c) E3 in sign, both years | PASS |
| (d) E5 | PASS |
| (e) `build_dof_ledger --check` shows zero new free parameters | PASS: `free_parameters current`; 5 entries, identical to the keeper's |

**→ RECOMMEND PROMOTE.** The offer multipliers stay 0.93 (rule 1(c)). `offer_curve_by_group` is byte-identical to
the keeper's on every year, as asserted by the attestation script.

**Attestation note.** The per-year `scenario_config` diff against the keeper is empty, with two exceptions, and both
are inert:
- fields added since the keeper was solved are absent from its config (the shard check verified them at default);
- `retiree_cems_cap` is absent from the leg because it was deleted on 2026-09-27 (rule 26). The keeper carried it at
  its frozen retired value, `False`.

## 5. Retrievability (rule 34(e))

The composite `results/calibration/spp94_arm_span` (the same 40 committable files as the keeper's bundle), its
sidecar and its run payload are committed on `claude/spp-95-curtailment-rows-k2zjfn` and land on `main` with that
PR. Promoting costs **zero re-solves**. The per-year legs are gitignored in the parent and are provenance only.

**Year set (rule 35(b)):** SPP's registered years are 2019–2025 on the keeper, with no other SPP run registered.
The arm covers all seven.

## 6. Out of scope, unchanged

The N↔S rating, the West/East partition (stays O), ramp limits, reserve headroom (SPP-91), gas-price levers, the
2022 coal markup (SPP-44) and the benchmark basis are untouched. `complete` / `frontier` for SPP: **not reached**,
because the validation tier 2019–22 is NOT-YET either way.

## 7. Promotion (executed 2026-09-28, rule 35)

Year set enumerated before pruning: SPP's registered years were 2019–2025, on `spp-86` only. `spp-94` covers all
seven, so the year set is unchanged. The promotion steps, in order:

1. Re-keyed `keepers/SPP.json`, including the `config_partition` tiers, and the `complete.SPP` entry in
   `calibration-complete.json`. Rebuilt `status/SPP.js` (CALIBRATED).
2. Ran `audit_keepers --iso SPP`. E1 passed; E13 flagged `spp-86` as a superseded run left behind.
3. Ran `prune_iso_runs.py --iso SPP --force-uncite`, which removed `spp-86`'s sidecar, payload and
   `spp86_arm_span`.
4. Re-ran the audit and got a clean PASS. The calibration-keeper-auditor agent also passed, with 0 repairs.

**Diagnostic note.** The D-4 FAIL rows go from 7 to 8. The one new row is 2021 `coal_mustrun` plant 6095:
0.0248 TWh floored, with a measured median of 0 MW over the 285 hours the floor binds. This is part of the extra
2021 coal commitment that replaces the removed wind. It is reported here and does not gate the promotion.
