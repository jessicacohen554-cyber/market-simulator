# Holdout-quarantine policy memo (2026-07) — rule 22 drift

**Scope.** CLAUDE.md rule 22 designates 2022 and H1-2026 as holdouts under
"FULL quarantine: no solves, no scoring, and no data intake" until an ISO's
`calibration-complete` marker exists. PRs #1298, #1300, #1304 (2026-07-03/04,
branch `claude/data-holdout-2022-2026-intake-3oc65k` +
`claude/data-holdout-intake-followups-fu3w37`) intook 2022 + H1-2026 source
data for ERCOT and PJM. `frontend/data/backcast/calibration-complete.json`
still reads `"complete": {}` — no ISO has been declared complete, no holdout
solve has been run, no holdout year has been registered on the dashboard. The
rule's *intake* clause has been breached in practice, under an explicit,
repeated owner instruction ("data intake only, no model solve — unblocks
D-6") recorded in `docs/out-of-sample-results-2026-07.md` §1.1. This memo
inventories what exists, traces whether the breach created a path to an
un-authorized solve or score, and lays out the policy choice this creates.

## (a) Inventory — what's in-repo, what's missing

**ERCOT + PJM (intake landed 2026-07-04):**

| Input | ERCOT 2022 | ERCOT H1-2026 | PJM 2022 | PJM H1-2026 |
|---|---|---|---|---|
| EIA-930 fuel-mix + demand (bench) | ✅ full | ✅ through Jun 30 | ✅ full | ✅ through Jun 30 |
| CAMPD unit-level (fleet + bench) | ✅ full | ⚠️ Q1 only (EPA hasn't posted Q2) | ✅ full | ⚠️ Q1 only |
| Unit-outage overlay (derived) | ✅ 569 windows | ⚠️ 220, clipped Mar 31 | ✅ 1,103 windows | ⚠️ 261, clipped Mar 31 |
| Delivered gas (EIA N3045) | ✅ 12 mo | ⚠️ Jan–Apr (EIA lag) | ✅ 8 zones | ⚠️ Jan–Apr |
| ERCOT zonal gas hub (Sch5 + Waha) | ✅ 7 zones | ⚠️ 7 zones, Jan–Apr partial | n/a | n/a |
| PJM native `gen_by_fuel` (DataMiner) | n/a | n/a | ✅ | ✅ full H1 (owner UI export) |
| Coal/CO2 F923 overlays + eGRID2022 vintage | ✅ (true 2022 eGRID) | ⚠️ Jan–Apr, parasitic deferred | ✅ | ⚠️ Jan–Apr |
| Facility-level CAMPD outage CSVs | ✅ +190/+62 windows | ⚠️ +79/+16, Q1-clipped | dead path (PJM keeper uses unit-level) | dead path |

**Still missing, ERCOT + PJM:** CAMPD Q2–Q4 2026 (EPA unpublished), delivered
gas May-2026+, `eia_demand_profiles` 2026 (full-8760 contract — unbuildable
from a partial year, F3, no builder script exists), `CALIBRATION_YEARS`/
`HENRY_HUB_ACTUAL` in `scripts/build_calibration_reference.py` have no 2026
entry (F4 — deliberately deferred to validation time).

**CAISO / MISO / NYISO / NEISO: zero holdout intake.** No 2022/2026 EIA-930,
CAMPD, outage, or delivered-gas rows exist for these four ISOs. The gap noted
in the original (pre-intake) assessment is unchanged for them.

**Net:** a 2022/H1-2026 one-shot score is *nearly* mechanically possible for
ERCOT today (CAMPD Q1-only 2026 and the missing demand-profile build are the
remaining blockers); PJM is a step behind ERCOT on the same two blockers; the
other four ISOs are untouched.

## (b) Contamination-risk trace

Traced whether any code path can *read* 2022/2026 outside an explicit,
authorized one-shot score.

1. **Loaders have zero year restriction.** `load_demand`,
   `load_eia_hourly_benchmark`, `load_fleet_from_csv`,
   `unit_outage_derate_factors`, and the fuel-basis functions all load
   2022/2026 exactly as they load 2023–2025 — confirmed directly, since
   `scripts/verify_holdout_intake.py` calls these same production functions
   to prove the intake is loader-resolvable. This is required for the
   one-shot score to work later, but it also means nothing at the loader
   layer stops a solve today.
2. **The solve entry points have zero year restriction.**
   `scripts/run_calibration.py` and `scripts/run_calibration_full.py` both
   take `--year` as a bare `argparse` int list (no `choices=`, no validation).
   `run_calibration.py --year` help text says "(2021-2024)" but nothing
   enforces it. **A direct invocation of either script with `--year 2022` or
   `--year 2026` solves today, with no code-level gate at all.**
3. **The GitHub Actions `workflow_dispatch` path (`calibration-run.yml`) *is*
   gated** — its shell wrapper rejects any `year` input not in
   `{2023, 2024, 2025}` before invoking `run_calibration_full.py`. This
   protects only the GH-Actions-UI trigger path, not a script run directly in
   a sandbox/session (which is the normal way calibration solves happen per
   CLAUDE.md's own parallel-launch guidance).
4. **The dashboard-registration gate (`scripts/audit_keepers.py`,
   `scripts/legitimacy_diagnostics.py --keepers`, D-6 quarantine check) is
   real code and correctly implemented** — it fails any registered bundle
   whose sidecar `years` falls outside `{2023, 2024, 2025}` unless that ISO
   has a `calibration-complete` marker. **But it is not wired into any CI
   workflow.** `grep -rl "audit_keepers\|legitimacy_diagnostics"
   .github/workflows/` returns nothing; `.github/workflows/lint.yml` runs only
   `ruff`, and the only workflow that runs `pytest` (`clean-parity.yml`) runs a
   narrow file list that doesn't include `test_legitimacy_diagnostics.py` or
   `test_calibration_verdict.py`. **CLAUDE.md rule 22's claim "CI enforces the
   quarantine" is not currently true** — these are correct standalone scripts
   that only catch a breach if a human/agent chooses to run them before
   committing a dashboard bundle.
5. **Data-intake scripts (`fetch_campd_unit_level.py`,
   `fetch_eia930_long.py`, `fetch_eia930_balance.py`,
   `fetch_eia_delivered_gas.py`, `derive_ercot_zonal_gas_hub.py`) have no year
   gate either** — this is exactly how the 2026-07-04 intake ran, and is the
   literal breach of rule 22's "no data intake" clause, done under explicit,
   session-logged owner authorization each time.

**Bottom line:** no solve and no score have happened — `calibration-complete.json`
is empty and the audit doc explicitly records "no holdout LP solve was run."
But the *only* thing currently preventing a future session from running
`run_calibration_full.py --iso ERCOT --year 2022` and registering it is
written instruction and reviewer attention — there is no code-level or
CI-level backstop on the two paths that matter most (direct solve invocation,
and the D-6 dashboard check never running automatically).

## (c) Two policy options

**Option 1 — strict re-quarantine.** Move landed holdout-year raw files
(the ERCOT/PJM 2022 + H1-2026 files from PRs #1298/#1300/#1304) into a
segregated path (e.g. `data/raw/_holdout-quarantine/<ISO>/<year>/`) that
ordinary loaders don't scan; loaders require an explicit opt-in
(`MARKET_SIM_ALLOW_HOLDOUT=1` + the ISO's `calibration-complete` marker
present) to read from it. CI enforcement: a new required workflow job that
(i) greps `data/raw/**` for any file whose name/content encodes 2022 or 2026
outside the quarantine path and fails the PR, (ii) runs the existing
`audit_keepers.py --keepers` / `legitimacy_diagnostics.py --keepers`. Pros:
matches rule 22's literal text exactly, technically closes the intake
channel, not just the solve/score channel. Cons: discards already-validated
work (F1/F2/F5/F6 close-outs, byte-identical rebuild checks against
2023–2025) that was done under explicit, repeated owner authorization; adds a
new loader-side code path (opt-in env var) that has to be built, tested, and
kept from rotting; doesn't change the fact that the *actual* leak vectors
(entry-point `--year`, D-6 CI wiring) still need fixing regardless.

**Option 2 — amend rule text, harden the two real gaps.** Rewrite rule 22 to
explicitly split "data intake" (owner-authorized, reproducible, no-LP,
allowed any time — codifying what already happened and what
`docs/out-of-sample-results-2026-07.md` already argues) from "solve" and
"score" (still fully quarantined until `calibration-complete`). Pair the
wording change with the two enforcement fixes items 3–4 above actually need,
independent of which option is picked:
- Add a real `--year` gate to `run_calibration.py` / `run_calibration_full.py`
  (or a shared chokepoint in `runner.py`): refuse any year outside
  `{2023, 2024, 2025}` unless `--holdout-authorized` is passed *and* the
  target ISO already has a `calibration-complete` marker.
- Wire `audit_keepers.py --keepers` and `legitimacy_diagnostics.py --keepers`
  into an actual required CI workflow (new `holdout-quarantine.yml` job, or a
  step added to `lint.yml`), so the D-6 check the rule already describes
  actually runs on every push/PR instead of only when someone remembers to.
Pros: matches what already happened and was explicitly authorized twice;
keeps the audited, reproducible intake work; the two CI/code fixes are small
and directly close the paths that matter (an accidental solve, an
unregistered-but-uncaught dashboard commit). Cons: weaker physical isolation
than Option 1 — the raw files sit in the ordinary tree, so a determined
in-session action (not just an accidental one) can still read them into an
ad hoc, unregistered analysis; relies more on the new entry-point guard and
code review than on file-location isolation.

## (d) Recommendation

Recommend **Option 2**. The intake already happened, twice, under explicit
owner instruction, with real reproducibility discipline (validate-first
rebuilds asserting 2023–2025 rows byte-identical before extending); reversing
it in Option 1 destroys audited work to close a channel — data intake — that
was never the vector that produces overfitting. The vector that matters is a
*solve* or a *score*, and that's still at zero occurrences with the
`calibration-complete` marker file empty. The two concrete gaps found in (b)
— no code-level `--year` gate on the solve entry points, and the D-6 CI check
not wired into any workflow — should be fixed regardless of which option the
owner picks; they're cheap and they close the actual risk.

**Owner decision required:** which policy — strict re-quarantine (Option 1,
move/gate the landed files) or amended rule text (Option 2, intake allowed,
solve/score still blocked, harden the two CI/code gaps) — and, either way,
explicit authorization to (i) add the `--year` guard to the calibration entry
points and (ii) wire `audit_keepers.py`/`legitimacy_diagnostics.py --keepers`
into CI. No holdout-year solve or score was run to produce this memo.
