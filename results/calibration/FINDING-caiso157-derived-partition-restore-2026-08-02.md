# FINDING — caiso-157: two absent derived CLEAN partitions silently re-armed a RETIRED fitted import scalar across five CAISO keeper promotions

**Pre-registration:** `PREREG-caiso157-derived-partition-restore-2026-08-02.md`
(committed before any arm solved).
**Probes:** `scripts/probes/_caiso157_partition_audit.py` (transcript
`PROBE-caiso157-partition-audit-2026-08-02.txt`),
`scripts/probes/_caiso157_arm_compare.py`.
**Class:** input-integrity defect fix (the caiso-152/153/155 class). No matrix
cell re-tested, no new `ScenarioConfig` field, **no config value changed in any
arm**. Rules 14 `[R-ACCURATE]`, 20 `[R-DOF]`, 24 `[R-REGISTRY]`.
**Rule 22:** 2023/2024/2025 only; CAISO holds no `complete` and no `final`
marker; no out-of-training year touched; no marker written.

---

## A. The defect

`data/clean` is derived-and-disposable (gitignored), so it does not travel with
the repo — every environment rebuilds it from `data/raw` (`scripts/data/curate_*.py`,
or `scripts/regenerate_clean.py` for the whole tree). Two partitions the CAISO
keeper's armed flags require were absent at solve time, and both loaders were
written to *degrade gracefully*: they log a warning and the mechanism becomes a
silent no-op.

| clean partition | armed flag | behaviour when absent |
|---|---|---|
| `hydro-plant-modes/CAISO` | `hydro_ror_split` | `data/hydro.py`: *"armed but no hydro-plant-modes classifier partition — fleet left fully shapeable"*. No RoR flat stamp, and the armed `hydro_min_flow_floor` is no longer reconciled onto the reservoir class alone (`scenarios.py` ~L1027). |
| `capacity-deliverability/CAISO` | `capacity_deliverability_limits` | `interchange/spec.py` Part A no-ops (`_seam_mw` falsy), so the published branch-group **MIC** seam cap is never installed. |

