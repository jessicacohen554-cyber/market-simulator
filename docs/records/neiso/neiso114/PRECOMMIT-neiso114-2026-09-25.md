# PRECOMMIT — neiso-114: the C1 CC_REGULAR miss left by the corrected-input keeper (2026-09-25)

**ISO:** NEISO · **Mode:** backcast · **LP spent before this doc:** zero ·
**Base:** `06d9a9da` (main, after COAL-SUB #6619 merged) ·
**Incumbent keeper (the control, rule 29(b) form 4):** `2026-09-24-r-neiso-inputs-2019`,
bundle `results/calibration/rneiso_span`, 2019–2025, solved at `c265c1c3`.

Keeper determination: train tier 2023–2025 CALIBRATED (lone ledgered C3c); full span NOT-YET on
C1 CC_REGULAR 2019 −4.66 / 2021 −3.17 / 2022 −3.12 TWh (band ≈ ±3.0 TWh and ±3.0 pp share).

## 0. Year set (rules 34(c) / 35(b))

Registered NEISO runs: exactly one, the keeper; year set **2019–2025**. Every arm below solves all
seven years, one shard per year (rule 36).

## 1. Root cause, measured at zero LP (work item 1)

Probes: `phase0_offer_census.py` (`run_year(fleet_only=True)` on the keeper recipe; `mc_base` is the
assembled offer the LP is handed) and the keeper's own committed `hourly/class_band_hourly_<Y>.parquet`.

**Where the keeper's excess coal / steam energy sits, by offer band (TWh, keeper P1):**

| year | coal `mustrun` band (unmeasured default) | Merrimack `committed` band | ST_GAS `committed` band | actual coal / ST_GAS |
|---|---:|---:|---:|---|
| 2019 | **1.67** (bare COAL: 568 + 2367) | 0.56 | 0.95 | 0.47 / 0.23 |
| 2020 | **1.05** (568 + 2367) | 0.26 | 0.80 | 0.17 / 0.32 |
| 2021 | **0.45** (568, to 2021-05) | 1.11 | 1.03 | 0.58 / 0.26 |
| 2022 | 0 | **2.07** | 0.19 | 0.35 / 0.21 |
| 2023 | 0 | 0.48 | 0.71 | 0.21 / 0.24 |
| 2024 | 0 | 0.33 | 0.55 | 0.26 / 0.12 |
| 2025 | 0.21 (2367 dead row) | 0.15 | 0.09 | 0.29 / 0.31 |

Three distinct gaps, one common origin: **NEISO's CAMPD-derived artifacts (`bin_assignments_NEISO.csv`,
`thermal_tranches_NEISO.csv`, `neiso_campd_marginal_hr_summary.csv`) were derived on the pre-correction
canonical 2025ER fleet** — coal = one 108 MW Merrimack unit, ST_GAS = Montville 546 alone. The
corrected fleet restores plants those artifacts never saw, and those plants fall through to defaults.

1. **Unmeasured coal must-run (the 2019–2021 bare-COAL energy).** Bridgeport Harbor 568 unit 3 and
   Schiller 2367 have no `(plant, COAL)` row in `thermal_tranches_NEISO.csv` (568's only row is its
   CC). They fall through `_DEFAULT_TRANCHE_PCT_BY_GROUP["COAL"]` = **45 % of nameplate must-run**,
   offered at **$10–14/MWh** (568: 173 MW in 2019, 116 MW in 2020–21; 2367: 43 MW) and held in all
   8,760 h by the coal sync window's `.get(code, 1.0)` default. This is exactly the two-default
   defect `coal_mustrun_requires_measured_row` (pjm-h14, zero DOF) was written for. **Matrix cell:
   NEISO `U`** — on-queue, never tested here.
2. **Merrimack's delivered coal price (the 2021–2022 committed-band energy).** EIA-923 carries **no
   delivered cost for any NEISO coal plant** (`FUEL_COST` redacted for unregulated receipts); the
   EIA API `cost-per-btu` is null for NH, CT, MA **and the New England census division** in every
   year (queried 2026-09-25). The model therefore prices Merrimack at the Tier-3 placeholder
   `COAL_PRICE_BASE["NEISO"] = 3.0` (≈ 2.80–2.94 $/MMBtu in 2019–2024, near-flat), while the
   measured Northern Appalachia bituminous price (EIA ACR, the basin of Merrimack's own receipts)
   rose **57.04 → 86.80 $/ton (+52 %) from 2021 to 2022**. Merrimack's offer ($43.7 / $49.2 in
   2021 / 2022) sits below the CC median in 5 / 11 months. **Not armed in this lane:** the only
   measured series is mine-mouth; a delivered NE price needs a transport leg no public source
   measures, i.e. a new free parameter. Routed as the named successor (§6), never fitted here.
   Secondary: Merrimack's own tranche row is corrupt (CEMS for 438 MW over the 108 MW nameplate →
   `p25_cf = median_cf = 150`, the cap; `committed_pct = 70`, the ceiling) — a rule-23 re-derive on
   the corrected fleet, also routed (§6).
