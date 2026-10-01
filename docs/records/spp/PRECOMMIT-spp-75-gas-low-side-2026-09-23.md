# PRECOMMIT — SPP-75: the gas half of the low side (who runs gas when SPP RT < 0, and why)

**Zero LP. Pushed before any attribution number below is read.** Base `efb7ec3d`.
Predecessor: `RESULT-spp-74-price-body-2026-09-23.md` §3a (gas deficit in RT<0 hours:
2020 model 2.33 vs EIA-930 NG 4.08 GW = **1.75 GW**; 2022 0.56 vs 3.01 = **2.45 GW**).
Probe: `scripts/probes/_spp75_gas_low_side.py`. Output: `results/calibration/_spp75_*.json`.

## 0. Hypothesis

The gas that runs in RT<0 hours is price-insensitive for an external reason the model does not
carry: CHP steam hosts / industrial must-run (i), rather than economic commitment of utility
CC/ST (ii) or fleet membership/zoning (iii).

## 1. Instruments (fixed now)

- **Hour set** `H_neg`: measured RT ≤ 0 on the model clock (`_spp74.hour_types` "NEG"), rung
  `hydro5_spp_floor_rung`, years **2020 and 2022** (the two years SPP-74 split); 2019/2021
  reported, not decided on.
- **Gap** `G_y` = mean over `H_neg` of EIA-930 SWPP NG − model gas classes (CC_*, CT_*, ST_*).
  Must reproduce 1.75 / 2.45 GW within 0.01.
- **Measured attribution**: CAMPD unit-level gross load, SWPP-BA plants (EIA-860 BA code, facilityId
  cast to int), gas units by `_spp73.classify`. Coverage κ = CAMPD gas MW / EIA-930 NG MW in
  `H_neg` (gross vs net and <25 MW units make κ ≠ 1; reported, not corrected).
- **Unit tags** (EIA-860 generator/plant, the run-year vintage the loader offers):
  CHP = any generator at the plant with `Associated with Combined Heat and Power System` = Y,
  or plant `FERC Cogeneration Status` = Y; sector = plant `Sector Name`; prime mover set.
- **Model side**: `class_hourly` P1 MW in `H_neg` per class; plant membership / class / zone from a
  `fleet_only` rebuild (`reconstruct_bundle_fleet`, one interpreter per year).
- **Price-insensitivity** of a measured group: ratio of its mean MW in `H_neg` to its mean MW in
  MID2 hours (flat ≥ 0.8).

## 2. The attribution (decision rule)

Each object's share of `G_y` is **measured MW in `H_neg` − the model's MW for the matching
class(es) in `H_neg`**, divided by `G_y`, with CAMPD scaled by 1/κ as a sensitivity only:

- (i) CHP/industrial: CAMPD CHP-tagged + industrial/commercial-sector units vs model
  CC_CHP + CT_CHP + ST_CHP. **Independent bound**: EIA-923 SWPP-BA gas CHP=Y annual net gen
  ÷ 8760 − model CHP classes' annual mean MW (a perfectly-flat CHP fleet's maximum reach).
- (ii) utility/IPP non-CHP CC + ST_GAS: CAMPD vs model CC_REGULAR + ST_GAS; plus the share of that
  group's `H_neg` MW on units at ≤ 1.2 × EIA-860 `Minimum Load (MW)` (min-load signature).
- (iii) CAMPD units whose plant is absent from the rebuilt fleet, or present under a non-gas
  class: their `H_neg` MW.
- CT (non-CHP) reported as its own line.

An object "explains" the gap if its share ≥ 50 % in **both** 2020 and 2022.

## 3. Admissibility gate (unchanged from the charter)

(i) or (iii) earns a lever only with a measured, forward-reproducible input (EIA-923 useful
thermal output / host-load profile, or an EIA-860 membership fix) and a zero-DOF construction.
(ii) is the SPP-44 / SPP-66 object and is **dead unless** the measurement shows something those
lanes lacked (they had no unit-level attribution in RT<0 hours). If nothing admits, the gas half
is routed, not built, and **no shard is launched**.

## 4. Predictions (scored in the RESULT)

| # | prediction |
|---|---|
| P1 | `G` reproduces 1.75 / 2.45 GW |
| P2 | κ in `H_neg` between 0.8 and 1.1 |
| P3 | (i) share < 50 % in both years; the EIA-923 flat bound < 0.6 GW |
| P4 | (ii) share ≥ 50 % in both years, and most of it at or near min load |
| P5 | (iii) share < 15 % |
| P6 | measured CHP group is flat (ratio ≥ 0.8); measured non-CHP CC/ST is not (< 0.8) |
| P7 | verdict: no admissible lever; gas half routed to the commitment family |

