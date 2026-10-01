# RESULT — miso-298: the owner-ruled gas form ALONE over 2019–2025 is KILLED by its own ex-ante kill rule K-1 (three criterion-year PASS→FAIL flips); keeper unchanged; both O cells → R

```
LANE     : miso-298 (owner ruling 2026-10-01, miso-297 card "What should miso-298 do?": "Gas form alone, full span (Recommended)")
PREREG   : docs/records/miso/PRECOMMIT-miso298-gas-form-alone-2026-10-01.md (pin 351f8efb8c125dc6f606a6df70fde59e29961ec3, pushed before any shard)
KEEPER   : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025) — UNCHANGED
ARM      : 2026-10-01-miso-298-gas-form (results/calibration/miso298_span, 2019-2025), registered on completion (rule 15) at commit c14c5e13, then taken off the registered set in this PR (rule 35 (f) / audit E13: keeper-only); git history is the record
DELTA    : miso_gas_marginal_commodity_pricing=true + miso_gas_variable_transport=true, nothing else (offer_curve_by_group byte-identical). DOF +0
CONTROL  : keeper bundle (G-DRIFT 8f765fef..351f8efb: 0 LIVE; solve_surface_register MISO moved rows 0; rule 29(b) form 4)
VERDICT  : KILLED — K-1 fires (C1 COAL_PRB 2019, C1 CC_REGULAR 2021, C3a 2019 PASS→FAIL) and K-2 fails; K-4 passes. Determination NOT-YET both runs; failing criterion-years 3 → 6
CELLS    : gas_marginal_commodity_pricing O → R, gas_variable_transport O → R (matrix §5.4 + MISO.js, this PR)
```

## 1. Legs (rules 32–36)

Seven single-year shards pinned to `351f8efb`, one container each. Every leg passed `scripts/probes/_miso298_shard_check.py`
in the parent: recipe = keeper + exactly the two fields (38 fields new since the keeper, none non-default); the seven
`-splitremap-` companions read at their pinned shas; inputs (incl. both daily hubs, the transport table + pool, the
zone→hub map) at their pinned sha256; EIA-860 vintage = solve year; hydro classifier `dc2a9d4b`; log markers (the
marginal-commodity line WITH the transport clause present; winter-delivered and bare-hub lines absent);
`hourly/unit_marginal_<Y>.parquet` present (rule 15, 15.5–16.7 MB each). Slack 0 in every year except the keeper's own 2024
event (18,531.5 MWh in 7 hours, hours 5700–5706, East/Illinois/Plains — byte-identical to the keeper). All 7 shards archived.

| year | leg commit (provenance; branch is transport, rule 33) | LW internal price keeper → arm $/MWh | CC_REGULAR Δ TWh | COAL_PRB Δ TWh | import Δ TWh |
|---|---|---:|---:|---:|---:|
| 2019 | `f5f35eb1` | 27.913 → 28.459 (+0.55) | −4.17 | +2.23 | +1.50 |
| 2020 | `a77405c8` | 24.511 → 25.058 (+0.55) | −4.13 | +1.70 | +1.90 |
| 2021 | `e692fada` | 37.031 → 38.071 (+1.04) | −2.14 | +0.55 | +1.02 |
| 2022 | `912263e9` | 58.638 → 59.681 (+1.04) | −0.56 | 0.00 | +1.33 |
| 2023 | `3d352481` | 32.737 → 32.262 (−0.48) | +4.03 | −0.70 | −1.92 |
| 2024 | `744d958c` | 30.781 → 30.708 (−0.07) | +0.17 | +0.01 | −0.39 |
| 2025 | `3fbfa75d` | 41.665 → 41.989 (+0.32) | −0.26 | +0.10 | +0.46 |

