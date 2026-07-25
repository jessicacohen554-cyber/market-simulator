# miso-89 session findings (2026-07-25) — three lanes, one determination question

**Session scope.** The owner directed all three handoff lanes in one session
(A: 2025 summer body price; B: CT coverage hole; C: solve memory retention),
against the standing constraint that A and B keep separate attribution.

**Outcome in one line:** Lane A and Lane B collapse into a single **NO-BUILD**
finding — the C3b-2025 miss is real, located and sized, but every enumerated
instrument for it is refuted, adjudicated data-blocked, or measured inert.
Lane C's root cause is identified and a verified partial fix is committed.

**No LP keeper was produced or promoted this session.** The MISO keeper remains
`2026-07-25-miso-88-egrid-hr` (NOT-YET on C3b price_shape). Nothing was
registered on the dashboard because no calibration run was completed — the only
solves run were memory-profiling reproductions, which were deleted (rule 15
applies to *completed calibration runs*; a killed profiling probe with no
bundle is not one).

---

## Lane A + B — see `results/calibration/FINDING-miso89-diurnal-spread-compression-2026-07.md`

The full evidence is in that finding. Headlines:

1. **C3b-2025 is diurnal-spread compression, not a 2025 summer level miss.** The
   model reproduces **29–47 %** of the observed peak-minus-night spread in every
   season of every year. 2025 fails only because the *actual* summer spread
   widened (26.3 → 32.7 $/MWh) while the model's stayed flat (11.7 → 12.2).
2. **The model's stack is ~0.6 $/GW** over a 39 GW dispatch range.
3. **MISO's scarcity apparatus is already built and live** — measured hourly
   reserve requirement (mean 2.64 GW), RDC to $3,500, zonal + Midwest
   subregional, per-asset reserve columns — and prices in **0 / 6 / 2 hours out
   of 8760**. Starved, not missing.
4. **No availability fix of plausible size can arm it.** The model carries
   **31.9 GW of idle fossil headroom** at summer peak (49 % above dispatch) and
   the solve's own log reports **32–37 GW of deliverable 10-min reserve ramp**
   against a 2.6 GW requirement — slack by >12×.
5. **The CT hole is real but is not a C3b mechanism.** CT_PEAKER + CT_CHP =
   **25.02 GW at 0.0 % CAMPD derate coverage** (vs 42–95 % for every other
   fossil class), and the statistical fallback puts POF in shoulder months only
   and 30 % of WEFOR in summer — so 25 GW of peaking capacity is at its *most*
   available exactly when the market is tightest. But a generous 15 % extra
   derate is ~3.4 GW against 31.9 GW of headroom: **~$4–6 of the $16.3 gap.**
6. **Congestion cannot drive C3b** — it scores a load-weighted mean, and a
   load-weighted-zero deviation cannot move one. Verified: imposing the *actual*
   zonal deviation pattern on the model's level leaves NRMSE identical to three
   decimals (0.081 / 0.129 / 0.206). Independently already NO-BUILD (miso-78/79).
7. **What the miss actually is:** model fossil derate at summer peak is flat
   across years (+1.76 GW into 2025) while MISO's published offline record jumps
   **+12.32 GW**. The gap is stable at ~14.6 GW in 2023/24 and breaks to
   **24.76 GW** in 2025 — a **~10 GW under-derate**, by difference-in-differences
   (so no cross-fuel attribution is required, respecting miso-87).
8. **2025 was not hot.** Zone-mean summer-peak TMAX: 29.6 / 29.2 / **29.8 °C**.
   The spike came at normal temperatures with cheap gas — a supply-side event.

### Instruments enumerated, all closed

| instrument | status |
|---|---|
| published total, uniform attribution | REJECTED (miso-85) |
| cross-fuel attribution | REFUTED at charter (miso-87) |
| congestion / zone refinement | NO-BUILD, data-blocked (miso-78, RO-3 dead per miso-79) |
| `temp_dependent_derate` | REJECTED (ERCOT gas fleet, 2026-07-09) |
| `gt_ambient_derate` | **PROVABLY INERT — measured this session.** Zone-mean TMAX exceeds the 35 °C reference in 24 h of 2023 and **0 h of 2024/2025**, and **0 h at summer peak in any year**. Removes **0 MW** in the failing window |
| CT-grain measured availability | NO SOURCE (CEMS-blind; MISO publishes region × cause only) |
| `unit_partial_outage_windows` | premise fails — targets plants *without* unit-level data; MISO already has 95.4 % coal / 90.1 % CC coverage |

