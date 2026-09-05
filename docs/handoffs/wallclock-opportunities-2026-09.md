# Wall-clock opportunities — per-year solve path, re-audited at HEAD (2026-09-05)

**STATUS: ASSESSMENT.** Session `claude/model-performance-optimization-vk1qgv`, main @
`4d4dc6ce`. Scope: decrease the wall-clock of solving a backcast/forecast year **without
changing the underlying math** — the LP, its objective, bounds and rows are untouched by
everything below; each lever is classed by the strongest identity claim it can make.

This extends the PERF-A/PERF-B lineage (`wallclock-efficiency-plan-2026-07.md`,
`wallclock-baseline-2026-07.md`, `perf-recheck-2026-08.md`, the PERF-B session 2/3
findings) and does **not** re-open anything those closed: threads, PAMI, IPM+crossover,
Dantzig pricing, LEAN scaling, `compute_monthly_markup`, the basis LUT, the basis-export
gate, C-1a/C-1b and the forecast cross-year flip are all disposed there and are not
re-run here. Every number below was measured in this session on the standard 4 vCPU /
15 GB box (6 GiB swapfile armed, HiGHS 1.14.0, `uv.lock` env) unless it cites a prior doc.

## 0. Headline

Two classes of lever remain, and they are of comparable size:

1. **Byte-identical data-layer and results-layer fixes worth ~110–130 s per NEISO year
   (≈45 % of a 272 s NEISO year) and ~70 s of every ERCOT invocation's first year.** A
   cProfile of the NEISO keeper year attributes them to four sites: openpyxl parsing of
   the 21 MB eGRID workbook three times per process (~54 s), a per-plant pandas loop in
   the EIA-860 COD map (~17 s real / 51 s profiled — **prototyped vectorized: 0.41 s,
   dict-identical**), and a 6.7 M-call Python function inside a hourly sidecar writer
   that runs *after* the year's phase-timing line and is therefore invisible to every
   wall-clock table on record (~21 s/yr). None touches the LP.
2. **A warm-start-class lever on the cold-P1 route worth most of a P1 solve per pass on
   ERCOT, NYISO and CAISO.** Every keeper with a P1-native floor bridge (ERCOT gas
   bridge, NYISO gas bridge, CAISO RA must-offer) cold-rebuilds a second `DispatchModel`
   for P1 and solves it **with no starting basis at all**, even though the P0 model of
   the same year has an identical column/row layout and an optimal basis in hand. The
   in-place refloor (C-4) was refuted because availability feeds reserve/ramp *rows*;
   seeding the second model with the P0 basis needs no in-place edit and is exactly the
   `apply_cross_year_basis` machinery already shipped for adjacent years. Measured on the
   ERCOT forward keeper config, 2025: see §3.

Both classes are additive. The first is gateable at `atol=rtol=0` with zero LP solves
(the COD map is a dict equality; the sidecar is a frame equality). The second is the
documented marginal-tie class (`docs/cross-year-warmstart.md`) and needs the plan-§6
owner memo before any default flips — this document supplies the measurement that memo
was waiting for.

## 1. Where a year's wall goes today (NEISO keeper `neiso-99`, 2023, determinism pin)

Replayed through the keeper recipe (`capture_keeper_goldens.build_solve_kwargs`) under
cProfile into a scratch dir (never a golden, never registered):

| phase | s | share of 272 s process wall |
|---|---:|---:|
| `data_prep` | 125.5 | 46 % |
| `solve_p0` (cold, 1 thread) | 79.7 | 29 % |
| `solve_p1` (warm) | 29.7 | 11 % |
| `markup` residual | 3.5 | 1 % |
| `results_write` | 4.9 | 2 % |
| **after the timing line** (hourly sidecars + post-loop) | **28.4** | **10 %** |

The phase line says `total=243.3s`; the process spent 271.7 s. The 28 s gap is the
sidecar block that runs after `log_year_phase_timing` in `solve_and_persist` — it is
booked to no phase and no prior table includes it. **The data layer, not HiGHS, is the
majority of a NEISO year**, which is the "118–190 s `data_prep` anomaly" PERF-B flagged
as unattributed; the profile attributes it:

| site | profiled cum. s | what it is |
|---|---:|---|
| `fleet/eia860.py::_egrid_boundary_hr_repairs_for` | 36.2 | `pd.read_excel` of eGRID `PLNT23` + `UNT23` (32.8 s; `UNT23` alone parses 4.6 M cells through openpyxl) |
| `cod_ramp.py::_load_cod_map` | 51.5 | a `for code, grp in work.groupby("pc")` loop — 14,330 groups, each doing `grp.dropna` / `sort_values` / `iloc` on a per-plant DataFrame (43 s of the 51 s is `dropna`) |
| `zone_assignment.py::_plnt23` | 20.9 | `pd.read_excel` of eGRID `PLNT23` (a second parse of the same sheet, different `usecols`) |
| `run_calibration_full.py::_write_class_band_hourly_sidecar` | 21.2 | `[_tranche_band(u) for u in d["unit_id"].astype(str)]` over the 6.7 M-row dispatch frame (14 s) + the per-element function itself (5 s) |
| `run_energy_solve` non-solve | ~5 | marshalling; already at the floor (see §4) |

Everything else in `data_prep` is diffuse pandas work under 3 s per site. These four
sites are **~130 s profiled / ~100–110 s real** of the 154 s the year spends outside
HiGHS and parquet, and all four are per-process, per-invocation costs (the three
loaders are `lru_cache`d, so years 2 and 3 of the same run do not pay them again — which
is exactly why year-1 `data_prep` reads 100–135 s on ERCOT against 35–63 s on warm
years, PERF-B anchor table).

## 2. Byte-identical levers (class A — gate with zero LP solves)

### A-1 · Vectorize `_load_cod_map` — **prototyped, dict-identical, 16.8 s → 0.41 s**

`src/market_sim/data/cod_ramp.py::_load_cod_map`. The per-group loop was rewritten in
this session as one stable sort on `pc` plus numpy slices per group, keeping the
*identical* per-group arithmetic (`np.average`, `floor`, `round`, the `sort_values
(["ry","rm"]).iloc[-1]` tie order reproduced with `np.lexsort`, NaN `rm` last). Result on
the live `data/raw/eia-860` vintage: **14,334 plants, `vec == ref` → `True`**, 16.8 s →
0.41 s unprofiled. The prototype is `scratchpad/proto_vec.py::cod_map_vec` in this
session's transcript; the gate for landing it is the dict equality itself (no solve),
plus the fast tier. Reach: every ISO, every invocation, and **twice on ERCOT** (PERF-A
§2.4: `_load_cod_map` called under two EIA-860 vintage keys). Also removes the
14,330 `dropna` calls that dominate the profile's call count.

### A-2 · Stop parsing eGRID xlsx on the solve path — **~54 s per process**

Three `pd.read_excel` calls per process read the same 21 MB workbook
(`data/raw/fleet-egrid/…xlsx`): `zone_assignment._plnt23` (PLNT23), and
`eia860._egrid_boundary_hr_repairs_for` (PLNT23 again, then UNT23 — the expensive one).
openpyxl's read-only parser is ~10 µs per cell; UNT23 is 4.6 M cells. Two ways to
remove it, both byte-identical by construction (the values read are the same values):

* **(a) Arm the existing `data/clean` seam for eGRID.** `_plnt23` already has a
  `MARKET_SIM_USE_CLEAN` branch that reads `data/clean/egrid/<vintage>` written by
  `scripts/data/curate_egrid.py`; it is default-OFF and the partition is absent in a
  fresh clone. But `_egrid_boundary_hr_repairs_for` has **no clean branch at all**, and
  its UNT23 read is the larger of the two — so arming the seam as-is recovers ~21 s, not
  54 s. The repair reader needs the same branch (and `curate_egrid.py` needs to emit the
  UNT sheet columns `ORISPL, HTIAN, UNTYRONL`).
* **(b) A content-addressed parquet mirror next to the workbook** (`<xlsx>.<sha>.
  <sheet>.parquet`, gitignored, written on first miss) inside a tiny `read_egrid_sheet
  (path, sheet, usecols)` helper both call sites use. Self-invalidating on a workbook
  change, zero configuration, and it makes the July plan's "data/clean is not a
  wall-clock lever" verdict true by removing the only raw-xlsx parse left on the path.

