# PRECOMMIT — ercot-243 Phase-0: census of the 2024/2025 EVENT-EXIT-HOUR POPULATION on the forward keeper's committed sidecars, pinned BEFORE any measurement

> Status: PRECOMMIT, pushed and blob-verified before any census scan runs.
> Session ercot-243, branch `claude/ercot-243-release-exit-r7owkv`.
> Charter: the ercot-243 handoff (LANE 2, the release-guard EXIT condition).
> Keeper state at dispatch (UNTOUCHED by Phase-0): two-config partition per
> `docs/FINDING-ercot-two-config-keeper-2026-08-26.md` — forward
> `2026-08-25-234-eastex-identity` (2024/2025), carve-out
> `2026-08-25-236-swcap-clip-k33` (2023).

## 0. Object and scope

`docs/FINDING-ercot239-h3068-phase0-2026-08-30.md` fully attributed
h3068-2024 as the EXIT EDGE of a one-hour-late model event on time-aligned
inputs: the ercot-223 event-release guard released the realized-spike hours
h3065–h3067 (pass-1 settle ≥ $1,000) but h3068 snapped back to its floor
($523.12 = p_hat 0.104625 × VOLL; the ercot-223 record's pass-1 settle
there was $675 < $1,000), holding ~1 GWh of storage out of the exit hour
and pricing it at $798 on the thermal wall + lingering reserve steps where
reality had collapsed to $110.41.

Per `[R-FLOOR-WINDOW]` the admissible repair must be driven by the
exit-hour POPULATION, never h3068 alone. Phase-0 is that census:
**ZERO-SOLVE**, reading only

- the forward keeper's committed hourly sidecars
  (`results/calibration/ercot234_eastex_identity/hourly/` — system,
  class_hourly, storage, reserve_family, adaptive; scored pass P1),
- the committed actuals
  (`data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`),
- the EIA-930 wide extract (`data/raw/eia-930-hourly/ERCO hourly.parquet`),
- the measured ORDC/reserves series
  (`data/raw/ercot/ercot_{2024,2025}_ordc_reserves_hourly.parquet`).

Census years: **2024 and 2025 only** (the forward keeper's designated
span). 2023 is the carve-out config's year and its entry-edge/conduct
questions belong to the SCED conduct lane, not this one. No solve of any
kind is licensed by this precommit. The entry edge (h3064) is explicitly
OUT of scope.

## 1. V-0 anchor (constructions verified before the scan)

Before any census row is read, the probe re-derives from the same
committed artifacts and asserts, byte-for-byte against the committed
`results/calibration/ercot239_h3068_phase0.json` record:

- model load-weighted h3068-2024 = **798.20 ± 0.05**,
- actual RT h3068-2024 = **110.41 ± 0.05**,
- adaptive `floor_usd[3068]` = **523.12 ± 0.01**,
- storage discharge h3068 = 0 ± 0.5 MW, h3069 ≥ 1,000 MW,
- demand alignment best at lag 0 (the ercot-239 lag-correlation
  convention), per census year.

V-0 failure is a stop-the-line event: no census is run, the mismatch is
reported.

## 2. The census signature, declared ex ante

All series are hourly, hour index h ∈ [0, 8759] per year, local
hour-ending per the repo convention (EIA-930 mapped exactly as
`scripts/probes/ercot239_h3068_phase0.py::_eia_2024` does, Feb-29 dropped
in 2024). Model price `m[h]` = demand-weighted zonal `price`; actual
`a[h]` = the actuals parquet `rt` column. Withheld-family activity at h =
max over {RegUp_withheld, RRS_withheld, ECRS_withheld, NonSpin,
ercot_ordc_total} of the family `dual`, and ORDC-total `shortfall_mw`.

Hour h is an **actual-collapse hour** iff:

