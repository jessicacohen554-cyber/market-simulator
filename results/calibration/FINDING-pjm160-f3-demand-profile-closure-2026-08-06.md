# FINDING (pjm-160, task 2): the F3 "demand-profile gap" was **mis-stated**. The hourly demand driver was never missing; only `load_demand_meta` was. Closed at the curation seam — **B1 and B3 are now CLOSED for PJM 2019**

**Session:** pjm-160 (task 2 — the F3 data closure)
**Date:** 2026-08-06
**Branch:** `claude/pjm-bench-regen-f3-closure-bj7q6o`
**Scope:** Channel-1 data intake. **Zero LP solves.** No out-of-training year was
solved, scored or registered; the holdout freeze is ACTIVE and `final` is EMPTY,
and nothing here changes either.

---

## §0 — the result in one table

| assessment blocker | claim it rested on | measured at HEAD | status now |
|---|---|---|---|
| **B1** 2019 unsolvable | *"`eia_demand_profiles.parquet` starts at 2021 for every ISO … `load_demand('PJM', 2019)` raises"* | **FALSE.** `load_demand('PJM', 2019)` returns a full `(8, 8760)` array, and so does every other ISO for 2019 **and** 2020 | **CLOSED** |
| | no `calibration_reference.json` `isos.PJM.2019` | true; the raise came from `load_demand_**meta**`, not `load_demand` | **CLOSED** — block built |
| | no `PJM_2019_renewable_capacity.csv` | true | **CLOSED** — built |
| **B3** locked-test C3a on a different statistic | `lw_retrofit` calls `load_demand`, "the F3-blocked artifact" | the call was never blocked | **CLOSED at the source** — `actual_lmp.json` PJM 2019 now carries `rt_lw 26.54 / da_lw 26.56` |

`scripts/probes/_pjm159_final_readiness.py` now reports **`2019: SOLVABLE`**
where it reported `BLOCKED` yesterday — and it reports it because it *calls*
`load_demand` / `load_demand_meta` instead of quoting the register (§3).

**B2 and B4 are untouched and still stand.** They are the two blockers the
assessment already flagged as owner decisions rather than session work, and
nothing in this task bears on either. B4 is in fact **sharpened** by §4.

---

## §1 — what the gap actually was

The register and the pjm-159 assessment both recorded the blocker as the
**demand driver**:

> *"`data/raw/eia-930/eia_demand_profiles.parquet` (what `load_demand` reads) —
> 2021-2025 for **every** ISO — the primary demand driver. `load_demand('PJM',
> 2019)` raises."*

That description was true once and is now two refactors stale. `load_demand`
resolves its system demand through `eia930.demand.DEMAND_LOADERS` — a per-ISO
adapter registry over the **per-BA** `data/raw/eia-930-hourly/<BA> hourly.parquet`
extracts. The demand-profiles parquet is only what an ISO falls back to when its
adapter returns `None`. And the per-BA extracts cover **2018-2026**:

```
PJM hourly.parquet rows by local year:
  2018 8760 · 2019 8760 · 2020 8784 · 2021 8760 · 2022 8760
  2023 8759 · 2024 8784 · 2025 8760 · 2026 4343
```

Measured this session, calling the real loaders:

| ISO | `load_demand` 2019 | 2020 | `load_demand_meta` 2019 / 2020 |
|---|---|---|---|
| PJM, CAISO, NYISO, NEISO, MISO, ERCOT | **OK** (all six) | **OK** (all six) | **RAISED** (all six) |

So the gap was real but **one function wide**: `load_demand_meta` reads the
repaired `demand-profile` clean partition when it exists and otherwise falls
through to `eia_demand_meta.parquet`, the legacy summary — which, like the
profiles file it summarizes, starts at 2021. That single
`ValueError: No EIA-930 data for ISO 'PJM' in year 2019` is what
`build_calibration_reference._demand_totals` hit, and through it the whole
`isos.PJM.2019` block and `PJM_2019_renewable_capacity.csv`.

**Why this matters beyond the bookkeeping.** A blocker recorded one layer away
from where it lives does not get fixed by the sessions that read the record —
it gets *routed around*. Four ISOs' `CALIBRATION_YEARS_BY_ISO` comments in
`scripts/data/build_calibration_reference.py` (CAISO, NYISO, NEISO, MISO) each
decline to add their pre-2021 years citing this artifact, and each says
"extending it is not a <this ISO>'s task." The extension needed was not to that
artifact at all.

