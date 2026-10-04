# RESULT closeout-CAISO-w2: daytime + late-evening DSW clean rungs in the unprinted hours (2026-10-04)

**Authority.** Owner ruling **R-63** (2026-10-04): *"A: Arm it, solve 7 years (Recommended)"*. The arm is an
OWNER-RULED TRANSFER of the R-CAISO-20 pattern, not a rule-13 measured admission.

**Records.** PRECOMMIT `PRECOMMIT-closeout-caiso-w2-unprinted-rungs-2026-10-03.md`; G-DRIFT
`ADDENDUM-closeout-caiso-w2-gdrift-2026-10-04.md` (clean).

**Runs.**
- Control: keeper `2026-10-02-closeout-caiso-w1-arm2` (bundle `closeout_caiso_w1_a2_span`), scored at HEAD with the
  same verdict code.
- Arm: probe `2026-10-04-closeout-caiso-w2-unprinted` (bundle `results/calibration/closeout_caiso_w2_a1_span`). It is
  registered **on the lane branch only** (E13).

**Verdict: every kill rule clears and target T2 is met, so the probe is recommended for promotion on structure.**
- **Determination stays NOT-YET** on C1 CC_REGULAR 2020/2021 and C4 2020/2021.
- Three fold FAILs flip to PASS: C1 CC_REGULAR 2019, C4 gas 2019, and the C2 2019 flag.
- DSW net-import error falls in every fold year: −9.0 / −14.6 / −9.5 → **+1.0 / −2.9 / −7.0 TWh**.

## Solves