- **A1** `a[h] < 200` (the program's census line), and
- **A2** `a[h−1] ≥ 200` (h is the FIRST collapsed hour), and
- **A3** `max(a[h−6 : h]) ≥ 500` (a real event precedes — the model is
  exiting from something reality actually priced).

An actual-collapse hour h is an **event-exit-lag hour** (the census
population) iff additionally:

- **M1 (model still inside its event)** `m[h] ≥ 200` AND (withheld-family
  dual at h ≥ 100 OR ORDC-total shortfall at h > 0) — the reserve-step
  decay is lagging;
- **M2 (guard hold active)** adaptive `floor_usd[h] ≥ 10` — the
  release-guard floor is holding at h (h is an in-window floored hour;
  $10 clears every storage vom and is two orders below any event-day
  floor);
- **M3 (storage re-timing)** storage discharge at h ≤ 100 MW AND
  max(discharge[h+1], discharge[h+2]) ≥ 300 MW — the held energy releases
  late;
- **M4 (model release is a LAG, not a miss)** min(m[h+1], m[h+2]) < 200 —
  the model exits within 2 h;
- **M5 (inputs aligned at h)** |model net load[h] − actual net load[h]| ≤
  2,500 MW (net load = demand − wind − solar on both sides; actual from
  EIA-930 Demand − NG:WND − NG:SUN);
- **M6 (reality's scarcity over)** measured `rtorpa[h] < 50` AND
  `rtordpa[h] < 50`.

Reported alongside, NOT in the population (informational strata, each with
its hour list):

- **S1 extended holds**: A1–A3 + M1–M3 + M5–M6 but model release later
  than h+2 (fails M4);
- **S2 non-guard exit lags**: A1–A3 + M1 + M5–M6 but `floor_usd[h] < 10`
  (the hold is carried by reserve-step decay alone — NOT repairable by the
  exit condition; if this stratum dominates, that fact is the finding);
- **S3 collapse hours where the model had already released** (A1–A3, model
  m[h] < 200) — the count of exits the model already gets right, the
  denominator for how exceptional the lag is.

## 3. The trailing-edge separation measurement (the re-identification test)

The pass-1 settle series is **not a committed artifact** (verified before
this precommit: the adaptive sidecar carries only `s_model_day`,
`p_hat_day`, `floor_usd`), so the per-hour pass-1 settle margin at held
hours is NOT measurable zero-solve; h3068's $675 exists only in the
ercot-223 record. What IS exactly measurable zero-solve is the
**structural** exit-condition candidate, which needs NO new numeric
constant:

> after the day's first guard-released window hour (the spike the floor
> anticipates is REALIZED), the remaining floored hours of that day's
> window release too — the anticipation is resolved for the event, not
> per-hour.

Its affected set is exactly enumerable from the committed adaptive
sidecar: **TRAILING SET** = { in-window hours (hod ∈ {17,18,19,20}) with
`floor_usd ≥ 10` whose day has an EARLIER in-window hour with
`p_hat_day × 5000 ≥ 10` and `floor_usd = 0` (a guard release) }. For each
trailing-set hour the census records `a[h]`, `m[h]`, storage discharge,
family duals, and classifies it:

- **release-RIGHT**: `a[h] < 200` (the hold is manufacturing a phantom
  event tail — releasing it moves toward reality);
- **release-WRONG**: `a[h] ≥ 200` (the hold is doing correct work —
  releasing it would surrender a real elevated hour).

The separation verdict is mechanical: the structural exit condition is a
**measured re-identification** (licensing a Phase-1 precommit + ONE
forward-span A/B per the charter) iff

- **T1** every census-population hour (§2) is in the trailing set (the
  condition actually reaches the object population), and
- **T2** release-WRONG = 0 across 2024/2025 (the condition surrenders no
  correctly-held hour; the trailing set is small enough — prior ≤ ~10
  hours — that a zero bar is the honest one).

A **threshold-form** re-identification (a new exit constant X < $1,000 on
pass-1 settle) is NOT measurable zero-solve for the reason above; if T1/T2
fail, no threshold value can be identified from committed artifacts, and
the lane records the kill — it does NOT spend the A/B license probing for
one, and any pass-1-settle instrumentation need is flagged to the owner as
its own future charter.

## 4. Population prior and kills, declared ex ante

**Prior.** The ercot-223 record measured 563 floored / 5 released window
hours in 2024 and ZERO floors in 2025 (the self-extinction) on the
2026-08-19-era config; the forward keeper's constants for the adaptive
family are unchanged since. Expected census population: **1–3 hours,
point prior 2** (h3068 + at most one or two summer-event exit edges in
2024; 2025 expected to contribute 0, and expected to carry few or no
floors at all). Expected trailing set: ≤ ~10 hours. A population an order
of magnitude above the prior (≥ 10) means the signature construction is
looser than the object and the session says so rather than proceeding.

**Kills — any one fires ⇒ Phase-0 records the kill in the finding, the
calibration log and the matrix evidence note, and the lane STOPS (no
Phase-1 precommit, no solve, no threshold search):**

- **K-1** the census population is {h3068-2024} alone (or empty).
- **K-2** T1 fails: some census-population hour is NOT in the trailing
  set (the structural exit condition cannot reach the population it is
  meant to repair).
- **K-3** T2 fails: release-WRONG > 0 (no clean separation — releasing
  the trailing set would surrender correctly-held hours; per the charter,
  "no threshold separating exits from holds", in the structural form that
  is zero-solve-measurable).
- **K-4** the S2 stratum (non-guard exit lags) is larger than the census
  population — the exit stickiness is predominantly NOT the guard's, and
  repairing the guard exit would be treating the minority carrier.

**If no kill fires**, the deliverable of Phase-0 is the census record +
finding + a SEPARATE Phase-1 precommit (its own push + blob-verify before
any code edit or solve) for the structural exit condition: one new
default-False `ScenarioConfig` boolean gated inside the existing
`iso == "ERCOT"` adaptive block, zero new numeric constants, ONE
forward-span A/B (solve 2023 2024 2025 sequentially, score --years 2024
2025, 2023 side-effect-reported per the two-config discipline), with the
charter's kill set (no new shed; C3c no-worsen per year; off-season
intact; lidless spur no-increase; coal ≤ +0.5 TWh; CT/ST ±1.0 TWh)
declared there in full. Borderline verdicts and ANY keeper change
ESCALATE, never self-adopt.

