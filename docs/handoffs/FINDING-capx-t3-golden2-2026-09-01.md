# FINDING — capx T3-NEISO-GOLDEN-2: the second §2.1b campaign (NEISO 2026–2050 BAU at the R-A-armed storage-entry posture)

**Session:** T3-NEISO-GOLDEN-2 (capacity-expansion / Forecast Finalization track), branch
`claude/capx-t3-golden-2-tm9eiy`, lane issued at the director's r#26 sitting, amendment 1
(`capx-director-ledger-2026-08.md` §0w + §3 Q25).
**Date:** 2026-09-01 · **HEAD at launch:** `5083e29e` (origin/main).
**Status:** §§1–4 are the PRE-DECLARATION — written and committed BEFORE any solve was
launched (rules 13/21 discipline; the T3-NEISO-GOLDEN §§1–4 pattern). §§5+ carry the
measured record and were written after.

---

## 1. The authorization (leg (d), cited verbatim)

Owner ruling **Q25**, capx r#26 sitting amendment 1, 2026-09-01, recorded in
`docs/handoffs/capx-director-ledger-2026-08.md` §3:

> **Q25** — The golden re-solve, fully ripe at last: Q16's ceiling premise discharged
> (FC-5 CAVEAT via D25; FC-6 CAVEAT via D26's repaired P1, which PASSES), the standing
> golden still records the pre-R-A posture (headline: ZERO storage entry in 25 years)
> while R-A armed exactly the storage-entry mechanisms and D25 measured that family as
> the corridor's largest divergence. Authorize a second §2.1b campaign? — **RULED
> 2026-09-01 (r#26 amendment 1) — AUTHORIZED, NOW** (over the after-D33 and hold
> options). One campaign: **T3-NEISO-GOLDEN-2**, NEISO BAU 2026–2050 at HEAD with the
> R-A-armed posture, its own FC-6 battery at its own vintage (the D26
> `carbon_price_delta` construction), full-rubric scoring, preserve-then-overwrite (the
> pre-R-A golden stays preserved with its posture-epoch caveat). Q13's "this campaign
> only" scoping carries over verbatim — a third campaign needs a new owner act.
> Execution = lane **T3-NEISO-GOLDEN-2** (Fable).

**Scope discipline:** ISO=NEISO, window=2026–2050 BAU golden at HEAD, budget per the
FF-3E basis the first campaign was priced on (~1.0 h wall / ~4.3 GB RSS for the campaign
solve) **plus the D26 §8.4 pricing rider** for the campaign's own FC-6 evidence (base +
three perturbed arms ≈ four ~30-min solves + the ~12–25 min battery ≈ +2 h). **THIS
CAMPAIGN ONLY** — Q13's scoping carries over verbatim; no standing authorization; a third
campaign needs a new owner act. `--full-solve-authorized` is licensed by Q25 and by
nothing else.

**What this campaign is for, stated so the lane cannot drift:** the question is whether
the ARMED storage-entry economics produce entry (and what the full-horizon system then
looks like) — NOT whether storage entry makes any verdict better. Rule 13 / D25
discipline: no input, parameter or threshold moves toward any corridor row; the corridor
is re-dispositioned against the new trajectory, never the other way around. **EITHER
storage outcome is a valid result** — zero entry under armed economics would itself be a
major finding, routed to the director, never "fixed" in-lane.

## 2. Gate-condition verification at launch (all four legs, read live at `5083e29e`)

- **(a) Backcast calibration proof — PASS, re-read live this session:**
  `frontend/data/backcast/calibration-complete.json` `complete` block = {ERCOT, NEISO,
  PJM}; NEISO entry keys keeper `2026-08-17-neiso-99-joint-p1`. `final` block empty
  (never required for forecast work). The holdout spend freeze is TIER-SCOPED to the
  locked test — orthogonal to a forecast-mode 2026+ campaign.