---

## §2 — the fix: `curate_demand_profile.curate_pre_window`

`data/raw` is immutable (CLAUDE.md), so the legacy extract is not appended to
and no new raw artifact is invented. The repair goes where the existing repair
already lives — the curation seam:

- `scripts/data/curate_demand_profile.py` gains `PRE_WINDOW_YEARS = (2019, 2020)`
  and `curate_pre_window()`, which writes a `demand-profile` clean partition for
  each of the six model ISOs for those years;
- the series is taken from **the ISO's own `DEMAND_LOADERS` adapter** — i.e. the
  exact series `load_demand` serves for that year, screens and all — not from a
  second, parallel reconstruction of it. The pre-window meta is therefore by
  construction the summary of the demand the LP would dispatch against;
- the 2021-2025 legacy pass is untouched and its partitions are byte-identical.

`load_demand_meta` prefers the clean partition, so it now resolves for
2019/2020 without reaching the legacy summary at all.

Twelve partitions written (6 ISOs × 2 years), 0 physically-impossible hours
flagged in any of them:

| | 2019 peak / total | 2020 peak / total |
|---|---|---|
| PJM | 155,276 MW / 800.3 TWh | **192,229 MW** / 768.0 TWh |
| MISO | 116,600 MW / 649.5 TWh | 112,940 MW / 622.5 TWh |
| ERCOT | 74,533 MW / 383.7 TWh | 74,166 MW / 380.2 TWh |
| CAISO | 43,849 MW / 214.2 TWh | 46,643 MW / 217.5 TWh |
| NYISO | 30,397 MW / 155.8 TWh | 30,660 MW / 149.8 TWh |
| NEISO | 23,973 MW / 118.3 TWh | 24,697 MW / 115.3 TWh |

### §2.1 — a defect found in the process, reported not buried (rule 14)

**PJM 2020's `peak_mw` is wrong by ~47 GW and the partition is written anyway,
labelled.** Its top-of-year hours are

```
2020 top-10: 192,229 · 176,085 · 145,428 · 145,056 · 144,562 · 144,329 · …
```

The first two are metering artifacts: every other PJM year's top-10 is a smooth
ladder with no such step (2019 `155,276 → 148,148`; 2023 `147,605 → 144,536`;
2025 `160,560 → 156,546`), and `max/median` is **2.26** in 2020 against
**1.66-1.75** in every other year — outside the ≤2.1 envelope this module's own
docstring derives empirically across all 35 legitimate series.

They survive because the loader's spike screen
(`eia930.demand._screen_demand_spikes`) triggers at **2.5× median** and the
curator's physical-bounds screen at **5× median**. Both catch 2020's 262,651 MW
hour and 2019's 417,669 MW hour; neither catches 192,229.

**Deliberately NOT fixed here, and the reason is a rule, not a shrug.** The root
cause is a threshold in the shared loader screen that every ISO and every year
runs through, including the three training years every keeper is calibrated on.
Tightening it is a solve-affecting change to a shared mechanism — it needs its
own evidence sweep across all six ISOs and its own keeper re-verification, and
adding a second, pre-window-only screen beside it would stack two mechanisms on
one phenomenon (rule 19 `[R-ONE-MECH]`). Inventing a threshold to make this one
series look right is exactly the move rule 5 `[R-NO-MAGIC]` forbids.

**Consequence, stated so nobody has to rediscover it:** PJM **2020 is NOT added**
to `CALIBRATION_YEARS_BY_ISO`, because a reference block is where a wrong
`peak_mw` would go to hide. 2019 is added; 2020 waits on the root-cause fix.
The impact is confined to `peak_mw` and other max-statistics — 2 artifact hours
in 8760 move `total_annual_mwh` by ~0.01 % and a load-weighted mean by less,
which is why the 2020 `rt_lw`/`da_lw` fields in §4 are unaffected.

---

## §3 — the readiness probe now tests instead of quoting

`scripts/probes/_pjm159_final_readiness.py::check_solvability` carried

