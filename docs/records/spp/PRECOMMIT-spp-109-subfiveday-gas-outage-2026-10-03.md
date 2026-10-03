# PRECOMMIT — SPP-109: the sub-5-day gas outage gap (closeout plan §3.4 row 1b), 2026-10-03

**Written and pushed BEFORE any number below was computed.** Readings, formulas, the arming bar and the kill
rules are fixed here and fail closed. Lane `closeout-SPP-2` (branch `claude/closeout-spp-2`), desk
session_01ALecU5Wjde4tkbLrnMExT9. Main at charter 7ac5034b; branch cut at 792e55ad.

- **Keeper (control, rule 29(b)):** `2026-10-02-w0-spp107r`, bundle `results/calibration/w0_sppr_span`
  (2019–2025, all legs 15a351a1). Recipe carries `unit_outage_short_windows` (coal) true,
  `unit_outage_short_windows_gas` false, `wefor_residual` 0.0 on `["ST_GAS"]`, `campd_split_remap_companions`
  true, `unit_outage_netload_mask_repair` true.
- **Open objection being answered:** SPP-105 §4 (`RESULT-spp-105-gas-family-outage-2026-09-30.md`): the CC/ST
  statistical WEFOR stood in for the sub-5-day gas outages the ≥ 5-day CAMPD windows miss. With ST_GAS
  `wefor_residual` 0.0 (owner R-29, "Still promote") those outages are now unrepresented on ST_GAS, and on CC
  they are still carried only statistically.

## 0. Matrix cells, adjudicated before compute (rule 28)

| cell | shard text says | what it really is |
|---|---|---|
| `unit_outage_short_windows_gas` | **R**. Its first sentence ("UNTESTED here … PJM's does not fill this cell") is the pjm-d4-4 seed text; the cell was then **MOVED U → R by SPP-32 (2026-09-12) on SPP's own solve**. | **An SPP-own R, not a PJM transfer.** SPP-32 armed the SPP gas extract (`campd-unit-outages-shortgas-SPP.csv`, PJM's byte-identical invocation, merit-order guard) on top of the FULL CC/ST statistical WEFOR, screen year 2025: G4 slack 10,911 MWh at VOLL in SPP-South, C3a +15.97 %, C3b 0.262, every > $200 hour at the slack price. The seed sentence is stale and is corrected in this session's cell update. |
| `wefor_residual` | **K** (ST_GAS only, R-29). Prior **R** on {CC_REGULAR, CC_CHP, ST_GAS, ST_CHP} = SPP-105 carrier A. | Carrier A's R reason was the missing sub-5-day representation, i.e. the gap this lane measures. |
| `wefor_statistical_stack` | U | Measured only (SPP-104). Unchanged by this lane. |
| `spp_commitment_posture` | R (pairing only) | Not touched. |

**New evidence over SPP-32's R** (required to re-open it): (i) the ST_GAS statistical WEFOR is now 0 by owner
ruling, so the measured short family on ST_GAS is no longer a stack but the only carrier of the phenomenon;
(ii) the arm below is a **replacement** (rule 19) on CC too, where SPP-32 stacked; (iii) the W0 fleet. Prior Rs
named for the desk card: SPP-32 (gas short windows), SPP-105 carrier A (CC/ST `wefor_residual` 0.0 alone).

## 1. Arm (named ex ante; one mechanism per phenomenon)

**Arm G+ = keeper + `unit_outage_short_windows_gas = true` + `wefor_residual_groups =
["CC_CHP", "CC_REGULAR", "ST_CHP", "ST_GAS"]` (value stays 0.0).**

- The companion is required by the semantics, not chosen on a residual. `wefor_residual`'s own definition
  (`scenarios.py`) is "the < 5-day events below the overlay's detector floor". The gas short family measures
  exactly those events on exactly the four groups of `_SHORT_GAS_GROUPS`, the same set carrier A relieved.
  Arming the family while CC keeps its statistical WEFOR would count CC sub-5-day outages twice (rule 19). The
  family has no per-class scope, so a CC-excluded variant does not exist without a new field; none is built.
- No other field moves. No offer band, no sweep, no second value, no sensitivity arm.
- **Data companion:** `campd_split_remap_companions` is armed in the keeper, so the gas path reads
  `campd-unit-outages-shortgas-splitremap-SPP.csv`, which does not exist (the loader raises). It is built with
  the shipped builder, `scripts/data/build_campd_split_remap_companions.py --iso SPP --family shortgas`
  (plant-scoped splice at the incumbent's recorded invocation; rule 23 trigger is the SPP-98 remap identity
  data change, not a residual). Its rows differ from the incumbent only on remap-touched facilities. The diff is
  recorded in the FINDING before any reading.

## 2. Readings (zero LP; fixed)

