# DEBUG-B charter — PJM EIA-930 fueltype input-clock repair (M-1 successor)

**Chartered by:** DEBUG-A (debug sweep, 2026-08-14), under the owner's D-5
pre-authorization (`docs/model-audit-release-plan-2026-08.md` §6 decision 2,
signed 2026-08-13: *"If DEBUG-A confirms the defect still exists on main, the
fix is chartered … without another round-trip"*). The fix is **solve-affecting**
(it moves PJM wind/solar/gas hourly input shapes and the DataMiner-fed
interchange/zonal-share inputs), so it lands here as a DEBUG-B session, not in
DEBUG-A.

**Session model:** Opus or Fable (rule 27 `[R-PUSH]` — core `src/market_sim/`
+ committed-data surface). `DATA PROFILE: pjm`.

---

## 1. The defect, as measured on main @ 5bf5f13 (2026-08-14)

Re-measured with the repo's own instruments (both committed at
`scripts/probes/`, unchanged):

`scripts/probes/_pjm2025_phase_drift.py` on the committed
`data/raw/eia-930-hourly/PJM hourly.parquet`:

| gate | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|
| C. `Demand` vs PJM `hrl_load_metered`, best lag (all 4 seasons) | 0 | 0 | 0 | **region family HEALED** |
| B. July `NG: SUN` generation-weighted centroid (chronological clock; astronomical ≈ 11.9, gate [11.5, 12.3]) | **10.91** | **10.94** | 12.03 | **fueltype family 1 h EARLY in 2023 AND 2024** |

`scripts/probes/_pjm2025_wind_anchor.py` (930 fueltype series vs the PJM
UTC-stamped gen-by-fuel feed, diff-series best lag):

| series | 2023 | 2024 | 2025 |
|---|---|---|---|
| WIND | **+1** | **+1** | 0 |
| SOLAR | **+1** (r 0.993 at +1) | **+1** (r 0.994 at +1) | 0 (r 0.971) |
| GAS | **+1** | **+1** | 0 |
| PJM-feed July solar centroid (truth) | 11.93 | 11.99 | 12.02 |

**Conclusion: the entire `NG: *` fueltype family of the committed PJM wide
extract is one hour early in local-2023 and local-2024.** 2025 is correct
(EIA fixed the source ~Feb-2025; the Jan-2025 straddle month reads 11.15 and
stays as-measured per the original M-1 decision — no fabricated sub-month
shift). The region family (`Demand` / `Demand forecast` / `Net generation` /
`Total interchange`) is aligned at lag 0 in every year and season and must
**not** be touched.

## 2. Why this differs from the 2026-07 patch — the patch must NOT be applied verbatim

`patches/pjm-m1-code.patch` (2026-07-15, archived by DEBUG-A at
`patches/archive/` with a note) was measured against the July-2026 parquet
state: 2023 region +1 late (vintage construction), fueltype −1 early at the
source through 2024 — offsetting in 2023, so its transform was *2023 region
−1 h, 2024 fueltype +1 h, everything else kept*.

The committed parquet has since been **replaced** (last touch: PR #3852's
lane, merged 2026-08-10) in a way that healed the region family in all years
— and thereby **exposed the source's 1 h-early fueltype clock in 2023**,
which the offsetting construction error had been masking. Two of the patch's
premises are therefore dead:

* its 2023 region −1 h leg would now **double-shift** an already-correct
  family (the patch README's own "a second run double-shifts" warning, in a
  form nobody anticipated);
* its "2023 fueltype kept" leg would leave the 10.9 centroid in place.

Of its four files: the `run_calibration_full.py` `--reuse-solved` hunk is
**already on HEAD** (landed independently); the other three are unapplied and
superseded by §3 below.

## 3. The chartered fix

