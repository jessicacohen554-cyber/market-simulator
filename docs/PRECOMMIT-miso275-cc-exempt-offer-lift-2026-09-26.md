# PRECOMMIT — miso-275: CC_REGULAR / CC_INTERMEDIATE exempted from the ×1.10 non-steam offer lift (owner-authorized price-tuning channel)

```
LANE    : miso-275 (MISO lever queue §5.4; routed by FINDING-miso274 §5/§6 candidate 3)
KEEPER  : 2026-09-25-miso-273-screened-coal (results/calibration/miso273_span, 2019-2025), legs solved at 09b152c5
ARM     : keeper recipe + ONE field: offer_curve_by_group replaced by the full table
          docs/miso275-arm-offer-curve-by-group.json (sorted-JSON sha256 prefix 7ca9dd66e70c6d50;
          keeper table d80c035df880310b). Eight cells move, all in CC_REGULAR / CC_INTERMEDIATE (§2)
CONTROL : none solved. G-DRIFT 09b152c5..this SHA is all INERT for MISO (§3), so the keeper bundle IS the control (rule 29(b) form 4)
SHARDS  : 7 arm legs, one year each 2019-2025 (rules 34(c), 36), pinned to this document's commit SHA
DATA    : DATA PROFILE: miso
DOF     : ±0 new parameters. The existing ledger entry "offer_curve_by_group non-steam fossil lift (1.10)" narrows
          its class scope from 11 to 9 classes; CC_REGULAR / CC_INTERMEDIATE return to the pre-miso-220 table values
```

## 1. The owner ruling (rule 1 `[R-STRUCT]` carve-out, rule 13 exception)

Asked 2026-09-26 in this session, with the FINDING-miso274 §5 evidence. The evidence: the CC_REGULAR shortfall
(−13.69 / −10.47 / −8.85 TWh in 2021 / 22 / 23) is a merit object. CC has 32–53 TWh/yr of headroom, all of it in
hours when coal runs above its committed band. The LP's CC econ offer sits ~×1.12 above the measured
7.13–7.29 MMBtu/MWh heat rate, and part of that uplift is the keeper's own ×1.10 non-steam lift (miso-220).

**Owner answer (verbatim option selected): "Exempt CC from ×1.10 (Recommended)"**, described in the question as:
*"Treat CC_REGULAR + CC_INTERMEDIATE like steam gas: take them out of the ×1.10 on all four bands (committed 1.005,
econ_low 0.95, econ_high 1.08, peak 2.25). Coal bands are unchanged. It extends the existing ruling's own structure
and needs no new number."*

How each carve-out condition is met:

| cond. | requirement | how this arm meets it |
|---|---|---|
| (a) | `offer_curve_by_group` band multipliers only | only `committed` / `econ_low` / `econ_high` / `peak` move, in two classes. `phys_*`, `econ_low_share`, `pct_peaking` are byte-identical in every class |
| (b) | ONE config across every scored year | the same table for all seven legs, 2019–2025 |
| (c) | set ex ante, never swept | the values are the pre-miso-220 table (`scripts/probes/_miso220_offer_table.py` lines 55–64), i.e. keeper ÷ 1.10 exactly; asserted to 1e-9 when the file was written. No alternative value is solved, and no value is selected by a gate |
| (d) | merit-order adjustment is intended | CC moves down against coal (lifted ×1.10) and steam gas (held), which is the object FINDING-miso274 §5 names |
| (e) | attestation `authorized_price_tuning` block + DOF ledger | the promotion (if ruled) rewrites the block's `value` to "×1.10 on 9 non-steam fossil classes; CC_REGULAR, CC_INTERMEDIATE, ST_GAS, ST_GAS_INTERMEDIATE held at the pre-lift table", cites this ruling, and narrows the ledger entry. No new free parameter: 1.10 is still the only one |

## 2. The delta (exactly eight cells)