Population: SPP CC_REGULAR, CC_CHP, ST_GAS, ST_CHP; years 2019–2025. Instruments: `fleet_only` rebuilds of the
keeper per year through `scripts.lib.bundle_fleet.reconstruct_bundle_fleet` (the SPP-105 probe's method), never a
config. Rebuilds: **K** (keeper as-is), **G** (K + gas short windows), **G+** (the arm), **K0** (K with
`wefor_residual` unset, i.e. ST_GAS statistical WEFOR restored: the pre-R-29 statistical reference).
Unavailable MW(t) = Σ pmax × (1 − availability) over the class's rows; annual means in GW.

- **R1, extract grain (unit, MWh):** per class × year, `L` = unit-capacity × window-hours of the ≥ 5-day
  extract the keeper reads; `S` = the same for the gas short extract (the companion); `S_lay` = the guard-rejected
  set in `campd-unit-outages-layup-shortgas-SPP.csv` if it is that set (checked from its deriver, reported
  either way). **Sub-5-day share = S / (S + L).**
- **R2, LP grain:** `S_g = unavail(G) − unavail(K)` per class × year (what the detector recovers on SPP's LP
  fleet).
- **R3, statistical it replaces:** `W_cc = unavail(G) − unavail(G+)` (CC/CHP WEFOR removed by the companion) and
  `W_st = unavail(K0) − unavail(K)` (ST_GAS WEFOR removed at R-29). Template: the R-29 PRECOMMIT's X / W.
- **R4, net:** `N = unavail(G+) − unavail(K)` per class × year.
- **R5, rule 14:** mean |keeper − SPP published Natural Gas outage| (portal `capacity-of-generation-on-outage`,
  `data/raw/spp-gen-outage/`), hourly, all hours and the SPP-84 upper tercile, for K and G+, on SPP-105's
  outage-type basis (flat GADS derate and flat summer class derate zeroed in both, as SPP-104/105 did).
- **R6, identification:** daily correlation of the short family's MW (from G − K) with SPP's published daily
  Natural Gas outage, pooled 2019–25 and per year.

## 3. Arming bar and kill rules (fixed)

- **Bar B1 (recovery):** in **each** train year 2023, 2024 and 2025, `S_g` summed over the four classes ≥ 50 % of
  the SPP-105 gap, the gas unavailability carrier A removed: **≥ 0.395 / 0.420 / 0.405 GW** (0.5 × 0.79 / 0.84 /
  0.81, DESIGN-spp-105 §4).
- **Zero-LP kills (any one → FINDING, cell update, no shards):**
  - **Z1 rule 14:** R5 all-hours mean |gap|, pooled over 2019–25, is larger for G+ than for K.
  - **Z2 identification:** R6 pooled daily correlation ≤ 0 (the family does not track SPP's own outage
    record, so it is not identified as outage; SPP-32 §7's economics worry).
  - **Z3 companion:** the splitremap shortgas companion cannot be built reproducibly (builder refuses, or its
    diff touches a non-remap facility).
- **Solve kills (post-solve, on the composed G+ bundle vs the keeper):**
  - **S1:** train C3a 2024 must move toward the ±10 % band (G+ > −11.2 %);
  - **S2:** unserved energy ≤ the keeper's in every year (read from each bundle's `hourly/system_<y>.parquet`);
  - **S3:** no new D-4 FAIL row in `legitimacy_diagnostics.json`;
  - **S4:** every leg Optimal.
  - **Recommendation rule:** all of S1–S4 pass → recommend promotion on structure (rule 1); any fails → recommend
    against, and the R stands with this record. C1, C3b, C3c and the full span are REPORTED, not gating.
    The 2025 EIA-923 data drift is labelled on the card.

## 4. Solve plan (only on B1 PASS and no Z kill)

Seven shards, one year each (rules 32/34/36), replaying `w0_sppr_span` with `--set
unit_outage_short_windows_gas=true --set 'wefor_residual_groups=["CC_CHP","CC_REGULAR","ST_CHP","ST_GAS"]'` at
the full 40-char SHA of the commit carrying the companion artifact. Compose with the composer the keeper used,
then `calibration_verdict.py`, `legitimacy_diagnostics.py`, and `dashboard_add_run.py` as a probe. RESULT gives the
per-(criterion, year) diff vs the keeper.

## 5. Then (row 1c, zero LP, this session either way)

SPP-81b marginal-setter decomposition (`scripts/probes/_spp81b_*.py`) on the keeper's P1 sidecars, 2023–25:
did the gas-independent RT level shift (+13.8 / +17.1 / +20.9 $/MWh on the old keeper) change under W0 + relief,
and does a measured, forward-reproducible driver own it. No lever without a named driver (rule 13).

## 6. DO NOT REDO

SPP-105 carrier A as solved (G+ differs: the measured family replaces what A removed); offer-band retunes;
curtailment ceiling; gas bridge; `spp_commitment_posture` alone; `coal_fuel_inventory` (SPP-108). Owner downloads
(STB EP 724, SPP portal) deferred under R-17.
