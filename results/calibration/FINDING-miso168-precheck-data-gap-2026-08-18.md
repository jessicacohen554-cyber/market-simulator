# FINDING miso-168 — PREREG-miso167 execution blocked again (15 GB), and the §3 pre-check has a data gap

**Session:** miso-168 (2026-08-18), chartered to EXECUTE
`PREREG-miso167-online-gated-reserve-supply-2026-08-18.md` (control + arm).
**Keeper:** `2026-08-16-miso-160-wefor-shape`, UNCHANGED.
**Outcome: BLOCKED — no solve, no pre-check, no `ScenarioConfig` field, no code built, no cell
verdict minted, no registration** (rule 15 `[R-DASHBOARD]` not engaged; the
miso-142/153/155/156/157/161/163/164/167 no-LP-session precedent). Nothing in the prereg is
amended: every threshold, kill gate and decision rule stands exactly as pre-registered.

---

## 1. The RAM blocker recurred: this container is 15 GB against the ≥24 GB requirement

The session order requires `free -g` verification before building, ≥24 GB, STOP-and-report
otherwise. Measured at session start:

```
               total        used        free      shared  buff/cache   available
Mem:              15           0           4           0          10          14
```

15 GB total / 14 GB available — the same provisioning miso-167 reported as not runnable, against
miso-161's measured **>13.9 GB/year** for a MISO plant-level LP (the keeper runs
`plant_level_fleet=True`, `use_campd_bins=True`; see `miso160_wefor_B/run_config.json`). The
control+arm pair over `--year 2023 2024 2025` (six year-solves) is not attemptable here. Reported
per CLAUDE.md and the session order; **not** routed to a GitHub Actions runner. (Corroborating
signal that this container was never provisioned for a solve lane: no `.venv`, no
pandas/pyarrow/highspy installed.)

## 2. NEW FACT — the prereg §3 "no-LP pre-check" is not executable from committed artifacts

Prereg §3 reads: *"Executed on the keeper's own **committed** P1 at **tranche grain**."* Those two
requirements cannot both be met on a fresh clone:

- The committed keeper bundle (`results/calibration/miso160_wefor_B/hourly/`) carries
  `class_hourly` / `system` / `storage` / `reserve_family` only — **class grain**, which §3 itself
  rules insufficient.
- The two series H_on/H_off need are exactly the `unit_hourly_<year>.parquet` sidecar's `mw` and
  `cap_mw` columns. The writer's own docstring
  (`scripts/run_calibration_full.py::_unit_hourly_frame`) is explicit that this sidecar exists
  precisely because a slim bundle *"exposes no per-unit series at all"*, and that *"online status
  is then the plant-level `sum(mw) > threshold` and headroom is `sum(cap_mw) − sum(mw)` over the
  online plants (both sums are linear in the tranches, so the plant grain is recovered exactly
  from this frame)"* — the exact construction the pre-check specifies.
- Repo-wide census (`git ls-files | grep unit_hourly`): the **only** committed `unit_hourly` in
  the entire repository is `results/calibration/neiso86_2022_corrected/hourly/unit_hourly_2022.parquet`
  (2.2 MiB). **No MISO bundle has ever committed one.** Rule 15's keeper commit set
  (class_hourly + system + reserve_family) does not include it.

So the pre-check is "no-LP" only on a machine that still holds the keeper's gitignored bundle half
(the solving container, long reclaimed). On any fresh clone, producing the tranche-grain series
requires a keeper P1 replay — an LP solve, i.e. the very operation §1 blocks. **miso-168 therefore
could not run the pre-check either**, and neither can any successor before its control solve runs.

## 3. Corrected execution order for the ≥24 GB successor (logistics only — no prereg change)

The prereg's semantics — *the pre-check can kill the lever before the ARM is solved* — are fully
preservable, because the §5 protocol already mandates a zero-delta CONTROL unconditionally:

1. **CONTROL replay first** (same HEAD, flag off, `--year 2023 2024 2025`, sequential): verify
   bit-identity against the committed keeper on `class_hourly`/`system`/`storage`/`reserve_family`
   before reading anything else. The control writes `hourly/unit_hourly_<year>.parquet` as a
   matter of course.
2. **Run the §3 pre-check on the CONTROL's `unit_hourly_2025.parquet` (P1 rows)** — bit-identity
   makes it the keeper's own P1. Push the pre-check record BEFORE building the mechanism, as the
   prereg orders, and **commit `unit_hourly_2025.parquet` (and 2023/2024, ~2–6 MiB zstd each)
   alongside the record** so the pre-check is reproducible from committed artifacts (the miso-167
   instrument precedent). K-PRE-B needs all-8760 coverage per year, so the 2023/2024 sidecars are
   in scope too.
3. **K-PRE-A / K-PRE-B verdicts exactly as pre-registered** (80 % / 99 %, thresholds untouched).
   K-PRE-A fires → DECLARE INERT, mint the MISO cell `I`, and the ARM is never solved.
4. Only if the pre-check passes: build `miso_reserve_online_gated` (GATED, default OFF,
   MISO-only, zero DOF), solve the ARM, and apply the §6 decision rule verbatim (K-1 …K-5,
   escalation clause included) plus rule-22 leave-one-year-out before any promotion.

The one thing this order cannot avoid is the control solve preceding the kill decision — that cost
is already mandated by §5 and is sunk regardless of the pre-check's verdict.

## 4. What this session changes

Nothing in the model, the keeper, the matrix verdicts, or any determination. Records: this file
and the miso-168 queue stamp in `docs/mechanism-testing-matrix.md` §5.4. The successor still
needs **≥24 GB RAM** (and a solve-capable environment: `hydrate_data.py --profile miso` + the
package stack), and executes §3 above.