```python
# ... taken from the register's measured statement rather than re-read here
demand_years = [2021, 2022, 2023, 2024, 2025]
```

and reported `2019: BLOCKED — missing: eia_demand_profiles.parquet (load_demand)`
on that hardcoded list. It now **calls `load_demand` and `load_demand_meta`** and
reports what they do. The assumption is what produced the wrong answer, so the
probe stops making one.

```
  calibration_reference.json isos.PJM : [2019, 2021, 2022, 2023, 2024, 2025]
  PJM_<y>_renewable_capacity.csv      : [2019, 2021, 2022, 2023, 2024, 2025]
  load_demand + _meta('PJM', 2019)    : OK
  2019: SOLVABLE
  2026: BLOCKED   (H1-2026 — unchanged, blocked by construction)
```

---

## §4 — B3 closed at the source, and B4 sharpened

`derive_actual_lmp.py --lw-retrofit --years 2019 2020` now runs (it calls
`load_demand` for the weights). PJM 2019 gains:

```
rt_lw 26.54 · da_lw 26.56   (legacy equal-hour: rt 25.44 · da 25.54)
src_lw: system hub hourly series load-weighted by measured system demand
```

So when a 2019 run is eventually registered, its bench part carries the
**load-weighted** basis and its C3a is scored on the same statistic as every
in-sample number. That is B3's whole demand.

**And it sharpens B4 rather than softening it.** The assessment sized PJM's
regime flip on the equal-hour spread (2019 `+0.10` vs `+0.89/+0.25/+0.82` in
training). On the basis the C3a gate actually uses:

| year | DA−RT | **DA−RT (load-weighted)** | tier |
|---|---:|---:|---|
| **2019** | +0.10 | **+0.02** | **LOCKED TEST** |
| 2020 | −0.25 | −0.29 | outside grant |
| 2023 | +0.89 | **+0.96** | train |
| 2024 | +0.25 | **+0.29** | train |
| 2025 | +0.82 | **+0.78** | train |

**On the gate's own basis 2019's spread is +0.02 — essentially zero, and an
order of magnitude below the smallest training year.** The `pjm_da_virtual_bids`
layer's C1 contribution is `≈ −(DA−RT) × dNet/dλ × 8760`, so on 2019 the basis
term all but vanishes and the model's own price error stands uncancelled. B4 is
not weakened by closing B1/B3; it is measured more precisely and points the
same way.

### §4.1 — a second reproducibility failure, recorded and NOT landed

Assessment §9 item 2 asked that the committed 2023-2025 `rt_lw` rows be verified
to re-derive byte-identically. **They do not.** Re-running the retrofit on
2023-2025 at HEAD gives PJM **29.58 / 31.36 / 45.89** against the committed
**29.55 / 31.31 / 45.80** (+0.03/+0.05/+0.09, ~0.1 %). NYISO and NEISO reproduce
exactly; ERCOT differs only because its `ERCOT_Native_Load_*.xlsx` zonal files
are absent in this container, which is an environment artifact, not a code one.

The cause is PJM-specific and structural: `_lw_fields` weights by
`load_demand`, and PJM's `load_demand` switched from the legacy demand-profiles
series to the per-BA extract (plus gained the dropout/spike screens) after those
rows were derived. The committed values are on the **old weight basis**.

**Restored, not landed.** `actual_lmp.json` was reverted to its committed bytes
and the retrofit re-run for **2019/2020 only**, so no committed year moved
(verified: the only diff is `rt_lw`/`da_lw`/`*_mon`/`src_lw` added to ERCOT and
PJM 2019-2020; zero existing fields changed). The reason is that `rt_lw` is a
**gate input** — `calibration_verdict.score_price_mean` reads it off the bench
part, and a bench part re-renders from `actual_lmp.json` on the next
registration. Refreshing it would silently move C3a for six ISOs at whatever
moment each next registered. That is a cross-ISO, owner-visible decision, not a
side effect of a PJM data task.

---

## §5 — `calibration_reference.json`: the rebuild propagates a documented repair

`build_reference()` regenerates the whole file, and the rebuild moved **152
numeric fields across existing blocks** as well as adding `PJM.2019`. This was
inspected before landing rather than waved through. It is not drift — it is the
`curate_demand_profile` repair finally reaching the reference, plus current
EIA-860 vintages and PJM's current 8-zone topology:

| field | committed | rebuilt |
|---|---:|---:|
| PJM 2021 `demand.peak_mw` | **2,147,480,000** | 149,590 |
| PJM 2021 `demand.total_twh` | **4,902.59** | 796.52 |
| MISO 2021/2022/2024 `demand.min_mw` | **0.0** | 51,007 / 52,159 / 52,878 |

The first is the 2.147e9 sentinel spike and the second the 0 MW "missing data"
sentinel — **both named explicitly in `curate_demand_profile.py`'s own docstring
as the defects it exists to repair.** Leaving them in place to keep this diff
small is precisely what rule 14 `[R-ACCURATE]` forbids.

**Verified not to be a gate input before landing:** neither
`scripts/calibration_verdict.py` nor `scripts/legitimacy_diagnostics.py` nor
`scripts/audit_keepers.py` reads `calibration_reference.json` at all, and the
solve reads only the top-level `henry_hub_actual` table
(`market_sim.pipeline.reference`), which is a frozen constant and is unchanged.
The one solve-side use of `isos.<ISO>.<year>` is a **printed** report comparison
in `run_calibration_full.py`. No gate moves for any ISO.

The `*_renewable_capacity.csv` set is regenerated by the same pass; those files
have **no code consumer** (they are the JSON's tabular export) and PJM's are
also re-based from the retired 4-zone topology (`PJM_Central/East/South/West`)
onto the live 8-zone one the JSON has been using all along.

---

## §6 — what this does and does not unblock

**Unblocked (data readiness only):** PJM 2019 now has every input a solve
requires — demand, demand meta, reference block, renewable capacity, and a
load-weighted price actual. Per rule 22 that is the *preparation*, and
preparation is explicitly unrestricted: *"what is held out is the SCORE, never
the DATA."* The point is that if a `final` grant is ever issued, the inputs are
already frozen and prepared, with nothing to assemble mid-spend.

**Not unblocked, and nothing here argues otherwise:**

- **The freeze is ACTIVE and `final` is EMPTY.** No 2019 solve, score or
  registration is authorized. Data readiness is not a grant, and a passing
  readiness check is never a reason to spend a year.
- **B2 stands** — `PJM_SEAM_LADDER_BY_YEAR` is still `{2023, 2024, 2025}`, the
  rule-19 firm-export floor still fires in the ladder's place outside them, and
  `measured_ramp_capability` / `measured_ct_heat_rates` are still pooled on the
  training window. Owner decision.
- **B4 stands, sharpened** (§4).
- **H1-2026 is unchanged** — blocked by construction (a partial year cannot
  satisfy the 8760 demand contract; CAMPD Q2-2026 and EIA gas May-2026+ unposted).

**Cross-ISO:** the twelve pre-window partitions are written for all six ISOs, so
CAISO / NYISO / NEISO / MISO can add their own pre-2021 reference blocks whenever
their lanes want them — the "extending it is not a <ISO> task" comments in
`build_calibration_reference.py` no longer describe a real obstacle. This session
adds **no** other ISO's years: that is each lane's call, and PJM 2019 is the one
this task was scoped to.

---

## §7 — governance

- **Rule 22.** Data preparation only. No out-of-training year solved, scored or
  registered. The freeze was read, not touched, and remains ACTIVE on its
  2026-07-25 basis; `final` remains empty. Intake needs no marker under the
  owner's 2026-08-06 clarification, and this session's authorization is the
  task's own explicit instruction, logged here.
- **Rule 14 `[R-ACCURATE]`.** Two defects surfaced (PJM 2020's peak artifact,
  §2.1; the `rt_lw` non-reproducibility, §4.1). Neither is buried: one is
  reported with its root cause and its year withheld from the reference, the
  other is reported and explicitly restored rather than landed.
- **Rule 19 / rule 5.** No new screen, no new threshold, no tuned constant.
- **Rule 28.** No mechanism proposed or tested; PJM's lever queue is untouched
  and no matrix cell moves.
- **Rule 15.** No run produced; nothing owed to either dashboard.
- **Rule 27 `[R-PUSH]`.** Opus. Edits are local and pushed as on-disk bytes.

**Next shorthand: pjm-161.**