| class | band | keeper | arm |
|---|---|---:|---:|
| CC_REGULAR | committed | 1.1055 | 1.005 |
| CC_REGULAR | econ_low | 1.045 | 0.95 |
| CC_REGULAR | econ_high | 1.188 | 1.08 |
| CC_REGULAR | peak | 2.475 | 2.25 |
| CC_INTERMEDIATE | committed / econ_low / econ_high / peak | same as CC_REGULAR | same as CC_REGULAR |

Unchanged: `CC_CHP`, `CT_CHP`, `CT_PEAKER`, `CT_INTERMEDIATE`, and all four coal subclasses stay lifted; `ST_GAS`
and `ST_GAS_INTERMEDIATE` stay held.

**Zero-LP footprint, by construction.** Within a class the common factor cancels, so CC merit order is unchanged
*within* CC. miso-220 §2 measured the lift at **+9.29 %** on the cap-weighted CC_REGULAR offer (S-2, 1,604 tranches,
0 outside the covered classes). Removing it lowers that offer by 9.29 / 109.29 = **8.5 %**, which takes the
FINDING-miso274 §5 CC econ band from ~×1.12 to ~×1.02 over the measured 7.13 MMBtu/MWh. No other array moves: pmax,
availability, heat rates and fuel prices are byte-identical. The shard check (`_miso275_shard_check.py`) enforces
this as HARD 1: the leg's recorded recipe must differ from the keeper's in `offer_curve_by_group` only, and must
equal the declared table exactly.

## 3. G-DRIFT (rule 29(b)) — keeper legs `09b152c5` vs this SHA

`git diff 09b152c5 <this SHA> -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference scripts/replay_keeper.py`
(23 files, +1203 / −25):

| hunk group | class | reason |
|---|---|---|
| `scenarios.py`: nine new fields (`reliability_floor_layup_window_mask`, `caiso_import_gas_coupling_ladder_only`, `caiso_intertie_gap_fill_measured_gas`, `coal_committed_nested_on_mustrun`, `unit_outage_membership_repair`, `nuclear_dormancy_defers_to_vintage_exit`, `nyiso_ldc_generator_delivered_gas`, `pjm_zonal_gas_basis_skip_923_priced`, `nwpp_demand_plant_basis`) | INERT | Each is default `False` and absent from the keeper recipe; no existing default or `__post_init__` moved |
| `run_calibration.py` `_reliability_floor_layup_shares`; `outages.py` membership-repair + ERCOT hour-grain path | INERT | Gated on `reliability_floor_layup_window_mask` / `unit_outage_membership_repair` (off). The ERCOT hour-grain branch is `iso == "ERCOT"` |
| `arrays.py` `hour_grain=` re-expression | INERT | For non-ERCOT it is the same predicate (`hour_grain and per_unit and merit_guard`). The keeper has `unit_outage_window_hour_grain: false` |
| `arrays.py` nuclear dormancy defer | INERT | Gated on its own default-off field |
| `campd_bins.py` `_APPLIED_MEASURED_FLAGS` (`eia923_identity`) | INERT | Only `_processed-legacy/campd_cc_heat_rates_CAISO.csv` carries an `eia923_identity` row; MISO's measured-rate artifacts carry none |
| `campd_bins.py` coal committed nested on must-run | INERT | Gated on its default-off field |
| `resolve.py` / `run_calibration.py` PJM basis skip-923; `basis/pjm.py` | INERT | `config.iso == "PJM"` and its own flag |
| `basis/nyiso.py` LDC delivered gas; `fuel/__init__` re-exports | INERT | Returns early unless the flag is on **and** `iso == "NYISO"` |
| `interchange/{caiso,core,spec}.py`, `neighbor_price.py`, `electric_power.py` state read | INERT | CAISO intertie paths, gated on the R-CAISO-3 flags |
| `eia930/demand.py`, `envelopes.py`, `runner.py`, `run_calibration_full.py` NWPP plant basis; `data/raw/reference/nwpp_plant_basis_energy.csv` | INERT | `iso == "NWPP"` and its own flag |
| `paths.py` `EIA_923_GENERATION_FUEL_*` | INERT | New constants; no MISO solve-path reader |
| `scripts/lib/forecast_parity_registry.py` | INERT | Forecast parity bookkeeping; not on the backcast solve path |
| `data/raw/_validation-source` | none changed | — |

