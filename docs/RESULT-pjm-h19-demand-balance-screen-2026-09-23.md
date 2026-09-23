# RESULT — pjm-h19: `demand_balance_screen` on PJM, all six years (2026-09-23)

Companion to `docs/PRECOMMIT-pjm-h19-demand-balance-screen-2026-09-23.md` (pushed before any solve;
shards pinned to `2d57aa2089d687d9251f229474f84601a3111059`). **Every number this lane cites is here.**

Arm = PJM keeper `2026-09-22-pjm-hydro2-ror-span` recipe **+ `demand_balance_screen=true`**, nothing else.
Control = the committed keeper bundles (rule 29(b) form 4).
Registered: **`2026-09-23-pjm-h19-dbs-span`** (2023–25) + **`2026-09-23-pjm-h19-dbs-touchpoint`**
(2020–22, stamped to the arm span). **Promotion: UNRULED.**

## 1. Verdict

**Every prediction written before the solve held.** The repair removes 41.7 GWh of phantom
load shed at VOLL, turns 2020 C3b **FAIL → PASS**, leaves 2020 C3a failing at the predicted ~+14 %,
and does not move any other year.

| | predicted (PRECOMMIT §6) | measured |
|---|---|---|
| 2020 C3b | 0.212 → ~0.15–0.16, FAIL → PASS | **0.212 → 0.155, FAIL → PASS** |
| 2020 C3a | +19.0 % → ~+14 %, still FAIL | **$25.22 → $24.28 vs $21.20: +14.5 %, still FAIL** |
| 2024 | < $0.01/MWh, no status change | +$0.001/MWh LW, no status change |
| span 2023–25 | stays CALIBRATED | **CALIBRATED, 8/8 PASS, zero status changes** |
| touchpoint 2020–22 | stays NOT-YET | **NOT-YET** (C1, C3a, C3b remain on 2022 and C1/C3a on 2020) |

## 2. Gates

| gate | result |
|---|---|
| **G0 drift** | **PASS, exact.** 2021, 2022, 2023, 2025 (byte-identical demand) reproduce the keeper: load-weighted price Δ 0.0000 $/MWh and every class Δ < 1e-4 TWh. No LIVE drift between `152c546a` and `2d57aa20`. |
| **G1 liveness** | **PASS.** VOLL shed 2020: 41,679 MWh → **0**. Repaired hours land on the neighbour interpolation (table below). |
| **G2 targeted** | **PASS as predicted** (§1). |
| **G3 no silent breakage** | Zero criterion status changes in either span. D-1/D-2/D-4 FAIL sets identical to the keeper's (27 span, 21 touchpoint; none new, none gone). |

G1 detail (`scripts/probes/pjm_h19_readout.py`):

| hour | served demand ctl → arm | slack | system price |
|---|---|---|---|
| 2020 h5003 | 192,229 → 132,060 MW | 28,180 → 0 | $1,991.95 → $33.37 |
| 2020 h5031 | 176,085 → 140,690 MW | 13,499 → 0 | $1,972.14 → $49.16 |
| 2020 h5383 | 138,575 → 99,324 MW | 0 → 0 | $44.68 → $23.78 |
| 2024 h7787 | 56,260 → 95,147 MW | 0 → 0 | $20.13 → $31.67 |

## 3. Scored moves (arm vs keeper, both on the HEAD-rebuilt benchmark)

**Span 2023–25:** only 2024 moves, all ≤ 0.03 TWh (CC_REGULAR 336.269 → 336.293, COAL_BIT
103.812 → 103.818, gas sysvol 383.34 → 383.36). Nothing else moves.

**Touchpoint 2020–22:** only 2020 moves.

| record | keeper → arm | actual |
|---|---|---|
| C3a mean LMP 2020 | 25.22 → **24.28** | 21.20 (FAIL, +14.5 %) |
| C3b NRMSE 2020 | 0.212 → **0.155** | PASS (bar 0.20) |
| C3c tail count 2020 | 2 → **0** | 2 (still PASS) |
| C1 CT_PEAKER 2020 | 15.521 → 15.502 TWh | 18.66 |
| C1 COAL_BIT 2020 | 156.956 → 156.951 TWh | 131.451 (FAIL, standing) |

