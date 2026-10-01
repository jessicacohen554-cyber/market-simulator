# ERCOT-97 results — plant-grain DAM availability + measured RUC + LOLP swap (2026-07-22)

Session on branch `claude/ercot-97-c3c-frontier-rtd17r`, baselined on the ercot96
keeper (`2026-07-22-ercot96-dam-hourly-grain`). Three lanes on the 2023-summer
C3c frontier; full narrative in `docs/calibration-log/ercot.md` § 2026-07-22 —
ERCOT-97. This file is the engineering hand-off (what shipped, how to reproduce,
what remains).

## What shipped (committed, branch `claude/ercot-97-c3c-frontier-rtd17r`)

| File | Kind | Lane |
|---|---|---|
| `scripts/data/build_ercot_dam_resource_crosswalk.py` | new | A-1 build script |
| `data/raw/reference/ercot-dam-plant-crosswalk.csv` | new | A-1 crosswalk (262 rows, 22 accepted) |
| `scripts/data/derive_ercot_thermal_dam_availability.py` | edit | A-2 site×hour emit (`--site-hourly-out`) |
| `data/raw/ercot-thermal-dam-availability-site-hourly.parquet` | new | A-2 input (2023; 1.9 M rows, 1.37 MB) |
| `src/market_sim/data/outages.py` | edit | A-2 `ercot_thermal_dam_availability_plant_series` loader |
| `src/market_sim/data/fleet.py` | edit | A-2 `_dam_waterfill` + `_ercot_dam_plant_hourly_apply` |
| `src/market_sim/config/scenarios.py` | edit | A-2 flag `ercot_thermal_dam_availability_plant` |
| `scripts/run_calibration_full.py`, `scripts/run_calibration.py` | edit | A-2 flag threading + run_config record |
| `tests/test_outages.py` | edit | A-2 tests (class-total invariant, pinning, missing-file no-op) |
| `scripts/probes/_ercot97_ruc_measure.py` | new | B measurement |

All Lane-A code is default-OFF and keeper-reproducing when off. `ercot96` keeper
byte-recipe intact (hourly CSV blob 7d93a2eb verified; the 7 patch files verified
against the ERCOT-96 manifest before any solve).

## Lane A — plant grain (PRIMARY): BUILT + directional A/B

**Crosswalk (A-1).** ERCOT DAM substation mnemonics (DDPEC, CBECII, WHCCS2…) do
NOT token-match EIA plant names, and 2-char initialisms collide (WHCCS2 →
Wharton is a FALSE match — it is Wolf Hollow II). So the accept gate is strict:
a row auto-accepts only on a *distinctive* abbreviation corroboration
(exact-initialism / ≥4-char token prefix / consonant skeleton — never a bare
2-char initials prefix) that is UNIQUE in class AND capacity-plausible, plus the
3 hand-forensic seeds. **22 accepted (12 CC / 6 CT / 4 ST), every one
hand-verified correct, zero false positives**; the other 240 are `accepted=0`
with full evidence → class-hour envelope fallback. A reviewer (or an ERCOT
RARF/settlement-point registry) extends coverage by toggling `accepted`.

**Mechanism (A-2).** `ercot_thermal_dam_availability_plant` (default off, requires
`_hourly`): each accepted plant is pinned to its own measured site-hour fraction
(Σ live / Σ rating over its mapped DAM sites), the unmapped remainder is
water-filled so the **class-HOUR total is unchanged** — a within-class
redistribution (which plant carries the derate), zero fitted parameters. Proven
by unit test: class total preserved exactly, mapped plants pinned, NaN
plant-hours fall back to the class grain.

