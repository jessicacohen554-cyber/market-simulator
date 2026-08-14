# ARCHIVED 2026-08-14 — pjm-m1-code.patch + README-M1-APPLY.md (D-5 closed)

Archived by the DEBUG-A debug sweep under owner decision D-5
(`docs/model-audit-release-plan-2026-08.md` §6 decision 2, signed 2026-08-13).
Kept as historical record, per D-5's "never silently delete".

**Status: the defect the patch targeted is CONFIRMED still live on main —
but the patch itself is superseded and must NOT be applied.** DEBUG-A
re-measured the committed `PJM hourly.parquet` with the patch README's own
probe instruments (2026-08-14, main @ 5bf5f13):

* the **region family is already healed** (demand vs `hrl_load_metered` best
  lag 0, all years/seasons — the parquet was replaced after the 2026-07
  diagnosis, last touch PR #3852's lane), so the patch's *2023 region −1 h*
  leg would now **double-shift** a correct family;
* the **fueltype family is 1 h early in BOTH 2023 and 2024** (July solar
  centroid 10.91 / 10.94 vs gate [11.5, 12.3]; wind/solar/gas diff-lag +1 vs
  the PJM UTC feed), so the patch's *2023 fueltype kept* leg would leave the
  defect in place;
* the patch's `run_calibration_full.py` `--reuse-solved` hunk is already on
  HEAD (landed independently); its file paths predate the 2026-07 scripts
  reorg (`scripts/curate_zonal_shares.py` → `scripts/data/…`; the
  `eia_loader.py` DataMiner loaders → `src/market_sim/data/eia930/envelopes.py`,
  which now carries a third `_ept` read site the patch never knew about).

**The live successor is the chartered DEBUG-B session:**
`docs/handoffs/debug-b-pjm-input-clock-charter-2026-08.md` — updated
transform (fueltype +1 h for 2023 AND 2024, region untouched), the four-site
`datetime_beginning_ept` → `datetime_beginning_utc` loader switch, the
source-anchored gates, and the full-span PJM re-solve + same-session
registration the fix's solve-affecting half requires (rules 15/16).
