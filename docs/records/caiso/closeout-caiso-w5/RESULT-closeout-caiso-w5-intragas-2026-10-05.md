# RESULT closeout-CAISO-w5: D1 + D3 + D4 stacked on w3 (2026-10-05)

**Records.**
- `PRECOMMIT-DESIGN-closeout-caiso-w5-intragas-2026-10-05.md`, including Addendum A (as-built, G-DRIFT, bars, kills,
  launch).
- `FINDING-closeout-caiso-w5-phase0-2026-10-04.md`, including Addendum A.

**Runs.**
- **Control:** the w3 probe `2026-10-04-closeout-caiso-w3-own` (bundle `closeout_caiso_w3_a1_span`).
- **Arm A1:** probe **`2026-10-05-closeout-caiso-w5-stack`** (bundle `results/calibration/closeout_caiso_w5_a1_span`).
  It is the w3 recipe plus three flags:
  - `measured_ct_heat_rates_crosswalk_remap` (D1);
  - `caiso_humboldt_local_area` (D3);
  - `caiso_ra_mustoffer_physics_eligibility` (D4).
- **Registration:** on `claude/closeout-caiso-w5` only (E13).

**Verdict: T1 MISSED; one new supporting-tier FAIL; NOT PROMOTED.**
- C1 CC_REGULAR 2020 moves +5.00 → **+4.80 TWh** against the ±4.60 band, still FAIL.
- Every pre-registered kill K1–K6 clears.
- **C3c 2023 goes PASS → FAIL** (model tail 51 → 144 h against 47 actual). That FAIL is produced entirely by the new
  HUMBOLDT pocket price (§3).
- The determination stays NOT-YET.
- The w3 promotion request stands unchanged.

## Solves

Seven year-isolated shards, all pinned to `d24bd6aaeab257e52251c972cdfa32ba29bc7ea8`. Every leg was fetched, its
parent and 17 files (including `dispatch/<y>_P1.parquet`) verified, all six flags checked, and HUMBOLDT slack read
before its shard was archived.

`_closeout_caiso_w1_compose_span.py` composed the legs: keeper + 6 arm fields, one solve-surface fingerprint, one
source SHA.

| Year | A1 shard commit (provenance; branch `claude/closeout-caiso-w5-a1-<y>`) |
|---|---|
| 2019 | `ad5c0bca3a8d055230dc3b80c6ce7c3d6c9c56bd` |
| 2020 | `12b54568463f8e1a236d0ae6d37a96c4e7ca5a7d` |
| 2021 | `a542e8457cd8c42c3d65e5b8da45fe50152960c9` |
| 2022 | `b7d6bc3a2ee437c3bc1a6218befd39286dd35782` |
| 2023 | `8a553b0ef5fbb842c06a06ff79f9aac0a24a39c0` |
| 2024 | `97837f6b50c05bf9aa8ec3ac456c0c062f460bd5` |
| 2025 | `d6f540b53178babc6f09c8478e567686be4c1772` |

**A2 (D1 only, attribution).** Legs 2019–2023 are verified and extracted:
- 2019 `af3455a6`, 2020 `6d040a9a`, 2021 `fe16c47d`, 2022 `7be62627`, 2023 `6d537304`.
- 2024 and 2025 are still solving.

## 1. Gate table (w3 → w5; every scored record that moved)

| Criterion | Year | w3 | w5 | Status |
|---|---|---|---|---|
| **C1 CC_REGULAR (T1)** | **2020** | 51.128 (+5.00) | **50.927 (+4.80)** | FAIL → FAIL (band ±4.60) |
| C1 CC_REGULAR | 2019 / 21 / 22 / 23 / 24 / 25 | 38.59 / 54.16 / 52.56 / 50.77 / 44.32 / 38.21 | 38.38 / 54.04 / 52.41 / 50.66 / 44.20 / 38.17 | PASS (2019 WATCH: −2.25 vs ±4.84) |
| C1 CT_PEAKER | 2019 … 2025 | 2.55 / 2.93 / 6.19 / 3.85 / 2.99 / 3.29 / 0.99 | 2.90 / 3.21 / 6.39 / 4.13 / 3.17 / 3.47 / 1.05 | PASS. Toward actual in 6 of 7 years (2021 away: WATCH, +1.83 vs ±4.83) |
| C1 ST_GAS | 2019 … 2024 | 0.08 / 0.52 / 0.16 / 0.29 / 0.04 / 0.15 | 0.10 / 0.59 / 0.17 / 0.30 / 0.03 / 0.15 | PASS |
| C2 gas | all | | ≤ 0.13 TWh moves | PASS |
| C4 gas r / NRMSE | 2019 / 20 / 21 | 0.288 / 0.288 / 0.294 | 0.290 / 0.290 / 0.294 | PASS. Worse by at most 0.002 (K2 clear) |
| C3a | 2021 / 2023 | +12.0 % / +7.6 % | +11.9 % / +7.5 % | unchanged |
| **C3c tail hours (> $200)** | 2022 / **2023** / 2024 | 515 / **51** / 0 | 580 / **144** / 93 | 2022 PASS; **2023 PASS → FAIL**; 2024 FAIL → FAIL (now over-fire) |
| C8 CC_REGULAR forced | 2019 | 11.7 % | 11.8 % | PASS |

