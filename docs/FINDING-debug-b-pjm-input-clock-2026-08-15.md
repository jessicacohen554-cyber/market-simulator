# FINDING — DEBUG-B: the PJM EIA-930 fueltype input-clock repair

**Date:** 2026-08-15 · **Lane:** DEBUG-B (measured-input repair, solve-affecting)
· **Head:** `origin/main` @ `c447199` · **Branch:** `claude/debug-b-pjm-input-clock-kcwiwn`
**Charter:** `docs/handoffs/debug-b-pjm-input-clock-charter-2026-08.md`, written by DEBUG-A
and merged in #3937. **Authority:** owner decision D-5,
`docs/model-audit-release-plan-2026-08.md` §6 decision 2 (SIGNED 2026-08-13) — chartered
without a further owner round-trip.
**Instruments:** `scripts/probes/_pjm2025_phase_drift.py`,
`scripts/probes/_pjm2025_wind_anchor.py` (both committed, both unchanged by this lane).
**Supersedes:** `patches/archive/pjm-m1-code.patch` (archived unapplied; see
`patches/archive/ARCHIVED-2026-08-14-pjm-m1.md`).

---

## Verdict in one line

**The `NG: *` fueltype family of the committed PJM wide extract was one hour early in
local-2023 and local-2024, and now is not.** The EIA-930 source clock ran 1 h early until it
was fixed upstream ~Feb-2025; the repair moves each affected cell — value unchanged — to the
UTC hour it actually measures. All three source-anchored gates pass at the corrected inputs.
The region family was already correct and is byte-identical at every row. **Keeper CANDIDATE
only; the owner promotes.**

---

## 1. REPRODUCE — DEBUG-A's measurements confirmed exactly on `c447199`

Both probes re-run before anything was changed. Every figure matches the charter's §1 table.

`_pjm2025_phase_drift.py` — B. July `NG: SUN` generation-weighted centroid hour
(astronomically fixed at ≈ 11.9; gate [11.5, 12.3]):

| year | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| July centroid, pre-fix | 10.73 | **10.91** | **10.94** | 12.03 |

`_pjm2025_phase_drift.py` — C. `Demand` vs PJM `hrl_load_metered` (UTC-stamped), best lag:

| year | DJF | MAM | JJA | SON | verdict |
|---|---|---|---|---|---|
| 2023 | 0 | 0 | 0 | 0 | region **healed** |
| 2024 | 0 | 0 | 0 | 0 | region **healed** |
| 2025 | 0 | 0 | 0 | 0 | region **healed** |

`_pjm2025_wind_anchor.py` — 930 series vs the PJM UTC-stamped gen-by-fuel feed, diff-series
best lag (pre-fix):

| series | 2023 | 2024 | 2025 |
|---|---|---|---|
| WIND | **+1** | **+1** | 0 |
| SOLAR | **+1** (r 0.993) | **+1** (r 0.994) | 0 (r 0.971) |
| GAS | **+1** | **+1** | 0 |
| PJM-feed July solar centroid (truth) | 11.93 | 11.99 | 12.02 |

Wind diurnal argmax/trough, pre-fix: 2023 PJM 22/9 vs 930 **21/8**; 2024 PJM 23/10 vs 930
**21/9** — the same one-slot lead, visible without any correlation machinery.

## 2. THE REPAIR

### 2a. Data — `NG: *` +1 h for local-2023 and local-2024 only

Implemented as `--rebuild-pjm-input-clock` in
`scripts/data/extend_eia930_hourly_from_balance.py` (the archived patch's machinery is the
mechanics template; its transform table is replaced). Value-preserving: the new value at UTC
hour `T` is the committed value at `T − 1 h`. No re-pull, no interpolation, no tuning —
rules 13 `[R-MEASURED]` / 14 `[R-ACCURATE]`.

| year | region family | fueltype family |
|---|---|---|
| 2023 | **kept** (already aligned) | shifted **+1 h** |
| 2024 | **kept** (already aligned) | shifted **+1 h** |
| 2025 | kept | kept (source fixed ~Feb; Jan-2025 straddle at 11.15 left as measured) |

**A defect found and fixed inside the repair itself.** 2023 and 2024 are adjacent blocks.
Applying them sequentially against the *accumulating* frame made the 2024 block's first row
read a slot the 2023 block had already moved — double-shifting exactly one hour,
`2024-01-01 06:00Z` (`NG: COL` 13674.0 where 13521.0 belongs). This is the archived patch
README's own "a second run double-shifts" warning in a within-run form; the patch's helper
has the same shape and would reproduce it for any two adjacent shifted years. Both blocks are
now sourced from an explicit pristine frame, and the byte-verification below is what caught
it.

**Byte-verification** (74,470 rows × 16 columns):

| check | result |
|---|---|
| 8 non-fueltype columns (region family + 4 time columns), all rows | **identical** |
| 8 `NG: *` columns outside local-2023/2024 (56,927 rows) | **identical** |
| 8 `NG: *` columns inside the two blocks (17,543 rows) | every cell **== pristine value at UTC `T−1h`** |
| NaN count in `NG: *` | 49,305 → **49,305** (unchanged) |
| row grid / `UTC time` / `Local date` / dtypes / column order | **unchanged** |

### 2b. Code — four PJM DataMiner read sites onto the absolute UTC stamp

Switched from the prevailing `datetime_beginning_ept` to the files' own
`datetime_beginning_utc`, converted to the model's fixed-EST clock (`Etc/GMT+5`, no DST), via
a new shared `_pjm_utc_hoy` helper:

