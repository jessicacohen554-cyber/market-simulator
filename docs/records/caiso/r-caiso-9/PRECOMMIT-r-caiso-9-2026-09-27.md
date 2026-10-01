# PRECOMMIT — R-CAISO-9: floor the SDGE per-year import cap at the static 1,436 MW (2026-09-27)

Written before any shard is launched. Every direction below is pre-registered.

## 1. What changes

**`caiso_import_cap_floor_static` (new, default off, CAISO-only).** Owner ruling 2026-09-27 (decision card):
*"Floor at static 1,436"*.
- Under `caiso_per_year_import_caps`, the `SP15_rest → SDGE` per-year LCT cap becomes
  `max(LCT peak − requirement, 1,436)`. The floor is the link's own baked static TTC (`_SDGE_IMPORT_CAP_MW`,
  `iso_configs.py`), read from the topology. **Zero new numbers** (rules 21/24).
- Declared **rule-14 reconciled estimate.** The LCT figure is a 1-in-10 N-1-1 planning-case capability, not the
  operating limit an all-hours LP link represents. Measured night-time SDGE imports exceed it in 2,773 / 784 / 886 h
  (2019 / 2020 / 2021; strict lower bound, `results/calibration/_rcaiso8/object2_sd_census.json`). The 1,436 floor
  is itself exceeded 167 h in 2019, so it is still a conservative estimate, not a measured operating limit.
- **LA Basin is not floored.** Census: LA's per-year LCT cap is below the static 12,008 MW in 2019 (11,150) and 2020
  (11,897). Taken to the owner as a card; ruling **"SD only"**, because no measured LA import census exists (LA
  Basin is not an OASIS TAC area). In the current fold the LA link binds 17 h (2019) and 0 h (2020).
- Rules: 14 (declared reconciliation), 19 (no new mechanism; the existing per-year cap applier), 21/24 (zero
  parameters; field + cache-key optional default in the same commit), 28(c) (matrix row + a cell in every shard).

Per-year SDGE cap (MW):

| year | LCT cap | with floor | moves? |
|---|--:|--:|---|
| 2019 | 386 | 1,436 | yes |
| 2020 | 718 | 1,436 | yes |
| 2021 | 635 | 1,436 | yes |
| 2022 | no LCT row → static 1,436 | 1,436 | no |
| 2023 | 1,436 | 1,436 | no |
| 2024 | 2,074 | 2,074 | no |
| 2025 | 2,071 | 2,071 | no |

## 2. Solve

Keeper recipe + the flag. One shard per year (rule 36), 2019–2025 (rules 34(c) / 35(c)). Each shard pushes its
full bundle (rule 34(a)) at a pinned SHA. Solves run in the foreground.

- 2019–21: `replay_keeper.py results/calibration/rcaiso8_A_tp_2019_2021 --years Y`
- 2022–25: `replay_keeper.py results/calibration/rcaiso8_A_span --years Y`
- Both with `--set caiso_import_cap_floor_static=true`. The keeper recipe already carries
  `caiso_intertie_partial_year_measured=true`.

2022–25 are solved even though G-DRIFT predicts no LP input moves there: rule 35(c) requires the incoming keeper
to carry every year, and a re-solve at HEAD also measures any drift G-DRIFT cannot see.

## 3. G-DRIFT (zero LP; `scripts/probes/_rcaiso9_gdrift_identity.py`)

Arms: the keeper pin `ee309e39` (both bundles were solved there), HEAD with the flag off, HEAD with the flag on.
Compared: mc_base, pmax, pmin, min_gen, availability, heat_rate, emission_rate, vom, ids, demand, and the topology
(every link TTC and interface limit).

Expected:
- **off → on:** only the 2019–21 `SP15_rest → SDGE` link TTC moves (386 / 718 / 635 → 1,436). Nothing in 2022–25.
- **pin → off:** nothing.

Measured: §6.

## 4. Pre-registered directions (fold values from `2026-09-27-caiso-r8-fold`)

