# RESULT — hydro-2: PJM `hydro_ror_split`, full year set (2026-09-22)

Companion to `docs/PRECOMMIT-hydro-2-pjm-2026-09-22.md` (pushed before any solve; shards pinned to
`152c546a31c2b32191aae643230aa1d32ba5856c`). **Every number this lane cites is here.**

Arm = PJM keeper `2026-09-22-pjm-h16-coalgrain` recipe **+ `hydro_ror_split=true`**, nothing else.
Control = the committed keeper bundles (rule 29(b) form 4; G-DRIFT all inert, PRECOMMIT §5).

## 1. Gate table

Hydro statistics, arm vs control, from each bundle's `hourly/class_hourly_<y>.parquet`
(`scripts/probes/hydro2_pjm_readout.py`). Top-decile = share of each month's hydro energy in that
month's top-10 % load hours (a flat fleet is 0.10).

| year | hydro TWh ctl → arm | G2 Δ | hours < 1 MW | p05 MW | p95 MW | top-decile | daily-SD ratio |
|---|---|---:|---|---|---|---|---:|
| 2020 | 10.0218 → 10.0218 | 0.0000 % | 1,634 → **0** | 0 → 470.9 | 3,317 → 2,446 | 0.274 → 0.193 | 0.510 |
| 2021 | 10.3759 → 10.3759 | 0.0000 % | 1,116 → **0** | 0 → 633.7 | 3,304 → 2,416 | 0.254 → 0.186 | 0.496 |
| 2022 | 8.9685 → 8.9685 | 0.0000 % | 1,965 → **0** | 0 → 464.5 | 3,292 → 2,360 | 0.289 → 0.201 | 0.476 |
| 2023 | 8.9030 → 8.9030 | 0.0000 % | 1,010 → **0** | 0 → 380.7 | 3,106 → 2,249 | 0.281 → 0.198 | 0.487 |
| 2024 | 8.8608 → 8.8608 | 0.0000 % | 1,867 → **0** | 0 → 281.0 | 3,202 → 2,264 | 0.297 → 0.211 | 0.513 |
| 2025 | 8.4636 → 8.4636 | 0.0000 % | 1,867 → **0** | 0 → 282.8 | 3,214 → 2,267 | 0.315 → 0.218 | 0.499 |

| gate | verdict |
|---|---|
| **G1 liveness** | **Zero-hours limb PASS** (0 < 500 every year). **MW limb FAIL, disclosed, NOT amended**: the RoR flat class carries 4.80–5.12 TWh/yr (D-2 `hydro_ror_flat`, 54–58 % of hydro), i.e. **548–584 MW-average**, against a ≥ 1,000 MW-average bar carried from hydro-1. That bar was unreachable by construction — the flat class can only carry its own EIA-923 budget (~4.87 TWh ≈ 556 MW) — so it was sized on nameplate (1,555.8 MW), not energy. A specification error in the bar, not an inert arm. |
| **G2 invariant** | **PASS, exact** — 0.0000 % every year. |
| **G3 targeted statistic** | **PASS every year** — zero-hours → 0, p05 up, p95 down, top-decile down, within-month banking roughly halved. |
| **G4 no silent breakage** | See §2. |

## 2. Scored rubric (G4)

**Span 2023–2025** (`2026-09-22-pjm-hydro2-ror-span`): **CALIBRATED, 8/8 PASS — identical to the
keeper, zero status changes** (`scripts/probes/hydro2_pjm_verdict_diff.py`). Largest moves:

| record | keeper → arm | actual | reading |
|---|---|---|---|
| C3a mean LMP 2023 / 2024 / 2025 | 29.70 / 30.26 / 42.55 → 29.77 / 30.41 / 42.79 | 29.58 / 31.36 / 45.89 | toward actual 2024–25; 2023 +0.07 past it |
| C3b shape 2024 / 2025 | 0.125 / 0.148 → 0.124 / 0.143 | — | slightly better |
| C1 CT_PEAKER 2023 / 2024 / 2025 TWh | 20.15 / 25.32 / 29.78 → 20.44 / 25.63 / 30.16 | 21.75 / 24.17 / 24.09 | +0.3 TWh; toward actual 2023, away 2024–25 |
| C1 CC_REGULAR TWh | −0.3 to −0.4 every year | | toward actual 2023–25 |
| C8 CT_PEAKER forced share | 0.128 / 0.132 / 0.148 → 0.124 / 0.128 / 0.144 | limit 0.15 | more headroom |

Mechanism of the CT move: hydro no longer shaves the evening peak (p95 −940 MW), so peakers take
it. That is the physically expected direction for removing a peaking hydro representation, and at
+0.3 TWh against a 24–30 TWh class it is small. Per rule 1 it stays either way.

**Touchpoint 2020–2022** (`2026-09-22-pjm-hydro2-ror-touchpoint`, stamped to the arm span): **NOT-YET —
identical to the keeper touchpoint** (same C1 / C3a / C3b FAILs, same C3c CAVEAT), **zero status changes**.