Every pinned MISO input (the twelve `_miso273_shard_check.INPUT_SHA` files) has an **identical git blob** at the
keeper SHA and at HEAD. **All hunks are INERT, so form 4 holds for every year.** No control solve is earned.

## 4. The arm command (per year Y, one shard each)

```
python scripts/replay_keeper.py results/calibration/miso273_span --years <Y> \
  --set "offer_curve_by_group=$(cat docs/miso275-arm-offer-curve-by-group.json)" \
  --out-dir results/calibration/miso275_arm_<Y> \
  --note "miso-275 arm <Y>: CC_REGULAR/CC_INTERMEDIATE exempt from x1.10 lift (owner ruling 2026-09-26)"
```

**Shard check:** `scripts/probes/_miso275_shard_check.py --leg results/calibration/miso275_arm_<Y> --year <Y> --log <log>`.
It covers the recipe (the keeper plus exactly §2's table), the pinned inputs (miso-273's, unchanged), the hydro
classifier `dc2a9d4be30a0727`, and the miso-273 log markers.

## 5. Predictions (fixed before any shard; directions only)

1. **CC_REGULAR** dispatch rises in every year; C1 CC_REGULAR 2021 / 2022 / 2023 move toward the band. 2019 and
   2024 / 2025 (−0.70 / −3.68 / −3.58) may overshoot above zero.
2. **Coal** (COAL_PRB, then COAL_BIT) falls in every year. C1 COAL_PRB 2019 (+8.02) moves toward the band.
3. **Price:** CC econ is on the margin in most gas-set hours, so load-weighted price falls. C3a 2022 (−11.7 %) moves
   further below the band, and train-year C3a may cross its lower edge. This is the declared cost of the channel.
4. **ST_GAS** falls (displaced by cheaper CC). C1 ST_GAS 2019 (−8.19) moves away from the band.
5. **C3b 2021:** the storm week is a gas-array object (D1, §7) and does not change.

## 6. Decision rule (fixed now)

Recommend promotion iff every structural gate holds:

* **S-1 recipe.** Every leg is the keeper plus exactly §2's table, with pinned inputs, the pinned hydro classifier
  and every miso-273 log marker present.
* **S-2 single delta.** Only offer levels in CC_REGULAR / CC_INTERMEDIATE differ; no other mechanism log line
  changes count.
* **S-3 slack.** An arm year with more slack than the keeper is reported with its hours.

Gates C1–C8 are reported per year, both ways, at full magnitude, and decide nothing (rule 1, condition (c): the
value is not selected by the gates). Promotion is the owner's decision (rule 31).

## 7. Other owner rulings taken at the same sitting (recorded, not in this arm)

1. **D1, the storm-month gas convention (C3b 2021): "Daily delivered price".** Described in the question as: *"Use
   the measured daily hub/delivered price through Uri, including the spike days."* That is not armed here. Rule 19
   gives it its own lane, and the single-delta arm stays attributable. Per FINDING-miso269 §4, a regional daily hub
   for MidCon / South is **not on disk**, and only the Chicago daily print is. So D1 needs a data intake first:
   daily regional hub or delivered gas for the non-Chicago zones. It then needs a replacement for
   `miso_winter_citygate_daily`'s storm-month construction. The hazard miso-269 §2 measured is declared here: the
   Chicago $129.52 weekend print passed straight through takes storm-week price from 158 to 317, against 141
   actual. The owner has now ruled that the spike days are included.
2. **Candidate 1 (CC outage numerator basis): "Wait for crosswalk".** Not armed until a CAMPD-unit → EIA-plant
   crosswalk exists. The Riverside 55641 / West Riverside 64020 mis-route (FINDING-miso274 §4) must be fixed in the
   same construction.
3. **Data ask (status only):** the CAMPD-unit → EIA-plant crosswalk is still outstanding.

## 8. Launch record

(appended after the pin; §1–§7 unchanged)
