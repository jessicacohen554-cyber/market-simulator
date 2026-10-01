# caiso-110 session handoff (2026-07-21): endogenous WECC-West node WIRED + diagnostic verdict

## Status
- **Keeper UNCHANGED**: `2026-07-19-caiso-102-hourfix`. All caiso-110 work is behind a
  default-off gate; non-endogenous runs are byte-identical.
- **W1 + W2 DONE** (wiring + gate), committed. The 4 NEW files are pushed; the 3 LARGE
  edited files are preserved as the verified patch below (git push 413s here).
- **W3 (the 3-year A/B) NOT run.** A 2024 DIAGNOSTIC solve completed and gives a clear
  verdict (below): the node as currently priced FLOODS. The West MC must be raised (a
  measured lever) before the A/B.

## DIAGNOSTIC VERDICT (2024, `results/calibration/caiso110_endog_diag`, NOT registered)
The results wiring is CORRECT: WECC_import is zone-excluded (`disp` zones = NP15/ZP26/
LA_BASIN/SDGE/SP15_rest only), and net import is computed from the tie flow. But the
endogenous node **FLOODS the tie** — a charter KILL condition, confirmed empirically:
- **Net import 57.3 TWh** vs actual 32.4 (+77% OVER).
- **Tie pinned at +7.5 GW (max West->CA export) in 82.6% of hours** (only 16.7% interior).
- **Gas 35.3 TWh** vs actual 61.0 (CA gas crushed — C5a would be FAR worse, not better).
- Solve time: P0 33 min + P1 48 min = ~84 min/yr (the tie-pinned degeneracy is likely a
  big part of the slowness; fixing the MC should relieve both).

**Root cause:** the West thermal is priced on Henry Hub (gas_cc MC ~$17-20 in 2024), far
BELOW the measured West wholesale price. The measured Palo Verde hub LMP (2024) is belly
$10 / mean $33 / evening $56; Malin similar. So the West is ~$15-25 cheaper than it should
be and exports at the tie limit almost every hour.

## THE FIX (next session, before the A/B) — a MEASURED lever, NOT a fitted throttle (rule 1/25)
Re-price the West thermal (coal / gas_cc / gas_ct in `src/market_sim/data/wecc_west_fleet.py`)
so the West's endogenous LMP reproduces the MEASURED delivered West hub, i.e. the export
price CA actually paid for imports. Concretely, replace the Henry-Hub `_thermal_mc` with the
measured Palo Verde / Malin delivered hub (the SAME series the existing import tranches use:
`market_sim.data.eia930.envelopes.measured_import_hub_prices` / the DSW_CCGT coupling hub),
OR add the measured delivered West-gas basis + the CARB border-carbon wedge that the existing
DSW_CCGT tranche pays (`IMPORT_TRANCHE_EF` 0.37). Target: the West export price ~$30-56 across
the day so the tie clears INTERIOR (~4 GW mean, matching actual 32.4 TWh) instead of pinned.
This is hour-varying, so set it via an `mc_base` override on the West rows after `assemble_mc`
(the import-price-injection pattern) rather than the scalar `vom`. Re-run the 2024 diagnostic;
iterate until net import ~32 TWh and gas rises toward 61 TWh. THEN run the 3-year A/B.

Secondary (may be moot once the tie is interior): if the solve is still slow, add a tiny
epsilon flow_cost on the WECC ties when endogenous (break the circulation-cycle degeneracy,
like the storage epsilon tiebreaker), or use HiGHS interior-point.

## What is on the branch (pushed via API)
- `src/market_sim/data/wecc_west_fleet.py` — West-fleet builder (measured inputs, 0 fitted).
- `tests/test_wecc_west_fleet.py` — passing.
- `scripts/probes/_caiso110_endogenous_diag.py` — throwaway 2024 diagnostic (recipe above).
- `scripts/probes/_caiso110_endogenous_B.py` — 3-year A/B B-leg (run AFTER the MC fix).
- `docs/handoffs/caiso110-wiring.patch.b64` — the 3 large-file edits.

## RESTORE the 3 large-file edits (run at repo root, on a fresh clone)
```
base64 -d docs/handoffs/caiso110-wiring.patch.b64 > /tmp/caiso110-wiring.patch
git apply --3way /tmp/caiso110-wiring.patch
```
Verified to reconstruct these exact blobs: scenarios.py `fa0c97b3`, run_calibration.py
`cbbdc8b6`, run_calibration_full.py `283d910f`. Patch blob `a2c6d8e40e7f935e0a3558d2f659dfdcb834e298`.
scenarios.py hunks are relative to main @ cf306c95 (added net_cone + registered nyiso cache-key
fields); if main advanced, `--3way`/fuzz. Also `.venv/bin/python scripts/regenerate_clean.py`
then `scripts/data/derive_wecc_west_supply.py` (fresh container) to rebuild `data/clean/`.

## Design (committed to main earlier)
`docs/handoffs/caiso-endogenous-wecc-node-design-2026-07-21.md`; the derive + schema.
EIA-860-West nameplate: gas 54.6 / coal 20.3 / nuclear 5.4 GW (thermal 80.2 >> peak+export
63.7). Clock: fold via `campd._hour_index_8760` on US/Pacific, SHIFT=0 (West solar aligns to
model CAISO solar r=0.984). West thermal-marginal in 100% of hours (structural belly fix holds
ONCE the MC is right).

## A/B gates (design §6 / B-leg docstring)
PRIMARY C5a CO2 -> 0 (gas TWh toward 74.2/61.0/51.6, no overshoot past +7%); C4 gas NRMSE
< 0.30, r >= 0.70; C3c scarcity tail up; GUARD C3a/C3b STAY PASS, net import toward
28.9/32.4/36.2 TWh; C8 forced-share within budget; rule-22 LOYO before any promotion.
