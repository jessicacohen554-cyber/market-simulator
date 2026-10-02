# RESULT — SPP-107: the repaired MMU offer-side carrier (arm EXR), solved

- **Lane:** SPP-107, on the owner card "Build + solve EXR (Rec.)" (2026-10-02).
- **Records:** DESIGN `DESIGN-spp-107-mmu-carrier-repair-2026-10-02.md`; PRECOMMIT
  `PRECOMMIT-spp-107-mmu-carrier-repair-2026-10-02.md` (pin `d787142d`).
- **Control:** keeper `2026-09-28-spp-100-chp-scope` (rule 29(b) form 4; G-DRIFT all INERT).
- **Arm EXR:** `spp_mmu_offer_unavailability = true` + `spp_mmu_offer_repair = true`. Run
  `2026-10-02-spp-107-exr-repaired`, bundle `spp107EXR_span`.
- **Solve:** 7 year-isolated shards (rule 36), 8–11 min wall each. The parent ran no LP.
  - Every leg passed `_spp107_shard_check.py` in its shard and again in the parent.
  - Composed with `_rspp_compose.py --require` on both fields; attested with `gen_spp107_attestation.py`, which
    confirms the offer curve and every other scenario field are byte-identical to the keeper.

## 1. What the arm did (arm − keeper)

| year | Δprice all h | Δ upper tercile | ΔCT / CC / PRB TWh | unserved MWh, keeper → EXR | pool MWh |
|---|---:|---:|---|---|---:|
| 2019 | +0.35 | +0.48 | +1.58 / +1.07 / −2.26 | 0 → 0 | 0 |
| 2020 | +0.31 | +0.38 | +1.34 / +0.74 / −1.82 | 0 → 0 | 0 |
| 2021 | +1.14 | +0.25 | +0.82 / +1.14 / −1.83 | 0 → 0 | 0 |
| 2022 | +0.94 | +0.67 | +0.97 / +1.57 / −2.25 | 0 → 0 | 0 |
| 2023 | +0.36 | +0.29 | +1.46 / +1.09 / −2.22 | 0 → 0 | 0 |
| 2024 | +0.18 | +0.14 | +1.37 / +1.16 / −2.24 | **862 → 443** | 1,334 (4 h, South) |
| 2025 | +0.72 | +0.68 | +1.23 / +1.21 / −2.36 | **136 → 44** | 725 (3 h, South) |

- **The scarcity failure is gone.** The pool clears only in the keeper's own South scarcity hours, always at the
  shed price, and it **halves** the keeper's unserved energy. EX had tripled it (2024: 862 → 3,737 MWh).
- **Price moves less than EX, as the DESIGN predicted.** Upper tercile +0.14 to +0.68 $/MWh, against an
  $11–15 gap in 2023–25. This carrier does not own that gap.
- **The coal shift survives.** COAL_PRB is −1.8 to −2.4 TWh in every year (EX: −2.1 to −3.1); gas CT and CC
  take the volume.

## 2. Scores (`calibration_verdict.py`), keeper → EXR (EX for reference)

| year | tier | C3a mean LMP | C3b NRMSE | C1 COAL_PRB, TWh | C1 CT_PEAKER, TWh | C4 gas |
|---|---|---|---|---|---|---|
| 2019 | validation | +11.5 → **+13.1 %** (EX +14.1) | 0.146 → 0.163 | +2.99 → +0.72 | +0.18 → +1.65 | PASS |
| 2020 | validation | +27.5 → **+29.3 %** (EX +30.4) | 0.343 → 0.362 (FAIL both) | −0.44 → −2.26 | +5.12 → +6.42 | PASS |
| 2021 | validation | +6.5 → **+9.6 %** (EX +11.3 FAIL) | 0.184 → 0.130 | +13.20 → +11.37 (FAIL both) | +0.37 → +1.18 | FAIL → **PASS** |
| 2022 | validation | −5.8 → −3.8 % | 0.184 → 0.179 | +13.17 → +10.92 (FAIL both) | −2.40 → −1.45 | FAIL both |
| 2023 | train | −6.7 → **−5.4 %** (EX −4.4) | 0.172 → 0.173 | +3.31 → **+1.08** | +1.59 → +2.99 | PASS |
| 2024 | train | −8.6 → **−8.2 %** (EX −6.0) | 0.172 → 0.184 | +3.59 → **+1.35** | +1.40 → +2.76 | PASS |
| 2025 | train | −5.4 → **−2.9 %** (EX −1.6) | 0.146 → 0.169 | (prelim 923, not gated) | (not gated) | PASS |