3. **ST_GAS bands identified on Montville alone (the ST_GAS committed-band energy).** The registry's
   0.79 / 0.85 / 0.89 are `marg_{committed,econ_low,econ_high}_p50 × 1.223` from the CAMPD
   marginal-HR derive, whose ST_GAS class is Montville 546 only (n = 2 units). The restored steam
   plants (Middletown 562, Newington 8002, New Haven Harbor 6156, West Springfield 1642) also carry
   no tranche rows and take the ST_GAS default tranche split, but the energy is in the committed
   band, which is priced by the multiplier.

**Work item 3 (bare `COAL` reporting) is already fixed on `main`** by COAL-SUB (#6619, owner
instruction 2026-09-25, ungated): every coal unit resolves its subclass at load, the last link being
its own EIA-860 energy-source code. At HEAD 568 → `COAL_PRB` (`SUB`) and 2367 → `COAL_BIT`. This
lane adds no code for it; a gated duplicate drafted before COAL-SUB was seen was discarded unpushed.

## 2. G-DRIFT (rule 29(b)) — keeper basis `c265c1c3` → HEAD `06d9a9da`

74 solve-path files changed. Audited **mechanically**: `gdrift_fleet_probe.py` rebuilt the keeper
recipe's LP inputs (per-unit pmax, pmin, heat rate, availability, min_gen, `mc_base`, demand, wind,
solar) with the basis code (a worktree at `c265c1c3`) and with HEAD, per year, and diffed them.

| year | unit set | max \|Δ\| over every array | verdict |
|---|---|---|---|
| 2019 | identical (759) | heat rate 1.56, min_gen 27.2 MW, `mc_base` 4.36 — **Bridgeport Harbor 568's nine coal tranches only** | **LIVE** |
| 2020 | identical (780) | heat rate 1.61, min_gen 18.3, `mc_base` 4.54 — 568 only | **LIVE** |
| 2021–2025 | identical | **0 on every array** (only `COAL` → `COAL_*` labels) | INERT |

The LIVE hunk is COAL-SUB giving 568 its `SUB` rank, so the PRB ladder/sigmoid now prices it in
2019/2020 exactly as the partial-exit registry already did in 2021. Remaining LP-side hunks (interchange
spec, reserve spec, commitment) are the COAL-SUB family-token refactor (label-only, confirmed by the
zero diffs above) and MISO-only 2019 seam rows. **Form 4 stands for 2021–2025; 2019 and 2020 earn a
control solve (arm C).**

## 3. Recipes — declared before any solve

Every leg: `scripts/replay_keeper.py results/calibration/rneiso_span --years <Y>` + the deltas below.

| arm | delta on the keeper | DOF | years |
|---|---|---|---|
| **C** control | none (keeper recipe at HEAD) | — | 2019, 2020 |
| **A** structure | `coal_mustrun_requires_measured_row=true` | **zero** (withdraws an unmeasured default) | 2019–2025 |
| **B** structure + ST_GAS bands | A + `--offer-curve-json docs/handoffs/neiso114/arm_b_offer_curve.json` | ST_GAS band magnitudes re-identified (existing ledgered channel, no new parameter) | 2019–2025 |

**Arm B's ST_GAS bands (work item 2) — the existing construction, re-run on the corrected class.**
`phase0_st_gas_marginal_hr.py` applies `derive_campd_marginal_hr.derive_unit_bands` **unchanged** to
the corrected ST_GAS membership (546, 562, 8002, 6156, 1642; 7 CEMS units) pooled over **every
scored year 2019–2025**, each unit normalised by its **own** steady-state average heat rate (the rate
the model multiplies the band into; for the Montville-only sample the two normalisations coincide).
Cap-weighted p50s: committed **0.727**, econ_low **0.872**, econ_high **0.983** (Montville alone over
the same years: 0.768 / 0.864 / 0.940). × NEISO's own CC reach 1.223 → registry values rounded to
the registry's 2 dp: **0.89 / 1.07 / 1.20**; × the keeper's fossil scalar 0.9547 (neiso-106,
unchanged) → effective **0.849683 / 1.021529 / 1.145640**. **Peak** is set equal to econ_high
(1.145640) because the registered full-output bound 1.0 would now sit below econ_high and invert
the ladder; the rule, "peak = max(registered bound, econ_high)", is fixed here before any solve.
Every other class's bands byte-identical. Conditions of rules 1/13's authorized channel: (a) band
multipliers only; (b) ONE config for all seven years; (c) set here, from CEMS, **never swept** —
no alternative value will be solved; (d) merit order moves by intent; (e) declared in the
attestation's `authorized_price_tuning` block and carried in the DOF ledger as a re-identified
magnitude (rule 21). Rule 23 citation: the source data change is the class membership the F1
vintage correction restored, not a residual.