**It is provable per bundle.** `meta.shared_inputs` pins exactly the
derived-not-committed inputs a solve read (`bundle_io.write_derived_solve_inputs`,
whose own docstring calls this *"the silent-degrade trap"* and notes that *"an
absent partition records nothing, exactly the state the solve degraded to"*).
Auditing all 131 bundles on disk: **24 of 34 armed (bundle, mechanism) pairs are
degraded, and every one is CAISO.** Pinned through `caiso142_*` (2026-07-30);
absent from `caiso146_*` onward (2026-07-31) — so the keepers promoted at
**caiso-146, -147, -148, -151 and -153** all solved with both mechanisms inert.
No caiso-146…155 log entry mentions it.

**The blast radius is bounded — CAISO only.** The same check on each ISO's
*designated keeper*:

| ISO | keeper | degraded |
|---|---|---|
| **CAISO** | `2026-07-31-caiso153-reid-b` | **`capacity_deliverability_limits`, `hydro_ror_split`** |
| ERCOT | `2026-08-02-ercot150b-zonal-anchor` | none |
| MISO | `2026-07-31-miso-109b-hy-level` | none |
| NEISO | `2026-07-31-neiso-72-hy-window` | none |
| NYISO | `2026-08-01-nyiso109-zonal-margin-anchor` | none |
| PJM | `2026-07-31-pjm-143b-hy-level` | none |

No other lane has an action here.

## B. Why it is a governance defect and not housekeeping

With Part A a no-op the CAISO import node falls back to the hard-coded
`WECC_import_simultaneous` interface limit, **`cap_mw = 7,500 MW`** — a
**residual-identified fitted scalar**. The keeper's own committed
`calibration_attestation.json` DOF ledger carries it verbatim as:

> `"identification": "residual"`, `"value": 7500.0`,
> `"where": "iso_configs.py CAISO interface_limits (fallback; capacity_deliverability_limits OFF only)"`,
> `"source": "… SUPERSEDED in the caiso-51 keeper by the published branch-group MIC sum … `**`Not in the keeper binding path`**`; governs the forecast / non-deliverability path only."`

and `iso_configs.py` (L414–428) records it as "a fallback-only DOF-ledger row
(scalar-remediation B-CAI-1, 2026-07-05) **so this fallback cannot silently
re-become the binding import limit**."

**Measured on that same keeper's committed `hourly/class_hourly_<year>.parquet`
(P1, `klass == "import"`, ±0.5 MW), the attestation is false:**

| year | hours pinned at 7,500 MW | share | mean import MW | binding concentrates at |
|---|---|---|---|---|
| 2023 | **757** | 8.64 % | 4,130 | hod 0–2, 23; Jan/May/Feb/Mar |
| 2024 | **472** | 5.39 % | 4,514 | hod 0–4; Jun/Nov/Dec/May |
| 2025 | **864** | 9.86 % | 4,692 | hod 0–4; Dec/Nov/Jun/Oct |

p95, p99 and max import are *exactly* 7,500.000 MW in all three years, and
**Sep–Dec 2025 is 528 of 2,928 hours (18.03 %)** — the window of the ledgered
C3a-2025 caveat. A retired fitted DOF that can silently re-arm itself is an
off-registry channel in effect (rule 24), whatever the intent.

**The published input the keeper intends**, resolved through the solve's own
loader (`import_limit_by_area` → `aggregate_by_zone` → `IMPORT_ZONE`):
**16,055 / 16,452 / 16,148 MW** for 2023/24/25 (36/36/33 branch-group areas).

This also reconciles a standing matrix claim rather than contradicting it.
caiso-133 measured the seam cap **inert in dispatch** — at 16 GW it sits above
the two corridor legs' own measured import envelopes (max 9,631/9,557/10,777 MW),
so its dual is 0.000 in every hour. That is true *of the accurate seam*. At the
degraded 7,500 MW the seam sits **below** those envelopes, which is exactly why
it became binding. Restoring the partition hands the binding limit back to the
measured corridor envelopes (`caiso_corridor_flow_limit`, armed) — i.e. back to
the instrument caiso-133 identified.

## C. The hydro half

The regenerated `hydro-plant-modes/CAISO` partition classifies **195 plants: 84
non-shapeable (904.6 MW, 13.5 % of the 6,703 MW EHA conventional-hydro fleet)
and 111 shapeable** (methods: `eha_mode` 97, `hilarri_reservoir` 78,
`hilarri_no_reservoir` 13, `corps_dam` 7; completion validation 86/97 plants and
84.7 % of labeled MW). Absent, the whole fleet is treated as shapeable — which is
precisely the caiso-125 §1 defect the RoR split was built to fix (the fleet
moving as one bang-bang block riding the p95 envelope ceiling overnight).

Baseline on the degraded keeper's own hourlies (P1 hydro, mean MW by hour band):

| year | night 0–5 | belly 9–15 | evening 17–21 | evening/night | cv | TWh |
|---|---|---|---|---|---|---|
| 2023 | 2,972 | 1,800 | 3,781 | 1.27 | 0.489 | 24.33 |
| 2024 | 2,947 | 1,508 | 3,275 | 1.11 | 0.526 | 22.27 |
| 2025 | 2,983 | 1,208 | 3,175 | 1.06 | 0.554 | 21.16 |

Overnight output is pinned near 2,950–2,980 MW in all three years regardless of
the water year — the flat-block signature.

## D. Arms — results

*(pending: filled from the four solved bundles.)*

## E. The root-cause guard

`market_sim.data.input_completeness.check_clean_partitions`, called once at the
top of `pipeline.year.run_year_solve` — the single per-year seam both
orchestrators share — raises `DegradedInputError` when an armed mechanism's
required clean partition is absent, naming every offender and the curate script
that rebuilds it. **No `ScenarioConfig` field, no threshold, no tunable**: a pure
config-vs-disk consistency assertion, ISO-generic, and a no-op for every flag
left at its default (so the entire default-off surface is untouched, and the
guard has no LP path — when it does not raise, the code after it is
byte-identical).

`capacity_deliverability` gained public `partition_expected` / `partition_available`
so the guard can tell a legitimate ISO-level no-op (ERCOT publishes no locational
RA construct) from a partition that was never curated. 7 unit tests over a tmp
`CLEAN_DIR` pin: defaults never raise; each armed flag raises when its partition
is absent; both offenders are reported together; present partitions pass; ERCOT
is not degraded; the NEISO→ISONE alias resolves.

Scope is deliberately the two mechanisms this session proves. **Filed, not
absorbed:** widening the check to other armed-flag/partition pairs, each of which
owes its own check that "absent" is distinguishable from a legitimate no-op.

## F. DO-NOT-REDO

*(pending: written with the arm results.)*
