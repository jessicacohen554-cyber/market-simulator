# PRECOMMIT — SPP-99: SPP's CEMS-derived solve inputs under the SPP-98 remap, through miso-280's split-remap companions

**Lane** SPP-99 (the named successor in `RESULT-spp-98-cems-eia-remap-2026-09-28.md` §3) · control = keeper
`2026-09-28-spp-98-cems-remap` (`spp98_remap_span`, rule 29(b) form 4, no control solve) · owner decision card
**"Extend miso-280 (Rec.)"**, 2026-09-28 · written **before any shard launches**. Everything below is zero LP.

**Trigger (rule 23).** The attribution change: SPP-98 added ten EPA CAMD–EIA crosswalk rows to
`campd.CAMPD_UNIT_PLANT_REMAP`, and every committed SPP CEMS artifact was derived before they existed. A residual is not
a trigger.

## 1. Which artifacts the remap reaches (per-artifact census)

**Method.**
- Each artifact the keeper reads was re-derived into scratch by its committed deriver, at **its own recorded
  invocation** (the `.meta.json` `derive_invocation`, or the `years` column for heat-rate CSVs).
- Each re-derive was diffed row by row against the committed file.
- The remap facility codes are {1416, 56565, 3006, 55655, 762, 7546, 63628, 2953}.

