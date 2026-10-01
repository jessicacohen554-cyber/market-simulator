# FINDING — soco-68: SOCO's CC gap is mostly an AVAILABILITY double count, not a capability basis

Lane soco-68, 2026-09-25. **Zero LP.** The handoff routed "the CC capability basis" (soco-67 RESULT §5.1): measured
CC net output exceeds the keeper's CC_REGULAR availability by 6.76 TWh (2023) / 7.67 TWh (2024) at plant grain. The
per-plant decomposition says the pmax basis is the **small** part. The large part is the flat summer class derate
stacked on a capacity already carried at its published net-summer rating, which is the miso-141 double count.

Every number here is reproduced by one of these probes (all zero LP, all on the keeper's own recipe):

- `scripts/probes/_soco68_gdrift_identity.py`: G-DRIFT. It is soco-67's probe re-pointed at `soco67_span`, and
  it now **hashes labels too**.
- `scripts/probes/_soco68_cc_capability.py`: per-plant decomposition, plus control/arm fleet rebuilds with `--set`.
- `scripts/probes/_soco68_basis_census.py`: the SOCO measurement of the miso-141 basis question.
- `scripts/probes/_soco68_greedy.py`: the greedy restack on the keeper's committed class-band hourlies.

## 0. G-DRIFT (rule 29(b)): all INERT, and the keeper is the control

The keeper legs were solved at `b2397ae03b2ab60528cfcb639cb03ae01ea19835`, which is not an ancestor of `main` (the
soco-67 lane was rebased). `main` @ `79c642bb` changes these solve-path files relative to it:

- miso-272 `cc_block_summer_rating`: default off, not in the recipe.
- R-ERCOT-4 `ercot_partial_outage_day_guard`: ERCOT-only, default off.
- NWPP-NEXT-2 `EIA930_REMOTE_GENERATION_DOUBLE_BOOKED` and `_mask_unbalanced_demand`: PSEI / pool members only.
- SPP validation-source parquets and NWPP `calibration_reference.json` rows.

**Measured, not argued.** `_soco68_gdrift_identity.py` rebuilds every keeper year at both shas on one shared data
tree. It hashes `unit_ids`, `mc_base`, `pmax`, `pmin`, `min_gen`, `availability`, `heat_rate`, `emission_rate`,
`vom`, demand, **and now `plant_group`, `fuel_type_idx`, `zone_idx`, `plant_code` and `nox_rate`**. soco-67 missed
the COAL-SUB relabel because it did not hash labels.

**Verdict: ALL LP INPUTS BIT-IDENTICAL in all seven years 2019–2025.** Three things differ between the shas, and
none of them reaches SOCO:

- Two `ScenarioConfig` fields were added (`cc_block_summer_rating`, `ercot_partial_outage_day_guard`). Both
  default off and neither is in the recipe.
- The constants that moved (`CAMPD_BINNING_ISOS`, `EIA930_PS_FOLDED_INTO_WAT`, `RGGI_MEMBER_STATES_BY_YEAR`, plus
  the added `EIA930_REMOTE_GENERATION_DOUBLE_BOOKED`) land identically for SOCO.
- The five path defaults differ only because the worktree has different absolute paths.

The committed `soco67_span` bundle is therefore the control, and no control solve is spent.

## 1. Where the plant-grain excess sits

The decomposition splits the excess per plant and per hour:

- **(a) basis:** `max(0, CEMS_net − pmax)`
- **(b) availability:** `max(0, min(CEMS_net, pmax) − avail)`

CEMS net is facility combined-cycle units × 0.97. The excess by year, in TWh:

| year | (a) CEMS above LP pmax | (b) CEMS ≤ pmax but above availability | total |
|---|---|---|---|
| 2019 | 0.227 | 5.452 | 5.679 |
| 2020 | 0.559 | 5.782 | 6.341 |
| 2021 | 0.576 | 6.832 | 7.409 |
| 2022 | 0.596 | 8.359 | 8.955 |
| 2023 | 0.583 | **6.181** | 6.764 |
| 2024 | 0.607 | **6.183** | 6.790 |
| 2025 | 0.636 | 5.962 | 6.598 |

The 2023 total reproduces soco-67's 6.76 TWh. Its 2024 figure of 7.67 was measured on the pre-clip fleet.

**The capability-basis channel is ~0.2–0.6 TWh a year and is spread thin.** The largest single plant is T.A.
Smith 55382, at 0.31 TWh in 2023. **About 90 % of the gap is availability.**

**2023 per plant** (`_soco68_cc_capability.py`):

| plant | LP pmax MW | 860 summer MW | 860 nameplate MW | CEMS p95 MW | (a) | (b) |
|---|---|---|---|---|---|---|
| McDonough 710 | 2,471.0 | 2,471.0 | 2,764.8 | 2,511 | 0.06 | 1.15 |
| T.A. Smith 55382 | 1,192.0 (guard: 1,344 → nameplate) | 1,344.0 | 1,192.0 | 1,318 | 0.31 | 0.49 |
| E B Harris 7897 | 1,304.0 (guard) | 1,314.8 | 1,304.0 | 1,277 | 0.01 | 0.65 |
| H A Franklin 7710 | 1,901.8 | 1,901.8 | 1,995.7 | 1,932 | 0.03 | 0.52 |
| Daniel 6073 | 1,132.4 (guard: 1,883.4 → nameplate) | 1,122.0 | 1,132.4 | 1,145 | 0.01 | 0.47 |
| McIntosh CC 56150 | 1,315.6 | 1,315.6 | 1,376.6 | 1,319 | 0.01 | 0.39 |
| Wansley CC 55965 | 1,184.8 | 1,184.8 | 1,239.0 | 1,201 | 0.02 | 0.38 |
| Chattahoochee 7917 | 466.0 | 466.0 | 539.7 | 511 | 0.11 | 0.25 |

McDonough's pmax **is** its 860 net-summer rating (2,471), and its p95 is 2,511. The handoff's "pmax 2,335" was a
summer-derated availability ceiling, not the pmax.

## 2. What the availability channel is made of

At a CC plant with no outage window, the hourly CC availability is:

- **0.945** in Jan–Feb and December (`1 − WEFOR`);
- **0.873 = 0.970 × 0.900** in Jun–Sep.

That summer factor is the flat `SUMMER_CLASS_DERATE` (CC 10 %, CT 12.5 %, `fuel_trajectories.py`) applied on top
of the seasonal WEFOR. It is visible as a flat step in every summer hour of McDonough, Franklin, Wansley and T.A.
Smith. The spring and fall dips are the measured CAMPD outage windows. The keeper has `temp_dependent_derate=False`,
so the flat step is not replaced by a temperature curve.

**The basis census** (`_soco68_basis_census.py`, SOCO's own fleet against the solve-year EIA-860 vintage) is the
miso-141 measurement:

| year | CC on net-summer basis | CC 860 nameplate→summer gap | CT on net-summer basis | CT gap | CC-only plants: summer plant-hours above `pmax × 0.9` |
|---|---|---|---|---|---|
| 2019 | 64.8 % | 6.56 % | 99.9 % | 15.54 % | 15,333 h / 0.686 TWh |
| 2020 | 64.8 % | 6.52 % | 99.9 % | 15.61 % | 17,106 h / 1.014 TWh |
| 2021 | 62.4 % | 4.99 % | 93.7 % | 13.84 % | 12,620 h / 0.815 TWh |
| 2022 | 62.4 % | 4.88 % | 93.3 % | 13.49 % | 17,376 h / 0.999 TWh |
| 2023 | 72.6 % | 5.66 % | 93.0 % | 14.10 % | 14,912 h / 1.031 TWh |
| 2024 | 76.1 % | 5.36 % | 94.0 % | 14.47 % | 13,560 h / 1.064 TWh |
| 2025 | 76.0 % | 5.44 % | 93.9 % | 14.56 % | 14,339 h / 1.177 TWh |

**How the fleet is carried.** CT_PEAKER pmax is on the published net-summer basis for 93–100 % of capacity. CC is
on it for 62–76 %. The rest of CC is the plants the always-on CC nameplate guard clipped onto nameplate. SOCO has no
`cc_capacity_reconcile_SOCO.csv`, so the guard's "trusted bound" is plain nameplate.

**What the derate does on that basis.** The net-summer rating already embeds the nameplate→summer ambient loss.
Applying the flat 10 % / 12.5 % again removes that loss a second time. The CEMS column confirms it: CC-only plants
measurably produce **above** the doubly-derated summer ceiling in 12,600–17,400 plant-hours a year.

**This is exactly the defect `summer_derate_basis_aware` repairs** (miso-148, MISO cell `K`). Under the flag, the
flat derate is suppressed for plants the loader carries on a measured net-summer basis. It is **kept** for plants
the CC guard clipped onto nameplate and for plants absent from EIA-860. It is class-agnostic (CC_REGULAR, CC_CHP,
CT_PEAKER, CT_CHP), has zero free parameters, and is a boolean over a data predicate.

## 3. Census of the arm (zero LP, both arms rebuilt all seven years)

Arming `summer_derate_basis_aware=true` on the keeper recipe moves **only `availability`**. `pmax` and `mc` are
byte-identical in every year, and so is every unit id.

| year | units moved | ΔCC_REGULAR | ΔCT_PEAKER | ΔCC_CHP | ΔCT_CHP | plant-grain CC excess, ctl → arm |
|---|---|---|---|---|---|---|
| 2019 | 171 | +2.992 | +3.205 | +0.086 | +0.052 | 5.679 → 4.383 |
| 2020 | 169 | +2.878 | +3.202 | +0.082 | +0.052 | 6.341 → 4.924 |
| 2021 | 171 | +2.927 | +3.262 | +0.084 | +0.052 | 7.409 → 6.326 |
| 2022 | 167 | +2.902 | +3.323 | +0.117 | +0.052 | 8.955 → 7.674 |
| 2023 | 168 | +3.246 | +3.381 | +0.088 | +0.052 | 6.764 → 5.350 |
| 2024 | 172 | +3.558 | +3.302 | +0.083 | +0.052 | 6.790 → 5.210 |
| 2025 | 167 | +3.398 | +3.297 | +0.088 | +0.052 | 6.598 → 5.170 |

Deltas are in TWh of class availability and fall in Jun–Sep only. The mechanism's own log line:
`SUPPRESSED for 168–174 of 185–197 flat-derate units; KEPT for 13–23 unit(s) across 4–7 plant(s)`. The kept set is
always {6073 Daniel, 7897 Harris, 55382 T.A. Smith, 57037 Ratcliffe}, plus 3 / 533 / 643 / 54730 / 54880 in some
vintages.

**The greedy restack** (`_soco68_greedy.py`) runs on the keeper's committed hourlies. It uses only hours where
CC_REGULAR sits at its control ceiling, displaces non-committed bands priced above CC (highest mc first), and does
not restack CT. Deltas in TWh:

| year | CC_REGULAR | CT_PEAKER | COAL_PRB | COAL_BIT | other |
|---|---|---|---|---|---|
| 2019 | +1.94 | −1.40 | −0.42 | −0.11 | |
| 2020 | +1.63 | −1.09 | −0.52 | −0.01 | |
| 2021 | +1.41 | −0.84 | −0.10 | −0.47 | |
| 2022 | +1.65 | −1.50 | | −0.11 | ST_GAS −0.03 |
| 2023 | +2.03 | −1.24 | −0.77 | | |
| 2024 | +2.03 | −1.04 | −0.68 | −0.29 | |
| 2025 | +2.06 | −1.40 | −0.38 | −0.28 | |

**CT gains are inert for dispatch.** CT_PEAKER sits at its own ceiling in only 0–3 h a year.

## 4. What this does and does not explain

**It repairs** the dominant, SOCO-wide channel: about 1.3–1.6 TWh of plant-grain CC excess a year. **It leaves**:

1. **The guard-clipped plants' basis.** T.A. Smith, Daniel and Harris keep both the nameplate clip and the flat
   derate, because SOCO has no demonstrated-peak table. That is `cc_capacity_reconcile_path` (U). The residual is
   (a) ≈ 0.3 TWh plus their (b) share. It is **routed, not stacked** (rule 19): a SOCO reconcile table would also
   move the always-on guard, so it is a separate lever with its own census.
2. **The spring and fall outage windows and the WEFOR base.** These are the rest of channel (b), about 4.5 TWh a
   year. They were not decomposed further in this lane.
3. **`campd-unit-outages-shortgas-SOCO.csv` Barry boiler routing** (≤ 0.06 TWh/yr), **CT daily cycling** (SOCO-65
   §4 owner question) and **ST_GAS under-dispatch**. All three are unchanged and still routed.