## 5. Fences and hygiene

- Zero-solve Phase-0: committed artifacts + measured `data/raw` series,
  read-only; no LP, no replay (a unit-level question would license a
  replay per the charter; none is expected — the census is hour-level).
- Years read ⊂ {2024, 2025}; no `--holdout-authorized`; the holdout
  freeze is untouched (`[R-HOLDOUT]`).
- ERCOT surfaces only (`[R-ISO-SCOPE]`).
- No mechanism verdict moves in Phase-0; the census outcome lands as an
  evidence NOTE on the ERCOT matrix shard's
  `ercot_storage_adaptive_expectation` cell (the ercot-239 §4-style
  permission), and as calibration-log entry ercot-243.
- Probe: `scripts/probes/ercot243_release_exit_phase0.py` →
  `results/calibration/ercot243_release_exit_phase0.json`, both committed.
- Push order: this precommit (blob-verified) → probe + JSON → finding +
  log + matrix note → (only if licensed) the Phase-1 precommit and its
  deliverables. Small commits off the fresh-main base; `git push`;
  HTTP/1.1 retry before any transport conclusion; blob-verify every
  pushed file ≥ 300 lines (`[R-PUSH]`).
- The parallel data task (2024/2025 all-resource SCED corpus intake,
  PRECOMMIT-ercot242 §6) is FLAGGED to the owner in the finding, not
  executed (unchartered).
- DO-NOT-REDO honoured in full (room-axis R, graded ladder R, ercot-219
  option-b R, storage RT offer surface R/Door A, topology G, cross-year
  seed R, ORDC/adder closures, ercot-178/-180 grains R,
  lowcurve/negative-offer variants, demand-gap CLOSED); the ercot-241/242
  committed measurements are read, never re-run.