| artifact (keeper reads it?) | remap-plant rows | non-remap rows at HEAD | carried by |
|---|---|---|---|
| `campd-unit-outages-netloadmask-SPP.csv` (yes: std ≥5-day layer) | **move** (6,581 → 6,472) | 5,989 / 5,989 byte-identical | `-netloadmask-splitremap-` |
| `campd-unit-outages-SPP.csv` (not by the solve; it is the tranches' outage-derated **denominator**) | **move** | — | `-splitremap-` |
| `campd_cc_heat_rates_SPP.csv` (yes, `measured_cc_heat_rates`) | **move**: +Ponca City 7546 rows; Stall 56565 **refused** (`steam_not_metered`, gross/net 0.63–0.67) → stays eGRID | drift: 50558 `eia923_identity`, +1 column | `-splitremap-` (splice) |
| `thermal_tranches_SPP.csv` (yes) | **move**: 1416, 3006, 2953 re-derived; +7546, +56565 | drift: **all 23 COAL rows dropped** by the HEAD plain path (§5), +1 column | `-splitremap-` (splice) |
| short / partial netloadmask extracts (yes) | **none**: re-derive is sha-identical (`5c016785…`, `3792217d…`) | — | incumbent |
| CT / ST / coal heat rates (yes) | **none**: 2953 / 3006 / 63628 / 1416 rows identical | drift elsewhere | incumbent |
| e923 / layup outage companions, gas / CT commitment params, CT run lengths | **not read** by the keeper (bridge, fuel split, measured runs, lay-up masks all off) | — | — |

## 2. Design: extend miso-280's mechanism; no new flag (rule 19)

miso-280 landed `ScenarioConfig.campd_split_remap_companions` for this exact phenomenon (a split-plant remap reaching
the solve only through re-derived artifacts). SPP-99 reuses it and adds no field.

- **Selector widened.** `campd_fuel_split_selector` used to **raise** when armed without `campd_unit_fuel_split`.
  - It now returns `PLAIN_SPLIT_REMAP_TAG`, and `_fuel_split_companion` resolves that tag to the plain artifact's own
    `-splitremap-` companion.
  - It still raises if that companion is absent, and it still raises under `campd_per_unit_attribution`.
  - MISO's fuel-split path is untouched.
  - `resolved_inputs` skips the fuel-split companion block for the plain tag.
- **Companions: plant-scoped splices**, by miso-280's builder `scripts/data/build_campd_split_remap_companions.py`.
  - Each is the incumbent's exact bytes with only the remap plants' lines replaced by the same deriver's lines at HEAD.
    Every other line is byte-identical, so the HEAD drift in §1 never enters.
  - Three families are added to the builder, all outside its default (MISO) set:

| family | deriver invocation |
|---|---|
| `stdmask` | the recorded invocation |
| `stdbase` | `--no-inmerit-filter`, which reproduces the pre-SPP-85 mask-`None` state |
| `tranches` | `derive_thermal_tranches.py --split-remap-denominator` (new: the plain path's derate from the `stdbase` companion, so numerator and denominator carry one identity) over the incumbent's recorded years 2023–2025 |

- **Splice CONTROL (`scripts/probes/_spp99_splice_control.py`).** Each deriver is run with the SPP rows **stripped**
  in-process and spliced the same way. All four reproduce their incumbent **byte-for-byte**:
  `05aced4f` / `43161365` / `bed19b45` / `fdeadb1a`, **PASS**.
- **Committed companions.**

| companion | sha256 |
|---|---|
| `campd-unit-outages-netloadmask-splitremap-SPP.csv` | `41ee31e0…` (= the full re-derive, byte-for-byte) |
| `campd-unit-outages-splitremap-SPP.csv` | `8cd6dbd9…` |
| `campd_cc_heat_rates-splitremap-SPP.csv` | `c144ddd7…` |
| `thermal_tranches-splitremap-SPP.csv` | `92ed67de…` (+ sidecar) |

## 3. Fleet delta, zero LP (`scripts/probes/_spp99_fleet_delta.py --arm F`, the real flag, all 7 years)

Every moved row is at a remap plant in every year (`outside_remap = []`). The control fleet is byte-identical between
keeper HEAD `ed8cec3f` and this HEAD in all 7 years.

| year | Δ available TWh | Stall 56565 avail | Ponca City 7546 CC avail / HR | Arsenal Hill 1416 ST_GAS avail / floor GWh | other |
|---|---|---|---|---|---|
| 2019 | −1.076 | 0.913 → 0.689 | → 0.323 / 6.975 → 7.99 | 0.155 → 0.196 / −58 | Ponca 762 ST_GAS 0.136 → 0.813 |
| 2020 | −0.786 | → 0.830 | → 0.151 / → 8.36 | 0.069 → 0.071 / −26 | |
| 2021 | −1.098 | → 0.762 | → 0.130 / → 8.28 | 0.118 → 0.126 / −43 | |
| 2022 | −0.798 | → 0.758 | → 0.250 / → 7.89 | 0.269 → 0.318 / −110 | Ponca 762 0.096 → 0.813 |
| 2023 | −0.808 | → 0.818 | → 0.147 / → 7.80 | 0.300 → 0.340 / −130 | |
| 2024 | −0.917 | → 0.788 | → 0.078 / → 8.26 | 0.221 → 0.323 / −89 | |
| 2025 | −0.753 | → 0.823 | → 0.194 / → 8.02 | 0.219 → 0.263 / −99 | |

**What each move means:**
- **Stall.** It had the generic 0.913 while its CT windows were booked to Arsenal Hill; it now carries them (each
  removes about half the block). Its new tranche row re-partitions ≤ 2 MW of pmax among its tranche rows.
- **Stall's tranche row is a disclosed limit.** It comes from CT-only CEMS over the 511 MW nameplate (committed
  42.7 %), so it understates the plant's true minimum-stable fraction (~55 % estimated). It replaces a class default
  of ~34 %; rule 14's misalignment is disclosed, not repaired.
- **Arsenal Hill.** The 150 %-CF row is gone: median CF 37 %, ST_GAS floor down.
- **Ponca City 7546.** CEMS unit 3 is the whole CC block (EIA gens 1 + 3, 73.8 MW), dark most of the year.

## 4. G-DRIFT, keeper `ed8cec3f` → HEAD (rule 29(b)) — every hunk INERT for SPP

| hunk | reason |
|---|---|
| `caiso_tac_shares_standard_time` (scenarios, eia930 demand / zonal shares, both runners) | CAISO-only, default off; the new argument is keyword-only |
| `pjm_da_virtual_settle_financial`, `virtual_bids.py`, `pipeline/solve.py` | default off |
| miso-280: `campd.py` 55641 remap rows | MISO facilities, in no SPP membership |
| miso-280: `split_remap` threading (outages / arrays / campd_bins / resolved_inputs / eia860 / assembly / runner / run_calibration) | default off; `measured_cc_heat_rate_selector` returns the same bool unarmed |
| R-ERCOT-12: `ISO_PLANT_ENTRIES`, `ba_membership.py`, `run_calibration_full` entry split | ERCOT-only |
| soco-84: `soco_energy_auction.py`, `paths.py`, `_validation-source/*SOCO*` | SOCO-only |
| `scripts/lib/seam_neighbour_price/*` | not on the solve path |
| **this lane** (the selector widening, builder families, `--split-remap-denominator`, SPP companions) | the arm's single delta: `campd_split_remap_companions = true` |

Corroboration: the control fleets are byte-identical across the two HEADs (§3).

## 5. Findings reported, not repaired here

1. **`derive_thermal_tranches.py` main path drops every COAL row at HEAD** (all ISOs). `_THERMAL_GROUPS` still holds
   bare `"COAL"`, but since the coal-subclass change (2026-09-25) generators carry `COAL_PRB` / `COAL_BIT` / ….
   - It is silent: the output has fewer rows and no error.
   - It blocks any wholesale plain-tranches re-derive; the splice avoids it.
   - Successor: an all-ISO fix.
2. **WFEC 55655 and Tinker 63628 rows vs the model fleet** (item d):
   - **WFEC.** EIA-860 vintages 2019–2024 list 55655 GEN1 / GEN2 (45 MW each); the 2025 Early Release consolidates
     them into Anadarko 3006. The SPP fleet follows that snapshot in every year (3006 CT_PEAKER = 225 MW; **no
     55655**). So the (3006, 7/8) → 55655 rows move CEMS off the plant that holds the capacity. The bench's npl = 1 MW is
     55655's absence from that snapshot, **not a missing nameplate**; nothing is fixed.
   - **Tinker.** 5A / 5B are Tinker's in every vintage, while the crosswalk maps them to a Mustang "5A / 5B" that the
     2017 GT1–7 rebuild retired.
   - **Solve reach of both: nil.** CT peakers carry no outage overlay; the CT heat-rate rows and Mustang's tranche row
     are unchanged. They are benchmark-domain rows (SPP-98's), reported to the owner.

## 6. Expectations, fixed now

| # | expectation |
|---|---|
| E1 | Every leg's shard check PASSes: recipe = keeper + exactly `campd_split_remap_companions = true`; resolved outage `41ee31e0…`; resolved tranches `92ed67de…` |
| E2 | Each year's \|Δ CC_REGULAR TWh\| ≤ 1.1; \|Δ ST_GAS TWh\| ≤ 0.15 |
| E3 | \|Δ demand-weighted price\| < $1/MWh in every year |
| E4 | No C1 / C3a / C3b / C4 row flips status in either tier. This is a **prediction, not a criterion**: the effect is ≤ 1.1 TWh against open C1 misses of 9–13.5 TWh |

## 7. Recommendation rule, fixed now

**RECOMMEND PROMOTE** iff:
- E1 holds on all seven legs;
- the composite registers and scores.

This is a rule-14 / rule-23 attribution repair of measured inputs, through the existing mechanism, with zero DOF. The
scored effect is reported at full magnitude and is **not** a criterion (rule 1). A train-tier downgrade would be a
discovered root-cause item, never a revert (rule 14); the owner decides. If E1 fails on any leg, **STOP**; that leg's
report is the record.

## 8. Shard plan (rules 32 / 34 / 36)

- **Shape.** Seven shards, one per year 2019–2025, pinned to this PRECOMMIT's merge SHA.
- **Solve.** Each runs `replay_keeper.py results/calibration/spp98_remap_span --years <Y> --set
  campd_split_remap_companions=true --out-dir results/calibration/spp99_arm_<Y>`.
- **Check and push.** Then `scripts/probes/_spp99_shard_check.py`, and push of the FULL bundle (including
  `dispatch/<Y>_P1.parquet`) to `claude/spp99-<Y>` through a `.gitignore` negation and a plain `git add`.
- **Template.** `docs/handoffs/spp99/shard_prompt_template.txt`.
- **Compose.** `_rspp_compose.py --side arm --require unit_outage_netload_mask_repair=true --require
  unit_outage_coal_extract_basis_share=true --require campd_split_remap_companions=true`.
