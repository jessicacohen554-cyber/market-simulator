# Wave-manager tranche review — merged PRs #1491–#1500 (2026-07-06 EVE)

**Reviewer:** wave-manager session (adversarial, artifact-based; four parallel verification
sweeps + live re-runs of `audit_keepers.py --check` (PASS, 6 warnings) and
`legitimacy_diagnostics.py --keepers` (exit 1 — see CI-red section) on `origin/main` @ `141966f`).
Tranche = the 8 merged PRs #1491, #1493, #1494, #1496, #1497, #1498, #1499, #1500
(#1492/#1495 are issues, not PRs). No code/artifacts modified by this review except this file
and the gap-register addendum.

## Verdicts

| PR | Claim | Verdict | Key evidence |
|---|---|---|---|
| #1491 rps-fuels-golden-verify | CX-6a nuclear-RPS dispatch-row fix + golden re-verify | **CLEAN** | `_build_rps_row` nuclear block removed; 2 new fast-tier tests pass at HEAD; golden provenance cites both causal changes per REGEN_POLICY. Caveat: the golden band check has *never* executed on Actions (weekly cron/dispatch only — G-36 honest). |
| #1493 CAISO L-10 cont. | Re-gate arm complete (caiso-57 A/B FAIL → drag stays; caiso-58 v2-regate candidate); owner decision remains | **CLEAN** | Both sidecars full-span; G-11/G-14/G-15 register rows updated in-PR; C8 59.7/65.9/65.4% disclosed on sidecar+log+register; zero `src/` changes (docs/results only). Nit: 59.3/65.8 vs 59.7/65.9 rounding mismatch sidecar-vs-bundle. |
| #1494 governance | E7 adjudication (no-op, honest), statmode boxes, register addendum | **CLEAN** | Diff = docs-only, matches claims; ERCOT stale-box genuinely added; G-03 honestly reported NOT closed. NEISO omission not chargeable (neiso-49 merged 27 min after #1494). |
| #1496 L-7c closeout | CDR accreditation basis + foresight adjudication memo | **Recorded, light-touch** (successor session in flight) | New `constants.py` registries all primary-cited (CDR Dec-2025 / Fact Sheet / Brattle / CPUC) with in-comment arithmetic. Foresight option (B) recommended, owner checkbox open; no defaults flipped. |
| #1497 MISO L-14 cont. | miso-42 twin closed; posture lever built; honesty-gate REJECTED probe miso-43 | **CLEAN** (register doc-lag: W21/G-25 rows now stale) | Lever default-off, zero fitted params, byte-identity-when-off test; gate scored vs measured ASM series and FAILED honestly (headroom 3.7–4.2× measured); C1/C3c unmoved and said so. miso-42 promotion recommendation stands (owner). |
| #1498 NEISO keeper swap (neiso-49) | Netload ST_GAS limb replaces 2 disabled temp limbs; first ST_GAS D-1 pass (2025); budget unchanged | **DEFICIENT (minor — bookkeeping, not calibration substance)** | (1) keeper bundle `metrics.json` stale ("UNATTESTED", empty caveats) vs status.js — G-14-class inconsistency in a brand-new keeper; (2) G-16 register row not updated; (3) new floor's D-2 row lands in the `''` class bucket w/ nuclear-inclusive denominator (true 2023 share ≈3.7%, still within budget); (4) NEISO statmode stale-box missing after TWO unflagged swaps; (5) keeper self-promoted in-session with no owner sign-off language (CAISO/MISO lanes deferred — governance now inconsistent); (6) "measured" offer bands embed the residual-fitted CC 1.15 band via reach ratio 1.223 — dependency undeclared in DOF ledger. Floor itself is rules-17/18/19 compliant; rationale is genuinely structural (accepts worse 2023 r + deeper C5b). |
| #1499 orchestrator Stage 4 | P2 core extracted; byte-identity gate vs current keeper golden | **CLEAN on the core question** | Gate ran against the post-swap ercot34 golden (manifests pin keeper id; before/after hashes equal, verified independently; §7.3.6 records commits/tolerances). Bounded deficiencies: PJM/NYISO/NEISO gate skips unacknowledged in §7.3.6; merged tree (manual `run_calibration.py` conflict resolution, self-merged in 8 s, empty body) never re-gated; dirty-tree capture provenance; one deliberate semantic fix (AS-adequacy `fam_class>=0` filter) whose divergent combination is untested by construction. Stages 6/7 remain. |
| #1500 PJM reserve Phase 2 | Per-gen co-opt on published Manual-11 ORDC; pjm-81 probe | **DEFICIENT (hygiene — mechanism clean)** | ORDC = pre-existing cited csv, untouched; both flags default-off; pjm-81 full-span, honestly inert (C3c 0 h ×3; blocker re-attributed to commitment posture). BUT merged 2–4 min before CI finished and **two PR-caused failures are live on main**: `test_clean_io.py::test_datatype_list_matches_schemas` (ramp-capability missing from ALL_DATATYPES) and `test_data_dictionary_sync.py::test_every_schema_has_a_section` (no dictionary section rendered); plus incidental blanking of the demand-profile coverage row; empty PR body for a 3.7k-line merge. |

## CI state (verified locally, not from prose)

`origin/main` @ 141966f is **red on both PR-gate jobs**:

- Fast tier: `test_hydro.py::test_climatology_skips_uncovered_years` (stale expectation post-#1490
  EIA-930 backfill — issue #1495, reproduced locally) + the two #1500-caused failures above.
- Quarantine gates: `legitimacy_diagnostics.py --keepers` exit 1 — D-2 recompute mismatch on 4
  keepers (issue #1488): part machinery (`''` class-bucket denominator differs between the
  dispatch-parquet path and the payload-fallback path) and part genuine staleness (NYISO floors
  re-derived after nyiso-53's diagnostics were committed). D-9/D-6 quarantine checks themselves PASS.

## Keeper integrity (three same-day swaps, checked, not assumed)

ercot34 / nyiso-53 / neiso-49 each carry: full-span [2023,2024,2025] sidecar, bundle
`calibration_attestation.json` with 5-entry DOF ledger, registered zero-forcing ablation twin,
D-9 overlay quarantine PASS, rule-20 D-2 readout disclosed (NYISO CT still the known C8 hard
breach; NEISO within budget; ERCOT C8 12.4% inherited family), and a structural (rule-1)
promotion rationale in the calibration log. ercot34/nyiso-53 carry owner sign-off language;
neiso-49 does not (see #1498 deficiency 5). ercot34 promotion additionally closed G-12
attribution (ercot35/ercot36 A/B) and flips C1-2024 to PASS — the §4 "C1-2024 ledger" judgment
item is moot on the new footing.

## Hygiene items found

- Malformed registry id `2026-07-03-32-head-regate` (ERCOT head-regate probe solved 07-06;
  missing ISO token, wrong date) — corrupts E7 newest-run ordering.
- `audit_keepers.py` E9 grandfather still lists superseded `2026-07-03-miso-39-reserve-pergen` (G-03).
- `forecast-invariants.yml` heavy tier has never fired on Actions; the regenerated golden has
  zero CI executions.
- Register rows stale: W21/G-25 (posture lever now built + probed), G-16 (new NEISO keeper).
- Rule-15 sweep: all 24 `2026-07-06-*` registrations reconcile with the calibration log — no
  missing runs.

## Owner-decision queue (as of this review)

1. CAISO keeper: swap to `caiso-58-v2-regate` vs stay `caiso-51` (#1346; C8 59–71% rule-20 tension disclosed).
2. MISO keeper: promote `miso-42-coal-econ` (recommendation standing; twin now registered, floors shown near-redundant).
3. PJM C8 drag: adjudicate drag-sizing vs D-2-exemption NOW (#1484 falsified the "wait for G-21" sequencing).
4. Foresight `entry_lookahead_reprice`: sign off option (B) from #1496's memo (stays default-off).
5. Keeper-swap governance: may a lane self-promote (NEISO did) or is in-session owner sign-off required (ERCOT/NYISO pattern)? One sentence in CLAUDE.md or the rubric settles it.
6. Close issue #1345 (Zone-K LCR/TSL landed in the nyiso-53 keeper).
7. W22 ERCOT HSL intake: still credential-blocked (owner action).
8. G-40 MISO memory: fund/approve a ≥24 GB solve host (blocks MISO golden + posture window-rows + ensembles).