Offer-level effect (census at HEAD, MW-weighted ST_GAS offer heat rate, committed / econ):
2019 12.75/14.04 → 14.36/18.32; 2021 9.12/9.78 → 10.27/12.75; 2023 7.66/7.66 → 8.63/9.99;
2024 9.78/10.92 → 11.01/14.25. Arm A's census: coal must-run 215 / 159 / 116 / 116 / 0 / 0 / 159 MW
→ **0 in every year**; **2023 and 2024 offer arrays are identical to the keeper's** (A is inert there
by construction).

## 4. Gates — declared before any solve (structural; rule 1)

A passing gate does not promote and a failing one does not kill; both are reported at full magnitude.

- **G1 recipe:** `docs/handoffs/neiso114/shard_check.py --arm {A,B,C}` passes on every leg.
- **G2 mechanism fires:** arm A/B legs 2019–2022, 2025 carry no coal `mustrun` band energy for
  568/2367; arm A 2023/2024 class TWh equal the keeper's within solver noise (inert prediction).
- **G3 no silent breakage:** C1, C2, C3a, C3b, C4, C8 re-scored per year against the keeper on one
  benchmark (committed parts held fixed); train tier 2023–2025 must stay CALIBRATED for a
  recommendation to promote. Prediction, stated before the solve: arm A moves C1 2019 and 2021 toward
  the band; **2022 is not expected to move under A** (its excess is Merrimack's committed band, §1.2);
  arm B additionally lifts CC in 2019–2021 and 2023–2024.

## 5. Shard plan

16 shards, launched at once, pinned to this doc's commit SHA (§7): `neiso114{a,b}_<Y>` for 2019–2025
and `neiso114c_<Y>` for 2019, 2020. Branch `claude/neiso114-<arm>-<Y>`. Full bundle pushed incl.
`dispatch/<Y>_P1.parquet` via a `.gitignore` negation + plain `git add` (rule 34(a)). The parent
composes, attests, scores and registers (`--no-prune`); it never solves (rule 32(a)).

## 6. Named successors (not in this lane)

1. **NEISO delivered coal price** — replace the flat Tier-3 3.0 $/MMBtu placeholder with a measured,
   year-varying delivered price. Owner decision needed on the transport leg (no public NE measure).
2. **Re-derive `thermal_tranches_NEISO.csv` on the corrected fleet** (rule 23: membership/nameplate
   changed) — repairs Merrimack's 150-CF row and gives the restored ST_GAS plants measured tranches.
3. **ST_GAS committed band on its physical basis** (`avg_committed_p50`, as CC_REGULAR's is) —
   `committed_band_measured_basis`, NEISO `U`.
4. GenConn Middletown 57068 / Mystic 7 on the class heat-rate table (no measured-oil channel) —
   report only, unchanged.

## 7. Launch record

All 16 pinned to **`9db30b45a55bf4bbd9cdbc3b2a7f51aa37dc7466`** (this doc's first commit), created
2026-09-25 04:19–04:23 UTC, tag `neiso114`. Branch `claude/neiso114-<arm>-<Y>`, out-dir `neiso114<arm>_<Y>`.

| leg | shard session | leg | shard session |
|---|---|---|---|
| A-2019 | `session_01V4VVsR423YDt9zXd1gLmXe` | B-2019 | `session_01KKWU9855UR7ueshT1bj7BN` |
| A-2020 | `session_01Wm2xhokRKUdhmsuXySBNjh` | B-2020 | `session_01KBDBsm7xsEMmL1LxAeSdXS` |
| A-2021 | `session_017EujoMRErRS5Cd3YQV2bpY` | B-2021 | `session_01GUV7wG7dNUZ7VW6jWKqUx9` |
| A-2022 | `session_01MiWgDvtytiG9hkwxxxVPpG` | B-2022 | `session_01Ktgf6vbkJMKzoNVQ1ZKTSo` |
| A-2023 | `session_018xZ8oPXmqzgkq45vpxpV7B` | B-2023 | `session_018jWeArftj6oKV5LPA9u4SF` |
| A-2024 | `session_01VizsRtHqC6kNU1jco9BugP` | B-2024 | `session_01SSDkXdZZqacMzsEne2SyMx` |
| A-2025 | `session_01XuGGPSfY13tV1tqUgFyWur` | B-2025 | `session_012G29DWufYACVYxDfWoSGMM` |
| C-2019 | `session_01AhXeVx6nkdYkYiQsNUn6Dg` | C-2020 | `session_01SfuGFdftrXhcWiPH31ewWk` |
