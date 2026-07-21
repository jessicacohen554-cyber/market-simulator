# caiso-110 session handoff (2026-07-21): endogenous WECC-West node WIRED, A/B pending

## Status
- **Keeper UNCHANGED**: `2026-07-19-caiso-102-hourfix`. All caiso-110 work is behind a
  default-off gate; non-endogenous runs are byte-identical.
- **W1 + W2 DONE** (wiring + gate), committed locally. The 4 NEW files are pushed to the
  branch. The 3 LARGE edited files are preserved as the verified patch below (git push
  413s here; inline-API push of huge files impractical).
- **W3 (the 3-year A/B) NOT run.** A 2024 diagnostic solve was running when the session
  was archived.

## What is on the branch (pushed via API)
- `src/market_sim/data/wecc_west_fleet.py` — the West-fleet builder (measured inputs, 0 fitted).
- `tests/test_wecc_west_fleet.py` — passing.
- `scripts/probes/_caiso110_endogenous_diag.py` — throwaway 2024 diagnostic.
- `scripts/probes/_caiso110_endogenous_B.py` — 3-year A/B B-leg.
- `docs/handoffs/caiso110-wiring.patch.b64` (this) — the 3 large-file edits.

## RESTORE the 3 large-file edits (run at repo root, on a fresh clone)
```
base64 -d docs/handoffs/caiso110-wiring.patch.b64 > /tmp/caiso110-wiring.patch
git apply --3way /tmp/caiso110-wiring.patch   # or: git apply -C1 --recount /tmp/...
```
The patch edits `scripts/run_calibration.py`, `scripts/run_calibration_full.py`, and
`src/market_sim/config/scenarios.py`. It was verified to reconstruct these exact blobs:
- scenarios.py -> `fa0c97b3fc1ca67c361cc78f208a18d49bcb9675`
- run_calibration.py -> `cbbdc8b6908a6919cd2ee87c957ae0ff75c9ae0f`
- run_calibration_full.py -> `283d910f84a7edcfd953b4ec77dccf61b0a6c89f`
The scenarios.py hunks are relative to the main state at commit cf306c95 (which added
`net_cone_forward_escalation` + registered the nyiso cache-key fields); if main advanced
further, apply with `--3way`/fuzz. Patch blob hash: `a2c6d8e40e7f935e0a3558d2f659dfdcb834e298`.

## Design (already committed to main earlier)
`docs/handoffs/caiso-endogenous-wecc-node-design-2026-07-21.md`,
`scripts/data/derive_wecc_west_supply.py` (writes `data/clean/wecc-west-supply/`),
`data/dictionary/schema/wecc-west-supply.schema.yaml`. Verified West demand ~54-57 GW,
solar 6.8/9.5/11.8 GW belly, net export +2.2 GW. EIA-860-West nameplate: gas 54.6 / coal
20.3 / nuclear 5.4 GW (thermal 80.2 >> peak+export 63.7 -> feasible). Clock: fold via
campd._hour_index_8760 on US/Pacific, SHIFT=0 (West solar aligns to model CAISO solar
r=0.984). West gas hub = Henry Hub; coal = COAL_PRICE_BASE PRB $2.0; HR/VOM from constants.

## OPEN ISSUES for the next session (in priority order)
1. **LP SLOWNESS**: the endogenous 2024 P0 solve ran ~36+ min (vs ~8 min baseline). Likely
   transmission-loop degeneracy (bidirectional WECC ties WECC_import<->NP15/SP15_rest +
   the internal NP15->ZP26->SP15_rest path form a free circulation cycle) OR West
   overcapacity degeneracy. FIX candidates: a tiny epsilon flow_cost on the WECC ties when
   endogenous (break the cycle, like the storage epsilon tiebreaker); tighter West thermal
   caps; or HiGHS interior-point. Confirm/fix BEFORE the full A/B (else 3yr x 2 legs is hours).
2. **WEST MC CALIBRATION** (the charter's sanctioned lever): Henry-based West gas_cc MC is
   ~$17-20 (2024) — may be too cheap vs the measured Palo Verde hub LMP (belly $10, mean
   $33, evening $56), risking evening/shoulder over-import. Measure the diagnostic net
   import (vs 32.4 TWh 2024) + belly/evening shape; if it floods, raise the West thermal MC
   with a MEASURED lever (the West delivered basis / the caiso-87 no-wedge treatment) — NOT
   a fitted throttle (rule 1/25). If it under-imports, the West is too expensive.
3. Then run `_caiso110_endogenous_B.py` (3yr, one bundle) vs a fresh `_caiso102_repro_A.py`;
   pre-registered gates in the B-leg docstring; rule-22 LOYO before any promotion; register
   on the dashboard; append `docs/calibration-log/caiso.md` (next number caiso-110).

## A/B gates (design §6 / B-leg docstring)
PRIMARY C5a CO2 -> 0 (gas TWh toward 74.2/61.0/51.6, no overshoot past +7%); C4 gas NRMSE
< 0.30, r >= 0.70; C3c scarcity tail up; GUARD C3a/C3b STAY PASS, net import toward
28.9/32.4/36.2 TWh; C8 forced-share within budget.
