# PJM-NEXT control 2020: G1(c) note (shard `claude/pjmnext-ctl-2020`)

Pin `7f0953845350089732892f83248726d4b04fb84f`. The solve completed with exit 0.

**G1(c) cannot pass as written.** The prompt requires the solve log to name the EIA-860 source
`vintage_2020`. The pinned code never logs that path, so the check has nothing to find.
`eia860.py:1923` prints only `Loaded PJM fleet from EIA-860 parquet (N generators)`, and
`runner.py:1500` calls `set_eia860_vintage` without logging it.

**How the vintage was confirmed instead (no LP).** I called the runner's own resolver on the written
`scenario_config`:
- Inputs: `eia860_vintage_year=None`, `weather_year=2020`, `mode=backcast`,
  `eia860_vintage_tracks_solve_year=True`.
- `resolve_backcast_eia860_vintage(...)` returns 2020.
- `paths._ACTIVE_EIA_860_DIR` is then `data/raw/eia-860/vintage_2020`.

**The other G1 checks all pass:**
- (a) All seven keeper flags are true.
- (b) The outage sha is `312a11b8…`.
- (d) The three card-1 flags are false.
- (e) Neither the carry log line nor the zone-coords log line appears.

I pushed the bundle anyway, as rule 34(a) requires. The parent decides whether this evidence
satisfies (c) or whether this leg should be discarded.