- **(b) POC gates green — PASS, re-read live:** bare `neiso-t1f` reads **PROMOTE** in
  `ff-verdicts.json` (the D25 re-score kept the determination; FC-5 now CAVEAT rather
  than SKIPPED).
- **(c) Worth-the-compute evidence — PASS, and stronger than at Q13:** the first
  campaign's committed record (25/25 years, 29.2 min, inside budget) plus the three
  post-campaign instrument closures — D25's FC-5 dispositions (0 UNEXPLAINED; the
  zero-storage family measured as the corridor's largest cross-ISO divergence, −56 % to
  −96 %, four ISOs), D26's repaired FC-6 P1 (PASSES on the correctly-constructed arm),
  and D24-R's cache-key repair (the armed/unarmed posture ambiguity of golden-1 §5.1(b)
  cannot recur — measured below).
- **(d) Owner authorization — the Q25 ruling quoted in §1.**

**Heavy-slot check at launch:** `git ls-remote --heads origin` shows two in-flight
branches — `claude/audit-program-director-irzj4a` (audit board, no solve),
`claude/miso-st-gas-steam-chp-calibration-9snn32` (owner's MISO backcast track, its own
container). No PJM (8.8 GB) / MISO (9.6 GB) no-co-run measure shares this container; the
~4.3 GB NEISO leg launches solo. **Collision map carried from the charter:** D33 (NEISO
position lane) is docs-only and had landed nothing at launch — its result informs
interpretation and is cited if it lands mid-session; D20 owns the seven LEGACY verdict
keys + the FC-7 scorer path (my keys are out of its scope; the committed-verdict control
below is re-run after any rebase that pulls a scorer change); D34 owns the
`carbon_price` validation seam (no overlap with `carbon_price_delta` usage); D31 is
MISO-side.

## 3. PRE-DECLARED run construction, budget, and expectations

**The campaign run — zero config invention, HEAD defaults at golden posture. The armed
posture IS HEAD's shipped defaults; nothing is hand-set:**

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2050 \
  --golden-posture --full-solve-authorized --out-dir results/ff-t3-neiso-golden/bau