## 2. Mechanism readout (2020, unit sums, TWh)

| | w3 | A2 (D1) | A1 (D1+D3+D4) |
|---|--:|--:|--:|
| CC_REGULAR | 51.207 | 51.201 | 51.01 |
| CT_PEAKER | 2.96 | 2.98 | 3.23 |
| ST_GAS | 0.519 | | 0.585 |
| Carlsbad 59002 | 0.068 | 0.166 | |
| Humboldt Bay 246 | 0.087 | | 0.347 |

**D1** (Carlsbad's measured rate, 9.07 vs 9.71):
- Carlsbad's output rises toward actual: 2019 0.105 → 0.297 against 0.372 actual; 2020 0.07 → 0.17 against 0.39.
- It displaces other peakers and imports. CC is unmoved (−0.006 TWh in 2020).

**D3** (Humboldt local area):
- Humboldt Bay runs 0.16–0.39 TWh against 0.35–0.55 actual; it was 0.01–0.29 before.
- HUMBOLDT slack is 0 in every year (K4 clear).
- The pocket energy displaces NP15 imports and gas only partly. CC falls about 0.1–0.2 TWh per year.

**D4** (physics-only bridge eligibility):
- Steam gains only 0.01–0.07 TWh. The P0 pattern seldom runs a steam unit on both sides of a gap, so the bridge has
  little to hold.
- In 2020 this is 0.066 TWh against the 0.57 zero-LP upper bound.

Separating D3 from D4 exactly needs the unrun A3 (D1 + D4). On the class sums, D4 is ≤ 0.07 TWh of steam in every
year, so D3 carries most of the CC move.

## 3. The C3c regression is the pocket price, not the system

**What C3c counts.** C3c counts hours in which the LP's maximum zonal dual exceeds $200
(`calibration_verdict.score_price_tail`).

**Where the extra hours come from.** Excluding HUMBOLDT, w5's tail is 515 / 61 / 0 hours in 2022 / 2023 / 2024, the
same as or below w3's 515 / 67 / 0. Every added hour is a HUMBOLDT hour:

| Year | HUMBOLDT hours > $200 | HUMBOLDT p99 ($/MWh) | HUMBOLDT max ($/MWh) |
|---|--:|--:|--:|
| 2022 | 552 | 477 | 560 |
| 2023 | 192 | 221 | 266 |
| 2024 | 93 | 202 | 203 |

**Why it is a basis mismatch.** The RT actual tail is measured at hubs. The pocket has no hub, and real SLAP_PGHB
prices are not in the reference. So the regression is real as the rubric scores it, but its cause is the scorer
reading a new pocket against a hub-basis reference.

**Two routes, neither taken here:**
- Exclude hubless pocket zones from the C3c model maximum. That is a rubric change, so a separate PR on an owner
  ruling (rule 37).
- Give HUMBOLDT an offer basis that bounds its pocket price. That would be new tuning and is not admissible.

## 4. Kills (PRECOMMIT Addendum A)

| Kill | Result |
|---|---|
| K1 any C1 PASS → FAIL | clear |
| K2 C4 NRMSE worse by > 0.02 | clear (≤ 0.002) |
| K3 C3a worse by > 1 pp | clear (improves by 0.1 pp) |
| K4 HUMBOLDT slack > 0.1 % | clear (0 MWh, all years) |
| K5 C8 breach | clear |
| K6 C2 leaves band | clear |

**Not pre-registered:** the C3c 2023 PASS → FAIL (§3).

## 5. Disposition

- **Decision rule (Addendum A):** the kills clear but T1 is missed, so the result is reported with **no slot
  request**.
- **Matrix cells:** all three stay **U** with this evidence:
  - D1 is a confirmed rule-14 correction with a small effect;
  - D3 is structurally right on Humboldt Bay but adds a scorer-basis C3c regression;
  - D4 is close to inert.
- **What would close C1 2020** (a further 0.2 TWh): nothing left in w5 reaches it.
  - The remaining intra-gas gap is the out-of-market and minimum-run conduct the FINDING maps.
  - The admissible next step is D2 (industrial self-generation reclass, +0.4–0.6 TWh/yr, owner scope ruling pending)
    or D5 (peaker minimum-run via the UC MILP, deferred).

## 6. DOF / retrievability

- **DOF:** zero fitted parameters.
  - Measured inputs: the Carlsbad and King City CEMS rows, the Humboldt ATL_LDF weight, the LCT capabilities, and the
    CAMPD steam minimum load.
- **Bundles:**
  - The span `results/calibration/closeout_caiso_w5_a1_span` and its legs are local and gitignored.
  - Their bytes are in the shard commits above.
- **Registration:** the sidecar and payload are on `claude/closeout-caiso-w5` only.
- **Benchmark parts:** registering this run re-rendered `frontend/data/backcast/bench/CAISO/<y>.json.gz`.
  - Cause: the D1 remap rows re-key Carlsbad's CEMS in the shared benchmark frame, so its hourly benchmark shape is now
    its own CEMS instead of flat.
  - Effect: the w5 C4 is scored on that slightly different hourly reference (C1 levels are EIA-923 and unchanged).
  - These parts ride the lane branch only.