(Δ = arm − keeper, P1 class TWh from each bundle's `class_hourly`; 2022 P0 2,213 s + P1 970 s, 56 min wall; others 20–35 min.)

## 2. Gates (live scorer, `scripts/probes/_miso298_gate_table.py` → `results/phase0/miso/_miso298_gate_table.json`)

### 2.1 Every criterion-year status flip (keeper → arm)

| criterion-year | keeper | arm | flip |
|---|---|---|---|
| C1 COAL_PRB 2019 (band ±8 TWh) | +6.40 PASS | **+8.63 FAIL** | PASS→FAIL (**K-1**) |
| C1 CC_REGULAR 2021 | −6.01 PASS | **−8.77 FAIL** | PASS→FAIL (**K-1**) |
| C3a 2019 | +8.7 % PASS | **+10.9 % FAIL** | PASS→FAIL (**K-1**) |
| C7 gas dispatch_corr 2021 | r 0.835 / NRMSE 0.283 PASS | **r 0.826 / NRMSE 0.301 FAIL** | PASS→FAIL (supporting tier) |
| C3b 2021 | 0.201 FAIL | **0.192 PASS** | FAIL→PASS |
| criterion C3b (price_shape) | FAIL | PASS | FAIL→PASS |
| criterion C7 (dispatch_corr) | PASS | FAIL | PASS→FAIL |

Determination: keeper NOT-YET (fuelmix, price_mean, price_shape); arm NOT-YET (fuelmix, price_mean, dispatch_corr). Failing
criterion-years: keeper 3 (C1 ST_GAS 2019, C3a 2020, C3b 2021) → arm 6 (C1 ST_GAS 2019, C1 COAL_PRB 2019, C1 CC_REGULAR 2021,
C3a 2019, C3a 2020, C7 gas 2021). C3c stays the lone ledgered caveat (identical hours both runs); C2, C4 (CO2), C6, C8
(forced share) PASS both; D-1/D-2/D-4 FAIL rows 11 → 11 (one D-1 row cleared, one D-4 row added).

### 2.2 C1 (model − actual TWh; band ±8), both runs

| class | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---:|---:|---:|---:|---:|---:|
| COAL_PRB keeper → arm | +6.40 → **+8.63 F** | +3.62 → +5.32 | +5.69 → +6.24 | +5.28 → +5.28 | −2.65 → −3.35 | −0.27 → −0.26 |
| COAL_BIT | −0.94 → +0.43 | −4.52 → −3.87 | −0.37 → +0.35 | +5.69 → +5.82 | −1.53 → −1.62 | −0.64 → −0.69 |
| COAL_LIGNITE | +1.04 → +1.11 | +1.33 → +1.43 | +0.61 → +0.64 | +0.12 → +0.12 | −0.47 → −0.50 | −0.45 → −0.45 |
| CC_REGULAR | +4.20 → −0.11 | −2.39 → −6.72 | −6.01 → **−8.77 F** | −4.09 → −4.73 | +0.21 → +4.21 | +1.82 → +1.87 |
| ST_GAS | −8.00 F → −8.79 F | −6.40 → −7.00 | −5.24 → −5.15 | −5.11 → −5.57 | −0.23 → −2.53 | −1.90 → −3.19 |
| CT_PEAKER | +0.82 → +0.91 | −3.62 → −3.42 | −4.92 → −4.97 | −5.24 → −5.39 | −3.39 → −4.11 | −4.09 → −4.02 |

2025 C1 cells SKIPPED (preliminary vintage) in both runs; C2 2025 gas −7.4 % / coal +0.1 % keeper, reported unchanged in kind.

### 2.3 C3a / C3b, both runs

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| C3a keeper → arm (%) | +8.7 → **+10.9 F** | +11.6 F → **+14.1 F** | −5.6 → −3.0 | −5.1 → −3.0 | +8.4 → +6.9 | +5.1 → +4.9 | −1.1 → −0.3 |
| C3b NRMSE keeper → arm | 0.114 → 0.131 | 0.165 → 0.181 | **0.201 F → 0.192 P** | 0.122 → 0.100 | 0.104 → 0.091 | 0.101 → 0.096 | 0.083 → 0.082 |

### 2.4 Kill rules (PRECOMMIT §5), read exactly as written

| rule | reading | result |
|---|---|---|
| K-1 no C1 class PASS→FAIL in any year | COAL_PRB 2019 +8.63 (band 8.00); CC_REGULAR 2021 −8.77 | **FIRES** |
| K-2 COAL_* and CC_REGULAR within band or toward actual, every year | COAL_PRB 2019 out of band and away (+6.40 → +8.63); CC_REGULAR 2020 −2.39 → −6.72 and 2021 −6.01 → −8.77 away (in/out of band) | **FAILS** |
| K-4 q1–q2 LW price error shrinks in 2023 and 2024 | 2023 +5.62 → +4.88; 2024 +4.10 → +3.79 (`_miso297_shard_readout.py`, `results/phase0/miso/_miso298_readout_arm.json` vs `_miso297_readout_keeper.json`) | passes |
| S-1 / S-1b / S-2 / S-3 / S-4 structural stops | all seven legs PASS the shard check; slack as §1 | hold |

**The arm is KILLED.** No promotion is recommended; the keeper stays `2026-09-28-miso-280-splitremap`.

### 2.5 K-3 / K-4 readout (reported, not gates), keeper → arm

| year | IMM coal SMP share | K-3 coal marginal share | q1 coal share | K-4 q1–q2 LW error $/MWh | all-hours LW error | q5 error |
|---|---:|---:|---:|---:|---:|---:|
| 2019 | 0.47 | 0.432 → 0.460 | 0.158 → 0.193 | +3.81 → +4.46 | +2.24 → +2.79 | −1.77 → −1.30 |
| 2020 | 0.40 | 0.254 → 0.269 | 0.075 → 0.067 | +4.09 → +4.75 | +2.54 → +3.09 | −1.03 → −0.48 |
| 2021 | 0.35 | 0.371 → 0.386 | 0.382 → 0.414 | +1.08 → +1.79 | −2.20 → −1.16 | −9.07 → −7.51 |
| 2022 | 0.24 | 0.177 → 0.165 | 0.320 → 0.306 | +4.34 → +5.48 | −3.81 → −2.57 | −19.45 → −17.87 |
| 2023 | 0.36 | 0.215 → 0.213 | 0.109 → 0.096 | +5.62 → +4.88 | +2.54 → +2.07 | −3.33 → −3.50 |
| 2024 | 0.36 | 0.197 → 0.205 | 0.072 → 0.073 | +4.10 → +3.79 | +1.50 → +1.42 | −2.53 → −2.30 |
| 2025 | n/a | 0.277 → 0.280 | 0.221 → 0.233 | +4.57 → +4.75 | −0.46 → −0.13 | −12.05 → −11.25 |

## 3. Reading

1. **Every PRECOMMIT §5 prediction held in direction.** CC_REGULAR fell in 2019–2022 (−4.2 / −4.1 / −2.1 / −0.6 TWh) and
   rose in 2023–2024 (+4.0 / +0.2); coal was the mirror; imports moved with the internal price (+1.0 to +1.9 TWh in
   2019–2022, −1.9 / −0.4 in 2023–2024); ST_GAS moved further from actual in six of seven years; C3a 2019/2020 worsened and
   2023/2024 improved; C3b 2021 did not merely hold — it cleared. The LP converted the static move at ~1.3× for CC_REGULAR
   in 2019/2020 (static −0.46 / −0.40 GW ≈ −4.0 / −3.5 TWh vs −4.2 / −4.1 solved), well above the 0.27× coal conversion
   miso-224/225 measured — CC is the marginal class and takes the fuel move almost one-for-one.
2. **The kill is the early-year sign the census named** (PRECOMMIT §3.1, FINDING-miso297 §1 item 4). The transport table was
   derived on 2023–2025 receipts; on the 2019–2022 fleets its own-plant CC_REGULAR rung ($0.35 / 0.36 / 0.28 / 0.26 per
   MMBtu) exceeds those years' print-over-hub wedge ($0.13–0.39), so the ruled form RAISED CC fuel by $0.07–0.14 there,
   pushed CC_REGULAR out of merit against coal that was already +5 to +6 TWh over actual (COAL_PRB 2019 +6.40 → +8.63), and
   lifted the low-load price (K-4 2019 +3.81 → +4.46, 2020 +4.09 → +4.75; C3a 2019 +8.7 → +10.9 %).
3. **Where it lowers CC fuel it does what the owner convention intends.** 2023: CC_REGULAR +0.21 → +4.21 (still in band),
   COAL_PRB −2.65 → −3.35, q1–q2 error +5.62 → +4.88, C3a +8.4 → +6.9 %. 2021/2022 (high-gas years) C3a improved by 2.1–2.6
   points through the import and ST_GAS channels even as CC fuel rose. The structure is not refuted; its level in the
   early years is.
4. **Not swept, not tuned.** No value was chosen on any result. The one admissible successor the kill points at is a data
   question, not a parameter: `miso_gas_variable_transport.csv` is a frozen derive on 2023–2025 receipts (rule 23). Deriving
   the 2019–2022 rows from those years' own EIA-923 plant receipts is a source-data extension, not a re-tune, and would
   be measured at zero LP first (the census machinery of miso-297 reads it directly). Untested here; the owner picks.

## 4. Where the bytes are (rule 31 / 33 / 34)

- **Registration, then retention.** The composed span was registered on completion as `2026-10-01-miso-298-gas-form`
  (rule 15) and committed at **`c14c5e13`** on this lane's branch (slim bundle incl. `hourly/` with `unit_marginal_<Y>.parquet`
  for every year, attestation with a `miso298` block and the inherited blocks nested, regenerated `legitimacy_diagnostics.json`,
  stamped partition passing `--check`; registry sidecar + payload; refreshed MISO bench parts — builder fingerprint only, bench
  content byte-equal). CI's keeper-integrity audit (E13, rule 35 (f)) admits only the keeper on the registered set, so the
  same PR takes the sidecar, the payload and the bundle back off the tree; the bundle dir is **gitignored, never `rm`-ed**
  (rule 31) and stays on disk in this container. Recover everything at zero LP once the PR has merged (the commit is
  reachable from `main`):

  ```
  git checkout c14c5e13 -- results/calibration/miso298_span \
      frontend/data/backcast/registry/2026-10-01-miso-298-gas-form.json \
      frontend/data/backcast/runs/2026-10-01-miso-298-gas-form.js
  ```
