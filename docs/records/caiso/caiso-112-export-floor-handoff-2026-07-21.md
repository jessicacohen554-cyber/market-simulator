# caiso-112 handoff (2026-07-21): export-floor ROOT-CAUSED to a P1-bridge min_gen clamp; fix wired behind `caiso_wecc_export_floor`; A/B mid-solve

## TL;DR
The caiso-111 "export-floor" (model min net import = 0, "tie can never reverse") is
**NOT a missing export sink**. The per-hub keeper already builds two priced
measured-hub export legs (`WECC_PNW_export_MALIN`, `WECC_DSW_export_PALOVRDE`,
`pmin = -corridor TTC`) and they clear correctly in **P0** (−1103 MW belly export).
The **scored P1** pass runs on the RA must-offer bridge's floored fleet, and the
shared floor tail `pipeline.commitment._bridge_floored_fleet` did
`new_min_gen = np.maximum(base_min_gen, bridge_floor)`; for the export legs
`base = -TTC`, `bridge_floor = 0`, so `np.maximum(-TTC, 0) = 0` **clamped the export
bound to zero** in every scored hour → min net import = 0. Proven by: P0 primal
(PNW export −1103 belly), LP col-lower dump (−4800 in P0 vs exact 0.000 in P1
output), and HiGHS reduced-cost (P0 leg RC ≤ 0, exports). This is a genuine bug,
not a modelling gap (rule 11).

## The fix (implemented on this branch, default-OFF, byte-identical off the flag)
New `ScenarioConfig.caiso_wecc_export_floor` (default False) threads a
`preserve_negative_min_gen` flag into `_bridge_floored_fleet`: raise `min_gen` only
where `bridge_floor > 0`, else keep `base_min_gen` — so the export legs keep their
negative bound and net-export in P1 (as they already do in P0). No fitted value:
export price = the SAME measured Malin/Palo Verde hub the import tranches use (rule
13). Mutually exclusive with the (not-yet-landed) `caiso_endogenous_wecc_node`
(rule 18). Core-infra (rule 26, Opus). **Verified byte-identical off the flag**:
A-leg (flag off) 2024 net = 42.03 TWh / 0 export hrs, identical to the keeper.

### EXACT source diffs to (re)apply if the branch is a fresh clone
**Fastest path — `git apply` the committed patches** (generated from the on-disk
fix vs `origin/main`, this branch):
```
git apply docs/handoffs/caiso112-commitment.patch docs/handoffs/caiso112-scenarios.patch
```
The verbatim diffs are also inlined below (hand-apply via the Edit tool if the
patches don't apply cleanly against a drifted base — both edits are small and
anchor-described).

**1. `src/market_sim/config/scenarios.py`** — insert AFTER the `caiso_corridor_flow_limit`
field's comment block (the line `    # groups. Default off (byte-identical); CAISO-only.`),
BEFORE `caiso_firm_import_shape`:
```python
    caiso_wecc_export_floor: bool = False  # L1a bidirectional-tie: let the
    # per-hub WECC export legs (WECC_PNW_export_MALIN / WECC_DSW_export_PALOVRDE,
    # priced at the measured West hub by inject_caiso_per_hub_intertie_prices)
    # NET-EXPORT in the SCORED P1 pass. build_caiso_per_hub_intertie already
    # builds those legs with a negative lower bound (pmin = -corridor TTC) and
    # they clear correctly in P0, but the P1-native RA/commitment bridge floor
    # (pipeline.commitment._bridge_floored_fleet) composed the bridge floor with a
    # plain np.maximum(base_min_gen, bridge_floor); for the export legs
    # base_min_gen = -TTC and bridge_floor = 0, so np.maximum clamped their bound
    # up to 0 and pinned them to zero in the scored fleet — the model could never
    # net-export (min net import = 0), so it imported in the ~700-900 belly hours
    # a year CAISO actually exports its spring-solar surplus (FINDING-caiso111
    # export-floor asymmetry). When on, the bridge preserves the negative export
    # bound (raising min_gen only where bridge_floor > 0), so the tie reverses to
    # export whenever CA λ falls below the measured West hub. No fitted value: the
    # export price is the same measured Palo Verde/Malin hub the import tranches
    # use (rule 13). Requires caiso_per_hub_intertie; MUTUALLY EXCLUSIVE with the
    # (not-yet-landed) caiso_endogenous_wecc_node gate — both re-price/re-sign the
    # WECC tie and must not compose (rule 18). Carried by
    # pipeline.commitment._bridge_floored_fleet (preserve_negative_min_gen).
    # Default off (byte-identical); CAISO-only.
```