```

- `mode="forecast"`, every `ScenarioConfig` field at its shipped HEAD default. The
  resolved config carries **`storage_entry_availability_gate=True`** and
  **`storage_entry_cost_normalized_rank=True`** (the R-A arming, commit `ecf9972`,
  epoch 2026-08-31) and **`carbon_price_delta=0.0`** (the D26 instrument field at its
  no-op default). Golden posture resolves the capacity-clearing gate through the ONE
  reader (`shipped_capacity_clearing_by_iso` — NEISO curve-ON);
  `forecast_xyear_warmstart` OFF per owner D-10. No flag beyond the two the charter
  names; **no new mechanism, no `ScenarioConfig` field, no matrix duty** (rule 28: if a
  field is ever wanted, STOP and route).
- **Resolved cache key, declared before launch:** **`706e7ba8e6582d42`** (the resolved
  NEISO 2026–2050 golden-posture config at HEAD `5083e29e`, single-root fold). Distinct
  from the pre-R-A golden's `a4b11ef4aaa1be35` — the D24-R (b′-1) declared-defaults
  ledger is what makes the two postures key distinctly (registration-time defaults
  False/False; the armed True values are non-default against the ledger and enter the
  hash). Golden-1's §5.1(b) scenario-identity ambiguity therefore CANNOT recur on this
  bundle: the key alone now identifies the posture.
- Years run SEQUENTIALLY within the invocation (rule 12); the FC-6 arm solves are also
  run sequentially, one at a time, per this lane's charter. Container: 15 GB RAM /
  4 CPU. `data/clean` was absent (fresh container) and is being rebuilt in full before
  launch (~30–35 min, the standing §2.4 prerequisite; measured time reported in §5).
- **Expected cost (pre-declared):** campaign solve ~30–60 min wall / ≤4.5 GB peak RSS
  against the Q25 budget basis of ~1.0 h / ~4.3 GB. Anchors: golden-1 29.2 min /
  3.50 GB and the D26 base arm 32.1 min / 3.44 GB — both UNARMED-posture solves. The
  armed screens add per-year candidate arithmetic (cheap); **if the screens admit
  storage entry, later-year LPs grow** (3 variables × 8760 h + SOC rows per entering
  unit), so wall/RSS above the unarmed anchors is an expected consequence of entry
  itself, reported not judged. FC-6 evidence: four ~30–35 min solves + battery ≈
  2.2–2.7 h. Measured-vs-projected reported in §5 whatever it reads.
- **Checkpoint discipline:** the runner writes `evolution_<year>.json` beside each
  year's cached result as the horizon progresses; per-year evolution artifacts are
  committed and pushed mid-horizon as checkpoints. **If the solve breaks mid-horizon,
  the failure record IS the deliverable** — reported at full magnitude; a partial run
  is never registered as complete.
- **Requirement bar carried unchanged** (the S-4b intake, all values ISO-NE's own ARA-3
  prints): DR-netted requirement factor 1.0286103, firm external-tie credit 409.31 MW.
  Nothing in this campaign re-derives or re-tunes any of it.

**Preserve-then-overwrite, declared in advance (executed in this pre-declaration commit
for the bundle, at registration for the record):**

1. **The bundle:** the standing pre-R-A golden bundle moves BYTE-IDENTICALLY (git mv, 45
   committed files) from `results/ff-t3-neiso-golden/bau/` to
   **`results/ff-t3-neiso-golden/bau-prera-2026-08-31/`** — its dated home, named by its
   solve date; its posture-epoch caveat travels with it (its `run_config.json` records
   both storage fields `False` and `git.basis_sha 9e56f0f`). It remains the pre-R-A
   record of note. The move lands in the SAME commit as this pre-declaration, BEFORE the
   campaign writes anything into `bau/`. (Path references inside previously-committed
   verdict provenance resolve at their recorded `scored_at_sha`, where `bau/` is the old
   bundle — checked: no script, test, or src file references the path; the three
   record-surface references are re-authored or annotated this session.)
2. **The verdict record:** at registration, the current bare `neiso-t3` entry (the D26
   re-score of the pre-R-A golden) is preserved BYTE-EQUAL at
   **`neiso-t3-prera-2026-08-31`** in `ff-verdicts.json`; the bare `neiso-t3` key then
   takes this campaign's verdict. The existing preserved chain
   (`neiso-t3-pre-fc5`, `-pre-fc6`, `-pre-fc6repair`) is untouched.
3. **The FC-5 table:** `results/ff-corridor/dispositions/neiso-t3.json` (authored by D25
   against the pre-R-A trajectory) moves to
   `results/ff-corridor/dispositions/neiso-t3-prera-2026-08-31.json` when the
   re-dispositioned table is authored; the bare name takes the new table.
4. **The run-explorer record:** the first campaign's
   `frontend/data/hindcast/neiso-2026-2050-t3-golden-bau.json` sidecar stays byte-equal
   (its embedded paths are registration-time provenance); this campaign registers under
   its own new run id via `register_forecast_run.py --summary … --label t3-golden2-bau
   --kind t3`.

**The FC-6 battery — this campaign's own vintage (= HEAD), the D26 construction, priced
before running:**

- **Paired arms**, each `reference_config("NEISO", 2026, 2050, cmc=False,
  golden_posture=True)` ± exactly one signal via
  `run_driver_battery.py --paired-arm {base, carbon_plus25, gasup150, gaspm5}
  --full-solve-authorized`, sequential:
  - `base {}` — the explicit reproduction control: its trajectory and I1–I14 vector must
    reproduce the campaign bundle exactly (same environment, same HEAD, same data; the
    CLI and the paired-arm driver share `reference_config` by construction). This solve
    doubles as the §5-attestation FF-4B reproducibility evidence. The perturbed arms
    launch only after it passes.
  - `carbon_plus25 {"carbon_price_delta": 25.0}` — the REPAIRED P1 arm (D26): a genuine
    +$25/t over the resolved RGGI trajectory in every year; the premise row is asserted
    by `check_forecast_invariants.carbon_pair_premise` (a violating pair yields P1=SKIP
    + FAIL premise, never a scored P1). **Never a `carbon_price` replace.**
  - `gasup150 {"gas_price_factor": 1.5}` (P2 merit-order sign) and
    `gaspm5 {"gas_price_factor": 1.05}` (P3 perturbation stability).
- **Battery:** the pre-registered NEISO ladder is T1.6 ONLY (2 rungs).
  `renewable_buildout_pace` — its pre-registered driver — is verified STILL consumed by
  no model code at HEAD `5083e29e`, so **both gate rows are expected VACUOUS ⇒ the
  battery leg is CAVEAT-at-best by construction** (D21 finding 2, the wiring decision is
  not this lane's). A vacuous rung is a CAVEAT, never a PASS. The ladder is run anyway:
  the battery output is the committed evidence OF that vacuity at this vintage, and the
  scorer's constant-series detection is what grades it.
- All FC-6 evidence lands in the campaign bundle's `fc6/` (the golden-1 layout), scored
  from THIS campaign's own bytes — no carry of any D21/D26 row (the arms are re-solved
  at this vintage precisely because FC-6's paired evidence is vintage-pinned).

**Verdict construction (declared in advance).** `forecast_verdict.py --tier t3`, scored
from committed artifacts only: this campaign's `full_horizon_summary.json` +
`run_config.json` + `dof_ledger.json` (built by the committed
`build_forecast_dof_ledger.py`) + this campaign's `fc6/` battery and paired-invariants
records + the re-authored corridor disposition table + the committed
`benchmark-corridor-anchors.json` + the committed T1-H score
(`results/hindcast/neiso-2021-2025-curve/NEISO/2ba529574d4982ea/score.json` — the
posture-matched curve-ON leg golden-1 disclosed; NO post-R-A NEISO T1-H exists, a stated
limit of FC-3's evidence, not a reason to solve backcast-window years off-charter) + the
committed D14 T1-X crossover score + **this campaign's own `forecast_attestation.json`**.

**The attestation, declared up front so it cannot be an outcome-shopping vector:**
golden-1 refused to author one mid-campaign because inventing an instrument after the
pre-declaration to clear a row is forbidden. The instrument now EXISTS (rubric §5;
`forecast_verdict._score_attestation`; the rubric's artifact table names "the producing
session (T3)" as its author). This campaign therefore declares NOW, before any solve:
after registration it authors `forecast_attestation.json` with the six §5 assertions,
each stated truthfully at authoring time — `dof_ledger_complete`,
`run_config_reproducible` (evidence: the base-arm reproduction),
`honest_unfit_referenced`, `quarantine_attested`, `no_off_registry_knobs`,
`registered` — and **any assertion that is not true is recorded `false` and FC-7 fails
on it at full magnitude**; nothing is softened to clear the row.

**Control-first, already executed before this pre-declaration:** the committed
`neiso-t3` verdict was REPRODUCED byte-for-byte (zero non-provenance diffs) from exactly
the committed inputs by the HEAD scorer, before anything was moved or overwritten — the
D25/D26 control pattern. The baseline is proven, not assumed.

**Pre-declared expectations (recorded before the solve):**

1. **The storage-entry outcome is OPEN.** No expectation is declared for it in either
   direction; both zero and nonzero entry are valid results. Whatever enters (GW by
   year, admitting mechanism, which screen leg binds) is reported at full magnitude.
   Zero entry under armed economics is routed to the director as a major finding.
2. **Head-of-horizon (2026–2030) reproduces the S-4b/golden-1 trajectory IF AND ONLY IF
   the armed screens admit no storage in those years.** The armed posture is the ONLY
   config delta vs the D26 base arm (which reproduced golden-1 exactly at its vintage),
   plus whatever `data/raw` intakes landed since `9e56f0f` (the RC-R NEISO
   demand-curve + confirmed-retirements rows — a HEAD-vintage campaign legitimately
   solves HEAD data; any head-year divergence is decomposed against BOTH candidates and
   attributed, never adjusted away).
3. **Out-year behavior (2031+) is REPORTED, never judged and never back-tuned** (rules
   13/21). No result feeds back into any input; no value is reverse-engineered to clear
   an invariant.
4. **Expected determination: HOLD** — FC-3 carries the committed T1-H FAIL and FC-4 the
   committed D14 T1-X FAIL regardless of anything this campaign solves; FC-1/FC-2
   depend on the new trajectory (golden-1's I3 dump FAIL and I13 cobweb WARN may move
   under storage entry — reported either way); FC-6's battery leg is vacuous-CAVEAT by
   construction (above); FC-5 re-dispositions are authored judgment. **The Q25
   authorization licensed the compute and the storage answer, not a promotion claim.**
   No instrument is invented mid-campaign to move any row (the attestation above is
   pre-declared, not invented after a row reads against us).
5. **FC-5 re-disposition:** the corridor memo convention imported whole (>15 % or
   opposite sign/direction ⇒ written ours-vs-theirs explanation naming the mechanism;
   any UNEXPLAINED row ⇒ FC-5 FAIL). With the D29 grain the summary now carries
   generation-by-fuel + the real `storage_power_mw` column, so the energy-mix anchor
   family becomes dispositionable on a golden for the first time, and the storage row is
   dispositioned battery-only (net of the documented NEISO PS residual 1,865.0 MW —
   the D29 classification trap, stated in the row basis). Anchors remain context, never
   targets.

## 4. The carried caveats (verbatim, per the Q25 ruling — nothing re-tuned)

**(i) The S-4b floor-dependence caveat carries wherever the head years reproduce.** If
2028/2029 clear at +419.0 / +333.6 MW again, those signs still ride on the 699.3 MW
retention response (S-4b §5.3, quoted in full in golden-1 §4(i)); if the armed posture
moves those years, the floor-attribution is re-measured from the new bundle's
`floor_retention_log`, not assumed.

**(ii) D14's retirement-composition miss carries verbatim.** Exit recall 2/6 reachable
≥300 MW targets in the crossover window; the economic screen concentrates exits in gas
(+66 % gas_cc) and missed the biomass/coal/gas_ct/oil exits entirely. Nothing in the
R-A arming touched the retirement screen, so every exit wave this campaign reports is
composed by the same screen and every out-year composition statement must be read with
it.

**(iii) The FC-7 instrument state is BETTER than golden-1's but the truth-telling duty
is unchanged.** The DOF-ledger instrument exists (lane D8) and the attestation schema
exists (rubric §5); this campaign builds its own ledger and authors its own attestation
per §3. What carries from golden-1 is the discipline: unidentified DOF entries are
listed open, false assertions are recorded false, and FC-7 reads whatever the artifacts
say.

**(iv) The FC-6 battery leg's vacuity carries** (D21 finding 2): NEISO's entire
pre-registered battery is the T1.6 ladder and its driver is still unwired at HEAD.
CAVEAT-at-best by construction; the wiring/registration decision remains the
director's/owner's, not this lane's.

**(v) FC-5 is permanently single-source for the t3-required table** (owner ruling Q23:
"None — I'm not getting more data"): AEO2025 alone anchors NEISO. A named, accepted
limitation; the CAVEAT is the steady state.

---

*(Sections below were written AFTER the solves; §§1–4 above were committed before
launch.)*