- Per-year leg dirs `results/calibration/miso_298_<Y>` are parent-local and gitignored; the leg SHAs in §1 are provenance
  only. Full bundles incl. `dispatch/<Y>_P1.parquet` sit on the shard branches until the PR merge cuts them. A re-solve of
  any leg costs 20–35 min (2022 ~56 min); a promotion from the recovered span costs no re-solve (every year, every sidecar).
- Phase-0 / scoring artifacts on `main`: `results/phase0/miso/_miso298_gate_table.json`, `_miso298_readout_arm.json`;
  probes `scripts/probes/_miso298_{shard_check,compose_span,attest,gate_table}.py`.
- No solved bundle was deleted (rule 31). The bench parts keep their refreshed builder fingerprint.

## 5. Promotion question and next

**Promotion: NOT recommended** (K-1 fired; the determination's failing criterion-years go 3 → 6). The owner's call under
rule 31; the bundle is recoverable at zero LP from `c14c5e13` either way (§4). Owner card in the session's final message:

- (A) **Record the kill; keeper unchanged.** The remaining full-span failures are C1 ST_GAS 2019 (routed), C3a 2020 (no
  admissible identified lever), C3b 2021 (routed). The chain's next lane is a zero-LP phase 0 of the owner's choice.
- (B) **Phase 0 (zero LP) on a per-year variable-transport table** — derive 2019–2022 rows from each year's own EIA-923
  receipts (rule 23: new source years), measure the static CC fuel move and the census footprint per year, PRECOMMIT only
  if the 2019–2022 CC fuel moves down. The forward analogue is unchanged (latest table carried forward).
- (C) **Promote anyway** as the structurally ruled convention (rule 1: structure over fit) — the RESULT states the cost:
  three new FAIL criterion-years incl. C1 COAL_PRB 2019 and CC_REGULAR 2021 out of band.
- (D) Something else.

Full span NOT-YET on C1 ST_GAS 2019, C3a 2020, C3b 2021. Train 2023–2025 CALIBRATED. **No frontier** (owner, 2026-09-28).
