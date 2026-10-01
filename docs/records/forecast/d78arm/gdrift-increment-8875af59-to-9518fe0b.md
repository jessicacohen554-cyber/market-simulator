# capx D78-ARM completion — G-DRIFT increment audit, recorded BEFORE the solve

**Base:** `8875af59` (the PRECOMMIT's declaration base, where every key in
`PRECOMMIT-capx-d78arm-2026-09-06.md` §2 was measured).
**HEAD:** `9518fe0b` (`origin/main` at 2026-09-07, this completion lane's solve HEAD).
**Question:** is any hunk that landed in between **LIVE** on a **PJM forecast T1-H**
(`run_capacity_hindcast.py --iso PJM --start-year 2021 --end-year 2025 --vintage 2020
--fuel-variant realized`)?

**Written before `run_arm.sh` was invoked**, per rule 29 `[R-SCREEN]` clause (b): the audit is
recorded so it cannot be written to fit the result.

## 0. The mechanical answer first — PJM's own key is unmoved, and ERCOT's is not

`docs/handoffs/d78arm/keys_probe.py` re-run at `9518fe0b` reproduces the committed
`keys_measured.json` **except two rows**:

| leg | committed (`8875af59` + arm) | at `9518fe0b` | |
|---|---|---|---|
| **`pjm bare`** | `fb16fda2ddb0a94a` | **`fb16fda2ddb0a94a`** | **unmoved** |
| every other PJM leg (10) | — | — | **all unmoved** |
| MISO / NYISO / NEISO / CAISO bare | — | — | unmoved |
| `ercot bare` | `46d013cbf1f35d27` | `f18431f2447bad01` | **MOVED** |
| `scenario_config_default_key` | `547053bdfccd4264` | `9ca2c6052b4850ea` | MOVED |

That asymmetry is capx D79's solve-surface fingerprint doing exactly its job: the ERCOT lane
`09c812aa` (ercot-253) re-declared `ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR` in
`solve_surface_declared.py`, which projects onto ERCOT and not onto PJM. So every change inside
the seven `SURFACE_MODULES` (`constants`, `capacity_market`, `fuel_trajectories`,
`ercot_envelopes`, `plant_taxonomy`, `entry_config`, `offer_curve_base.generic`) is answered
mechanically: **none of them projects onto PJM**, or PJM's key would have moved with ERCOT's.

## 1. The hunks the fingerprint does NOT cover, classified

`git diff 8875af59 9518fe0b -- src/market_sim scripts/run_capacity_hindcast.py scripts/lib
data/raw/reference` — 40 files, +1,873 / −32. Every hunk outside the fingerprint's reach:

| file | classification | reason |
|---|---|---|
| `scripts/run_capacity_hindcast.py` | **INERT** | the `--retirement-sector-gate` **help string** only (it now names the PJM arm). No code path. |
| `config/scenarios.py` | **INERT** | two new fields, `miso_seam_neighbour_hourly_spp` (miso-233) and `gas_offer_margin_anchor_vintage` (pjm-169 F4). Both land in `_CACHE_KEY_OPTIONAL_FIELDS` **registered at `"False"`**, so they are dropped from the hash at their declared default — which is *why* PJM's key is unmoved — and both are default-OFF and byte-identical off. The pjm-169 F4 field is PJM-relevant but **not armed**: nothing on `_pjm_config` sets it. |
| `pipeline/backcast_config.py` | **INERT** | two hunks: the ERCOT ORDC vintage is `iso.upper() == "ERCOT"`-gated; `pjm_interface_feed_admissibility_gate` is armed **in the BACKCAST recipe**, and its own comment says so ("ARMED HERE, in the BACKCAST recipe, and NOT in `iso_configs._pjm_config.default_scenario_overrides`"). `run_capacity_hindcast.py` never imports or calls `backcast_config` — a T1-H is `mode="forecast"`. |
| `model/reserves/spec.py` | **INERT** | the one changed call (`ercot_as_plan_requirement_mw` → `ercot_as_measured_requirement_mw`) is inside `_ercot_multiproduct_design`. |
| `results/scarcity.py` | **INERT** | pure addition of `ercot_as_measured_requirement_mw` + its 2021 fallback. ERCOT-only by name and by its single caller above. |
| `config/iso_configs.py` | **INERT** | three hunks: the D78-ARM block **in `_pjm_config` — this lane's own arm**, already in the measured key; `_spp_config` (new ISO); `_ISO_BUILDERS` / `SUPPORTED_ISOS` gaining `SPP`, appended last. |
| `config/solve_surface.py` / `solve_surface_declared.py` | **INERT for PJM** | `SURFACE_ISOS` gains `SPP` **appended last** and no surface name carries an `SPP` token, so the six earlier ISOs' projections are unchanged by construction; the one new `DECLARED` entry is the ERCOT ORDC table (§0). |
| `data/campd.py`, `data/renewables.py`, `data/transmission_expansion.py`, `data/zone_assignment.py`, `data/fleet/models.py`, `data/eia930/{frames,__init__}.py` | **INERT** | registry **additions keyed on `"SPP"` / `"SWPP"`**. No existing key's value is edited. |
| `data/eia930/demand.py` | **INERT** | a bad-value screen whose own docstring states "THE ONE LIVE CASE is SPP 2023"; it is a no-op on every training year of the six earlier ISOs. |
| `data/eia930/envelopes.py` | **INERT** | pure addition of `measured_miso_spp_hub_prices` / `spp_net_interchange`; consumed only by the MISO sub-gate below. |
| `data/neighbor_price.py` | **INERT** | an **import-time uniqueness guard** over `INTERFACE_NEIGHBORS` plus SPP entries. The guard changes no value; it fails the import if a key ever names two ISOs' neighbours (it does not). |
| `model/interchange/miso.py` | **INERT** | `neighbour_hourly_spp: bool = False`, a **sub-gate of** `miso_seam_neighbour_hourly`, MISO-only and default off. |
| `model/interchange/registry.py` | **INERT** | one `"SPP":` row added. |
| `scripts/lib/{confirmed_retirements,load_forecast,nuclear_license_status,transmission_expansion}` | **INERT** | per-ISO `spp.py` modules + their registry rows. |
| `data/raw/reference/spp_seam_*` | **INERT** | new SPP-only reference CSVs. |

## 2. Verdict

**ALL HUNKS INERT for this lane.** The 49-commit increment is, in substance, one new ISO (SPP,
lane SPP-14/-20) plus one ERCOT price-formation vintaging (ercot-253) plus two default-off
`ScenarioConfig` fields. G-DRIFT clause (b) form 4 is therefore valid at `9518fe0b`: the
committed D67-ARM bundle (`a9c66d8ea25acb9d`) and D78-R2's documented arm remain the controls,
and **no control solve is earned**.

**A residual limitation, stated rather than smoothed:** an unmoved cache key is evidence of an
unmoved *declared* surface, not a proof that no code path changed — which is exactly why §1
audits the uncovered hunks by hand rather than resting on §0. The two together are the claim.