Zero degrees of freedom; a measured-input repair under rules 13/14
(`[R-MEASURED]`/`[R-ACCURATE]`) with the identical value-preserving mechanics
the 2026-07 M-1 established (`data/raw/eia-930-hourly/README.md` §"PJM
per-family input-clock convention"). Applied **consistently across every year
the extract carries** (rule 22's "data applies to all years" clause):

1. **Data.** Shift the `NG: *` fueltype family of `PJM hourly.parquet`
   **+1 h for local-2023 and local-2024 rows** (each cell keeps its measured
   value and moves to the UTC hour it belongs to). Region family untouched,
   all other years untouched, Jan-2025 straddle untouched. Re-implement the
   shift under `scripts/data/extend_eia930_hourly_from_balance.py` (the
   archived patch's `--rebuild-pjm-input-clock` machinery is the template,
   with the transform table replaced by this section's). Byte-verify: every
   cell outside the two shifted (family, year) blocks identical pre/post.
2. **Code.** Switch the four PJM DataMiner read sites from the prevailing
   `datetime_beginning_ept` stamp to `datetime_beginning_utc` converted to
   the model's fixed-EST clock (`Etc/GMT+5`, byte-identical outside DST,
   1 h earlier inside — the archived patch's construction, verbatim):
   * `src/market_sim/data/eia930/envelopes.py::pjm_net_interchange` (~L1051),
   * `…::pjm_zonal_interchange` (~L1125),
   * the per-counterparty sibling (~L1234) — **new since the patch**, added
     by the reorg; same fix, same rationale,
   * `scripts/data/curate_zonal_shares.py::parse_pjm_shares` (~L100), and
     regenerate + re-commit its curated zonal-shares artifact if one is
     committed (trace `load_zonal_shares`' read path).
3. **Gates (source-anchored, residual-blind — never the backcast fit):**
   * July solar centroid ∈ [11.5, 12.3] for 2023/2024/2025 (expect ≈ 11.9);
   * wind/solar/gas diff-lag 0 vs the PJM UTC feed, all three years;
   * demand daily-peak vs `hrl_load_metered` **stays** at lag 0 / ≥95 %
     mode-0 (proves the region family was not touched);
   * both probes re-run and their outputs recorded in the session log.
4. **Re-solve + register (the solve-affecting half).** Full-span PJM
   `--year 2023 2024 2025` in ONE bundle (rule 16 `[R-ALLYEARS]`), replaying
   the current keeper recipe (pjm-152) at the corrected inputs; register on
   the backcast dashboard **same session** (rule 15 `[R-DASHBOARD]`), verdict
   reported at full magnitude whatever it is. Keeper **CANDIDATE only** —
   the owner promotes. Re-stamp the PJM mechanism-matrix shard if any cell's
   evidence cites the superseded input state (rule 28 duty b). LOYO is
   structurally n/a (no parameter; a measured-input repair — the neiso-85/86
   gas-basis precedent).

## 4. Expected blast radius (report, don't tune)

PJM 2023/2024 solar/wind CF profiles move +1 h (morning/evening merit-order
edges, evening net-load ramp); the gas benchmark series moves with them, so
C2/C4-family fuel benchmarks recompute; interchange envelopes and zonal
shares move only inside DST hours (the `_ept` sites). If any criterion
worsens at the corrected inputs, that is rule-14 territory: keep the accurate
input, file the root cause — never revert the repair to buy the residual
back.

---

## 5. OUTCOME — DEBUG-B session, 2026-08-15

**Executed on branch `claude/debug-b-pjm-input-clock-kcwiwn`, off `origin/main` @ `c447199`.**
Full write-up: `docs/FINDING-debug-b-pjm-input-clock-2026-08-15.md`.

**§1 reproduced exactly.** Both probes re-run before anything changed; every figure in the
charter's §1 tables matched (July `NG: SUN` centroid 10.91 / 10.94 / 12.03; wind/solar/gas
diff-lag +1 / +1 / 0; demand vs `hrl_load_metered` best lag 0 in all years and seasons).

**§3.1 data — done.** `NG: *` shifted +1 h for local-2023 and local-2024 under the new
`--rebuild-pjm-input-clock` in `scripts/data/extend_eia930_hourly_from_balance.py`. Region
family and all other years untouched. Byte-verified over 74,470 × 16: the 8 non-fueltype
columns identical at every row; the 8 `NG: *` columns identical outside the two blocks
(56,927 rows); inside them (17,543 rows) every cell equals the pristine value at UTC `T−1h`;
NaN count unchanged.

> **Defect found inside the repair mechanics, and fixed.** 2023 and 2024 are adjacent, so
> applying the blocks sequentially against the accumulating frame double-shifted exactly one
> hour — `2024-01-01 06:00Z`. Both blocks are now sourced from an explicit pristine frame.
> The archived patch's helper has the same shape and would reproduce this for any two
> adjacent shifted years; the byte-verification is what caught it.

**§3.2 code — done, all four sites.** `pjm_net_interchange`, `pjm_zonal_interchange` and
`pjm_neighbor_interchange` (the per-counterparty sibling the archived patch did not know
about) in `src/market_sim/data/eia930/envelopes.py`, plus `parse_pjm_shares` in
`scripts/data/curate_zonal_shares.py` with the `notna()` NaT guard — all onto
`datetime_beginning_utc` on `Etc/GMT+5` via a shared `_pjm_utc_hoy`. Measured on the
interchange files: identical placement outside DST (67,078 rows/yr), exactly 1 h earlier
inside (~125,600 rows/yr). **No curated zonal-shares artifact is committed** (`/data/clean/`
is gitignored and derived), so the charter's "regenerate + re-commit if committed" conditional
did not fire; `load_zonal_shares`' raw fallback imports `_PARSE_FUNCS` from the repaired
script, so the solve consumes the fix regardless.

**§3.3 gates — all pass.**

| gate | 2023 | 2024 | 2025 | bar |
|---|---|---|---|---|
| July `NG: SUN` centroid | 11.90 | 11.93 | 12.03 | ∈ [11.5, 12.3] |
| wind / solar / gas diff-lag vs the PJM UTC feed | 0/0/0 | 0/0/0 | 0/0/0 | 0 |
| demand daily-peak mode-0 vs `hrl_load_metered` | 96.7 % | 97.0 % | 97.0 % | mode 0, ≥95 % |

Fast test lane, run locally per the charter: **6,838 passed / 0 failed** (31 skipped, 2
xfailed, 437 subtests). `check_mechanism_matrix.py` and `ci_refactor_guards.py` both pass.

**Rule 28 duty b — re-stamp NOT due this session.** No cell's evidence in
`docs/codebase-site/data/mechanism-matrix/PJM.js` cites the superseded input state (the
shard's only "clock" occurrence is the items-12-13 phrase "measured on the SEAM instead of on
the clock"). The shard's keeper+gates stamps describe the still-current keeper
`2026-08-04-pjm-152-collapse`; this run is a CANDIDATE and the owner promotes, so re-stamping
now would misdescribe live state. **The re-stamp becomes due at promotion**, and the
input-state-sensitive cells to revisit then are the diurnal-amplitude family (items 12-13) and
`seam_flow_envelopes`.

**Open scope, filed not actioned — years ≤ 2022.** The extract carries 2018-2026 and the
1 h-early source clock affects *every* year before 2025: the July `NG: SUN` centroid still
reads **10.73 in 2022** (comparably early 2018-2021). This charter scopes the repair to
local-2023/2024 and says "all other years untouched", so that instruction was followed rather
than silently widened — but the committed extract now carries two fueltype clocks, and any
lane using ≤ 2022 PJM fueltype data is still on the early one. Extending the same
value-preserving `+1 h` re-placement to 2018-2022 is a one-line change to
`_PJM_INPUT_CLOCK_SHIFTS` and needs an owner charter. See the FINDING §6 and the
`data/raw/eia-930-hourly/README.md` scope note.

**§3.4 re-solve + registration:** see the FINDING §8.
