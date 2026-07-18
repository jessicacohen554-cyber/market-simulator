# SCOPE: split ERCOT West into Far_West (Permian) + West to close the CT_PEAKER over-run (2026-06)

**Status: scoped, not built.** Next-session implementation plan.

## Why

The CT_PEAKER over-run (+6.8 / +6.8 TWh, +1.0pp share, 2024/25) is the
accepted zonal-LP limitation from enabling the zonal gas basis
(`ERCOT_ZONAL_GAS=1`): on ~$0 Waha gas, West/Permian CT peakers out-compete
out-of-zone CCs and run baseload, because the single `West` model zone lets all
Permian generation reach the 10 GW WESTEX export interface freely. In reality
the cheap Permian CTs are bottled behind intra-Permian (<200 kV) transmission
and a large *local* Permian load. The fix is to give the Permian its own node.

This is the **same move already proven for NE_LOB** (the `Northeast` zone was
carved out of `North` behind a measured ~1,300 MW export GTC to trap the Martin
Lake / NE-CC lobe). Far_West is the direct analogue.

## The decisive data point

ERCOT NP6-345 native load by weather zone (2024):

| weather zone | annual load | = model zone |
|---|---|---|
| **FWEST (Permian)** | **57.77 TWh (12.5% of ERCOT)** | currently → `West` |
| WEST (Abilene/San Angelo/CREZ) | 11.84 TWh (2.6%) | currently → `West` |
| (West total) | 69.6 TWh (15.1%) | matches `West.load_share` 0.1494 ✓ |

FWEST is **ERCOT's ~3rd-largest load zone**, not a generation backwater — the
oil-&-gas electrification boom. Pooling a 57.77 TWh load+gen pocket with a
transmission interface is exactly what needs its own node. A real Far_West node
lets the Permian CTs serve their (large) local load while their *export* is
capped by a measured internal limit — which is the physical reality the pooled
zone erases.

## Implementation steps

1. **Topology (`config/iso_configs._ercot_config`).**
   - Add `Zone(name="Far_West", load_share=0.125)`; cut `West` to ~0.025
     (re-derive both from `scripts/data/derive_load_shares.py` so all 8 sum to 1.0).
   - Wire `Far_West` behind `West`: `TransferLink(from_zone="Far_West",
     to_zone="West", ttc_mw=<measured Permian export limit>)`. Keep WESTEX on
     `West->North` (7300) + `West->South_Central` (2700) as the outer boundary
     (so Permian gen traverses Far_West→West→{North,SC}). Confirm the wiring
     against the actual GTC station geography (step 3) — Far_West may also need
     a direct `Far_West->South_Central` leg.

2. **Load + weather-zone mapping (`eia_loader._ERCOT_LOAD_ZONE_GROUPS`).**
   Change `"FWEST": "West"` → `"FWEST": "Far_West"` (leave `"WEST": "West"`).
   ERCOT native load already reports FWEST and WEST separately, so each node
   gets its own measured hourly shape for free via `ercot_zonal_load_shares`.

3. **The measured internal limit — THE open data task (do not tune to the CT residual).**
   - Re-run `scripts/data/derive_ttc_limits.py` over the NP6-86 SCED binding-constraint
     archive and look for Permian/Far-West-internal GTCs (`TRDWEL` "single line",
     and any constraint whose FromStation/ToStation sits in the Permian) — the
     same FromStation-empty GTC method that produced WESTEX/PNHNDL/NE_LOB.
   - If no single clean GTC maps, source the Permian export limit from the
     **ERCOT Permian Basin Reliability Plan / PUCT Permian studies** (the
     published 765 kV build-out studies state present-day Permian import/export
     stability limits) — a measured, forward-defensible transfer limit.
   - **Admissibility (#1/#11/#12):** the limit must be a measured transmission
     value, NOT dialed so CT volume lands on actual. If the best available limit
     is a GTC that collapses several parallel paths (like the N_TO_H carve-out),
     document the misalignment and use a reconciled measured value, not a guess.

4. **Plant siting (`zone_assignment._ercot_zone`).** Split the `lon < -99.5`
   branch: Far_West for the deep Permian (e.g. `lon < -101.0` — Midland 31.99/
   −102.08, Odessa/Ector 31.85/−102.37, Colorado City), West for −101.0 ≤ lon <
   −99.5 (Abilene/San Angelo/CREZ). Keep the `lat >= 33.5` Panhandle rule.
   Verify the over-running peakers (Morgan Creek 3492, Topaz 63688, Quail Run,
   Odessa-Ector) land in Far_West and that CREZ wind splits sensibly.

5. **Gas basis (`data/ercot_zonal_gas_hub.csv`).** Add a `Far_West` row = Waha
   (copy the `West`/`Panhandle` Waha basis: −0.72 / −2.19 / −2.38). Both Permian
   nodes stay on the Waha hub — the split is about *transmission*, not gas price.

6. **Sanity-check every per-zone consumer** keys off `zone_names` (renewables
   CF siting, hydro, storage siting, the gas-basis idx, load shares). Adding a
   zone changes `n_zones` → LP column count (`4×n_zones`); grep for any
   hard-coded ERCOT zone count or name list.

## Gates (re-gate whole fleet, 3-yr, on the run151 coal keeper recipe)

- **Primary:** CT_PEAKER over-run shrinks toward band WITHOUT a per-class fit,
  and the freed MWh lands back on CC_REGULAR/ST_GAS (gas-family conservation),
  not slack. CC_REGULAR 2025 (−0.5pp) and the West/North CC spatial split
  should also improve (the split is the real fix the zonal-gas probe couldn't
  deliver).
- **Must-not-regress:** C2 gas/coal family volume, C3 LMP MAE (27.9/15.3/11.4)
  + duration, the closed COAL_PRB and ST_GAS-drag results. Watch that the big
  FWEST local load doesn't create a Far_West slack/VOLL artifact (under-gen if
  the internal limit is too tight + local gen insufficient in some hours).

## Risks / unknowns

- **The internal limit is the whole ballgame and may not have a clean single
  GTC.** If it doesn't, the honest outcome may be "Far_West node confirms the
  mechanism but the limit is unmappable" (a documented limitation), mirroring
  the zonal-gas probe disposition. Budget a diagnostic probe before committing.
- Tier-0 topology change → invalidates cross-scenario comparison vs prior
  ERCOT runs; the keeper baseline must be re-solved on the new topology.
- CREZ wind in the West region: confirm the split doesn't strand wind capacity
  on the wrong side of the internal limit (would distort renewable dispatch).

## Reproduce baseline to compare against

```
ERCOT_ZONAL_GAS=1 KEEPER_RTORDPA=1 KEEPER_PERSIST_P2=1 KEEPER_STGAS_DRAG=1 \
  KEEPER_PRB_PARAMS='{"coal_prb_passthrough_floor":0.78,"coal_prb_follower_floor":0.78}' \
  python scripts/probes/_keeper_2023as_run.py coalprb_foll078_3yr 2025 2023 \
  '{"ST_GAS":{"committed":0.0}}'
```