### Recommendation (owner decision)

C3b-2025 is a measurement gap of the same family as the ledgered C3c tail.
Recommended: **ledger it with the §7 difference-in-differences as its evidence
and re-gate MISO**, and open a standing **data ask** for MISO outage data at
unit or fuel grain (rule 22 permits training-year intake under logged owner
authorization). Do **not** charter miso-78 RO-2 believing it closes C3b — the
§6 decomposition shows it does not move the metric at all.

---

## Lane C — root cause found, partial fix committed and verified

**Reproduced the failure under telemetry** (new stdlib `/proc/self/status`
instrumentation, committed):

```
year 2023 phase timing: data_prep=77.7s solve_p0=436.5s markup=44.7s
                        solve_p1=172.5s results_write=40.3s total=771.7s
year 2023 memory after release: resident=2.98 GB peak=14.42 GB
-> year 2024 OOM-killed at 15,943,968 kB   (matches the reported 15.95 GB)
```

**The residual is not the accumulated frames.** Measured directly:
`campd_hourly` **0.055 GB/year** (4.2 M rows, already float32/int16), `eia930`
**0.002 GB/year** — 0.17 GB across all three years. The 2.98 GB is **freed
glibc heap**: `del` + `gc.collect()` return the LP's memory to the allocator,
but glibc keeps large fragmented arenas instead of unmapping them, so the next
year's build starts on the previous year's high-water RSS.

**Fix committed** (`c4be52d`): `malloc_trim(0)` after the existing release
block. Frees only already-free heap, so it cannot touch a live object and
dispatch is unaffected; glibc-only, no-ops elsewhere.

**Verified effect, same 2-year case:**

| | before | after |
|---|---|---|
| year-2023 resident handed to year 2024 | 2.98 GB | **1.56 GB** |
| year-2023 peak | 14.42 GB | 14.41 GB (unchanged, as expected) |
| accumulators | — | 0.07 GB (confirmed) |
| year 2024 | died in **build** | reached and completed **P0** (496 s), died in P1 |

**Honest limit: this does NOT make a multi-year MISO run fit on a 15 GB box.**
The binding term is the **~14.4 GB single-year peak**, which leaves <0.6 GB of
headroom. MISO's P1 re-solves the *same* model in place (`_warm_p1`), so unlike
the cold-P1 path there is no second model to release at the seam — the peak is
one model and is irreducible without shrinking the LP.

**The staged one-year-per-process `--reuse-solved` recipe remains necessary for
MISO on this box.** The fix is still worth having: it is a permanent ~1.4 GB
reduction in cross-year carry that benefits every ISO, and it converts a
build-time death into a P1-time death (i.e. it buys most of a year).

**Named next levers** (untested, for a successor session):
* Clear the unbounded module-level `lru_cache`s between years —
  `data/miso_outages.py` has four `maxsize=None` caches over per-year arrays,
  plus `pjm_outages`, `neiso_operable_capacity`, `coal`, `loss_surface`.
* Release and rebuild the fleet / binned-fleet objects between years.
* Target: baseline under ~0.6 GB, which is what a 14.4 GB peak needs to fit.

---

## Hygiene items from the inbound handoff — both already resolved on main

* `scripts/render_calibration_html.py` is **restored** on `origin/main` at 1,911
  lines (commit `3babe5f` merged); the corruption from `2668ae0` is gone. The
  intended delta-heatmap feature still never landed.
* The miso-88 branch is merged; the keeper, bundle, hourly sidecars and handoff
  doc are all present on main. Nothing stranded.
* Still open and worth a look: `file-integrity-guard.yml` did not block
  `2668ae0` (1 insertion / 1,911 deletions), which is exactly its purpose.

## Commits on this branch

| commit | contents |
|---|---|
| `d891c8a` | Lane A/B finding + per-year RSS telemetry |
| `c4be52d` | `malloc_trim(0)` between years + accumulator-footprint telemetry |
| (this) | session handoff |
