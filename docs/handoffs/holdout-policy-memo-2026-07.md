# Holdout-quarantine policy memo (2026-07) — rule 22 drift

**Scope.** CLAUDE.md rule 22 designates 2022 and H1-2026 as holdouts under
"FULL quarantine: no solves, no scoring, and no data intake" until an ISO's
`calibration-complete` marker exists. PRs #1298, #1300, #1304 (2026-07-03/04,
branch `claude/data-holdout-2022-2026-intake-3oc65k` +
`claude/data-holdout-intake-followups-fu3w37`) intook 2022 + H1-2026 source
data for ERCOT and PJM. `frontend/data/backcast/calibration-complete.json`
at the time this memo was written read `"complete": {}` — no ISO had been
declared complete, no holdout solve had been run, no holdout year had been
registered on the dashboard. **Update 2026-07-11:** this is no longer
current — NEISO was declared complete 2026-07-07 (keeper
`2026-07-08-neiso-54-steamgas-ct`) and its 2019 + H1-2026 locked-test
one-shot was scored once, against the frozen `neiso-53` config
(`2026-07-07-neiso53-winter-fuelsec-coldsnap`), and stands per rule 22 — it
was not re-scored when neiso-54 was promoted. The rest of this memo's
analysis (the intake/solve/score gap trace, the Option 1/2 policy choice)
is otherwise unaffected and is left as written. The
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
`HENRY_HUB_ACTUAL` in `scripts/data/build_calibration_reference.py` have no 2026
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
   **[Landed 2026-07-06 for `run_calibration_full.py` — see (e).]**
   `enforce_holdout_year_gate()` (module scope, `scripts/run_calibration_full.py`)
   now hard-fails any `--year` outside `{2023, 2024, 2025}` unless
   `--holdout-authorized` is passed **and** the target ISO already carries a
   `calibration-complete` marker in `calibration-complete.json`. This closes
   the gap for the production entry point named in CLAUDE.md rule 22's
   enforcement clause. `scripts/run_calibration.py` (the non-`_full` script)
   still has no such gate — confirmed still open, verified against current
   source.
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
   **[Landed since this was written — confirmed in current tree, see (e).]**
   `.github/workflows/ci.yml` now has a required `quarantine-gates` job that
   runs `audit_keepers.py --check` and `legitimacy_diagnostics.py --keepers`
   (which calls `run_d6_quarantine`) on every pull request. CLAUDE.md rule
   22's "CI enforces the quarantine" claim is now true; this point's
   objection is resolved.
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
**[Update 2026-07-06 — see (e)]** Both backstops named in this sentence are
now landed and confirmed against the current tree: `run_calibration_full.py`
hard-fails an unauthorized holdout-year solve (point 2 above), and the D-6
dashboard check now runs automatically in `ci.yml`'s `quarantine-gates` job
(point 4 above) rather than only on manual invocation. The residual gap is
narrower than this paragraph states: `run_calibration.py` (the non-`_full`
script) and direct loader calls remain ungated by design (Option 2, see (e)).

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

## (e) Decision: DECIDED — Option 2, 2026-07-06 (lane L-2, gap register G-17)

**Status update.** Both of (d)'s "regardless of which option" hardening items
are now landed, changing the cost calculus below:

