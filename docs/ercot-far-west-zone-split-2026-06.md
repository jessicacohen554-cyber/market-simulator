# ERCOT Far_West (Permian) zone split — REJECTED PROBE: CT over-run is not transmission-closable (2026-06)

**Status: built, validated, and REVERTED.** The Far_West (Permian) node was
built end-to-end and validated as structure, but three diagnostic probes proved
the CT_PEAKER over-run is a cheap-Waha-gas CT-economics artifact, **not** a
transmission-topology artifact — the Permian export limit (the scope doc's
"whole ballgame") is **irrelevant** to it. With only the honest *loose* limit
(no measured intra-Permian GTC is available), the node is a pure dispatch no-op
that moves no metric. It was therefore reverted as a rejected probe rather than
carried as inert topology; the finding below is the deliverable, and a future
session can rebuild it (the recipe is fully recorded here) the moment a measured
intra-Permian limit lands **and** the upstream Waha-gas CT root cause is fixed.
The build lives in git history at commit `aad79c1` (reverted by the commit that
restored this doc).

## What was built (commit aad79c1, since reverted)

The mirror-image of the NE_LOB carve-out, splitting `Far_West` (the Permian /
FAR_WEST weather zone) out of the old `West` zone:

1. **Topology** (`config/iso_configs._ercot_config`): added
   `Zone(Far_West, load_share=0.1211)`, cut `West` to `0.0283`, and re-derived
   all eight ERCOT load shares together from NP6-345 (one pass,
   `scripts/data/derive_load_shares.py ercot`) so they sum to 1.0. Wired the Permian
   tie as a **pair of one-way links** (`is_bidirectional=False`) for an
   asymmetric rating: a loose `West->Far_West` *import* leg (the basin must pull
   in the bulk of its load) and a separate `Far_West->West` *export* leg. Both
   default to the WESTEX-class ~10 GW (loose); a `FW_EXPORT_TTC` / `FW_IMPORT_TTC`
   env hook (`_ttc_env`) sweeps them for diagnostics.
2. **Load mapping** (`eia_loader._ERCOT_LOAD_ZONE_GROUPS`): `FWEST -> Far_West`
   (was `West`); `WEST` stays `West`. Far_West gets its own measured hourly shape
   (12.9% of system, 2024) via `ercot_zonal_load_shares`.
3. **Plant siting** (`zone_assignment._ercot_zone`): split the `lon < -99.5`
   branch — `lon < -101.0` (and `lat < 33.5`) -> `Far_West`, else `West`. This
   sites *renewables* (eGRID per-plant lookup) into Far_West.
4. **Thermal bin sheet** (`data/raw/reference/custom-bin-assignments.csv`): the
   CAMPD-binned dispatch fleet carries a hard-coded `ERCOT_Zone` column (NOT the
   `_ercot_zone` heuristic), so the 13 Permian plants (lon < −101: Permian Basin
   3494, Odessa-Ector 55215, Quail Run 56349, Ector County 58471, C R Wing Cogen
   52176, + small CTs) were reassigned `West -> Far_West`, exactly as Martin Lake
   / Tenaska / Stryker were hand-assigned to `Northeast` for NE_LOB.
