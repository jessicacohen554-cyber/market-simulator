# FINDING — NWPP-39: the zero-baseline guard on the EIA-930 `NG:` unit-slip screen

**Lane** NWPP-39 · **Base sha** `a9950612` · **Date** 2026-09-16 · **Model** Fable
**PRECOMMIT** `docs/handoffs/PRECOMMIT-nwpp-39-2026-09-16.md` (committed as `166b8b24` before the
screen was edited and before the nine-region measurement was taken) · **No LP run**
**Branch** the harness-designated `claude/tender-edison-9nu5h8` (as NWPP-37b's was), not the charter's
stem — stated so the record is not searched for a branch that does not exist.

---

## 0. Report first

1. **How the guard was derived — a construction, in my own words.** The screen's peak limb rests on
   one premise: the top of a legitimate fuel series is a *plateau*, so no hour can sit 2.5× above the
   ninth-largest. That premise needs the ninth-largest hour to lie inside the occupied top regime. The
   guard tests the anchor by **the screen's own premise, one decade of rank coarser**: if the p99.9
   (rank ≈ 9) is itself more than 2.5× the p99.0 (rank ≈ 88), the series' top is a tail, not a
   plateau; the limb's premise is falsified by the series itself, and the column passes through
   untouched — the existing `peak <= 0` sentence extended from *not positive* to *not a plateau
   level*. No new factor (2.5 is `_FUEL_SPIKE_RATIO`, the demand screen's by import); the rank is the
   decade step the screen already took from the maximum to the p99.9, taken once more
   (100 − 10 × (100 − 99.9) = 99.0); it is a ratio of two order statistics of the same series, so it
   reads no MW level, no other column, no other BA and no residual. **No other rank and no other
   factor was tried, before or after reading the data.** What I read before fixing it, and why that is
   not fitting, is in §2.2.
2. **SOCO `NG: OIL` is restored.** 2024 benchmark `oil` 0.0017 → **0.0056 TWh** (the frame-level
   sum NWPP-37 §6 quoted, 0.0012 → 0.0056); h386–392 carry the filed 530 / 649 / 660 / 687 / 762 /
   801 / 350 MW. The 2023 series is restored too (one hour, h7975 = 2023-11-29 08:00, a
   146 → 390 → 100 MW morning start on a 33 → 38 GW demand ramp), which NWPP-37 §4 had listed as a
   flag but not examined.
3. **Both known artifacts are still caught.** SWPP 2023 `NG: WND` h3907 (ratio 1.060) and NYIS 2024
   `NG: OTH` h6759 (ratio 1.051) are NaN after the screen; the SPP 2023 wind benchmark still reads
   103.0488 TWh and the NYISO 2024 other benchmark 3.3197 TWh — the existing live pins pass unchanged.
   Every NWPP member slip (AVA `NG: OTH` / `NG: WAT`, NWMT `NG: COL` / `NG: WAT`, ratios 1.02–1.06)
   and SOCO 2025 `NG: NG` (1.087) is still repaired.
4. **Nine regions × 2019–2026, 1,779 signatures: 7 move, all in the four series the PRECOMMIT
   predicted; every released hour classified *restores real data*; no STOP fired.** ERCOT, CAISO,
   PJM, NYISO, MISO, NEISO and SPP are byte-identical at every frame, every member, every benchmark
   series and every delivered renewable profile.

## 1. The defect, re-verified at base sha

Reproduced NWPP-37 §6 exactly from the committed `SOCO hourly.parquet`: 2024 `NG: OIL` median 0.0 MW,
p99.9 71.727 MW, 285 positive hours of 8,752, 28 hours ≥ 50 MW, 8 hours ≥ 100 MW; the unguarded
screen flags h386–392 (7 hours, max 801 MW) and deletes 4,439 MWh. The same fleet's 2025 series has
p99.9 = 851 MW — it ran ≥ 9 hours above that level — and the screen flagged nothing there. Whether a
real peaker start was deleted depended on whether the event lasted nine hours.

## 2. What was built

### 2.1 The guard

`actuals.py`: one derived constant, `_FUEL_SPIKE_PLATEAU_PCT = 99.0` (the derivation in its comment
and pinned by test), and one condition inside `_screen_fuel_spike_columns`, after the existing
`peak <= 0` pass-through:

```
plateau = p99.0(series)
if peak > _FUEL_SPIKE_RATIO * plateau:   # the anchor is itself a "spike" at the coarser rank
    continue                             # no operating scale — the column passes through
```

`plateau = 0` under a positive `peak` (the top 1 % is idle — the IPCO / NEVP oil case) falls out of
the inequality with no branch. The guard can only *release* a column; it can never flag an hour the
unguarded screen would not. `frames.py` is untouched: the seam does not need to know.

### 2.2 What was read before the construction was fixed, stated plainly

Before writing the PRECOMMIT I computed a census of every `NG:` series on disk (26 extracts ×
2019–2026 × every fuel column: 737 series, 687 with a positive p99.9) — median, p95, p99, p99.9,
max, positive-hour fraction and the current screen's flag count — and I read from it where the
population sits relative to the plateau test. I did **not** choose the rank or the factor from that
census: the factor was fixed by import before the census existed, and the rank is the decade step.
The census told me what the guard *would* do (§3) so the PRECOMMIT could predict it, which is the
opposite of fitting: a prediction that could have been wrong, written down before the measurement.
Four alternative constructions were rejected on principle, not on what they flag (PRECOMMIT §2.3):
a MW floor (a magic number, not scale-invariant between a 200 MW PUD member and a 47 GW BA);
`median > 0` as eligibility (releases every solar series); a minimum positive-hour fraction (a new
free number); the anchor against the median (the docstring already proves that is not a scale).

## 3. The population, and where the guard is active

Ratio `p99.9 / p99.0` over the 687 screenable series: median **1.066**, p90 1.337, p95 1.915. The
26 series above 2.5 are, with two exceptions, rarely-run `NG: OIL` fleets (FLA, NYIS, ISNE, SWPP,
SOCO, PJM 2022) and sub-10-MW idle series (IPCO / NEVP / PSEI `NG: OIL`, CISO `NG: COL`, SOCO
`NG: OES`); the two exceptions are ERCO `NG: OTH` 2019 and 2025 (§7). Of the **21 series the
unguarded screen flags**, the guard is active on exactly four:

| series | p99.0 | p99.9 | ratio | flagged hours (unguarded) | max |
|---|---:|---:|---:|---|---:|
| SOCO 2023 `NG: OIL` | 22.41 | 88.24 | 3.94 | h7975 | 390 MW |
| SOCO 2024 `NG: OIL` | 25.00 | 71.73 | 2.87 | h386–392 | 801 MW |
| IPCO 2024 `NG: OIL` | 0.00 | 2.24 | ∞ | h298 | 6 MW |
| NEVP 2024 `NG: OIL` | 0.00 | 1.00 | ∞ | h82 | 3 MW |

The other 17 flagged series sit at ratios 1.020–2.357 and are byte-identical: SWPP 2023 `NG: WND`
(1.060), NYIS 2024 `NG: OTH` (1.051) and 2026 (1.148), AVA 2024/2025 `NG: OTH` and 2025 `NG: WAT`
(1.039–1.064), NWMT 2024/2025 `NG: COL` / `NG: WAT` (1.020–1.024), NEVP 2024/2025 `NG: NG` (1.863 /
1.305), SOCO 2025 `NG: NG` (1.087), PGE 2023 `NG: OTH` (**2.357 — below the bar; NWPP-37b's
reported-not-adjudicated flag stands exactly as that lane left it**), and FLA 2023/2024 `NG: OTH` /
`NG: SUN` (1.10–1.25; FLA is a proxy BA in `interchange/spec.py`, not a registered region).

## 4. EXIT TABLE — nine regions, every series that moves against NWPP-37 / 37b's post-state

Method: for every region × 2019–2026, every `NG:` column of the region frame
(`_eia_hourly_frame_filled`; the NWPP pool; the ERCOT filled frame; all 17 NWPP member frames as
`_pool_member_frames` returns them), every `load_eia_hourly_benchmark` series, every
`load_eia_hourly_renewable_gen` series, `measured_monthly_hydro` and `measured_gas_floor_profile` —
length, NaN count, nansum and a SHA-256 of the array bytes, captured before the edit (commit
`166b8b24`, the PRECOMMIT) and after. **1,779 signatures.**

| region | signatures | moved | series that move |
|---|---:|---:|---|
| ERCOT | 221 | **0** | — byte-identical |
| CAISO | 164 | **0** | — |
| PJM | 157 | **0** | — |
| NYISO | 157 | **0** | — |
| MISO | 151 | **0** | — |
| NEISO | 182 | **0** | — |
| SPP | 165 | **0** | — |
| NWPP | 495 | **3** | 2024 pool frame `NG: OIL` +6 MWh (380,800 → 380,806); member IPCO `NG: OIL` −59.5 → −56.0 MWh; member NEVP `NG: OIL` 20.5 → 23.0 MWh |
| SOCO | 87 | **4** | 2023 frame `NG: OIL` 824 → 1,214 MWh (NaN 1 → 0) and benchmark `oil` 947 → 1,214 MWh; 2024 frame `NG: OIL` 1,173 → 5,612 MWh (NaN 15 → 8, the 8 being filed gaps) and benchmark `oil` 1,696 → 5,603 MWh |

Every one of the 7 is one of the four predicted series; nothing unpredicted moved. The NWPP
benchmark `oil` does not appear because `load_eia_hourly_benchmark("NWPP", ·)` is `None` by
construction (the pool code names no file); the pool's `NG: OIL` reaches consumers through the frame
only, and no reader consumes `NG: OIL` from a frame today (the only `NG: OIL` reader in `src/` is the
benchmark). Every moved series is reported at full magnitude regardless.

### 4.1 Classification of every released hour (PRECOMMIT §4.2, S1 / S2 / S3)

| hour | local time | value | BA net gen | neighbours | S1 fuel > total | S2 ≥ 10× both neighbours | S3 gap within ±1 h | class |
|---|---|---:|---:|---|---|---|---|---|
| SOCO 2023 h7975 | 2023-11-29 08:00 | 390 | 37,586 | 146 / 100 | no | no | no | **restores real data** |
| SOCO 2024 h386 | 2024-01-17 03:00 | 530 | 41,028 | 155 / 649 | no | no | no | restores real data |
| SOCO 2024 h387 | 04:00 | 649 | 41,982 | 530 / 660 | no | no | no | restores real data |
| SOCO 2024 h388 | 05:00 | 660 | 43,833 | 649 / 687 | no | no | no | restores real data |
| SOCO 2024 h389 | 06:00 | 687 | 45,729 | 660 / 762 | no | no | no | restores real data |
| SOCO 2024 h390 | 07:00 | 762 | 47,065 | 687 / 801 | no | no | no | restores real data |
| SOCO 2024 h391 | 08:00 | 801 | 47,123 | 762 / 350 | no | no | no | restores real data |
| SOCO 2024 h392 | 09:00 | 350 | 45,178 | 801 / −3 | no | no | no | restores real data |
| IPCO 2024 h298 | 2024-01-13 11:00 | 6 | 1,882 | 3 / 2 | no | no | no | restores real data (a 3 / 6 / 2 MW three-hour ramp, integer-MW resolution) |
| NEVP 2024 h82 | 2024-01-04 11:00 | 3 | 4,287 | 0 / 1 | no | no | no | restores real data (a 3 / 1 MW two-hour ramp) |

**Zero re-admitted artifacts. No STOP.** The two SOCO events are coherent starts tracking the BA's
own demand ramp (2024: 41.0 → 47.4 GW, the Heather winter peak; 2023-11-29: a 33 → 38 GW morning
ramp); the IPCO / NEVP hours are MW-scale readings of a fleet that is otherwise off, and a unit slip
is a decade mis-scaling of a real value — 6 MW between 3 and 2 is not a decade off anything.

### 4.2 Committed benchmarks, keepers, cache keys

SOCO has no keeper and no committed `bench/SOCO/*.json.gz`; NWPP has no keeper. No registered
keeper's C1/C4 score can move (the seven pre-existing regions are byte-identical on every benchmark
series). `cache_key()` is unaffected: `data/eia930` is not in `config/solve_surface.SURFACE_MODULES`
(`check_cache_key_registration.py`: "305 solve-surface names across 7 module(s), all declared").

## 5. Interaction with the routed items — stated, not absorbed

* **Pool dilution (NWPP-37 §5).** Taken by NWPP-37b, which screens each NWPP member on its own
  population before the sum. The guard is evaluated on whatever population the caller hands the
  screen — member or pool — and changes nothing about that choice. Measured consequence: the guard
  fires on two *member* series (IPCO, NEVP `NG: OIL` 2024, one MW-scale hour each) that only exist as
  screened populations because of 37b; on the pooled 2024 `NG: OIL` series the unguarded screen
  flagged nothing (the pool's oil column is plateau-topped), so the pool moves by exactly the two
  members' released hours, +6 MWh. Rule 19 holds: one mechanism per phenomenon, and neither lane's
  mechanism does the other's job.
* **NWPP-37b's two reported-not-adjudicated member flags.** PGE 2023 `NG: OTH` (ratio 2.357) and
  NWMT 2024 `NG: WAT` (1.024) are both below the bar: **unchanged**, still awaiting the desk's
  adjudication on the BAs' fleet data. This lane does not pre-empt it.
* **The demand-side CHPD cold-snap failure** (`frames._pool_hourly_frame`) is the same failure mode
  in `_screen_demand_spikes`, a different phenomenon; not touched (rule 19), as the charter set out.

## 6. What the guard gives up, stated

A series whose top is a tail is not screened at all, so a future unit slip in such a series passes
through. The 26 guard-active series today carry **no** hour the unguarded screen was catching
*reliably*: on a tail-topped series the p99.9 is not a level, so the unguarded screen could not tell
a slip from an operating event either (the SOCO 2024 vs 2025 asymmetry in §1 is the proof). Nothing
that was a reliable repair is lost.

## 7. ROUTED — two ERCO `NG: OTH` years carry a ≥ 9-hour run the screen cannot see, with or without the guard

The census surfaced the two non-oil guard-active series: ERCO `NG: OTH` **2019** (p99.9 22,972 MW
against p99 122 MW: **24 consecutive hours of 2019-12-18 at 23–27 GW**, in a series whose normal
level is ~20–120 MW — ~40 % of the whole ERCOT system posted as "other", an artifact run by
inspection) and **2025** (p99.9 3,801 vs p99 118: 44 hours between 2025-12-06 and 12-14 up to
5,716 MW, in an extract whose December is not yet a scored year). In both, the run is longer than the
anchor's rank, so the p99.9 *is* the run and the unguarded screen flagged nothing — the "run of four
or more consecutive slip hours" limit the docstring already states. The guard changes nothing there
(0 flags either way; byte-identical). It is a different defect (a *run* screen would need its own
construction, and its own evidence), so it is routed, not fixed: 2019 is outside every ERCOT
keeper's years and the benchmark `other` series for ERCOT 2019 carries it today.

## 8. Tests and gates

* `tests/unit/data/test_eia930_fuel_spike_screen.py`: **35 pass** (was 26 on this host; +9).
  New `TestZeroBaselineGuard` (5): the unguarded limbs would flag the Heather-shaped synthetic run
  (the pin is load-bearing) and the guard's condition holds on it; the run survives on the benchmark
  and frame paths; the guard is per column — the SWPP-style wind slip in the same frame is still
  repaired in the same pass; a plateau-topped peaker with median 0 is still screened (the test is the
  plateau, never the median); an idle top percentile is the same case with no branch.
  `TestScreenIsParameterFree` +1: the plateau rank is one decade below the anchor's, derived.
  `TestZeroBaselineGuardLivePins` (3, `fulldata`): SOCO 2024 h386–392 are the filed values and the
  benchmark reads 0.0056 TWh; SOCO 2023 h7975 = 390 MW; SWPP 2023 h3907 and NYIS 2024 h6759 are
  still NaN.
* `tests/unit/data` + `tests/regression`: **2,782 pass, 15 fail, 24 skipped** (177 s, `-n auto`). The same 15 fail at base sha
  `a9950612` with this lane's two files reverted — node-ID lists diffed and **identical**
  (`test_soundness` end-to-end ×6, `test_key_provenance_exceptions` ×3, the gas-offer zonal
  anchor vintage ×2, the CAISO ST-gas peak registry pin, the ERCOT fleet-arrays golden, the NYISO
  solve-surface fingerprint pin, `test_cached_results_load_cleanly`). This lane introduces no
  failure and fixes none; none of the 15 touches `data/eia930`.
* `ruff check` + `ruff format --check`: clean. `check_cache_key_registration.py`: ok.
  `check_mechanism_matrix.py`: no new warning (the `startup_co2_reporting` anchor and the NYISO
  keeper-stamp warnings are pre-existing and belong to other lanes).
* **No matrix row, no cell edit, no `ScenarioConfig` field, no CLI flag**: a correction to a data
  repair is not a mechanism; rule 28(c) does not fire.

## 9. Rules

**14 `[R-ACCURATE]`** — the whole charter: a screen that deleted a documented weather event was
burying measured data; the measured data is kept and the screen's own construction is what was
repaired. **1 `[R-STRUCT]`** — the guard is derived from what makes an order statistic a scale
estimator, never from which hours it saves; no rank or factor was swept; the census-read predictions
were written before the measurement. **13 `[R-MEASURED]`** — two order statistics of the same
series, regenerating for any forward year from its own extract, reading no residual. **19
`[R-ONE-MECH]`** — one screen, one seam, one guard inside it; the demand screens and the pool
population question untouched. **24 `[R-REGISTRY]`** — nothing tunable: the factor by import, the
rank derived. **27 `[R-PUSH]`** — `actuals.py` (751 lines) and the test file (712) edited locally
with the Edit tool and pushed as on-disk bytes; fetch-back verified after the push. **28(c)** — no
field, no row. **31 / 32 / 34** — no solve, nothing to retain, nothing to shard.

## Log entry

*(appended verbatim to `docs/calibration-log/nwpp.md` by the NWPP ADDITION DESK — plan §8.0 rule 1;
this lane did not write it into that file.)*

## nwpp-39 — 2026-09-16 — zero-baseline guard on the NG: unit-slip screen (owner ruling N13, zero-LP)

Fable, base a9950612, PRECOMMIT + FINDING `docs/handoffs/*-nwpp-39-2026-09-16.md`. No solve, no
field, no matrix row. Repairs the rule-14 false positive NWPP-37 §6 measured and routed: the screen
deleted SOCO's Winter Storm Heather oil start (2024-01-17 03:00-09:00, 530→801→350 MW on a 41→47 GW
demand ramp, 4.4 GWh) because a near-zero-baseline series' p99.9 (71.7 MW) is not an operating
scale. Guard CONSTRUCTED, not fitted: the anchor must pass the screen's own premise at one decade
coarser rank — if p99.9 > 2.5 × p99.0 (`_FUEL_SPIKE_PLATEAU_PCT` = 100 − 10 × (100 − 99.9)) the
series' top is a tail, not a plateau, and the column passes through, extending the existing
`peak <= 0` pass-through; no new factor, rank derived, scale-invariant, release-only. Population:
687 series, ratio median 1.066 / p95 1.915; 26 guard-active (rarely-run oil fleets, sub-10-MW idle
series, two ERCO OTH years with a lifted anchor). Exit over nine regions × 2019-2026, 1,779
signatures: **7 move, all in the four predicted series** — SOCO `NG: OIL` 2023 (h7975, 390 MW,
a 2023-11-29 morning start) and 2024 (Heather; benchmark oil 0.0017→0.0056 TWh), and one MW-scale
hour each in IPCO / NEVP `NG: OIL` 2024 (pool +6 MWh); ERCOT/CAISO/PJM/NYISO/MISO/NEISO/SPP
byte-identical. Every released hour classified restores-real-data under the pre-registered
S1/S2/S3 rule; **zero re-admitted artifacts** — SWPP 2023 wind h3907 (ratio 1.060) and NYIS 2024
other h6759 (1.051) still repaired, every NWPP member slip still repaired, PGE 2023 OTH (2.357)
untouched for the desk's adjudication. Tests 35/35 in the screen file (+9). Routed: ERCO `NG: OTH`
2019 carries a 24-hour 23-27 GW artifact run (2019-12-18) longer than the anchor's rank, invisible
to the screen with or without the guard — a run-screen question, not this lane's.