Expected direction if a lever did exist: raises supply in low hours → C3a 2020 down; C1/C2 2022
must be checked. Not solved unless §3 admits.

---

## 5. ADDENDUM — the CHP arm, chartered by the owner (2026-09-24, verbatim: "Yes charter the CHP fix")

Written after the zero-LP RESULT (`RESULT-spp-75-gas-low-side-2026-09-23.md`) and **before any
shard is launched**. The owner overrode the 50 % bar of §2; the arm is chartered on structure
(rule 1), not on reach.

**Single delta.** `chp_steam_floor_p25: false → true`, the existing registered level source on the
one `MECH_CHP_STEAM` floor (rule 19). No new field, no code change, zero new DOF (rule 21:
`steam_level_cf` is a committed column of `thermal_tranches_SPP.csv`).

**Shards (rules 32/34/36).** Seven, one per year 2019–2025, pinned to one 40-char SHA. Each shard
solves **its own control and arm** in its own container (no reliance on form 4):

```
python scripts/replay_keeper.py results/calibration/<K> --years <Y> \
  --out-dir results/calibration/spp75_ctl_<Y> --note "SPP-75 control, <Y>"
python scripts/replay_keeper.py results/calibration/<K> --years <Y> --set chp_steam_floor_p25=true \
  --out-dir results/calibration/spp75_chp_<Y> --note "SPP-75 arm: chp_steam_floor_p25, <Y>"
python scripts/probes/_spp75_shard_check.py --year <Y> --keeper results/calibration/<K> \
  --control results/calibration/spp75_ctl_<Y> --arm results/calibration/spp75_chp_<Y>
```

`<K>` = `hydro5_spp_floor_rung` for 2019–2022, `hydro5_spp_floor_span` for 2023–2025 (the two
recipes differ; each year replays its own). The check must pass (control = keeper recipe;
arm = control + exactly the one flag) before a push. Both bundles, including
`dispatch/<Y>_P1.parquet`, are pushed to the shard's own branch by `.gitignore` negation and a plain
`git add`.

**Predictions (arm − control), every year unless stated.**

| # | quantity | prediction |
|---|---|---|
| Q1 | CHP classes, annual | +1.0 to +2.2 TWh (floor +245 MW, less the CHP output already above the old floor) |
| Q2 | CHP MW in measured RT≤0 hours | +180 to +250 MW (2020 control ≈ 158 → arm ≈ 380) |
| Q3 | wind MW in RT≤0 hours | falls, by 60–100 % of Q2 (wind is marginal there) |
| Q4 | demand-weighted mean price | falls, by less than $0.30/MWh |
| Q5 | C3a 2020 | moves down by < 1 pp and **stays FAIL** |
| Q6 | status flips | no C1/C2/C3a/C3b row changes status in 2023–2025; C2 gas 2022 direction not predicted |
| Q7 | control reproduces its keeper | max \|Δ class TWh\| < 0.05 (both warm-start knobs default off since rule 36; a larger number is reported, not hidden) |

**Structural gate (K-1, over-forcing; decides the recommendation, not the residual).** The arm's
CHP output must not exceed what was measured:
- CHP MW in RT≤0 hours ≤ the measured CHP group's (CAMPD gross): 437 / 453 / 431 / 424 MW for 2019–2022;
- annual mean CHP MW ≤ EIA-923 SWPP gas CHP=Y: 522 / 551 / 520 / 538 / 595 / 615 MW for 2019–2024
  (2025's EIA-923 vintage is partial, 361 rows, so 2025 is reported, not gated).

Pass in every gated year → recommend promotion on structure. Any exceedance → recommend against,
and report the plant. The owner decides either way (rule 31).

### 5.1 Launch record (appended after the shards were created, 2026-09-24)

All seven pinned to `79dcc45ad97c8d6bdb7e4f2da3df72a31398a9f5` (the commit carrying §5 and the
self-check), tagged `spp-75`; branches `claude/spp75-chp-<Y>`.

| year | keeper bundle | shard session |
|---|---|---|
| 2019 | hydro5_spp_floor_rung | `session_01HgmHmpwH1Fzun3xWpe3opR` |
| 2020 | hydro5_spp_floor_rung | `session_01G3QQBFU9dWanVq6eNLhJgR` |
| 2021 | hydro5_spp_floor_rung | `session_01UppPYC7RLhFAAp3aZgLGC6` |
| 2022 | hydro5_spp_floor_rung | `session_016tZ96GEp5Z21xHxNrn73zD` |
| 2023 | hydro5_spp_floor_span | `session_011YqJTzVJK9CbGeA7AqhuE9` |
| 2024 | hydro5_spp_floor_span | `session_01Y8oeetJFd8dvqrUhbEjYAG` |
| 2025 | hydro5_spp_floor_span | `session_01WFiErjX8ZN3xu1TAFTeuES` |