- The D-6 CI wiring (item ii) was already in place before this lane
  (`ci.yml`'s `quarantine-gates` job runs `legitimacy_diagnostics.py
  --keepers`, which calls `run_d6_quarantine`) — gap register W17 notes this
  as "de facto Option 2".
- The entry-point `--year` guard (item i) landed in this lane:
  `scripts/run_calibration_full.py`'s `enforce_holdout_year_gate` now hard-
  fails any `--year` outside `{2023, 2024, 2025}` unless **both**
  `--holdout-authorized` is passed **and** the target ISO already carries a
  `calibration-complete` marker in `calibration-complete.json`. A bare
  `--year 2022` invocation — the exact gap (b)(2) flagged — now exits 1
  before any solve starts. `legitimacy_diagnostics.py --keepers` also now
  recomputes (gap G-06, same lane) each keeper's D-2 forced-energy shares
  from the bundle's own committed data and fails on drift from the committed
  artifact — an independent integrity check, not a holdout-quarantine
  mechanism, but it closes a second "CI trusts a committed number instead of
  re-deriving it" gap in the same family.

No holdout data was touched, no holdout year was solved or scored, and
CLAUDE.md rule 22's text was **not** amended to produce this section — the
below is a decision draft for owner sign-off, not a decision.

**Exact consequences — Option 1 (strict re-quarantine).**

1. Move the ERCOT/PJM 2022 + H1-2026 files landed by PRs #1298/#1300/#1304
   (`data/raw/campd-unit-level/{TX,PA,...}_2022.parquet` and the matching
   EIA-930/outage/delivered-gas/F923/eGRID2022 files enumerated in (a)) from
   their current paths into a segregated tree, e.g.
   `data/raw/_holdout-quarantine/<ISO>/<year>/`.
2. Add an opt-in gate to every loader that currently reads them
   unconditionally (`load_demand`, `load_eia_hourly_benchmark`,
   `load_fleet_from_csv`, `unit_outage_derate_factors`, the fuel-basis
   functions) — a new `MARKET_SIM_ALLOW_HOLDOUT=1` env-var check plus the
   ISO's `calibration-complete` marker, per (c). This is new surface area in
   hot data-loading code paths that today have zero year-awareness by
   design.
3. Rewrite `scripts/verify_holdout_intake.py` (and any fetch script that
   writes into the old paths) to target the segregated tree.
4. Add a new required CI job that greps `data/raw/**` for any holdout-year
   file outside the quarantine path and fails the PR — a new enforcement
   surface, on top of (already-landed) D-6/D-2.
5. Net effect: the entry-point `--year` guard landed this lane becomes
   *redundant* defense-in-depth rather than the primary control — the
   loader-side opt-in becomes primary. Physically stronger (a determined
   read still has to pass two independent gates instead of one), but it
   re-opens code in `data/eia_loader.py` and friends that has been stable,
   and it discards nothing already computed — the intake itself stays, only
   its location and load path change.

**Exact consequences — Option 2 (amend rule text, harden the two real gaps).**

1. Rewrite CLAUDE.md rule 22 to explicitly read as two clauses: "data
   intake" (owner-authorized, reproducible, no-LP, allowed any time) vs
   "solve" and "score" (still fully quarantined until `calibration-complete`).
   This is a documentation-only change to `CLAUDE.md` — no code, no data
   movement.
2. Both enforcement items the option pairs with the wording change are
   **already done** (see Status update above) — Option 2 today costs
   **zero** further implementation. The rule-text edit is the entire
   remaining action.
3. Net effect: physical isolation stays weaker than Option 1 — the raw files
   remain in the ordinary `data/raw/` tree, so an in-session action that
   calls the loaders directly (not through the gated CLI entry point) can
   still read 2022/H1-2026 data into an ad hoc, unregistered analysis. The
   two things that actually produce an illegitimate result — an
   unauthorized *solve* and an unauthorized *score/registration* — are both
   gated today (this lane's `--year` guard; the pre-existing D-6 CI check).

**Recommendation (unchanged from (d), now cheaper): Option 2.** The
rationale in (d) still holds — the intake happened twice under explicit
owner authorization with real reproducibility discipline, and reversing it
destroys audited work to close a channel that was never the actual
overfitting vector. What's changed is the cost comparison: Option 2 now
requires *only* the CLAUDE.md wording edit (an owner-authored/approved
change to rule 22, out of scope for this lane), while Option 1 still
requires the loader-side opt-in gate, the file moves, and a new CI grep
job — net-new code whose only benefit over the status quo is closing the
"direct-loader-call, bypass-the-CLI" residual risk named in Option 2's own
"cons" above. If that residual risk is judged unacceptable, Option 1 remains
available as a superset: nothing here forecloses layering the loader-side
opt-in on top of Option 2's rule-text split later.

**Owner action — DECIDED 2026-07-06: Option 2.** The CLAUDE.md rule 22 wording
split described above has been landed verbatim (gap register G-17) — data
intake owner-authorized/no-LP-validated, solve and score still fully
quarantined, 2026 forecast-mode runs left unrestricted, enforcement citing
`ci.yml`'s `quarantine-gates` job and `run_calibration_full.py`'s
`--holdout-authorized` gate. Option 1's loader-side opt-in gate remains
available as a future superset if the residual "direct-loader-call,
bypass-the-CLI" risk is later judged unacceptable, but is not required by
this decision.
