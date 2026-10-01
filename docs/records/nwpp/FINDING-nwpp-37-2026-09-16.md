# FINDING — NWPP-37: the `NG:` unit-slip screen now runs at the frame seam

**Lane** NWPP-37 · **Base sha** `5a696353` · **Date** 2026-09-16 · **Model** Fable
**PRECOMMIT** `docs/handoffs/PRECOMMIT-nwpp-37-2026-09-16.md` · **No LP run** (nothing to solve)

---

## 1. Result, in three lines

1. **Six** unscreened `NG:`-column readers found, not the desk's dozen — the desk over-counted
   `envelopes` (4 of 7, not 7) and was right to flag `demand.py` for careful classification: **none**
   of its eight sites reads a fuel column. Enumeration table: PRECOMMIT §2.
2. **Shape (A) taken** — the screen moved to the frame CONSTRUCTOR, the three per-reader call sites
   collapsed to one, the false docstring claim repaired. I agree with the desk's position, and the
   deciding argument is measured rather than aesthetic: **the screen is not idempotent**, so (B)
   leaves a live cascade hazard that (A) makes structurally impossible (§7).
3. **Outside the control set, exactly one region moves: SOCO**, and it is an unambiguous defect
   repair (a fuel column exceeding the BA's whole net generation). 1,158 consumer series measured;
   19 move; all 19 are NWPP or SOCO. **ERCOT, CAISO, PJM, NYISO, MISO, NEISO and SPP are
   byte-identical.**

Two defects are **found, measured and ROUTED, not fixed here** — both are threshold questions, and
this lane's charter is the seam only: the pool dilution (§5) and a rule-14 false positive on SOCO
`NG: OIL` that deletes a real cold-snap oil run (§6).

---

## 2. The defect, re-verified at my own base sha

Confirmed exactly as the desk described. Three call sites, all in `actuals.py`;
`frames._eia_hourly_frame_filled` does no screening. The docstring's claim — "no consumer can reach
an unscreened copy" — held only of readers in `actuals`. `0d261bdd` is an ancestor of `5a696353`;
the 22 intervening commits touch no file under `data/eia930`.

---

## 3. What was built

The screen function, its threshold, its two order statistics and its `NG: <CODE>` scope are
**unchanged**. Only the application point moved.

```
_eia_hourly_frame_raw(ba, year)      NEW, private, UNCACHED — the only unscreened constructor
   ├─ pool → _pool_hourly_frame()    (cached separately)
   └─ single BA → parquet slice
_eia_hourly_frame(ba, year)          = _screen_fuel_spikes(_eia_hourly_frame_raw(...))   [cached]
_eia_hourly_frame_filled(ba, year)   fast path: returns _eia_hourly_frame()  → screened
                                     reconstruction: own parquet read → _screen_fuel_spikes()
_ercot_hourly_frame(year)            _eia_hourly_frame_raw → _fill_hourly_frame_from_long → screen
actuals.load_eia_hourly_benchmark    own parquet read → _screen_fuel_spike_columns (KEPT)
```

Deleted as redundant (rule 19): `actuals._ercot_hourly_frame_screened` (5 callers repointed), the
explicit call in `load_eia_hourly_renewable_gen`, and the per-member call in
`build_calibration_reference._eia930_pool_annual_by_fuel`.

**`load_eia_hourly_benchmark` keeps its own application and that is not a second seam.** It reads
the parquet itself because it accepts a year SHORT of 8760 and mean-pads it — a tolerance neither
`frames` loader has. Routing it through `frames` would change what it returns. The honest statement,
now in the docstring, is that the screen runs at every point a frame is *constructed*, and that
there are three such points.

### 3.1 Two things the move broke, found by test, fixed

* **Ordering.** ERCOT's `_fill_hourly_frame_from_long` fills NaN windows from the long-format API
  series. Screening first would have let it **refill the holes the screen had just made** from a
  long series that may carry the same slip. Before this lane the screen ran *after* that fill. The
  `_eia_hourly_frame_raw` split exists to preserve that order exactly; ERCOT is byte-identical.
* **A cache the test suite could not see.** `_eia_hourly_frame_raw` was initially `lru_cache`d; the
  existing tests clear caches *by name*, so a synthetic `SWPP` fixture leaked out of one test class
  into a live-data assertion in another. It is now uncached — the pool branch it delegates to is
  cached on its own, so the cost is at most one extra parquet slice per (BA, year).

Also fixed, one word: `_fill_hourly_frame_from_long` wrote in place into `to_numpy()`'s possibly
read-only view (`ValueError: assignment destination is read-only`). The reordering avoids reaching
it, but the fragility is real and would bite the next lane; `copy=True` cannot change a value.

---

## 4. Frame-level census — what the screen flags, nine regions × 2019-2026

This is the ground truth the exit table rests on. **13 flagged (BA, year, column) series in total.**

| region | years with any flag | columns | verdict |
|---|---|---|---|
| ERCOT | **none** | — | cannot move at any consumer, any year |
| CAISO | **none** | — | cannot move |
| PJM | **none** | — | cannot move |
| MISO | **none** | — | cannot move |
| NEISO | **none** | — | cannot move |
| NYISO | 2024 | `NG: OTH` h6759 (16,117 MW, p99.9 3,290) | SPP-41 control set |
| SPP | 2023 | `NG: WND` h3907 (3,589,445 MW, p99.9 22,597) | SPP-41 control set |
| NWPP | 2024, 2025 | `NG: WAT`, `NG: NG`, `NG: COL`, `NG: OTH` | **the lane's target** |
| SOCO | 2023, 2024, 2025 | `NG: NG` (2025), `NG: OIL` (2023-24) | **new — §6** |

**Five of nine regions carry no flagged hour in any column in any year.** That is a proof of
byte-identity for them under any seam placement, not a sample.

NWPP detail (pooled series): 2024 `NG: WAT` h5723/6707 at 76,472 / 73,452 MW against p99.9 19,533;
2025 `NG: WAT` h6817/6818/6875 at 817,202 / 197,283 / 109,058 MW against p99.9 23,358. Pooled hydro
2025: **111.4407 → 110.3171 TWh**.

---

## 5. ROUTED #1 — the pooled screen is diluted, and misses real artifact hours

On a POOL frame the statistics are the *pooled* series', so a member slip the footprint sum dilutes
below 2.5× the pool's own p99.9 is not flagged. Measured, pooled-screen hits vs per-member-screen
hits on NWPP `NG: WAT`:

| year | pooled catches | per-member catches | **missed by pooled** |
|---|---|---|---|
| 2024 | h5723, 6707 | + h5556, h7603 | NWMT 1,782 / 5,939 MW |
| 2025 | h6817, 6818, 6875 | + h6874, h7236, h8052 | NWMT 32,416 / 17,162 / 29,149 MW |

The 2025 misses are decisive: **NWMT posting 32,416 MW of hydro is many times that BA's entire
hydro fleet**, and it lands at 1.83× the pooled anchor — under the 2.5× bar purely by dilution.
Pooled recovers 1.124 TWh of the 1.169 TWh artifact, **96 %**; per-member would recover all of it.

**Why I did not do it here.** Screening per member re-bases the statistic on a per-member
population. That is a *threshold* change, and the charter is explicit: "the SEAM ONLY: you change no
threshold, no statistic and no per-region branch." It is also not free — on the same measurement the
per-member screen additionally flags **PGE `NG: OTH` 119 MW (2023 h732)** and **NWMT `NG: WAT`
1,782 MW (2024 h5556)**, neither of which is obviously an artifact. Deciding that needs the same
kind of evidence §6 needs, and it is one decision, not two.

Note for whoever takes it: `build_calibration_reference` **already** sums NWPP per member precisely
to get the per-member screen, and documents why. So the two paths currently disagree by design —
the reference builder is per-member, the pool frame is pooled. That inconsistency is the real
finding here.

---

## 6. ROUTED #2 — SOCO `NG: OIL`: the screen deletes a REAL cold-snap oil run (rule 14)

**Pre-existing, not introduced by this lane** — SOCO `NG: OIL` already reached the committed
benchmark through `load_eia_hourly_benchmark`. Surfaced because this lane censused the regions
SPP-41 could not (SOCO and NWPP were registered a week after it measured).

SOCO 2024 h386-392 is **2024-01-17 03:00-09:00, Winter Storm Heather**:

| hour | local time | `NG: OIL` MW | `Net generation` MW | `Demand` MW |
|---|---|---|---|---|
| 385 | 02:00 | 155 | 41,106 | 41,011 |
| 386 | 03:00 | **530** | 41,028 | 41,297 |
| 388 | 05:00 | **660** | 43,833 | 43,557 |
| 390 | 07:00 | **762** | 47,065 | 47,368 |
| 391 | 08:00 | **801** | 47,123 | 47,209 |
| 392 | 09:00 | **350** | 45,178 | 45,293 |
| 393 | 10:00 | −3 | 42,875 | 42,813 |

That is a coherent peaker start, ramp and shutdown tracking SOCO's winter peak hour for hour. 801 MW
against 47,123 MW of net generation is entirely possible. **The screen fires only because a
near-zero-baseline series has no operating scale**: median 0.0 MW, p99.9 71.7 MW, so the "robust
peak" it tests against is meaningless. 4.4 GWh of real generation is deleted (0.0056 → 0.0012 TWh).

This is the fuel-column analogue of the CHPD cold-snap failure `frames._pool_hourly_frame` already
documents for the DEMAND spike screen — and it is the same failure mode the screen's own docstring
warns about for partial years. A fix needs a floor on the anchor, or a minimum-baseline eligibility
test; both change the statistic. **Routed.** Recorded in the screen's docstring so it cannot be
rediscovered as a surprise.

For contrast, the SOCO `NG: NG` flags are unambiguous: **70,683 MW of gas in an hour whose whole
`Net generation` is 32,574 MW.** A single fuel cannot exceed the total. Four such hours in 2025.

---

## 7. The screen is NOT idempotent — measured

Re-applying the screen to an already-screened series recomputes the p99.9 with the flagged hours
gone, which **lowers** the anchor and can flag more. Over all 17 NWPP members plus the nine regions,
2019-2026, a second pass takes three further hours:

| series | hour | MW |
|---|---|---|
| PGE 2023 `NG: OTH` | h2233 | 81 |
| NEVP 2025 `NG: NG` | h2507 | 20,354 |
| SOCO 2024 `NG: OIL` | h385 | 155 — **the first hour of the Heather ramp in §6** |

This is why the redundant applications had to be deleted rather than left stacked, and it is the
argument that decided shape (A) over (B). Pinned by
`test_re_reading_the_frame_does_not_cascade`.

---

## 8. EXIT TABLE — nine regions, before vs after

**1,158 consumer series** captured per region × year (benchmark per fuel, delivered renewable
profile, monthly hydro, hydro envelope, hydro min-flow, gas floor, interchange envelope, demand,
plus the CAISO solar fraction and six net-interchange series). Series signature = length, sum, min,
max and a SHA-256 of the array.

**19 moved. All 19 are NWPP or SOCO.**

| region | years | series moved |
|---|---|---|
| ERCOT, CAISO, PJM, NYISO, MISO, NEISO, SPP | all | **0 — byte-identical** |
| NWPP | 2024 | `hydro_month` −149,924 MWh · `hydro_env` −68,764 · `hydro_minflow` −1.1 · `gas_floor` −4,530 |
| NWPP | 2025 | `hydro_month` **−1,123,543 MWh** · `hydro_env` −27,671 · `hydro_minflow` −7.8 · `gas_floor` −3,028 |
| NWPP | 2019-22, 2026 | `hydro_env` −31,042 · `hydro_minflow` −0.2 (identical in each: these years have no NWPP extract and read the **climatology** over 2023-25, so they inherit the 2024/25 repair — correct propagation, one mechanism) |
| SOCO | 2025 | `gas_floor` −19,759 MWh |

**Against the charter's control set.** The charter named SPP 2023 wind and NYISO 2024 other as
expected movers. They do **not** move, and that is correct: that set is the control for *introducing*
the screen (SPP-41), and both reach their consumers through `load_eia_hourly_benchmark` /
`load_eia_hourly_renewable_gen`, which were **already** screened. This lane relocates the screen, so
its effect is disjoint from SPP-41's by construction: exactly the previously-unscreened readers.

**The one region outside the control set that moves is SOCO**, via `measured_gas_floor_profile`
reading `NG: NG`. It is a defect repair (§6, fuel > total). Its only model consumer,
`interchange/caiso.py::inject_caiso_gas_commitment_floor`, returns early unless `iso == "CAISO"`, so
**no SOCO solve path reads it today** — the moved series is real and is reported at full magnitude,
but it changes no dispatch.

Shape (A)'s pre-registered condition is met: no pre-existing region moves, and the one new mover is
named and shown to be a repair.

### 8.1 Committed benchmarks do not move

`load_eia_hourly_benchmark` was already screened, so every committed `bench/<ISO>/<year>.json.gz`
is unchanged and **no registered keeper's C1/C4 score moves**. Confirmed by the zero-move rows
above. `cache_key()` is not affected either: `data/eia930` is not in
`config/solve_surface.SURFACE_MODULES` (`check_cache_key_registration.py`: "305 solve-surface names
across 7 module(s), all declared"), and data has never been in the key.

---

## 9. ROUTED #3 — two committed derived artifacts carry the artifact hours today

`scripts/` derive scripts read the same seam, so they inherit the repair on their **next legitimate
re-derive** (rule 23 `[R-FROZEN-DERIVE]`: a re-derive needs a source-data change, so nothing moves
now). Measured, what would move:

| script | series | before → after |
|---|---|---|
| `scripts/lib/wind_shape.py` (SPP wind shape) | SWPP 2023 `NG: WND` | 106.6345 → 103.0450 TWh |
| `scripts/data/build_nwpp_hydro_budget.py` | NWPP member `NG: WAT` 2024 | −139,492 MWh |
| `scripts/data/build_nwpp_hydro_budget.py` | NWPP member `NG: WAT` 2025 | **−1,178,411 MWh** |

Read the other way: **the committed SPP wind shape and the committed NWPP hydro budget were built
from unscreened series and carry these artifacts now.** Every other derive script reads only ERCOT /
CAISO / PJM / MISO / NEISO, which §4 proves clean, or a non-fuel column. Routed to the desk as a
re-derive decision, not taken here.

`build_calibration_reference`'s own output is **byte-identical**: its per-member screen and the
constructor's use the same series and the same statistics, so removing the explicit call changes
nothing — verified directly, 0 mismatches over all 17 NWPP members × `NG:` columns × 2023-2025.

---

## 10. Tests and gates

* `tests/unit/data/test_eia930_fuel_spike_screen.py`: **18 pass** (was 12). New:
  `TestScreenOnTheEnvelopePath` (4 tests — monthly hydro, hydro envelope + min-flow, gas floor, and
  a pin that `_eia_hourly_frame_raw` is the ONLY unscreened door), plus
  `test_the_frame_loader_itself_returns_the_repair`, `test_re_reading_the_frame_does_not_cascade`
  and `test_the_pool_cache_is_not_written_through`.
* **One existing test was rewritten, deliberately**: `test_the_cached_frame_is_not_mutated` asserted
  that `_eia_hourly_frame_filled` returns the RAW spike — it pinned the defect. Its real invariant
  (a repair is never written back into a cache) survives as
  `test_the_pool_cache_is_not_written_through`.
* `tests/unit/data` + `tests/regression`: **2,713 pass, 35 fail**. The same 35 fail at base sha
  `5a696353` with this change stashed — node-ID lists diffed and **identical**. This lane introduces
  no failure and fixes none.
* `ruff check` + `ruff format --check`: clean. `check_cache_key_registration.py`: ok.
  `check_mechanism_matrix.py`: no new warning (the NYISO keeper-stamp and anchor-drift warnings are
  pre-existing and belong to other lanes).
* **No matrix row and no cell edit**: this is a data repair, not a mechanism; no `ScenarioConfig`
  field is added, so rule 28(c) does not fire.

---

## Log entry

**NWPP-37 (2026-09-16, base `5a696353`) — EIA-930 `NG:` unit-slip screen moved to the frame
constructor.** Desk r#7b diagnosis confirmed; enumeration refined: **six** unscreened fuel-column
readers, not a dozen — `envelopes` ×4 (`measured_monthly_hydro`, `_hydro_wat_month_hod`,
`measured_gas_floor_profile`, `caiso_solar_fraction`) and `neighbor_price` ×2; `envelopes`' other
three read `Total interchange` (outside the screen by ruling) and **all eight `demand.py` sites read
`Demand` alone**. Shape **(A)** taken — screen applied at `frames._eia_hourly_frame`,
`_eia_hourly_frame_filled`'s reconstruction and `actuals.load_eia_hourly_benchmark` (its own parquet
read); the three per-reader call sites collapsed to one; `_ercot_hourly_frame_screened` deleted; the
false rule-19 docstring claim repaired. Deciding argument: the screen is **not idempotent** (a second
pass flags 3 more hours), so (B) would leave a live cascade. Exit: **1,158 consumer series, 19 moved,
all NWPP or SOCO**; ERCOT/CAISO/PJM/NYISO/MISO/NEISO/SPP byte-identical, and five of nine regions
carry **no flagged hour in any year** — a proof, not a sample. NWPP 2025 pooled hydro
111.4407 → 110.3171 TWh (`measured_monthly_hydro` −1.124 TWh); 2019-22/2026 move only through the
climatology. SOCO is the one mover outside the control set: `measured_gas_floor_profile`,
−19,759 MWh, an unambiguous repair (`NG: NG` 70,683 MW in an hour whose whole `Net generation` is
32,574 MW) with no model consumer today. Committed benchmarks and keeper scores unchanged; no cache
re-key. Tests 18/18 in the screen file; 2,713 pass / 35 fail across `unit/data`+`regression`, the
same 35 failing at base sha. **Three items ROUTED, none fixed here (all threshold questions, charter
is seam-only):** (1) the pooled screen is **diluted** — it misses 2 of 4 NWPP `NG: WAT` artifact
hours in 2024 and 3 of 6 in 2025, incl. NWMT at 32,416 MW, recovering 96 % of the artifact, while
`build_calibration_reference` already screens per member, so the two paths disagree by design;
(2) **SOCO `NG: OIL` is a rule-14 false positive** — the screen deletes a real Winter Storm Heather
oil ramp (2024-01-17 03:00-09:00, 155→801 MW tracking a 41→47 GW demand ramp), 4.4 GWh, because a
near-zero-baseline series has a meaningless p99.9 of 71.7 MW; pre-existing, in the committed
benchmark; (3) the **committed SPP wind shape and NWPP hydro budget carry artifact hours** today
(SWPP 2023 wind 106.6345 vs 103.0450 TWh; NWPP member hydro −1.178 TWh in 2025) and would change on
their next re-derive.