(b) is the smaller change and needs no curation step; (a) is the architecturally
sanctioned route. Either way the gate is `frame.equals` on the three sheet reads.

### A-3 · Vectorize the class-band sidecar and put the sidecar block on the clock — **~21 s/yr**

`scripts/run_calibration_full.py::_write_class_band_hourly_sidecar` re-reads the
per-pass dispatch parquet and maps `unit_id → band` **per row** (6.7 M calls to
`_tranche_band`, plus a 14 s list comprehension). The band is a pure function of
`unit_id`, and the frame has ~1–3 k distinct ids: compute it once per category and index
by the categorical codes. Prototyped in this session on the NEISO 2023 P1 frame (6,718,920 rows): **12.7 s →
2.16 s, categorical element-wise identical, same categories** (§6). Same class as PERF-B change (a) (`Categorical.from_codes`),
which took the *other* sidecars from 10 s to 2 s.

Independently of the fix, **the sidecar writers run after `log_year_phase_timing`** —
`_write_class_hourly_sidecar`, `_write_class_band_hourly_sidecar`, `_write_p0_commitment
_sidecar`, `_write_storage_hourly_sidecar`, three `_write_hourly_sidecar` calls and the
ERCOT audit sidecars all sit between `_t_end` and the next iteration's `_t_year`, so
they are in no phase and no year's `total`. Move `_t_end` (or add a `sidecars` part to
`results_write_parts`) so the instrument sees them; the wire format's six fields are
unchanged if the seconds are folded into `results_write`.

### A-4 · Persist the per-process loader caches across invocations — **~70 s off every ERCOT/NEISO run's first year**