| quantity | 2019 | 2020 | 2021 | direction |
|---|--:|--:|--:|---|
| SDGE unserved (slack), MWh | 419,683 | 12,125 | 2,259 | **down** each year (2019 to near zero is expected, not required: 167 h exceed even 1,436) |
| SDGE mean price, $/MWh | 388.8 | 53.6 | 59.6 | **down** each year |
| hours SDGE − SP15_rest > $0.01 (SP15_rest→SDGE binding) | 7,155 | 2,584 | 3,835 | **down** each year |
| C3a 2021 mean LMP (+13.5 %) | — | — | +13.5 % | **down** (improves). 2019–20 unscoreable (no measured LMP). |
| C3b 2021 | — | — | PASS | **stays PASS** |
| C3c 2021 hours > $200 (model 108 vs RT 27) | — | — | 108 | **down** |
| CC_REGULAR TWh (C1) | +20.4 | +24.8 | +10.1 | **not pre-registered in sign**. Served-SDGE energy rises (more CC upstream) while SDGE in-pocket gas/peakers fall. Expected \|Δ\| ≤ 1 TWh; the 2019–20 C1 miss stays FAIL. |
| C4 gas NRMSE | 0.575 | 0.530 | 0.387 | not pre-registered; expected small |
| 2022–25 (keeper) | — | — | — | **no movement** beyond solver noise. Any score movement is drift, reported at full magnitude. C4 2025 (0.299) is the one to watch. |

## 5. Decision rule (set before the solve)

- Promotion candidate iff 2022–25 remain CALIBRATED (rule 1: the mechanism is kept on structure, not on the fold's
  residual). The fold is reported, never gating (rule 30(c)).
- If 2022–25 read NOT-YET, promotion would withdraw the complete marker: that trade goes to the owner as a decision
  card, never taken in-session.

## 6. G-DRIFT measured

Artifact: `results/calibration/_rcaiso9/gdrift_input_identity.json`. **Matches §3 exactly.**

| pair | 2019 | 2020 | 2021 | 2022–25 |
|---|---|---|---|---|
| off → on | SDGE link 386 → 1,436 | 718 → 1,436 | 635 → 1,436 | nothing |
| pin → off | nothing | nothing | nothing | nothing |

- No fleet array, mc_base, demand or interface limit moves in any year in either pair.
- `defaults_changed` (six `*_path` fields) and `constants_changed` (`CAMPD_BINNING_ISOS`,
  `EIA930_PS_FOLDED_INTO_WAT`, `RGGI_MEMBER_STATES_BY_YEAR`) are serialization artifacts: the paths are
  worktree-root-relative and the three constants are sets hashed in iteration order. They also differ in
  off → on, where the code is identical, so they carry no LP content.
- New fields since the pin: `caiso_import_cap_floor_static` (this lane) and `pjm_offer_midcurve_shape_segments`
  (a PJM field, default off, INERT for CAISO).

### 6a. G-DRIFT addendum — rebase base `baf382bd` (code audit, zero LP)

G-DRIFT above ran at base `a6347bd8`. Before launch the branch was rebased onto `baf382bd`. Every changed hunk on
the backcast path (`git diff a6347bd8 baf382bd -- src/market_sim scripts/run_calibration*.py scripts/lib
data/raw/_validation-source data/raw/reference`) is **INERT for CAISO**:
- SPP-93 (`zonal_shares.py`, `eia860.py`, `zone_assignment.py`, `renewables.py::_allocation_zone`, `iso_configs.py`,
  `topology_variant.py`, `data/raw/reference/spp_plant_reserve_zone.csv`): SPP-only, and gated on
  `spp_zone_partition` (default `north_south` = byte-identical).
- soco-81 (`campd_bins.py::coal_incremental_hr_ratios`, `assembly.py` two-sided coal HR, the `year=` pass-through):
  gated on `coal_econ_marginal_hr_two_sided` (default off, absent from the CAISO recipe), and no CAISO artifact
  exists.
- R-ERCOT-10: regenerated ERCOT partial-outage extracts only.

Form 4 stands: the committed keeper and fold bundles are the controls.