**Against the arm, stated:** 2020 C3c's model tail count falls **2 → 0** while the actual is 2. The
keeper's two "scarcity" hours were the two phantom-load hours, so it matched the real count by
accident. Still PASS. CT_PEAKER 2020 moves 0.02 TWh further from actual.

Still failing after the repair (touchpoint): **2022 C3a −10.4 % / C3b 0.242** (Elliott, Card B),
**2020 C3a +14.5 %** (the CC-marginal overshoot, Card C), and C1 COAL_BIT 2020/21, CC_REGULAR 2022,
CT_PEAKER 2021.

## 4. Benchmark drift (`ad42fe43`), measured

`--rebuild-benchmark` re-rendered PJM's six `bench/PJM/<y>.json.gz` parts at HEAD, which carries
`ad42fe43` (the EIA-923 dual-fuel oil re-attribution). That moves the **keeper's own** scored
actuals too: C1 actuals by ≤ 0.2 TWh, sysvol by ≤ 0.2 TWh, a vestigial generic `COAL` C1 row
(0.001 TWh actual) disappears (18 → 16 free-class records), and C8's COAL records go SKIPPED → PASS.
**Zero keeper status changes; PJM stays CALIBRATED.** `status/PJM.js` rebuilt accordingly. All §3
comparisons are on this same benchmark, so none of it is attributed to the arm.

## 5. Disclosed

1. **The bar changed twice before any solve** (PRECOMMIT §2): v1 was degenerate (IQR 0), and v2 blamed
   a correct CAISO 2019 hour. The four PJM targets were known from pjm-h18 before any bar was written.
2. **Off-PJM hours the screen would repair if armed there** (not armed): CAISO 2019 (17 h), 2020
   h6730, **2025 h5076** (a CAISO training year), and PJM 2019 h8031/h8296. Matrix cells carry them.
3. **Out of reach, named:** artifacts EIA-930 also carried into NG − TI (SPP 2024 h4774, SPP 2025
   h4107, SOCO 2025 ×5), multi-hour clusters, NWPP.
4. **Shards:** every shard's `regenerate_clean` lost `emissions-unit-annual` to OOM (not a solve
   input). The 2022 shard went idle mid-solve and resumed on its own when its background solve
   exited. Neither affected a result.
5. **`audit_keepers --iso PJM`** reports E13 on the two registered-but-unpromoted runs, as it did
   for hydro-2 pending. It clears on the owner's ruling (promote or prune).

## 6. Retrievability (rule 34(e))

The two registered composites (slim keeper shape: attestation, hourly sidecars, diagnostics, meta,
metrics, run_config) and their payloads are **committed on this lane's branch** and land on `main`
with its PR. The six per-year legs (17 files each, `dispatch/<y>_P1.parquet` included) are on this
container, gitignored. Provenance SHAs (rule 33(d), not a recovery route): 2020 `8c6a96bd`,
2021 `c6a7f5f9`, 2022 `8ae9314d`, 2023 `97bf7bdb`, 2024 `180f5f9c`, 2025 `43de66bd`. Any leg not
on `main` costs a ~20 min re-solve.

## 7. Promotion — the question for the owner

**FOR.** A rule-14 source-data repair with **zero free parameters**. EIA-930's own balance identity
shows the four readings are wrong by 35–57 GW, and the model was shedding 41.7 GWh at $2,000 to serve
them. Four of six years are bit-identical. 2020 C3b clears on the predicted mechanism. No criterion
regresses in status, and the D-diagnostic fail sets are unchanged.

**AGAINST.** It closes no determination: the touchpoint stays NOT-YET and the span was already
CALIBRATED. 2020 C3c's tail count now reads 0 vs 2 actual. The screen is ISO-agnostic code armed only
for PJM, so the CAISO 2025 h5076 artifact stays in CAISO's keeper until that lane rules.

**If promoted** (rule 35 order): re-key `keepers/PJM.json` and PJM's `calibration-complete.json`
block to `2026-09-23-pjm-h19-dbs-span`; year union {2020…2025} is covered exactly by the pair;
`build_status --iso PJM`; `audit_keepers --iso PJM`; then `prune_iso_runs.py --iso PJM --keep
2026-09-23-pjm-h19-dbs-touchpoint --force-uncite` removes the hydro-2 pair; matrix cell `O → K`.