| record | keeper → arm | actual | reading |
|---|---|---|---|
| C1 CT_PEAKER 2020 / 2021 / 2022 TWh | 15.21 / 12.28 / 16.30 → 15.52 / 12.80 / 16.84 | 18.67 / 21.52 / 19.69 | toward actual all three |
| C1 COAL_BIT 2020 / 2021 TWh (FAIL rows) | 157.19 / 176.23 → 156.96 / 175.83 | 131.46 / 156.60 | toward actual, still FAIL |
| C1 CC_REGULAR 2022 (FAIL row) | 319.84 → 319.15 | 308.09 | toward actual, still FAIL |
| C1 ST_GAS 2020–22 TWh | +0.13 / +0.24 / +0.16 | | away from actual (small) |
| C3a mean LMP 2020 / 2021 / 2022 | 25.13 / 38.37 / 66.14 → 25.22 / 38.57 / 66.36 | 21.20 / 38.53 / 74.07 | 2020 away +0.09; 2021 ≈; 2022 toward |
| C3b shape 2020 / 2022 (FAIL rows) | 0.208 / 0.245 → 0.212 / 0.242 | — | 2020 slightly worse, 2022 slightly better |
| D-2 CT_PEAKER forced share | 0.217 / 0.341 / 0.266 → 0.209 / 0.321 / 0.254 | limit 0.15 | better every year (pre-existing FAIL, C8 still PASS via rule 20 grounding) |

D-4 fail set is the keeper touchpoint's own (plant 3138 `st_netload_drag`, 7213 coal, a handful of
`cc_mustrun_per_plant` rows), plus **one new trivial row** — plant 62926 / 2022, 0.0014 TWh over 3 h.

## 3. Disclosed

1. **G1's MW limb fails on a mis-sized bar** (§1). Not amended after the number landed.
2. **`hydro_ror_flat` is a D-2 floor on 54–58 % of hydro energy.** Hydro is 1.0–1.1 % of PJM load,
   below rule 20's 2 % materiality line, so C8 does not gate it. Its D-4 window is `h0-23` with
   0 off-window energy — a run-of-river plant has no off-window by construction.
3. **Virtual-bid corpus re-fetched** per shard (PRECOMMIT §2); no `SHA256SUMS` exists to prove byte
   identity with the keeper's fetch.
4. **PJM has no clean hourly conventional-hydro reference** (both published series fold 5,046 MW of
   pumped storage), so "toward reality" for the hydro shape rests on the RoR physics plus the folded
   series' one-sided overnight floor, not on a falsification test.
5. **Not armed:** `hydro_min_flow_floor`, `hydro_dispatch_envelope` (PS-contaminated `NG: WAT`
   readers — live code gap, rule 14).
6. **Shard setup miss (mine):** the shard prompts omitted `regenerate_clean.py`; five shards
   recovered on their own, 2022 stopped correctly and was relaunched. No result affected.

## 4. Retrievability (rule 34(e))

Legs pushed full 17-file bundles; provenance SHAs (rule 33(d), not a recovery route):
2020 `6ae86e4d`, 2021 `997b3af7`, 2022 `213b06f9`, 2023 `f97de728`, 2024 `e0e9b7cd`, 2025 `985ad948`.
The composites and their registrations are committed on this lane's branch and land on `main` with
its PR. Any leg not on `main` costs a ~12 min re-solve.

## 5. Promotion — OWNER DECISION PENDING (rule 31)

**FOR.** A rule-17 structural repair with **zero free parameters**: a run-of-river plant has no
reservoir, so its output is its inflow. The keeper parks PJM hydro at **0 MW for 1,010–1,965 hours
every year**; the arm eliminates that in all six years with annual energy **unchanged to four
decimals** (G2 exact) and within-month banking halved. No scored criterion changes status in either
span; most material moves are toward actual (CT_PEAKER, coal, CC, D-2 peaker forcing). The owner's
standing instruction — structural integrity can outweigh gate regression — is not even needed here.

**AGAINST.** G1's MW limb fails (a mis-sized bar, §1). Small away-from-actual moves: C1 CT_PEAKER
2024–25 (+0.3 TWh), ST_GAS 2020–22, C3a 2020 (+$0.09) and 2023 (+$0.07). No clean conventional-hydro
hourly reference exists for PJM, so the shape improvement rests on physics, not a falsification test.

**Retention.** All six legs and both composites are on disk here and the composites are committed on
this branch. Nothing is pruned until the owner rules (rule 31). If promoted: re-key
`keepers/PJM.json` + `calibration-complete.json`, `build_status.py --iso PJM`, `audit_keepers --iso PJM`,
then `prune_iso_runs.py --iso PJM --keep 2026-09-22-pjm-hydro2-ror-touchpoint --force-uncite`
(rule 35(e) order). Year union {2020…2025} is covered exactly.
