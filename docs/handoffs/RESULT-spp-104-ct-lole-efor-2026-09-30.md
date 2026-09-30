# RESULT — SPP-104: CT_PEAKER outage from SPP's own LOLE-study EFOR, solved

**Lane** SPP-104. PRECOMMIT `docs/handoffs/PRECOMMIT-spp-104-ct-lole-efor-2026-09-30.md` (pin `264dbb2a`, Addenda
A/B). Control = keeper `2026-09-28-spp-100-chp-scope` (rule 29(b) form 4). Run
**`2026-09-30-spp-104-ct-lole`**, bundle `results/calibration/spp104_arm_span` (2019–2025).

- **Arm:** keeper + `spp_ct_lole_efor=true`. Each CT_PEAKER plant takes the capacity-weighted SPP 2023 LOLE seasonal
  gas EFOR (Tables 9/10) in place of the statistical WEFOR.
- **Solve:** seven year-isolated shards (rule 36). The parent ran no LP. The offer curve and every other scenario field
  were verified byte-identical to the keeper in all seven years (`gen_spp104_attestation.py`).

## 1. What it did (arm − keeper)

| year | ΔCT_PEAKER TWh | ΔCC_REGULAR | ΔST_GAS | ΔCOAL_PRB | Δprice $/MWh (demand-wtd) | unserved MWh, keeper → arm |
|---|---:|---:|---:|---:|---:|---|
| 2019 | −1.55 | +0.29 | +0.36 | +0.78 | +0.65 | 0 → 0 |
| 2020 | −1.95 | +0.41 | +0.39 | +1.01 | +0.28 | 0 → 0 |
| 2021 | −1.00 | +0.57 | +0.22 | +0.14 | +0.97 | 0 → 0 |
| 2022 | −0.97 | +0.42 | +0.35 | +0.13 | +1.41 | 0 → **1,215** (5 h, SPP-South, May/Sep) |
| 2023 | −1.81 | +0.37 | +0.59 | +0.75 | +0.59 | 0 → 0 |
| 2024 | −1.96 | +0.39 | +0.56 | +0.85 | +2.55 | 862 → **5,283** (10 h, Aug/Sep/Oct) |
| 2025 | −1.40 | +0.40 | +0.56 | +0.30 | +1.50 | 136 → **2,572** (5 h, Jul/Dec) |

The zero-LP price prediction held in sign every year and in size for 2019 (+0.7) and 2024 (+2.6). 2021 was smaller
than feared (+0.97).

## 2. Scores (rubric, `calibration_verdict.py`), keeper → arm

| year | tier | C3a mean LMP | C3b NRMSE | C3c >$200 h (RT) |
|---|---|---|---|---|
| 2019 | validation | +11.5 → **+14.6 %** (FAIL) | 0.146 → 0.173 | 0 → 6 (47) |
| 2020 | validation | +27.5 → **+29.3 %** (FAIL) | 0.343 → 0.355 (FAIL) | 0 → 0 (23) |
| 2021 | validation | +6.5 → +9.1 % | 0.184 → **0.152** | 352 → 362 (140) |
| 2022 | validation | −5.8 → **−2.6 %** | 0.184 → 0.176 | 0 → 8 (99) |
| 2023 | train | −6.7 → **−4.4 %** | 0.172 → **0.155** | 0 → 4 (42) |
| 2024 | train | −8.6 → **+1.4 %** | 0.172 → **0.156** | 7 → **24** (59) |
| 2025 | train | −5.4 → **−0.2 %** | 0.146 → 0.143 | 2 → **13** (68) |

- **Train 2023–25: CALIBRATED → CALIBRATED** (lone ledgered C3c, unchanged).
- **C1 / C4 validation rows move slightly the right way:**
  - C1 CC_REGULAR 2021: −9.65 → −9.08 TWh.
  - C1 CC_REGULAR 2022: −10.84 → −10.43 TWh.
  - C4 gas: 0.307 / 0.356 → 0.309 / 0.359.
