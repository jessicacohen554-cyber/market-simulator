# RESULT — SPP-102: the SPP commitment posture, solved

**Lane** SPP-102 · PRECOMMIT `docs/handoffs/PRECOMMIT-spp-102-commitment-posture-2026-09-29.md` (pin `62ac90e2`,
Addendum A) · control = keeper `2026-09-28-spp-100-chp-scope` (rule 29(b) form 4) · registered run
**`2026-09-29-spp-102-commitment-posture`**, bundle `results/calibration/spp102_arm_span` (2019–2025).

- **Arm:** keeper + `spp_commitment_posture=true`. That is 23 per-plant CC pools with min-load 0.209, min-up 15 h,
  min-down 8 h and NREL start costs, with the P1 startup markup zeroed on the postured units.
- **Solve:** seven year-isolated shards (rule 36). The parent ran no LP.

## 1. What it did (arm − keeper)

| year | ΔCC_REGULAR TWh | ΔCOAL_PRB | ΔCOAL_LIGNITE | ΔCT_PEAKER | Δprice $/MWh | unserved |
|---|---:|---:|---:|---:|---:|---|
| 2019 | +2.21 | −1.47 | −0.33 | −0.30 | −0.31 | 0 = 0 |
| 2020 | +2.05 | −1.19 | −0.23 | −0.42 | −0.43 | 0 = 0 |
| 2021 | +2.03 | −1.58 | −0.18 | −0.23 | −0.36 | 0 = 0 |
| 2022 | +0.85 | −0.92 | −0.09 | +0.12 | −0.58 | 0 = 0 |
| 2023 | +1.32 | −0.85 | −0.14 | −0.24 | −0.36 | 0 = 0 |
| 2024 | +1.28 | −0.79 | −0.09 | −0.16 | −0.42 | 862 = 862 MWh |
| 2025 | +1.63 | −1.21 | −0.10 | −0.21 | −0.34 | 136 = 136 MWh |

CC gains **1.1–2.7×** the zero-LP DP bound in 2019–21 and 2023–25, and **7.7×** in 2022. The pre-registered
caveat (PRECOMMIT §2) named the reason: zeroing the P1 startup markup makes CC offers cheaper, and that channel was
not in the bound.

## 2. Expectations (PRECOMMIT §5)

| # | expectation | result |
|---|---|---|
| E1 | Shard check PASS ×7 | **PASS** (re-run in the parent on every leg) |
| E2 | Optimal within the budget | **PASS** |
| E3 | Unserved energy not up > 500 MWh | **PASS** (identical every year) |
| E4 | No new D-4 FAIL row | **PASS** (8 FAIL rows in both, same set); C8 unchanged (2022 ST_GAS 31.3 % vs 31.2 %, grounded) |
| E5 | Train 2023–25 stays CALIBRATED, no flip | **FAIL**: C3a 2024 goes PASS → FAIL, −8.6 % → **−10.3 %** (band ±10 %) |

## 3. Validation rows (reported, not the basis)

| row | keeper | arm | status |
|---|---|---|---|
| C1 CC_REGULAR 2021 | −9.65 TWh | **−7.61** | still FAIL (volume now in band, share −3.0 pp out of band) |
| C1 CC_REGULAR 2022 | −10.84 | −10.00 | FAIL |
| C1 COAL_PRB 2021 / 2022 | +13.20 / +13.17 | +11.62 / +12.25 | FAIL |
| C4 gas 2021 NRMSE | 0.307 | **0.281** | **FAIL → PASS** |
| C4 gas 2022 NRMSE | 0.356 | 0.339 | FAIL |
| C3a 2019 / 2020 | +11.5 / +27.5 % | +10.0 / +24.9 % | FAIL |
| C3b 2020 | 0.343 | 0.320 | FAIL |

Every validation row moves the right way, and one flips to PASS. The train tier loses C3a 2024 by 0.3 pp.

## 4. Recommendation (pre-registered rule, PRECOMMIT §6)

**RECOMMEND AGAINST promotion: E5 fails** (C3a 2024 −10.3 %).

This is the rule's verdict, not a judgement against the structure. By rule 1 the posture is real commitment physics
on measured parameters, and every validation row improves. What it costs is a lower price level across all years
(−$0.31 to −$0.58/MWh), which pushes 2024 just past the band. SPP's 2023+ price is already short of RT (the SPP-79/82
upper-tercile object), so a structure that adds cheap committed CC deepens that miss.

The owner decides (rule 31).

**OWNER RULING (2026-09-29, decision card): "Don't promote (Recommended)."** Keeper `2026-09-28-spp-100-chp-scope`
stands (train tier CALIBRATED). The field stays in the code, off by default. Its matrix cell goes O → **R**
(rejected as a standalone arm), with a named re-open route: **SPP-103, "Pair posture + price fix"** (owner card, same
sitting). That lane looks for a structural, measured driver of SPP's 2023+ price shortfall, so the posture can be
re-tested together with it without breaking C3a 2024. The registration was removed under rule 15's keeper-only
retention and rule 31 trigger (i); the bundles are gitignored.

## 5. Retrievability (rules 33(d) / 34(e))

- **The composite** is in this lane's working tree, **not promoted** and gitignored. This RESULT doc and git history
  are the record.
- **The legs** were pushed as provenance only: 2019 `9efe9d9e`, 2020 `7646a1dc`, 2021 `012273be`, 2022 `807adee2`,
  2023 `d8ef67b9`, 2024 `dbca2693`, 2025 `54f8f0d3` on `claude/spp102-<y>`. Treat these SHAs as provenance, not as
  a recovery route.
- **Cost to reproduce** if the working tree is lost: about 30 min of seven parallel shards.
- **Round 1:** seven shards stopped at the ARMED hard stop (Addendum A) and pushed nothing.
- **Shards:** all 14 are archived.

## 6. Rules

- **1 / 18 / 19 / 21:** structure on measured parameters; one posture construction; startup charged once; zero
  fitted parameters.
- **13:** no outcome pinned.
- **29(b):** keeper as control, G-DRIFT all INERT.
- **36:** year-isolated shards.
- **28(b):** `spp_commitment_posture` cell O → R (owner ruling), evidence appended.