Seven year-isolated shards, all pinned to `e857053252d65b893bb171422002b5d75428cc36` (main after #7184). Each leg was
fetched, extracted and verified before its shard was archived: parent `e8570532`, 17 files including
`dispatch/<y>_P1.parquet`, and `caiso_dsw_daytime_lateevening_unprinted_arm: true`.

`_closeout_caiso_w1_compose_span.py` composed the legs. Every leg equals the keeper recipe plus the arm field, with one
solve-surface fingerprint (`7293a431a6884d7d`) and one source SHA. `legitimacy_diagnostics.json` was regenerated over
the composite.

| Year | Shard commit (provenance; branch `claude/closeout-caiso-w2-a1-<y>`) |
|---|---|
| 2019 | `9f642a4479df7774a6f79543947090f9d9ad3ae2` |
| 2020 | `728b4a6bb5015ff96f3aa5c35bfd9828816ca4fc` |
| 2021 | `6ed37d8fad034599407d576d690571d19ac84c08` |
| 2022 | `35c125d30096eaa5252fedcdc5b054ef62efff11` |
| 2023 | `ddcef18d16eb5345331cf6f0871422fbd4948d21` |
| 2024 | `6f9d9f904663c3e46d9d0a7c0023d307facf2ec5` |
| 2025 | `b2705b88e49c68f1e9613bf868eb64927d5f8f29` |

## Gate table (keeper → arm; every record that moved)

| Criterion | Year | Keeper | Arm | Status |
|---|---|---|---|---|
| **C1 CC_REGULAR (T2)** | **2019** | +5.63 TWh FAIL | **−1.75 TWh** | **FAIL → PASS** (band ±4.84) |
| C1 CC_REGULAR (T3, reported) | 2020 | +13.46 FAIL | +5.39 | FAIL → FAIL (−8.07; 0.79 short of ±4.60) |
| **C1 CC_REGULAR (T1)** | **2021** | +6.59 FAIL | **+4.98** | FAIL → FAIL (−1.61 against a pre-fixed −1.76; **0.15 TWh short**) |
| **C4 gas r / NRMSE** | **2019** | 0.888 / 0.385 FAIL | **0.897 / 0.291** | **FAIL → PASS** |
| C4 gas r / NRMSE | 2020 | 0.893 / 0.399 | 0.884 / 0.317 | FAIL → FAIL (eases) |
| C4 gas r / NRMSE | 2021 | 0.857 / 0.348 | 0.877 / 0.321 | FAIL → FAIL (eases) |
| C1 CT_PEAKER | 2019 / 20 / 21 | +0.38 / −0.04 / +2.52 | −1.46 / −2.06 / +2.06 | PASS → PASS |
| C1 CC_CHP | 2019 / 20 / 21 | +0.61 / +0.98 / +1.10 | +0.41 / +0.80 / +1.04 | PASS → PASS |
| C1 ST_GAS | 2019 / 20 / 21 | −1.07 / −1.05 / −1.17 | −1.18 / −1.35 / −1.17 | PASS → PASS |
| C2 gas (model; actual 54.03 / 60.31 / 64.62) | 2019 / 20 / 21 | 59.52 / 73.61 / 73.62 | 49.99 / 63.03 / 71.48 | PASS → PASS; 2019 "all classes in band" |
| C3a (covered window) | 2021 | +12.7 % | +12.6 % | unchanged |
| C3b NRMSE | 2021 | 0.148 | 0.147 | unchanged |
| C8 CC_REGULAR forced | 2019 / 20 / 21 | 8.6 / 6.2 / 6.8 % | 11.3 / 8.6 / 7.3 % | ≤ 30 % PASS |
| every record | 2022–2025 | | | **identical** |

**Not a regression.** C3a/C3b 2019–21 and C3c 2021/2024 read FAIL/SKIPPED on the probe and CAVEAT on the keeper, at
identical magnitudes. The reason is that the probe carries no attestation or exceptions ledger: the R-40
reference-coverage caveats, the R-34 relabel and the C3c-2024 ledger enter through attestation. `promote_keeper.py`
carries the outgoing ledger forward (rule 35).

## DSW / PNW net import vs EIA-930 (TWh, model − measured; P1 unit sums vs `corridor_net_import`)

| | Total | h0–5 | h6–21 | h22–23 | PNW total |
|---|--:|--:|--:|--:|--:|
| 2019 keeper → arm | −9.02 → **+0.99** | +0.38 → +0.27 | −8.10 → +0.73 | −1.30 → −0.02 | +7.51 → +7.22 |
| 2020 keeper → arm | −14.57 → **−2.91** | −1.66 → −1.65 | −10.56 → −0.41 | −2.35 → −0.85 | +3.78 → +2.88 |
| 2021 keeper → arm | −9.49 → **−7.00** | −0.94 → −0.94 | −6.77 → −4.55 | −1.78 → −1.50 | +2.29 → +2.01 |

Tranche energy (TWh):

| | 2019 | 2020 | 2021 |
|---|--:|--:|--:|
| DSW_daytime_clean | 0 → 17.30 | 0 → 13.72 | 5.06 → 8.17 |
| DSW_lateevening_clean | 0 → 2.45 | 0 → 1.89 | 0.86 → 1.18 |
| DSW_CCGT | 5.60 → 0.24 | 3.15 → 0.10 | 1.01 → 0.34 |
| WECC_scarcity | 3.73 → 0 | 0.48 → 0 | 0.24 → 0 |

The remaining 2021 DSW gap sits in printed May–Dec hours (unchanged by construction). The 2020 residual is mostly
overnight, at −1.65 TWh.

## Kill rules (PRECOMMIT §4)

| Kill | Result |
|---|---|
| K1 undeclared C1 PASS→FAIL | **clear** (none) |
| K2 whole-year \|DSW error\| grows in any fold year | **clear**: falls 9.0→1.0, 14.6→2.9, 9.5→7.0 |
| K3 C4 NRMSE worse by > 0.02 in any fold year | **clear**: improves in all three |
| K4 C3a 2021 above +13.7 % / C3b above 0.158 | **clear** (+12.6 % / 0.147) |
| K5 any 2022–25 record moves beyond noise | **clear**: byte-identical per-unit dispatch in 2022–25 |
| K6 C2 gas leaves band | **clear** (2019 −4.04 vs ±4.84) |

**Targets:** T2 met (2019 C1 PASS). T1 missed by 0.15 TWh (2021 C1 still FAIL). T3 and T4 were reported, not
claimed.

**Decision rule §5 applies:** all kills clear and T2 is met, so the scored flips go to the desk with a request for the
promotion slot. The attestation must declare the arm as a ruling-authorised transfer (R-CAISO-20 pattern + R-63).

## DOF / retrievability

- **DOF:** zero fitted parameters. The two unprinted depth tables are measured p95 values over the armed window (rule
  21 source: the measurement). The arming window is ledgered to R-63.
- **Bundles:**
  - The composed span `results/calibration/closeout_caiso_w2_a1_span` (739 MB with dispatch) and the seven legs
    `closeout_caiso_w2_a1_<y>` are local and gitignored; they are not kept on `main`.
  - Their bytes are in the shard commits above.
  - A promotion needs **no re-solve**: re-compose from the leg SHAs, then run `promote_keeper.py`.
- **Registration:** the probe registration (sidecar + payload) sits on `claude/closeout-caiso-w2` only (E13).