- **C8 PASS. C6 PASS.**
- The price level rises in every year, as the zero-LP census said it would.
  - This is the sign SPP-79 asked for in 2023–25, where the keeper under-prices. It is the wrong sign in 2019–20.
  - The owner pre-accepted ~5 pts of C3a damage in 2019/20; the measured cost is +3.1 / +1.8 pts.
  - 2024 C3a goes from −8.6 % (the SPP-102 knife-edge) to +1.4 %.

## 3. Expectations (PRECOMMIT §5)

| # | expectation | result |
|---|---|---|
| E1 | Shard check PASS ×7 | **PASS** (re-run in the parent on every leg) |
| E2 | Optimal within the budget | **PASS** (every leg ~8–12 min wall) |
| E3 | Unserved energy not up > 500 MWh | **FAIL**: 2022 +1,215, 2024 +4,421, 2025 +2,436 MWh, all in shoulder/summer hours when CTs are out at the 12–23 % summer / 16–28 % winter EFOR |
| E4 | No new D-4 FAIL row (keeper 7) | **FAIL, by one knife-edge row**: 2021 `coal_mustrun` unit-conduct at plant 6095. The floor is identical (0.0265 TWh, 304 binding h); the measured-zero share moves 0.500 → 0.503 across the gate |
| E5 | Train stays CALIBRATED, no C1/C3a/C3b/C4 flip in 2023–25 | **PASS** (every 2023–25 C3a/C3b row improves) |
| E6 | Rule-14: gas outage-type within SPP's published outage | **FAIL** (zero-LP, DESIGN §6): over SPP's published gas outage in all 7 years (+0.5 to +3.8 GW) |

## 4. Recommendation (pre-registered rule, PRECOMMIT §6)

**RECOMMEND AGAINST promotion: E3, E4 and E6 fail.**

- **The structural case (rule 14).** The input over-states CT unavailability against SPP's own measured outage in
  every year. The service-hour EFOR, applied per calendar hour, puts about 70 % of SPP's summer gas outage on CTs
  alone. The new unserved-energy hours are that over-statement binding.
- **What the solve adds.** Raising the CT outage fixes the train-tier price level: 2024 C3a goes to +1.4 % and C3b
  improves in five of seven years. This is the "upper-tercile price is short in 2023+" signal (SPP-79) that SPP-102/103
  could not find.
- **Why that is not a reason to promote (rule 1).** A correct fit reached through an input that SPP's own outage data
  contradicts is the fitted-mechanism route. It is evidence that **the keeper is short of scarcity in 2023–25**, and a
  pointer to a successor. It is not a keeper.
- The owner decides (rule 31).

**Named successor (not launched).** The price improvement says the 2023+ keeper lacks unavailable gas capacity in the
scarce hours. SPP's published gas outage (hourly, by fuel) already says how much outage exists. The admissible object is
a **gas-family** outage allocation matched to SPP's measured hourly total, with a CT/ST split from SPP's own data. SPP-84
refused the aggregate pro-rata rebase, so this needs an owner charter and a rule-14 split that does not yet exist.

## 5. Retrievability (rules 33(d) / 34(e))

- **The composite** `results/calibration/spp104_arm_span` (292 MB with `dispatch/`) is in this lane's working tree
  and is **not committed**. It is registered locally as `2026-09-30-spp-104-ct-lole`; the sidecar and payload wait on
  the owner's ruling. It does not survive the session unless the owner promotes it.
- **The legs were pushed as provenance only:**
  2019 `d70150e5`, 2020 `b9a6aa04`, 2021 `ad69a3ce`, 2022 `92eb6165`, 2023 `e0de6f60`, 2024 `e6dfaec4`,
  2025 `e7291627` on `claude/spp104-<y>`. They are provenance, not a recovery route.
- **Cost to reproduce** if the working tree is lost: about 12 min wall across seven parallel shards.
- **Shards:** all 7 are archived.

## 6. Rules

- **1:** judged on structure; the price improvement is reported, not the basis.
- **13:** SPP's published rate; nothing pinned.
- **14:** E6 is the failing reconciliation.
- **19:** replaces WEFOR and never stacks on it.
- **21:** zero free parameters.
- **25:** SPP only.
- **29(b):** keeper as control; G-DRIFT all INERT.
- **31–36:** the parent solved nothing, bytes are in hand before archive, one year per shard.
