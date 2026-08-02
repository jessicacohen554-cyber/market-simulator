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

**Gates (all pre-registered before any arm solved).** K1 PASS — each arm's own
`meta.shared_inputs` confirms its intended input state (A: both absent; B: both
present), never the staging. K2 PASS — arm A reproduces the committed keeper's
C3a *exactly* (56.00 / 37.82 / 38.60 $/MWh) and its D-1 rows to three decimals,
so the A/B contrast is clean and the control is the keeper's degraded state.
K3 PASS — no `ScenarioConfig` field differs between arms. K4 PASS — both carry
[2023, 2024, 2025]. K5 PASS — arm B logs `seam import cap set to
16055/16452/16148 MW`, `RoR split — 69/171` (2023) and `61/160` (2025) plants
flat, and `min-flow floor reconciled with the RoR split … allocated over the
reservoir class only`.

**The structural result — the seam, read from the LP's own duals:**

| arm | year | seam limit | binding h | congestion rent |
|---|---|---|---|---|
| A control | 2023 / 2024 / 2025 | 7,500 MW | **757 / 472 / 857** | −$187.2M / −$15.1M / −$26.9M |
| B restored | 2023 / 2024 / 2025 | 16,055 / 16,452 / 16,148 MW | **0 / 0 / 0** | **$0.000M** |

The retired fitted DOF is off the binding path in every hour of every year, and
the binding constraint returns to the measured corridor envelopes, whose own
binding counts rise to take it back (2023: `+WECC_DSW>SP15_rest` 2,850 → 3,360 h
reaching its full 6,755 MW; `+WECC_PNW>NP15` 3,116 → 3,273 h reaching 3,846.5 MW).

**The price result — the gate did NOT close, and that is the honest headline.**

| year | model λ A → B | actual RT | miss A → B | verdict |
|---|---|---|---|---|
| 2023 | 56.00 → 55.84 | 54.17 | +3.4 % → +3.1 % | PASS |
| 2024 | 37.82 → 37.79 | 34.60 | +9.3 % → +9.2 % | PASS |
| 2025 | 38.60 → 38.52 | 34.39 | **+12.2 % → +12.0 %** | **FAIL (band ±10 %)** |

C3a-2025 needed ≤ +10.0 % — a −$0.77/MWh move — and got −$0.08. **No closure of
the C3a-2025 caveat is claimed**, and the direction being favourable is *not* the
justification for the promotion (rule 1): the input goes in because it is the
accurate one, and would equally have gone in had the residual worsened.

**Why the movement is small is measured, not assumed.** Relaxing the seam does
not buy several TWh of import, because the *measured* corridor envelopes bind
almost immediately behind it. The realised substitution is small and clean —
import in, gas CC out, essentially 1:1:

| year | import | CC_REGULAR | CT_PEAKER |
|---|---|---|---|
| 2023 | +0.456 TWh | −0.398 | −0.050 |
| 2024 | +0.153 TWh | −0.157 | — |
| 2025 | +0.398 TWh | −0.398 | — |

**The hydro half is very nearly inert at fleet level** — an unpredicted result
worth recording. Restoring the classifier pins 904.6 MW (13.5 % of the EHA
fleet) flat, but the fleet diurnal profile barely moves: 2023 night
2,972 → 2,966 MW, belly 1,800 → 1,805, evening 3,781 → 3,779, cv 0.489 → 0.489;
2025 night 2,983 → 2,972, cv 0.554 → 0.554. The armed `hydro_min_flow_floor`
already held most of that overnight level, so the RoR split mostly re-attributes
*which* plants supply it rather than changing the shape. This does not make the
restoration optional (the attribution is the accurate one, and it is what the
D-2 mechanism ledger reports), but it does mean the caiso-125 §1 bang-bang
signature is **not** resolved by the RoR split alone — filed as a live object.

**Determination: CALIBRATED-WITH-CAVEATS, unchanged**, 0 FAILs, the same 2 of 3
non-protective ledgered slots. No gate regressed; every C3a year improves.
Protective gates hold on both arms (C7 PASS, C8 PASS, D-4 PASS, D-2 PASS). D-1's
`ST_GAS` FAIL rows (2024 r 0.158, 2025 r −0.049) are bit-comparable to the
control's (0.162 / −0.044) and to the committed keeper's — pre-existing, on a
class the rubric skips as immaterial (0.3 % / 0.1 % of ISO load), **not**
introduced here.

**Arm B was PROMOTED KEEPER** (`2026-08-02-caiso157-partition-restore-b`) on
structural-integrity grounds under rules 1/14/20/24, with the price outcome
recorded above rather than buried. `audit_keepers.py`: 0 failures, 0 warnings.

**Attribution arms C (seam only) and D (hydro only)** run after B and are
registered when they land; if the session is cut before they complete, that is
stated here rather than omitted. Their expected reading, given the fleet-level
hydro inertness above, is that arm C ≈ arm B and arm D ≈ arm A.

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

## F. DO-NOT-REDO (binding on successors)

1. **Do not re-test "restore the partitions" as a price lever.** It is measured:
   the seam relaxation buys +0.456 / +0.153 / +0.398 TWh of import and −0.08 to
   −0.16 $/MWh of λ, because the measured corridor envelopes bind behind it.
   Any successor proposing the import seam as a C3a-2025 lever must bring
   evidence against *that* measurement.
2. **Do not read this session as reopening C3a-2025 or C3c-2023/24.** Both
   remain the owner's ledgered caveats from caiso-145. This session claims no
   closure of either. It *does* correct one premise in the record — caiso-140's
   D3 walk-down attributed the Sep–Dec 2025 belly λ to a "2.7–3.0 GW economic
   import-parity plateau", and §B shows that in 18.0 % of those hours the
   plateau was partly a hard fitted cap — but correcting the premise did not
   move the gate, so it is a record correction, not a lever.
3. **Do not quote the RoR split as a shape fix on the strength of its arming.**
   §D measures it very nearly inert at fleet level in this configuration. The
   caiso-125 §1 overnight bang-bang signature is **not** resolved by it.
4. **Do not widen the input-completeness guard by analogy.** Each added
   armed-flag/partition pair owes its own demonstration that "partition absent"
   is distinguishable from a legitimate ISO-level no-op (as `partition_expected`
   does for ERCOT). A guard that fires on a legitimate no-op would break lanes.
5. **Do not treat the bundle sweep as the durable record.** Top-15-per-ISO
   retention pruned `caiso138_envclip_B` and `caiso139_control_A` during this
   session's registrations, and further CAISO registrations may prune
   `caiso142_*`. The committed probe transcript
   (`PROBE-caiso157-partition-audit-2026-08-02.txt`) is the permanent record of
   every bundle's armed-vs-pinned state; re-running the probe later will show
   fewer bundles, which is retention, not a change in the finding.
6. **Do not assume other ISOs need this fix.** §A measured every ISO's
   designated keeper: CAISO alone was degraded. Re-run
   `_caiso157_partition_audit.py` section 1b rather than assuming either way.