| site | file |
|---|---|
| `pjm_net_interchange` | `src/market_sim/data/eia930/envelopes.py` |
| `pjm_zonal_interchange` | `src/market_sim/data/eia930/envelopes.py` |
| `pjm_neighbor_interchange` | `src/market_sim/data/eia930/envelopes.py` — **new since the archived patch**, added by the reorg |
| `parse_pjm_shares` | `scripts/data/curate_zonal_shares.py` (+ the `keep = ts.notna() & …` NaT guard) |

Measured effect on the PJM interchange files — exactly the predicted signature, no surprises:

| year | rows placed identically (outside DST) | rows moved 1 h earlier (inside DST) |
|---|---|---|
| 2023 | 67,078 | 125,636 |
| 2024 | 67,078 | 125,630 |
| 2025 | 65,639 | 121,992 |

**No curated zonal-shares artifact is committed.** `/data/clean/` is gitignored — "DERIVED and
disposable" — so there was nothing to regenerate and re-commit. The charter's conditional
("if one is committed") is not met. This is not a gap in the fix: `load_zonal_shares`' raw
fallback imports `_PARSE_FUNCS` from `scripts.data.curate_zonal_shares`, i.e. the very
function repaired above, so the solve consumes the corrected placement whether or not the
clean parquet has been materialised.

## 3. GATES — source-anchored, residual-blind (never the backcast fit)

All three pass at the corrected inputs.

| gate | 2023 | 2024 | 2025 | bar |
|---|---|---|---|---|
| July `NG: SUN` centroid | **11.90** | **11.93** | **12.03** | ∈ [11.5, 12.3] |
| wind / solar / gas diff-lag vs the PJM UTC feed | **0 / 0 / 0** | **0 / 0 / 0** | **0 / 0 / 0** | 0 |
| demand daily-peak mode-0 vs `hrl_load_metered` | **96.7 %** | **97.0 %** | **97.0 %** | mode 0, ≥ 95 % |

Full post-fix July-centroid row, for the record: 2023 **11.90**, 2024 **11.93**, 2025 12.03
against the PJM feed's own 11.93 / 11.99 / 12.02 — agreement to within 0.06 h in all three
years, where the pre-fix gap was a full hour in two of them.

Wind diurnal argmax/trough post-fix: 2023 PJM 22/9 vs 930 **22/9** (was 21/8); 2024 PJM 23/10
vs 930 **22/10** (was 21/9).

The demand gate is the control: it is measured with the repo's own construction
(`_pjm2025_phase_drift.load_metered_total` + `_pjm2025_event_phase.daily_extreme_hours`) and
is unchanged by this lane *by construction*, since the region family is byte-identical at
every one of the 74,470 rows. Probe C's per-season correlations are identical to four decimal
places pre- and post-fix.

## 4. Rule-28 duty b — matrix re-stamp determination

**Not due in this session.** No cell's evidence in
`docs/codebase-site/data/mechanism-matrix/PJM.js` cites the superseded input state: the
shard's single occurrence of "clock" is the items-12-13 flat-stack phrase *"measured on the
SEAM instead of on the clock"*, which is about where the amplitude defect was observed, not
about the extract's input clock. There is no reference to the input clock, to
`DIAGNOSIS-pjm-2025-phase-drift-*`, to M-1, or to the pre-repair centroid.
`scripts/check_mechanism_matrix.py` passes, including *"keeper stamps match every
keepers/<ISO>.json"*.

The shard's keeper+gates stamps describe the **current** keeper (`2026-08-04-pjm-152-collapse`,
solved at the pre-repair inputs), which is still the keeper — this run is a candidate and the
owner promotes. Re-stamping now would misdescribe live state. **The re-stamp becomes due at
promotion**, and the input-state-sensitive cells to revisit then are the diurnal-amplitude
family (items 12-13) and `seam_flow_envelopes`, both of whose evidence rests on diurnal shape
and seam flows that this repair moves.

## 5. LOYO

Structurally n/a: no parameter is introduced or moved. This is a measured-input repair — the
`neiso-85/86` gas-basis precedent.

## 6. Scope left open, deliberately — years ≤ 2022

The extract carries **2018-2026**, and the 1 h-early source clock is a property of the EIA-930
source until ~Feb-2025 — so it affects **every year before 2025**, not only the two this repair
shifts. The July `NG: SUN` centroid still reads **10.73 in 2022** (and comparably early in
2018-2021) against the astronomical ≈ 11.9.

The charter scopes the repair to local-2023/2024 — the solve span — and its §3 table says "all
other years untouched". That instruction is followed here rather than silently widened: a
zero-DOF charter is not the place to extend a data transform on my own judgement, and the
holdout rule (22 `[R-HOLDOUT]`, fail-closed) makes unilateral reach into other years exactly
the wrong reflex. **But the inconsistency is real and is filed here rather than left to be
rediscovered:** the committed extract now carries two different fueltype clocks — corrected for
2023-2025, uncorrected for ≤ 2022. Any lane that trains, validates or backcasts PJM on ≤ 2022
fueltype data is still on the early clock. Extending the same value-preserving `+1 h`
re-placement to 2018-2022 is a one-line change to `_PJM_INPUT_CLOCK_SHIFTS` and needs an owner
charter, not new analysis.

## 7. Blast radius — reported, not tuned

Expected and confirmed in direction: PJM 2023/2024 solar and wind CF profiles move +1 h
(morning and evening merit-order edges, the evening net-load ramp); the gas benchmark series
moves with them, so the C2/C4-family benchmarks recompute; interchange envelopes and zonal
shares move only inside DST hours.

Rule 14 governs the outcome: **if any criterion worsens at the corrected inputs, the accurate
input stays and the root cause gets filed. The repair is not reverted to buy a residual back.**

## 8. Re-solve and registration

See §8 below (appended after the full-span bundle completed).
