# RESULT — SPP-106: MMU offer-side unavailability carrier EX, solved

- **Lane:** SPP-106, on the owner card "Build EX anyway" (2026-10-01).
- **PRECOMMIT:** `docs/handoffs/PRECOMMIT-spp-106-offer-side-unavailability-2026-10-01.md` (pin `392633a1`, Addenda A–C).
- **Control:** keeper `2026-09-28-spp-100-chp-scope` (rule 29(b) form 4; G-DRIFT all INERT).
- **Arm EX:** `spp_mmu_offer_unavailability = true`. Run `2026-10-01-spp106-mmu-offer-side`, bundle `spp106EX_span`.
- **Solve:** 7 year-isolated shards (rule 36). The parent ran no LP.
  - Every leg passed `_spp106_shard_check.py` in its shard and again in the parent.
  - The composite was built with `_rspp_compose.py --require spp_mmu_offer_unavailability=true` and attested with
    `gen_spp106_attestation.py`, which confirms the offer curve and every other scenario field are byte-identical to the keeper.

## 1. What the arm did (arm − keeper)

| year | Δprice all h, $/MWh | Δ upper tercile | ΔCT / CC / ST / PRB TWh | unserved MWh: keeper → EX (hours) |
|---|---:|---:|---|---|
| 2019 | +0.54 | +0.82 | +2.18 / +0.91 / −0.24 / −2.51 | 0 → 0 |
| 2020 | +0.47 | +0.67 | +1.82 / +0.69 / −0.17 / −2.12 | 0 → 0 |
| 2021 | +1.78 | +0.82 | +1.25 / +1.53 / −0.20 / −2.51 | 0 → 0 |
| 2022 | +1.86 | +2.15 | +1.40 / +1.96 / −0.18 / −2.95 | 0 → **420** (3 h, May) |
| 2023 | +0.59 | +0.60 | +1.99 / +1.15 / −0.24 / −2.75 | 0 → 0 |
| 2024 | +0.66 | +1.40 | +2.02 / +1.18 / −0.32 / −2.81 | 862 → **3,737** (2 → 5 h, Oct) |
| 2025 | +1.08 | +1.16 | +1.88 / +1.31 / −0.12 / −3.10 | 136 → **1,568** (1 → 4 h, Dec) |

- **The zero-LP prediction held on price.** The instrument predicted +0.4–0.7 in the 2023–25 upper tercile; the solves
  moved it +0.6 to +1.4.
- **It did not hold on scarcity.** The instrument found no short hours. The LP, which has ramps, zones and reserves,
  goes short in a few shoulder hours. Rule-14 note: the MMU bands remove ~6.5 % of every fossil row all year, with no
  seasonal shape.
- **The largest volume effect is coal.** Coal PRB falls 2.1–3.1 TWh every year: it loses ~6.5 % of capacity where the
  incumbent removed ~3 %. Gas, mostly CT, takes up the volume.

## 2. Scores (`calibration_verdict.py`), keeper → EX

| year | tier | C3a mean LMP | C3b NRMSE | C3c >$200 h (RT) | C1 COAL_PRB | C1 CT_PEAKER |
|---|---|---|---|---|---|---|
| 2019 | validation | +11.5 → **+14.1 %** | 0.146 → 0.172 | 0 → 0 (47) | +2.99 → +0.47 | +0.18 → +2.25 |
| 2020 | validation | +27.5 → **+30.4 %** | 0.343 → 0.371 | 0 → 0 (23) | −0.44 → −2.55 | +5.12 → +6.89 |
| 2021 | validation | +6.5 → **+11.3 % (PASS → FAIL)** | 0.184 → 0.125 | 352 → 375 (140) | +13.20 → +10.69 (FAIL) | +0.37 → +1.59 |
| 2022 | validation | −5.8 → −1.6 % | 0.184 → 0.178 | 0 → 4 (99) | +13.17 → +10.22 (FAIL) | −2.40 → −1.04 |
| 2023 | train | −6.7 → **−4.4 %** | 0.172 → 0.173 | 0 → 0 (42) | +3.31 → **+0.56** | +1.59 → +3.50 |
| 2024 | train | −8.6 → **−6.0 %** | 0.172 → 0.178 | 7 → 7 (59) | +3.59 → **+0.78** | +1.40 → +3.40 |
| 2025 | train | −5.4 → **−1.6 %** | 0.146 → 0.170 | 2 → 4 (68) | (prelim 923, not gated) | (not gated) |