5. **Gas basis** (`data/raw/ercot_zonal_gas_hub.csv`): added `Far_West = Waha`
   (copied West's −0.72 / −2.19 / −2.38). The split is transmission, not gas.

### Validation — the structure is right

- **Far_West thermal fleet = 2,796 MW** (CC_REGULAR 1,703 + CT_PEAKER 862 +
  CC_CHP 230). This matches ERCOT's **measured ~2,800 MW** of Permian Basin
  conventional generation almost exactly (Permian Basin Reliability Plan Study,
  HB 5066, PUCT Proj. 55718, Jul-2024 workshop: "Permian Basin lacks local
  conventional generation compared to the North Central and Coast Weather
  Zones"; Permian conventional gen capacity ~2,800 MW against a 16,577 MW 2029
  non-coincident peak).
- **Far_West load = 57.9 TWh** vs **57.1 TWh local generation** (wind 24.5 +
  solar 14.6 + CC 11.7 + CT 6.0): the basin is roughly balanced / mildly
  net-importing, as the reliability plan describes.
- **Far_West slack = 0.0001 TWh** (max 67 MW) even with export capped to 2 GW —
  the loose import leg prevents any under-gen artifact.

## The decisive finding — the CT over-run is not transmission-closable

2024 diagnostic probes (run151 coal keeper recipe, `KEEPER_YEARS=2024`):

| probe | Far_West→West export cap | CT_PEAKER model | vs EIA-923 8.21 |
|---|---|---|---|
| pre-split baseline (run151) | — (single West zone) | 15.01 TWh | **+6.80 TWh (+82.8%)** |
| A: split, loose limit | 10,000 MW | 15.01 TWh | **+6.80 TWh** |
| B: split + thermal re-zoned, loose | 10,000 MW | 15.01 TWh | **+6.80 TWh** |
| C: split + thermal re-zoned, tight export | **2,000 MW** | 15.01 TWh | **+6.80 TWh** |

The over-run is **identical to the part-per-thousand** across all four. Why:

- With a **loose** limit the Far_West/West interface is copper-plate, so the
  split is a pure no-op on dispatch (probes A, B).
- With a **tight export cap** (probe C) the cap still doesn't bind on the CTs,
  because **the Permian CTs serve local load, they do not export.** Far_West is
  load-balanced/net-importing (57.1 gen vs 57.9 load), so its 6.0 TWh of CT runs
  to meet local demand during low-renewable hours — capping *export* changes
  nothing. The remaining CT over-run sits in **West** (Morgan Creek p3492 ~3.7
  TWh + Laredo, in Mitchell/Webb counties, exporting via the *measured* WESTEX)
  and **Houston** (2.1 TWh) — neither behind the Permian tie.

**Root cause (redirect):** the CT_PEAKER over-run is the cheap-Waha-gas CT
economics. With `ERCOT_ZONAL_GAS=1` the West/Permian CTs see ~$0 Waha gas
(2024 basis −2.19), so at HR ~10 they offer ~$0–5/MWh and out-compete
out-of-zone CCs and imports, running baseload. In reality these units (Morgan
Creek, Permian Basin, Odessa-Ector, Ector County) run as peakers / behind-meter
oil-&-gas cogen, not merchant baseload. The fix lives in the **CT offer / gas
treatment** (e.g. a Waha-gas intraday-volatility or take-or-pay floor on the CT
offer, or BTM/must-run treatment of the Permian oil-field cogen CTs), **not** in
the transmission network. This is the same disposition as the zonal-gas probe
(`docs/ercot-zonal-gas-basis-ct-relocation-2026-06.md`): the reduced zonal LP
cannot bottle these CTs with transmission because they are not export-bound.

## Disposition

- **The Far_West node was REVERTED.** It is the most structurally faithful
  representation of the import-dependent Permian (the load + the ~2,800 MW
  generation poverty are physical), and rebuilding it is the correct foundation
  for a future *measured* intra-Permian limit. But with only the honest loose
  limit it is a pure dispatch no-op (the Far_West/West interface is copper-plate;
  CT_PEAKER, CC, ST_GAS, COAL_PRB, LMP all byte-for-byte unchanged vs run151),
  and it cannot be made *active* without a measured limit that does not exist in
  this environment. Rather than carry an inert 8th zone (a Tier-0 change that
  invalidates cross-scenario comparison for no benefit), the build was reverted;
  the recipe above is fully recorded so it can be rebuilt in one pass when both
  preconditions are met.
- **The measured intra-Permian export GTC was NOT sourced.** The NP6-86 SCED
  binding-constraint archive (the data-first source for WESTEX/PNHNDL/NE_LOB) is
  not present in this environment, and the public ERCOT Permian Basin Reliability
  Plan studies are forward-looking (2030/2038 import paths; "765-kV raises the
  West Texas stability limit by 13%") rather than a clean present-day
  intra-Permian limit. This is moot, though: probe C proves a tight export cap
  would not move the CT over-run regardless of its value.
- **Two orthogonal bugs were found in `scripts/data/derive_load_shares.py` (also
  reverted with the node, so still open):** its `REF` path predates the W1 data
  collapse (`data/reference` → `data/raw/reference`), and its ERCOT weather-zone
  map still sends `EAST → North` although the live model carved EAST into the
  Northeast zone (`eia_loader._ERCOT_LOAD_ZONE_GROUPS` has `EAST → Northeast`).
  The script therefore cannot reproduce the committed Northeast load share. Worth
  a standalone fix.
- **Next investigation (the actual root cause):** the Waha-gas CT offer / Permian
  BTM-cogen treatment — a C2-family, not a C3/transmission, lever. The West +
  Permian CTs (Morgan Creek, Permian Basin, Odessa-Ector, Ector County) run
  baseload on ~$0 Waha gas; in reality they are peakers / behind-meter oil-field
  cogen. Candidate fixes: a Waha-gas intraday-volatility or take-or-pay floor on
  the CT offer, or BTM/must-run treatment of the Permian cogen CTs.

## Reproduce

```
# baseline (single West zone) is run151 = results/calibration/coalprb_foll078_3yr
# split, tight-export diagnostic (2024):
FW_EXPORT_TTC=2000 FW_IMPORT_TTC=10000 ERCOT_ZONAL_GAS=1 KEEPER_RTORDPA=1 \
  KEEPER_PERSIST_P2=1 KEEPER_STGAS_DRAG=1 KEEPER_YEARS=2024 \
  KEEPER_PRB_PARAMS='{"coal_prb_passthrough_floor":0.78,"coal_prb_follower_floor":0.78}' \
  python scripts/probes/_keeper_2023as_run.py fw_probe_exp2000_2024 2025 2023 \
  '{"ST_GAS":{"committed":0.0}}'
```