- **Train tier 2023–25: CALIBRATED → CALIBRATED** (lone ledgered C3c, unchanged: >$200 h 0 / 4 / 4 vs RT
  42 / 59 / 68).
- **No new failing row anywhere** in 2019–25. 2021 C3a stays inside ±10 %, though close to the edge (+9.6 %).
- **Moves the right way:** C4 2021 FAIL → PASS. C1 CC_REGULAR and COAL_PRB errors shrink in every year 2021–24.
- **Moves the wrong way:** 2019–20 C3a (+1.6 / +1.8 points) and C3b NRMSE in five of seven years.
  CT_PEAKER over-count grows ~1.4 TWh/yr, though it stays inside the band.
- **D-4:** the same 7 FAIL rows as the keeper (plants 1230, 3008, 6193). C8: PASS.

## 3. Expectations (PRECOMMIT §5)

| # | expectation | result |
|---|---|---|
| E1 | shard check PASS ×7 (incl. pool present / offer / scarcity-only) | **PASS** |
| E2 | Optimal within budget | **PASS** (8–11 min wall) |
| E3 | unserved not up > 500 MWh in any year | **PASS**: down 419 MWh (2024) and 92 MWh (2025); 0 elsewhere |
| E4 | no new D-4 FAIL row (keeper 7) | **PASS** (identical set) |
| E5 | train CALIBRATED; no C1/C3a/C3b/C4 flip 2023–25 | **PASS** |
| E6 | instrument: train C3a moves toward 0 by less than EX | **PASS**: +1.3 / +0.4 / +2.5 points vs EX +2.3 / +2.6 / +3.8 |

**Instrument check.** The DESIGN predicted C3a −5.3 / −7.7 / −3.3 % for 2023–25; the solve gave −5.4 / −8.2 / −2.9 %.
For 2021 it predicted +9.5 % and the solve gave +9.6 %. COAL_PRB 2023 / 24 was predicted at +1.4 / +1.8 TWh and
came in at +1.1 / +1.35 TWh.

## 4. Recommendation (pre-registered rule, PRECOMMIT §6)

**RECOMMEND PROMOTE: E1–E5 hold.**

- **Structure (rules 1, 14):** the flat, uncited GADS performance and summer class derates on SPP fossil rows are
  replaced by SPP's own measured MMU classes. They are now applied on the MMU's own definitions, with zero
  free parameters.
- **The cost, stated:**
  - the validation years 2019–20 get more over-priced (+1.6 / +1.8 C3a points);
  - 2021 C3a moves to +9.6 %, at the edge of the band;
  - the inputs are digitized annual white-paper figures, and the recurring ASOM disagrees by ~15 % (SPP-106 DESIGN §1).
- **It does not close the 2023+ upper-tercile gap and does not claim to.**
- **The owner decides (rule 31).**

## 5. Retrievability (rules 33 / 34)

- **Composite:** `results/calibration/spp107EXR_span` (7 years, attested, scored). It is in this lane's working
  tree, gitignored, registered locally only.
- **On promotion:** `promote_keeper.py` commits it to `main` inside the keeper bundle.
- **If not promoted:** it is lost with the container. Re-solving costs ~10 min wall across 7 shards.
- **Leg provenance** (shard branches; transport, not storage):

| 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| `2d78e59f` | `e7eeb9a0` | `4a5ff042` | `5e202afd` | `6e7f3d58` | `04dae204` | `75a1d9f6` |

- **Shards:** all 7 are archived.

## 6. Rules

- **1:** judged on structure; the recommendation follows the pre-registered rule.
- **13:** measured MMU classes held to the nearest year; the pool is endogenous.
- **14:** the bands now use the MMU's own measurement basis.
- **19:** a sub-gate of one mechanism.
- **21:** zero free parameters.
- **25:** SPP-only.
- **29(b):** the keeper is the control.
- **31–36:** the parent solved nothing; bytes were in hand before archive; one year per shard.