- **Train tier 2023–25: CALIBRATED → CALIBRATED** (lone ledgered C3c, unchanged). C3a improves in all three years,
  and the keeper's coal PRB over-count falls by ~2.8 TWh a year.
- **C4:** gas 2021 FAIL → PASS. No 2023–25 flip.
- **Validation:** 2021 C3a newly fails; 2019–20 become more over-priced.
- The ISO determination already reads NOT-YET on the validation years (rule 30(c)). The arm adds a failing year
  (2021 C3a) to them.

## 3. Expectations (PRECOMMIT §5)

| # | expectation | result |
|---|---|---|
| E1 | shard check PASS ×7 | **PASS** |
| E2 | Optimal within budget | **PASS** (each shard ~8–10 min wall) |
| E3 | unserved not up > 500 MWh in any year | **FAIL**: +2,875 MWh in 2024 and +1,432 MWh in 2025 (+420 in 2022, within tolerance) |
| E4 | no new D-4 FAIL row (keeper 7) | **PASS** (7, identical set) |
| E5 | train stays CALIBRATED; no C1/C3a/C3b/C4 flip 2023–25 | **PASS** |
| E6 | upper-tercile price rises in each of 2023–25 | **PASS** (+0.60 / +1.40 / +1.16) |

## 4. Recommendation (pre-registered rule, PRECOMMIT §6)

**RECOMMEND AGAINST promoting.** E3 fails: unserved energy rises 2.9 GWh in 2024 and 1.4 GWh in 2025. That is a few
shoulder hours, but it is the SPP-105 B failure mode again: removing capacity flat leaves the fleet short where SPP
actually served load.

What the solve shows, at full magnitude:
- **On structure:** it replaces an uncited flat approximation with SPP's own measured classes and does what it says. It
  moves price up, and it reduces the coal over-count the keeper carries in every year (C1 PRB 2023 / 24 +3.3 / +3.6 →
  +0.6 / +0.8 TWh).
- **On the target:** train C3a improves 2.3–3.8 points. The upper-tercile gap ($11–15) closes by $0.6–1.4 only, as the
  DESIGN predicted. It is not the owner of the 2023+ shortfall.
- **The cost:** it is a flat level mover. Validation 2019–21 get more over-priced (2021 C3a newly FAILS), and E3 fails.
- **The owner decides (rule 31).** A promotion would be on the owner's override of E3, as SPP-105 B's rule-13 pin was
  recorded as the owner's override.

## 5. Retrievability (rules 33(d) / 34(e))

- **Composite** `results/calibration/spp106EX_span` (295 MB) is in this lane's working tree, **not committed**.
  - It is gitignored and registered locally only (sidecar + payload, uncommitted).
  - It does not survive the session unless the owner promotes.
- **Cost to reproduce** if lost: ~10 min wall across seven parallel shards.
- **Leg provenance** (shard branches; transport, not a recovery route):

| 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| `af4dd3a8` | `73927ea5` | `db2aea9d` | `649b8889` | `49d27243` | `7e2b7a32` | `e6f55d8b` |

- **Shards:** all 7 are archived.

## 6. Rules

- **1:** judged on structure; the recommendation follows the pre-registered rule, not a residual.
- **13:** inputs are measured MMU classes, held to the nearest year.
- **14:** replaces an uncited approximation; its rule-14 tension (ASOM vs white paper) is declared.
- **19:** replacement, not stack.
- **21:** zero free parameters.
- **25:** SPP only.
- **29(b):** the keeper is the control.
- **31–36:** the parent solved nothing; bytes were in hand before archive; one year per shard.