PERF-A §2.4 established that ~98 % of the year-1 `data_prep` premium is *per-process cold
caches* (`_load_cod_map`, the eGRID repair set, `build_zone_lookup`), not the binned-fleet
parquet. A-1 and A-2 remove most of that cost at the source; what remains
(`build_zone_lookup`'s own derivation, `_rows_to_generators`) is a candidate for the same
content-addressed on-disk memo as A-2(b), keyed on the input file hashes. Lower priority
once A-1/A-2 land; listed so the year-1 premium is not re-chartered as a mystery.

### A-5 · The held CAMPD normalization (PERF-B change f) — **already measured, not on main**

`load_campd_hourly` −64–71 % on the 14-state ISOs (PJM `bench` 21–35 s/yr → ~7 s) is
measured, byte-gated on NEISO and ERCOT, and **held only on the MISO golden's staleness**
(`perf-recheck-2026-08.md` §5.4–5.5). `git branch -r --contains 27b3a92c` is empty at
HEAD. It is the largest already-paid-for win on the table for PJM/MISO and needs a
director decision, not a session.

### A-6 · `malloc_trim` at the cold-P1 seam — memory, hence concurrency

On the cold-P1 route `run_energy_solve` sets `model = None` before building the second
model, but the freed HiGHS workspace stays in glibc arenas until the *year-end*
`_malloc_trim()`; the session-3 RSS record shows the year peak (12.1–13.4 GB on ERCOT) is
the P1-rebuild moment, not P0. A `malloc_trim(0)` right after `model = None` cannot touch
a live object (byte-identical by construction) and is the cheapest chance to pull the
peak under the 14 GB cgroup that currently forbids a second concurrent ISO on the box —
rule 12's concurrency cap is a wall-clock lever in disguise. Measure with
`MARKET_SIM_MEM_DEBUG=1` before claiming a number.

## 3. The warm-start-class lever: seed the cold P1 from the P0 basis (class B)

**Who pays.** The P1 route is decided in `pipeline/solve.py::run_energy_solve`: a
`p1_fleet_prep` floor (bridge) or a `p1_kwargs_prep` override sends P1 to
`solve_dispatch(...)` — a **fresh `DispatchModel` and a cold `h.run()`**. At HEAD that is
the route of:

| keeper | why cold | P1 vs P0 wall on record |
|---|---|---|
| ERCOT `ercot248` (both configs) | `ercot_gas_commitment_bridge` raises availability; ERCOT co-opt → `refloor_thermal_inplace` declines | `solve_p1` 351–762 s vs `solve_p0` 399–524 s (s3 finding §5) |
| NYISO `nyiso-192` | `nyiso_gas_commitment_bridge` + co-opt + ramp | `solve_p1` 100–173 s vs `solve_p0` 98–180 s (PERF-B anchor) |
| CAISO `caiso-251` | `caiso_ra_mustoffer` bridge (default-on) | not in the anchor tables; same route |

NEISO / PJM / MISO warm-solve P1 on the live model (P1 ≈ 0.3–0.4× P0) and are untouched.
A cold P1 costing as much as P0 is the signature: the intra-year warm start that the July
plan lists as "already optimal" is simply *not reached* on the floor-bridge ISOs.

**Why the refuted C-4 does not block this.** C-4 proposed editing the live P0 model's
column bounds in place; it declines because the bridge's availability raise also feeds
the reserve-headroom / pool-cap / ramp RHS rows. (Those are all *row bounds*, never
matrix coefficients — `reserve_rows.py:192,807`, `rows.py:921` — so a `changeRowsBounds`
extension of the in-place path is also possible, but it is a larger surface.) The lever
here is different: keep the cold rebuild exactly as it is and **hand the new model the P0
basis** through the shipped `apply_cross_year_basis` (same `T`, same `unit_ids`, so the
column map is the identity, and HiGHS repairs the few bound-inconsistent statuses as an
alien basis). Nothing about the floored LP changes; only the simplex starting point does.

**Measurement (this session).** ERCOT forward keeper config (`ERCOT__forward`), 2025 — the
year C-1a reduces to exactly two HiGHS runs — replayed under the determinism pin with the
second model seeded from the P0 basis (driver monkeypatch; no repo code changed):

<!-- ERCOT_BENCH_TABLE -->

**Class and gate.** This is the neutrality class every shipped warm start already lives
in: objective and total generation identical, per-unit differences confined to marginal
ties, prices to dual degeneracy (`docs/cross-year-warmstart.md`; H2 table in the baseline
doc). It **cannot** be proved on `regression_gate.py --mode byte` and it is exactly the
plan-§6 memo case. Under the goldens/replay pin (`MARKET_SIM_WARMSTART_XYEAR=0`) it should
stay off so keeper goldens remain cold-vs-cold — which means it is a calibration-CLI
default (like the cross-year flip, P-2), not a golden-path change. Wiring: in
`run_energy_solve`'s cold branch, export the P0 basis before `model = None` (the export
already happens there when `_xwarm` is armed) and pass it into `solve_dispatch` (or build
the model and call `apply_cross_year_basis` before `solve`). The adaptive pass's P1
(ercot-221/230, caiso-205) benefits a second time per year, and could be seeded from
pass-1's *P1* basis rather than the P0 basis — closer still.

## 4. What is at the floor (verified, do not re-charter)

* **Solution marshalling** (`p0_post`/`p1_post`, ~10 s per pass on ERCOT): highspy 1.14
  returns `HighsSolution` vectors as Python lists on every attribute access — measured
  here at 0.45 s per 2 M elements, i.e. ~3 s per 13 M-column vector, and `solve()`
  already touches each of `col_value` / `col_dual` / `row_value` / `row_dual` exactly
  once. No array accessor exists in 1.14 (`getSolution` is the only path). Re-check only
  on a highspy release that adds one.
* **Basis export/apply**: 0.39 s per 2 M-element `getBasis` access, same reason; the LUT
  (PERF-B b) and the consumer gate (PERF-B e) are in.
* **Matrix build** (7.9 s NEISO, 10–27 s ERCOT keeper): kron + `_vstack_csr_free`, no
  hour loops; `addCols` 2.5 s + `addRows` 3.0 s are HiGHS's own copy.
* **HiGHS options**: threads/PAMI/IPM/Dantzig/LEAN all measured negative or inert
  (baseline doc Exp 1–4, `pjm-reserve-ordc.md`). Not re-run. One un-benched knob remains
  — `simplex_dual_edge_weight_strategy=1` (Devex) for the *cold* P0 — but Dantzig's
  10 min+ non-convergence on the degenerate co-opt LP is a strong prior against cheaper
  pricing, and a Devex arm was not spent here.