**A/B (2023 rule-16 throwaway).** Base = keeper config re-solved (gas bridge
floored 51,607 unit-hours — matches the keeper's ~50k, base faithful). Probe =
base + plant flag. Comparator `scripts/probes/_ercot96_ab_readout.py`:

| metric | base | probe (plant) | Δ |
|---|---|---|---|
| tail hours (px>200) | 77 | 71 | −6 |
| tail_in_actual | 45 | 47 | **+2** |
| spurious | 32 | 24 | **−8** |
| mean px | 37.66 | 33.58 | −4.1 (actual 49.93) |
| summer hod-corr vs actual | 0.403 | 0.596 | **+0.19** |

Dispatch: CC_REGULAR +1278 GWh, ST_GAS −449, CT_PEAKER −251, COAL_PRB −429 (the
predicted merit-mix redistribution). **Read:** a genuine structural refinement —
fewer spurious tails, markedly better summer afternoon price shape — but the
cheaper-CC merit shift lowers mean price further below actual, a C3a-level cost.
NOT a clean C3c closer; the "C3a not worse" gate is not met on price level.
Needs full rubric + LOYO + owner judgment before any promotion — **not promoted**.

Caveat: the committed 2023 site-hour parquet is December-short (needs the
`60d_DAM_Gen_Resource_Data_2024_Jan-Mar` file for the Nov-Dec-2023 60-day
spillover); ~17.5k CC plant-hours fell back to class grain, so the measured
effect is a floor. Regenerate full-span once 2024/2025 DAM Gen_Resource files
are present:
`.venv/bin/python scripts/data/derive_ercot_thermal_dam_availability.py --years 2023 2024 2025`
(writes all three grains; the day/hourly CSVs must reproduce their committed blobs).

## Lane B — measured RUC conduct: IMMATERIAL, no mechanism

`.venv/bin/python scripts/probes/_ercot97_ruc_measure.py` over the slim SCED
tail/control-day subsets (2024/2025; 2023 SCED purged — re-fetch to extend):
ONRUC ≈ **303 unit-hours total (281 gas)**, evening-ramp weighted, ST_GAS-fleet
dominated. vs the keeper gas bridge ~51k unit-hours ⇒ **178× smaller ⇒ not
material**. Lane B step 2 not triggered (rule 19 one-mechanism / rule 14
measured-over-derived — the bridge + ST_GAS drag already carry vastly more
committed state; a RUC floor would replace a sliver). Composes with the Lane A
crosswalk for plant grain (5 of 64 ONRUC sites are crosswalk-accepted) if ever
revisited on a full 2023-2025 SCED corpus.

## Lane C — published ORDC-LOLP swap: REJECTED standalone

Keeper 2023 replay `--set ordc_lolp_params_path='"data/raw/_validation-source/ercot_ordc_lolp_params.csv"'`
(summer mu 0→904, sigma 1400→1333): tail 77→112 (real +17) but spurious 32→50
(**+18**); mean px 37.66→39.70. The published envelope raises scarcity pricing
but adds more spurious than real tail — **zero-spurious gate FAILS**. Not
adoptable standalone (confirms the ERCOT-95 prediction: "NOT a C3c closer").

## Disposition

C3c still out of band after all three lanes. Keeper UNCHANGED. The plant grain is
banked as a default-off, LOYO-pending structural asset; RUC is immaterial; the
LOLP swap is refuted standalone. The ERCOT-95/96 close-out stands as the owner's
option: LEDGER C3c 2024/2025 (3/3 MAX_LEDGERED_CAVEATS → CALIBRATED-WITH-CAVEATS)
— **owner sign-off, never unilateral**. Do NOT flip `keepers/ERCOT.json` without
an explicit promotion.

## Environment / transport notes (rule 26/27)

- This session ran the full ERCOT solve in-environment: `.venv` built from
  `requirements.txt` (numpy/scipy/pandas/pyarrow/highspy), the ERCOT input corpus
  fetched incrementally via sparse-checkout lazy-fetch (~1.4 GB — F923, EIA-860,
  eia-930, fleet-egrid, CAMPD unit-level, gas/coal prices, ORDC actuals). ERCOT
  2023 solves in ~5–8 min (~5 GB RAM), MALLOC_ARENA_MAX=2.
- **git push from the blob-filtered partial clone** (`--filter=blob:limit=2m`)
  triggers a multi-GB promisor backfill during pack negotiation that disconnects
  (`could not fetch <blob> from promisor remote` / `early EOF`), and each failed
  attempt leaves a multi-GB `tmp_pack_*` in `.git/objects/pack/` (filled the disk
  once — delete them to reclaim). The objects genuinely NEW in the commit are only
  ~24 (all local: `git rev-list --objects HEAD --not origin/main`). Reliable
  workaround: **disable the partial-clone extension for the push** so git fails
  fast naming the one boundary blob it needs instead of bulk-backfilling, then
  `git cat-file -t <oid>` each named boundary blob individually (the promisor
  serves single objects fine), re-enabling the extension only for the fetch. A
  full non-filtered refetch is NOT the fix — it re-downloads the whole history
  (~20 GB) and still disconnects. This is an environment limitation, not a
  pack-size 413.