**2. `src/market_sim/pipeline/commitment.py`** — `_bridge_floored_fleet`: add
`preserve_negative_min_gen: bool = False` to the signature, and replace the
`new_min_gen = np.maximum(...)` + `new_mech[...]` block with:
```python
    base_mech = getattr(fleet_arrays, "min_gen_mechanism", None)
    new_mech = (
        base_mech.copy()
        if base_mech is not None
        else np.zeros(bridge_floor.shape, dtype=np.int8)
    )
    if preserve_negative_min_gen:
        new_min_gen = np.where(
            bridge_floor > 0.0, np.maximum(base_min_gen, bridge_floor), base_min_gen
        )
        new_mech[bridge_floor > np.maximum(base_min_gen, 0.0)] = mech_id
    else:
        new_min_gen = np.maximum(base_min_gen, bridge_floor)
        new_mech[bridge_floor > base_min_gen] = mech_id
```
(move `base_mech`/`new_mech` computation ABOVE this block; it was after `new_min_gen`).
And in `caiso_ra_p1_floor_fleet`, change the final return to:
```python
    return _bridge_floored_fleet(
        fleet_arrays, ra_floor, MECH_RA_MUSTOFFER,
        preserve_negative_min_gen=getattr(config, "caiso_wecc_export_floor", False),
    )
```
ERCOT bridge callers (lines ~452, ~558) keep the default (False) — unchanged.

## A/B result (single delta, in-session; A = keeper repro flag-off, B = flag on)
Recipes: `scripts/probes/_caiso102_repro_A.py` (A), `scripts/probes/_caiso112_export_floor_B.py` (B).
Compare: `scripts/probes/_caiso112_ab_compare.py A_BUNDLE B_BUNDLE`.

| year | actual net | A net | B net | gas tgt | A gas | B gas | B export hrs | B gas vs tgt |
|---|---|---|---|---|---|---|---|---|
| 2023 | 28.9 | 37.2 | **28.6** | 74.2 | 60.6 | 67.8 | 1643 | −8.6% |
| 2024 | 32.4 | 42.0 | **28.1** | 61.0 | 54.4 | 65.7 | 1135 | **+7.6%** |
| 2025 | 36.2 | 42.7 | *(solving)* | 51.6 | 45.7 | — | — | — |

The fix recovers the export-floor (belly export appears, net import moves toward
actual). 2023 is excellent (net spot-on); 2024 over-corrects (net undershoots, gas
+7.6%). Raw-gas TWh above is DIRECTIONAL — the C5a verdict uses eGRID-weighted CO2,
so **score officially** via registration (below).

## NEXT SESSION — finish + decide (Opus/Fable, rule 26)
1. **Confirm B-leg 2025 finished** (`results/calibration/caiso112_export_floor_B/dispatch/2025_P1.parquet`).
   If the branch is a fresh clone, re-apply the two diffs above, rebuild data
   (`regenerate_clean.py` + egrid rename note below), and re-run
   `scripts/probes/_caiso112_export_floor_B.py` (3 years, rule 16).
2. **Register B** (rule 15, KEEPER or REJECTED): `calibration-report` skill /
   `scripts/dashboard_add_run.py --label "caiso 112 export floor" --bundle
   results/calibration/caiso112_export_floor_B`, then `build_manifest.py`. This
   computes the OFFICIAL C-gate metrics.json.
3. **Score**: `scripts/calibration_verdict.py --run-id <B-id>`. Compare the fail
   set to the keeper {C3c, C4, C5a}. Watch C5a overshoot (task guard +7%), C3a
   (mean LMP — B raises λ 29.9→38.7, over-price risk), C3b, C7, C8.
4. **Decide** (owner direction 2026-07-21): if B clears + structurally faithful +
   **rule-22 LOYO within 2023-2025 holds** → PROMOTE (swap `frontend/data/backcast/
   keepers/CAISO.json` + rebuild `status/CAISO.js` via `build_status.py --iso CAISO`,
   run `calibration-keeper-auditor`). Else → keeper stays `2026-07-19-caiso-102-hourfix`;
   B is a rejected probe on the dashboard.
5. **Append** `docs/calibration-log/caiso.md` (bottom) with caiso-112 (draft in this
   handoff's sibling scratch / the log entry below).

## The over-correction + continuation (if B rejected)
The minimal un-clamp is UNBOUNDED: the export legs also absorb the must-flow firm
imports locally (net flow stays import, so the corridor export ENVELOPE never
binds), over-exporting ~16 TWh gross vs reality ~1.5 → over-burns CA gas in the
smaller-under years (2024/2025). **Continuation lever L1a′:** bound the export
legs' absorption by the measured p95 net-export envelope (`caiso_corridor_flow_
limit`'s export side already computes it; extend it to cap the export-LEG dispatch,
not just the link flow) so the tie exports only the measured surplus. If that still
leaves the import-hours DEPTH failing C5a → escalate to **L1b** (endogenous WECC
West node, caiso-110 West-MC fix). The BUG FIX stands regardless.

## Environment notes (fresh container)
- `data/raw` from the base clone was stale; materialize from HEAD as needed. The
  egrid 2023 file is on disk misnamed `egrid2023_data_rev2 2.xlsx` — `cp` it to
  `egrid2023_data_rev2.xlsx` (byte-identical) or the solve FileNotFoundErrors.
  Also materialize `data/raw/_validation-source/caiso_offer_*` and `data/raw/reference/`.
- Solve ~7-10 min/yr, 15 GB RAM → strictly sequential.
- `git push` 413s here → push via `mcp__github__push_files` only; blob-verify
  commitment.py + scenarios.py after push (rule 27).