* **Forecast cross-year warm start**: the 2.3× is real (D-9) and owner-disarmed on
  resumability grounds (D-10); not re-litigated.

## 5. Ranked execution order

| # | lever | class | expected | gate |
|---|---|---|---|---|
| 1 | A-1 vectorize `_load_cod_map` | byte-identical | 16–17 s per process (×2 on ERCOT) | dict equality (done here) + fast tier |
| 2 | A-2 eGRID parquet mirror (both call sites) | byte-identical | ~54 s per process | `frame.equals` on the three sheet reads |
| 3 | A-3 band sidecar vectorization + put sidecars on the clock | byte-identical | ~20 s per year, every ISO | frame equality on the sidecar |
| 4 | B seed cold P1 from the P0 basis (ERCOT/NYISO/CAISO) | warm-start class | §3 table — most of a P1 solve per pass | owner memo (plan §6) + `diff_warmstart_bundles.py`; off under the goldens pin |
| 5 | A-5 merge the held CAMPD normalization | byte-identical (already gated) | PJM/MISO `bench` −15–25 s/yr | MISO golden refresh (director) |
| 6 | A-6 `malloc_trim` at the cold-P1 seam | byte-identical | memory → concurrency | `MEM_DEBUG` peak before/after |
| 7 | A-4 on-disk memo for the remaining year-1 caches | byte-identical | residual of the year-1 premium | content-hash keyed; frame equality |

Items 1–3 together are ~90–100 s per NEISO year at the measured 272 s (and ~70 s of every
ERCOT run's first year plus ~20 s of every later one) with no solve in the gate. Item 4
is the only lever that touches HiGHS iteration counts, and the only one that needs an
owner decision.

## 6. Addendum — prototype and bench records

### 6.1 NEISO 2023 keeper replay under cProfile (this session)

Driver: `capture_keeper_goldens.resolve_capture_targets` + `build_solve_kwargs` for
`NEISO` (`2026-08-17-neiso-99-joint-p1`), `solve_and_persist(years=[2023])` into a
scratch dir, `MARKET_SIM_HIGHS_THREADS=1`, `WARMSTART=1`, `WARMSTART_XYEAR=0`. Phase line:

```
year 2023 phase timing: data_prep=125.5s solve_p0=79.7s markup=3.5s solve_p1=29.7s
results_write=4.9s total=243.3s (markup: setup=0.0s p0_post=1.6s markup=0.1s seam=0.0s
p1_post=1.7s tail=0.0s other=0.1s) (results_write: state=0.2s frames=1.4s parquet=1.5s bench=1.9s)
TOTAL wall 271.7s      # process wall from the driver; 28.4 s falls after the phase line
```

cProfile (171 M calls; profiled seconds run ~1.5–3× real on pandas-heavy code, shares are
the signal): `highspy._core.run` 109.5 s self (2 calls); `_fleet_group_by_code` 57.5 s cum
→ `load_fleet_from_csv` → `_rows_to_generators` (4 calls) → `_egrid_boundary_hr_repairs`
36.2 s + `_assign_zones` 21.1 s; `_load_cod_map` 51.5 s cum with 14,330 `DataFrame.dropna`
calls (43.0 s cum); `read_excel` 53.7 s cum over 3 calls (openpyxl `get_sheet_data` 49.0 s,
`parse_cell` 4.65 M calls); `_write_class_band_hourly_sidecar` 21.2 s cum
(`_tranche_band` 6,718,920 calls, 5.2 s cum; the list comprehension 14.0 s).

### 6.2 Zero-LP prototypes (this session, unprofiled)

| prototype | shipped | prototype | identity |
|---|---:|---:|---|
| `_load_cod_map` on `data/raw/eia-860` (14,334 plants) | 16.8 s | 0.41 s | `dict == dict` → True |
| `_tranche_band` over the NEISO 2023 P1 dispatch frame (6,718,920 rows) | 12.7 s | 2.16 s | categorical values and categories identical |

<!-- ADDENDUM -->
