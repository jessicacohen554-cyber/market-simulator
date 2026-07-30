# Forecast-readiness remediation — prompt pack (FFR waves)

**Execution vehicle for `docs/forecast-readiness-audit-2026-07.md` §4** (findings FR-1..FR-27).
Produced 2026-07-30 against `origin/main` HEAD `fd60eef`. This pack extends the FF program
(`docs/forecast-development-plan-2026-07.md`) with remediation waves; it does **not** supersede
that plan — its §7 standing constraints bind every session below, and the FF wave manager may
adopt these rows into its ledger as `FFR-*`. FF Wave 4 (golden solves) remains WITHDRAWN; this
pack schedules **nothing** beyond T0/T1 windows (§2.1b cap, ≤5 solve-years per invocation).

**House conventions (as FF §6):** waves are sequential; prompts within a wave are independent
parallel sessions unless flagged; `[FABLE]` = hard structural/adjudication work, `[OPUS]` =
spec'd execution, solve campaigns, intake, plumbing (never Sonnet — rule 27); `⛔` = gate.

**Every prompt implicitly begins:**
*Read CLAUDE.md, `docs/forecast-readiness-audit-2026-07.md` (your FR items + §4 row), and
`docs/forecast-development-plan-2026-07.md` §7 (binds). Fresh branch off latest `origin/main`;
`git config user.email noreply@anthropic.com && git config user.name Claude`.*

**Every prompt implicitly ends:**
*Push via `mcp__github__push_files` (server-side; session clones are history-grafted and raw
`git push` of a rebased branch 413s) or a verified small-pack `git push`; blob-verify any pushed
file ≥300 lines (fetch back, compare). Register every run on the forecast-validation namespace
in the producing session (`scripts/register_forecast_run.py`; NEVER the backcast registry).
Update the mechanism-matrix cell for any mechanism you test, rejections included (rule 28).
Findings doc to `docs/handoffs/ffr-<id>-<topic>-<date>.md`. No tuning: a residual closable only
by an unidentified value is an open blocker, written up (rules 1/13/14/21).*

---

## 0. Wave map (dispatch at a glance)

| Wave | Sessions (model) | Parallel? | Solves? | Gate to next wave |
|---|---|---|---|---|
| **W1 fix** | 1A (F), 1B (F), 1C (O), 1D (O), 1E (O) | yes — file-disjoint; 1D's `ci.yml` hunk precedes 1C's (flag §W1) | T0 probes + ≤2-ISO T1-F acceptance probes only | all five merged + **Wave-1 close checklist** (§W1-X: single cache-epoch bump) |
| **W2 evidence** | 2A (O), 2B (O), 2C (O), 2D (F) | yes — ≤2 concurrent solve invocations (rule 12) | T1-X ×3, T1-H probe legs, T0/T1 probes | evidence docs committed → **OWNER SITTING** |
| **⛔ OWNER** | decision batch D-1..D-7 (audit §4 Phase 2) | one sitting | none | signed decisions |
| **W3 re-baseline** | 3A (O), 3B (O) | 3B first or parallel (3B lands schema, 3A populates) | the ONE consolidated battery: T1-F ×6 + T1-X folds + T1-H re-scores + FC-6 | boards regenerated & current |
| **WS structural** | SA (F), SB (F), SC (O) | yes | T0 smoke only; everything ships **default-off/no-solve** so the W3 baseline stays valid | owner arming decisions (later) |
| **WP intake** | PA (O), PB (O) | parallel-**anytime** (data/docs only, no solve) | none | — |
| **WG gate-open** | per-ISO, order: PJM → NEISO → MISO → ERCOT → NYISO → CAISO | — | **HELD.** Prompts re-authored at gate-open per §2.1b(d); not included here by design (FF Wave-4 withdrawal stands) | — |

**Lane threads (sequential per lane across waves):**
L-CAP: 1A → 2B → (owner D-1/D-2) → 3A → WG · L-SCAR: 1B → 3A · L-VAL: 1D/1E → 2A → 3B/3A ·
L-INP: 2C + WP → SA/SB · governance: 2D → owner sitting → 3A step-0.

**Efficiency rules baked into this pack** (why the ordering is what it is):

1. **No solve before its inputs settle.** T1-X re-runs sit in W2 because the 1B fix
   (`weather_year=2025` Martin Lake leak) changes every crossover comparator — running them in W1
   would burn the solves twice. The full 6-ISO battery runs ONCE, in W3, after the owner batch.
2. **One cache-epoch bump**, at Wave-1 close (§W1-X) — not per session. Every W1 session ships
   code + byte-identity proofs + minimal acceptance probes; bulk re-solving waits for W3.
3. **Reuse committed BEFORE legs** — never re-solve a leg your change provably doesn't touch;
   resume killed runs from the per-year cache (FF §2.4-3).
4. Rule-12 concurrency: ≤2 concurrent solve invocations; PJM/MISO (≥8.6 GB) never co-run.

---

## Wave 1 — structural fixes + guardrails (5 parallel sessions)

File-ownership (one owner per file this wave): 1A `model/capacity_evolution/{evolve,retirements}.py`
+ `results/evolution_ledger.py` + `scripts/check_forecast_invariants.py` · 1B `data/fleet/*` +
`model/reserves/spec.py` · 1C `model/capacity_evolution/adequacy.py` + `config/capacity_market.py`
(new constants) — **not** `runner.py` · 1D `runner.py` (CLI guards) + `config/scenarios.py` +
`.github/workflows/ci.yml` + `scripts/{pb5_*,golden_forecast_bands,check_registry_payload_parity,
register_forecast_run tests}` · 1E new `scripts/check_forecast_parity.py` (its `ci.yml` hunk lands
only **after 1D merges** — flagged serialize).

### FFR-1A [FABLE] — Confirmed-exit accounting: ledger the derates, complete the exits

```
[FABLE] FFR-1A — Close the I4/A1 capacity-accounting leak (FR-1), the partial-year exit
ghost (FR-2), and the latent additions-baseline gap (FR-13)

Read (beyond the implicit set): audit §3.1 FR-1/FR-2 + §3.2 FR-13 + FR-23;
src/market_sim/model/capacity_evolution/{evolve.py,retirements.py};
results/evolution_ledger.py; scripts/check_forecast_invariants.py (I4);
docs/handoffs/confirmed-retirement-plan-2026-07.md (registry semantics).

Two arms, two commits, strictly in this order:

ARM 1 — bookkeeping (dispatch-inert by construction):
1. Write the documented-but-never-written `confirmed_derates` ledger rows in the
   derate branch of apply_confirmed_exits (unit_id, fuel, mw_before, mw_after,
   derate_mw), and the documented `reason` split (`confirmed`|`announced`) at the
   retirement recorder. new_events() creates the key.
2. Teach check_i4_capacity_accounting to close the per-fuel balance including
   derates: fleet_after == fleet_before − retirements − confirmed_derates + adds.
3. Move the step-4.5 additions baseline snapshot ABOVE the commissioned-unit
   insert (FR-13) so a future entry_commissioning_lag arming ledgers its MW.
4. Add the missing reconciliation unit test at the evolve_fleet seam (per fuel,
   trivial 2-unit fixture first — the test FR-26 says would have caught FR-1).
5. Fix the FR-23 docstring drift in the SAME commit (evolution_ledger.py schema
   text ↔ writers now true; retirements.py:109-114 hydro claim — delete or
   correct; hydro itself is FFR-1C's, do not touch adequacy.py).
   Acceptance: dispatch/LP output byte-identical (ledger-only change); I4 now
   PASSES on re-probed T1-F for NEISO and PJM (audit: both clear FC-1 on this
   fix alone) — probe exactly those two ISOs, 2026-2030, nothing else.

ARM 2 — behavioral (separate commit, cited):
6. Complete partial-year confirmed exits in year+1 (FR-2): a registry row with
   exit_month ≤ 6 derates to its annual-average factor in effective_year and to
   its full reduced factor the following year. Cite each affected registry row
   in the commit. T0 probes NEISO+ERCOT before/after; then re-probe PJM + NEISO
   T1-F (Brandon Shores/Wagner + Merrimack are the live cases).
   Expect retirement-MW deltas — attribute them in the findings doc; do NOT
   re-tune anything in response (rule 1).

Do not: touch adequacy.py, arrays.py, runner.py, or any default; widen any band;
run any window >5 solve-years. Do NOT bump the cache epoch here (§W1-X owns it) —
your acceptance probes use isolated --out-dir caches.
Deliver: findings doc with the per-ISO I4 before/after and the Arm-2 MW deltas;
matrix row for the ledger fields if any ScenarioConfig field is added (none expected).
```

### FFR-1B [FABLE] — Solve-year availability: the fleet ages, measured events stay in backcast

```
[FABLE] FFR-1B — Key thermal availability to the SOLVE year (FR-7); gate the measured
2025 derate out of forecast (FR-8); fix the weather_year-keyed regime/reserve lookups (FR-12)

Read: audit §3.2 FR-7/FR-8/FR-12; src/market_sim/data/fleet/arrays.py
(:392,:568,:581,:688 and the 3 sibling BIN_FORCED_DERATE_BY_YEAR reads at
:1292,:1380,:1450); data/fleet/eia860.py:2411-2429; model/reserves/spec.py
(:1220,:1237-1239,:1303-1305 and the weather_year lookups at :1896,:2228,:2533,
:2875); results/scarcity.py:643-661 (ercot_market_regime — the correct seam).

1. FR-7: feed the age model the solve year (already available in
   _availability_matrix as `year`), not config.weather_year. Weather-shape
   lookups that genuinely mean "the pinned weather 8760" keep weather_year —
   separate the two meanings explicitly at each site. Assert entrant age ≥ 0 in
   a unit test; add a T0 forecast probe showing monotone availability aging.
2. FR-8: gate BIN_FORCED_DERATE_BY_YEAR (all 4 read sites) behind
   mode=="backcast" (or outage_source=="historic") so the Martin Lake 2025 event
   can never reach a forecast/crossover year. The table header already declares
   the retirement path for the entry — honor it, don't delete the entry.
3. FR-12: route the ERCOT non-releasable-withholding regime test through
   ercot_market_regime(year, config); sweep the reserve layer's
   int(config.weather_year) artifact lookups — each becomes solve-year-keyed
   (where the artifact has a forward story) or hard-gated backcast-only (where
   it is a measured record). One line each in the findings doc: which, why.
   Add the missing __post_init__ guard: bare ercot_multiproduct_as_coopt in
   forecast without ercot_as_forward_requirement is the same hard error the
   endogenous variants already raise.

BYTE-IDENTITY IS THE ACCEPTANCE BAR: in backcast weather_year == solve year, so
every change above must be a no-op there — prove dispatch byte-identity on all
six keeper configs (the FF-1F attestation pattern) before anything else. If any
keeper moves, STOP and file it as a finding (rule 11) — do not adjust.
Do not: touch evolve.py/retirements.py (FFR-1A's), adequacy.py (1C's),
runner.py/scenarios.py beyond the one guard (1D owns scenarios.py — coordinate
the single __post_init__ hunk with 1D's session or land it via 1D; flag in PR).
No cache-epoch bump here (§W1-X).
Deliver: findings doc with the site-by-site disposition table + byte-identity
attestation + the T0 aging probe.
```

### FFR-1C [OPUS] — Hydro in the accredited ledger (I7/A2)

```
[OPUS] FFR-1C — Accredit hydro in accredited_firm_capacity_mw at its published
per-ISO credit (FR-3)

Read: audit §3.1 FR-3; docs/handoffs/ff-2b-adequacy-basis-2026-07.md §"hydro"
(the spec: CAISO 3,601 MW / NYISO 3,343 MW / NEISO 30 MW dispatched-but-
unaccredited); src/market_sim/model/capacity_evolution/adequacy.py:131-198;
data/hydro.py (capacity source); docs/parameter-citations.md.

1. Add the hydro term inside adequacy.py: hydro nameplate (from the hydro
   fleet/capacity loader, resolved for the solve year — NOT via the persistent
   fleet, which never contains hydro) × the ISO's PUBLISHED accreditation basis:
   CAISO NQC/RA counting, NYISO UCAP derate, MISO SAC wet/dry, NEISO/PJM/ERCOT
   per their published constructions. Every credit a cited constant in
   config/capacity_market.py (rules 5/13) — NEVER a value tuned to clear I7.
   Where no published basis exists, document and use nameplate × published
   class derate with the citation; no invented numbers.
2. Unit test asserting which fuels enter the accredited ledger (the FR-26
   missing test) — hydro present, and the known FF-2B gap magnitudes reproduced
   on a fixture.
3. Re-probe I7 at T0/T1 scale for CAISO/NYISO/MISO only (the three failing
   ISOs). Movement must be attributable to the cited credits alone.
Do not: touch runner.py (the firm_clean_mw display seam rides FFR-3B — flag it),
evolve.py, arrays.py; do not "fix" any remaining I7 gap with anything but a
cited published parameter — a residual is a finding.
Deliver: findings doc with per-ISO before/after I7 margins + citations table;
parameter-citations.md rows.
```

### FFR-1D [OPUS] — Enforcement wave: make the written rules executable

```
[OPUS] FFR-1D — CI + guards + config hygiene (FR-24, FR-25, FR-10, FR-11, FR-15,
FR-26-cheap)

Read: audit §3.5 FR-24/FR-25 + §3.2 FR-10/FR-11/FR-15 + FR-26;
.github/workflows/ci.yml; scripts/run_full_horizon.py:114-155
(assert_schedulable — the pattern to extend); config/scenarios.py __post_init__
(:8698-9144) + _CACHE_KEY_OPTIONAL_FIELDS.

1. CI (FR-24): add a no-solve job running check_forecast_invariants.py over the
   committed t1f/hindcast sidecars in frontend/data/hindcast/ (artifact-level —
   no LP); add frontend/data/{hindcast,forecast}/** to ci.yml path filters; add
   a mode/kind assertion to check_registry_payload_parity.py so a forecast run
   can never register into the backcast namespace. Correct the FF plan §1.1
   "CI-wired" sentence to describe what is now true.
2. §2.1b guard (FR-25): extract assert_schedulable to a shared helper and call
   it from EVERY schedulable entry point: market-sim run/sweep/ensemble/matrix
   (runner.py CLI), pb5_member_slice.py, pb5_assemble.py,
   golden_forecast_bands.py seed. Tests: >5 unauthorized years refused from
   each; 5 allowed; authorized 25 allowed.
3. Config hygiene: correlated_forced_outage backcast coercion in __post_init__
   (FR-10, one line, the datacenter_load_path pattern — prove backcast cache
   keys unchanged); hard forecast-mode errors for the backcast-only overlay
   family (FR-11 — the gas_price_factor pattern; enumerate all ~20 in the
   findings doc, guard each); delete the three inert FF-3D CLI flags + their
   ScenarioConfig fields (rule 26 — deleted means deleted); dedupe
   _CACHE_KEY_OPTIONAL_FIELDS (FR-15).
4. Cheap test debt (FR-26): registration-path smoke test (reindex over a tiny
   fixture namespace, assert chips/manifest well-formed); golden-fixture
   staleness expiry (test FAILS when any cache-key-affecting default differs
   from the seed's run_config — turning the frozen fixture from silent to
   loudly-stale; do NOT reseed, that is owner-authorized D-7).
NOTE: ci.yml is yours this wave; FFR-1E lands its parity job only after you
merge. scenarios.py is yours; FFR-1B's one AS-guard hunk lands through you or
after you merge (coordinate — flagged in both prompts).
Mechanism-matrix duty: field deletions + any new field ⇒ matrix rows same PR.
Deliver: findings doc listing every guard added + every field deleted; CI green.
```

### FFR-1E [OPUS] — Backcast→forecast parity check (the D-5 gap, generalized)

```
[OPUS] FFR-1E — A standing no-solve parity check between keeper postures and the
forecast orchestrator (FR-22)

Read: audit §3.5 FR-22; docs/FINDING-nyiso102-d5-parity-wiring-2026-07-30.md
(the incident: three NYISO downstate mechanisms existed only on the backcast
path); frontend/data/backcast/keepers/<ISO>.json (keeper flag surfaces);
runner.py (forecast orchestrator seams).

1. scripts/check_forecast_parity.py: for each ISO's current keeper run_config,
   enumerate armed solve-affecting mechanisms; assert each has (a) a forecast-
   orchestrator consumer, or (b) an explicit entry in a small committed registry
   (data or module constant) declaring it backcast-only-by-design with one line
   of why (e.g. measured overlays, rule 13). Fail loud on any mechanism in
   neither set. No LP anywhere.
2. Seed the registry honestly: sweep the six current keepers; every mechanism
   lands in (a) or (b) or becomes a FILED FINDING in your findings doc (the
   next D-5). The NYISO downstate family must pass (a) — it was wired
   2026-07-30.
3. Tests trivial-first (synthetic keeper config). CI wiring: add the job to
   ci.yml ONLY AFTER FFR-1D merges (file owned by 1D this wave).
Do not: wire any mechanism you find missing (that is a follow-up finding with
its own session — this session builds the detector).
Deliver: parity report for all six ISOs + the registry + findings doc.
```

### §W1-X — Wave-1 close checklist (run by whichever session merges last, or the dispatcher)

1. All five merged; keeper byte-identity attestations from 1A-arm-1/1B/1D present.
2. **Bump the operator cache epoch ONCE** (`results/cache.py` documented mechanism) — FR-1/2/7/8
   change forecast output under unchanged keys; stale 2026+ cached bundles must not be reused.
3. Confirm no Wave-1 session widened a band, moved a default (other than the enumerated
   guard/coercion/deletion set), or touched an out-of-training year.
4. Green-light Wave 2.

---

## Wave 2 — evidence for the owner sitting (4 sessions; ≤2 concurrent solve invocations)

### FFR-2A [OPUS] — Crossover seam + T1-X refresh (ERCOT/PJM/MISO)

```
[OPUS] FFR-2A — Fix the crossover neighbor-gas seam (FR-9), diagnose the vanished
MISO crossover, re-run T1-X on the fixed availability envelope

Read: audit §3.2 FR-9 + §3.5 FR-21 (comparator staleness); runner.py:1352;
data/neighbor_price.py:206,481; scripts/run_capacity_hindcast.py (crossover
mode); scripts/score_crossover.py + scripts/_ff2d_crossover_adapter.py;
docs/handoffs/ff-t1-gate-2026-07.md §4.2-4.3.

1. FR-9: neighbor seam honors crossover_forward_gas_path for forward years and
   uses _hold_flat_extrapolate instead of raw dict indexing; extend
   assert_forward_drivers to cover the neighbor seam and weather_year-keyed
   overlays (belt-and-braces with FFR-1B's fix).
2. Diagnose why the FF-2D MISO crossover never registered (T0-scale repro of
   its first forward year; the audit's hypothesis is the seam KeyError —
   confirm or refute, one line).
3. Fold the two FF-2D L-VAL follow-ups: serialize refusal_marker + the flat
   metrics list inside score_crossover.py itself (retire the adapter), and add
   the fractional family-volume metrics (gas_twh/coal_twh) the rubric's FC-4
   rows need — currently uncovered, never silently passed.
4. Re-run T1-X 2023-2027 for ERCOT, PJM, MISO at post-W1 HEAD (the 1B fix
   changes the comparators — that is WHY this is Wave 2). Score with
   forecast_verdict --tier t1x against the CURRENT keepers' committed scores;
   note in the findings doc that CO2 remains reconstruction-basis-partial
   (treat price as load-bearing). Rule 12: ≤2 concurrent; PJM solo if RSS says.
   Quarantine: scoring stops at 2025; ≥2026 refusal tests must still pass.
Deliver: input-gap table vs current keepers + registered runs + findings doc.
```

### FFR-2B [OPUS] — Retirement-rule + entry-damper evidence (the D-1/D-2 case)

```
[OPUS] FFR-2B — Re-probe retirement_rule="pipeline" and the entry dampers at
post-W1 HEAD; deliver the owner's D-1/D-2 evidence (FR-4, FR-5)

Read: audit §3.1 FR-4/FR-5 + §3.3; docs/handoffs/ff-retirement-rule-
implementation-2026-07.md (the implemented rule + its probe arms);
docs/handoffs/forecast-retirement-calibration-plan-2026-07.md §2.1/§3 (T-R
bands — never restated looser); docs/handoffs/ff-entry-stack-completion-2026-07.md.

1. Probe arms at post-W1 HEAD, reusing every committed BEFORE leg that is
   invariant (never re-solve unchanged legs): PJM + MISO curve-ON T1-H legs
   (2021-2025, 2022 bridged) with retirement_rule=pipeline; MISO T1-F with
   pipeline + entry_rate_limits + entry_commissioning_lag armed (FR-13 is fixed
   by FFR-1A, so the commissioning ledger is now sound — verify I4 stays green
   with the lag armed, the latent-defect test).
2. Score: T-R battery + T-R10 no-inversion guard + LOYO within 2023-2025
   (scorer-side folds); re-measure I13 (cobweb) and BLK-10 (backstop MW) on the
   armed arms. Bands never widened.
3. Deliver the D-1/D-2 owner box: measured before/after per ISO, what each flip
   re-opens (expected: nothing — both are identified constructions), and your
   recommendation. The flips themselves are the OWNER's (executed in FFR-3A
   step 0) — do not change any default in this session.
Rule 12: the two multi-zone curve legs are ~8.6 GB each — sequential, never
co-run with FFR-2A's PJM leg (coordinate solve windows with the dispatcher).
Deliver: findings doc + registered probe runs + the decision box.
```

### FFR-2C [OPUS] — Net-CONE currency + FF-G3 activation evidence (the D-3 case)

```
[OPUS] FFR-2C — Re-anchor stale net-CONE vintages from PUBLISHED results; prepare
the FF-G3 escalation decision (FR-19)

Read: audit §3.4 FR-19; docs/handoffs/ff-g3-net-cone-forward-2026-07.md (design
landed, inert; D1-D5 open); config/capacity_market.py:1231-1418.

1. Rule-23 data-change re-derivations, one commit per ISO, each citing the
   published instrument: PJM 2028/29 BRA clearing (325.69 $/MW-day — the +34%
   the audit flags), and NYISO/MISO/NEISO wherever a newer published vintage
   exists than the on-disk last (verify each; no value without its citation).
   Reconciliation tests updated in the same commits.
2. Populate the FF-G3 owner box D1-D5 with the measured spread each escalation
   option implies vs hold-last (no default flip — decision is the owner's).
3. T0 smoke (NEISO 2026-2028) before/after the re-anchors; capacity-price
   validation script re-run (validate_capacity_prices, no LP).
Constants collide with nobody this wave (FFR-1C merged in W1). Matrix duty if
any new ScenarioConfig field appears (none expected).
Deliver: findings doc + citations + the D-3 box.
```

### FFR-2D [FABLE] — Governance brief: the owner sitting's packet

```
[FABLE] FFR-2D — Assemble the owner-decision packet (D-1..D-7) + the two marker
briefs (docs only, no code, no solve)

Read: audit §2, §4 Phase 2; frontend/data/backcast/calibration-complete.json;
docs/handoffs/neiso-calibration-complete-memo-2026-07.md (the precedent);
docs/calibration-log/pjm.md tail; keepers/PJM.json + keepers/NEISO.json;
docs/handoffs/nyiso-neiso-capacity-pairing-adjudication-2026-07-15.md.

1. One packet doc (docs/handoffs/ffr-owner-sitting-<date>.md): the seven
   decisions with, per item: what it changes, the evidence doc (FFR-2A/2B/2C
   outputs as they land), what it re-opens, recommendation, sign-off line.
   D-5 gets its own two briefs attached:
   (a) PJM calibration-complete memo in the NEISO-memo pattern — keeper
   pjm-137 CALIBRATED, zero failing criteria, the thin C3c margin stated
   honestly (1 h / 2.5 h vs the 0.5× floor), what marker declaration authorizes
   (rule 22 one-shot remains an owner-run event OUTSIDE this program);
   (b) NEISO marker re-key brief — marker frozen to neiso-54/-60 vs HEAD keeper
   neiso-61, holdout freeze HELD (governance 2026-07-26): lay out re-key vs
   hold options; the freeze-lift is the owner's alone.
2. D-6 NYISO brief: C3c sole blocker, EMPTY lever queue (every candidate
   adjudicated) — frame as adjudication (ledgered-caveat precedent vs stay-
   withdrawn), plus the FF-3D pair-evidence regeneration order (rule-11 taint).
3. Keep the packet strictly decision-support: no recommendation dressed as a
   default change, no number without its measured source.
Deliver: the packet + briefs, cross-linked from the audit doc (one-line edit).
```

**⛔ OWNER SITTING** — decisions D-1..D-7 signed (or explicitly deferred, which re-scopes FFR-3A
step 0 to the signed subset). Nothing in Wave 3 starts before this.

---

## Wave 3 — re-baseline (the single consolidated battery)

### FFR-3B [OPUS] — Staleness machinery + bookkeeping reconciliation (land first or parallel)

```
[OPUS] FFR-3B — Make verdict/HEAD drift detectable; reconcile the stale registries
(FR-21, FR-23, FR-27-cheap)

Read: audit §3.5 FR-21/FR-23; scripts/register_forecast_run.py;
frontend/data/forecast/{program-status.json,ff-verdicts.json} (schema only —
do NOT hand-edit contents; FFR-3A regenerates them).

1. Schema: every verdict/board artifact carries scored_at_sha + cache_epoch +
   scored_at_date (register_forecast_run + the battery emitters). FFR-3A
   populates them.
2. CI staleness check (WARN-level): flags when solve-affecting paths
   (src/market_sim/**, the schedulable scripts) have moved ≥N commits past the
   newest scored_at_sha on the board — the audit's "ten days dark" failure mode
   becomes visible. WARN, not FAIL (backcast velocity must not be blocked).
3. Bookkeeping desync (FR-21/FR-23): FF plan §1.2 + WAVE FI rows to landed
   truth (G2/G3/G5 landed, G4 memo-only); gap-register rows; wave-manager
   ledger gains the FF-G rows + these FFR rows; ercot.md:336 ERCOT-93 claim
   corrected (machinery NOT merged, patch rotted); firm_clean_mw display seam
   from FFR-1C's flag; forecasting-entry-exit-assessment.md headline re-graded
   post-flip (state what FF-2C changed; keep every measured claim sourced).
4. Add the forecast DOF-ledger builder STUB chartered honestly (FR-27): emit
   the ledger skeleton from run_config with identification-source fields left
   explicitly UNATTESTED — turning FC-7's silent CAVEAT into a fillable
   artifact. (Full attestation is WG/Phase-B work.)
Deliver: findings doc; CI check live; docs reconciled — every claim it corrects
cites where the truth now lives.
```

### FFR-3A [OPUS] ⛔ — Execute signed decisions + re-score everything

```
[OPUS] FFR-3A — Execute the signed owner decisions, then re-run the T1 gate
battery at the post-fix HEAD and regenerate every board

Requires: Wave 1 + 2 merged, owner sitting done, FFR-3B schema landed.
Read: audit §4 Phase 3; docs/handoffs/ff-t1-gate-2026-07.md (the battery recipe
to mirror); docs/forecast-determination-rubric.md; the signed packet.

0. One dedicated commit per SIGNED decision, each citing the sign-off (FF-2C
   pattern): retirement_rule default (D-1), damper arming (D-2), net-CONE
   escalation choice (D-3), fuel option (D-4), marker actions (D-5 — the
   calibration-complete.json edit follows the NEISO memo pattern verbatim),
   NYISO adjudication (D-6), golden reseed IF authorized (D-7 — it is a
   15-solve-year invocation; run it ONLY under its own written authorization,
   --full-solve-authorized, per §2.1b(d)).
1. The consolidated battery, rule-12 scheduled (pairing: light ISOs pair, PJM
   solo, MISO solo; budget ~1 day wall): T1-F 2026-2030 × 6 ISOs; T1-H re-scores
   (re-solve ONLY legs the signed decisions touch — a flipped retirement rule
   touches all four curve legs; an unflipped one means scorer-only); fold
   FFR-2A's T1-X (re-run only if a signed decision moved dispatch); FC-6 driver
   battery at the CURRENT posture (first time since 2026-07-12 — required for
   any future T1→T2 promotion); FF-3E readiness battery re-run.
2. Score with forecast_verdict per tier; regenerate ff-verdicts.json,
   program-status.json (from the new evidence — gate (a) rows now carry the
   HEAD keepers + the marker actions), the FF-3E scorecard, and the mechanism-
   matrix header re-stamp. Every artifact carries scored_at_sha + cache_epoch
   (FFR-3B schema).
3. Deliverable docs/handoffs/ffr-t1-regate-<date>.md: per-ISO promotion table,
   regression vs FF-2D with every moved metric naming its causal commit, and
   the refreshed per-ISO §2.1b gate scorecard for the owner. Promotion/gate-open
   decisions remain the owner's; your output is the measured scorecard.
Do not: tune anything in response to a re-score; widen bands; touch
out-of-training years; exceed 5 solve-years in any single invocation (the
golden reseed, if authorized, is its own separately-authorized invocation).
```

---

## Wave S — structural mechanisms (default-off / no-solve; W3 baseline stays valid)

### FFR-SA [FABLE] — Load-shape evolution (FF-G4 Option B, implement)

```
[FABLE] FFR-SA — Implement the FF-G4 Option-B load-shape mechanism (additive EV +
heat-pump end-use layers), DEFAULT OFF (FR-16)

Read: docs/handoffs/ff-g4-load-shape-design-memo-2026-07.md (the decided design
— implement, don't re-design); audit §3.4 FR-16; runner.py:274-289
(_scale_demand); data/datacenter.py:312 (electrification_shape stub).

1. Implement per the memo: cited end-use shapes, additive layers over the
   weather-8760, ScenarioConfig field(s) default OFF, backcast/hindcast-coerced
   (the datacenter_load_path pattern), cache-key-registered, matrix rows in the
   same PR. Every parameter cited (parameter-citations.md).
2. Acceptance: backcast byte-identity; T0 smoke NEISO then PJM 2026-2028 armed
   vs off — the ISO-NE winter-peak trajectory becomes EXPRESSIBLE (directional
   check vs CELT, context not fit target); invariants green.
3. Owner box for arming posture — no default flip here.
Rule 19: enumerate what already shapes demand (DC block) and document the seam —
one mechanism per phenomenon, additive layers must not double-count DC MW.
```

### FFR-SB [FABLE] — Nuclear-registry consumption design memo (no code)

```
[FABLE] FFR-SB — Design how the FF-G5 nuclear license/SLR registry enters the
exit path WITHOUT a second exit mechanism (FR-18/BLK-9; memo only)

Read: docs/handoffs/ff-g5-nuclear-registry-2026-07.md (registry + loader, 59
units, consumed by nothing); audit §3.3/§3.4; model/capacity_evolution/
retirements.py (the ONE exit path); confirmed-retirement-plan (instrument bar).
Research step (FF §4): how IPM/ReEDS treat license horizons vs economic exit.

Memo (docs/handoffs/ffr-sb-nuclear-consumption-<date>.md): candidate designs
graded vs rules 13/19/23 (license ceiling as an availability horizon vs a
confirmed-exit-grade instrument vs an announced-retirement date source), what
each regenerates from for a forward year, identification per parameter, an
owner-decision box. Explicitly: NO second exit mechanism — the design must
compose with the existing screen/registry. No code, no solve.
```

### FFR-SC [OPUS] — FF-G1 transmission A/B + input refresh follow-ups

```
[OPUS] FFR-SC — Run the owed FF-G1 T1-F A/B (transmission expansion gate);
execute surviving small input refreshes

Read: docs/handoffs/transmission-expansion-grounding-2026-07.md + the fast-tier
D2 apply note (engine landed 2026-07-26, default off, A/B never run); audit
§3.3/§3.4 FR-20.

1. T1-F A/B (one ISO with committed instruments, e.g. PJM or CAISO 2026-2030,
   gate off vs on): invariants, price/flow deltas at the registered interfaces,
   findings + registered runs. No default flip — owner box.
2. Input refreshes as data lands from WP: ATB 2025/2026 re-derive of
   NEW_ENTRY_COSTS (rule 23, cited; tests updated), demand-anchor bumps to the
   2026 Gold Book / MISO LTLF vintages where FF-G4 D4 flagged them.
Rule 12; ≤5 solve-years; registration + matrix duties standard.
```

---

## Wave P — parallel-anytime intake (data/docs only; no solve; dispatch whenever)

### FFR-PA [OPUS] — Confirmed-retirements re-query (time-sensitive)

```
[OPUS] FFR-PA — Refresh the confirmed-retirements registry; adjudicate the
Eddystone §202(c) expiry (FR-18) — DATA ONLY

Read: data/raw/confirmed-retirements/ (+README, vintage 2026-07-05); audit
§3.4 FR-18; docs/handoffs/confirmed-retirement-plan-2026-07.md (instrument bar).

1. Re-query every ISO's rows: the PJM Eddystone DOE §202(c) order expires
   2026-08-22 — record the successor state (renewed / lapsed / superseded)
   WHEN PUBLISHED, never speculatively; Brandon Shores/Wagner FERC extension
   status; MISO Attachment Y cross-check (the never-done item); NYISO stays an
   honest zero unless a real enforceable instrument exists.
2. Every row change carries its public instrument citation (the plan's bar);
   registry README vintage updated; loader tests green. Propose (don't build)
   a quarterly re-query cadence line for the plan.
No solve; no CI workflow (owner-billed runners); rule 22 untouched.
```

### FFR-PB [OPUS] — Cost/policy vintage intake (M1/M2 closure)

```
[OPUS] FFR-PB — Land ATB 2025 (or 2026) and the §45Y/48E primary-statute
verification (FR-20; FF-0D M1/M2) — DATA + CITATIONS ONLY

1. M1: fetch/land the newer NREL ATB electricity workbook through the
   data-intake contract (schema'd, curated partition); do NOT re-derive
   NEW_ENTRY_COSTS here (FFR-SC executes the re-derive against this data).
2. M2: verify the 2033-36 "other-clean" phase-down steps against primary
   statute/Treasury text; correct scenarios.py citation comments (values only
   if the primary source differs — rule 23 citation either way).
3. Where the proxy blocks a source, log MANUAL DOWNLOADS NEEDED rows — never
   guess values.
```

---

## Dispatch cheat-sheet (owner)

1. **Now:** launch FFR-1A/1B/1C/1D/1E in parallel (+ FFR-PA/PB anytime). Watch for the two
   byte-identity attestations (1A arm-1, 1B) — a keeper that moves is a stop-the-line finding.
2. **Wave-1 close:** run §W1-X (single cache-epoch bump), then launch FFR-2A/2B/2C (≤2 solve
   sessions at a time; PJM/MISO legs never co-run) + FFR-2D.
3. **Sitting:** decide D-1..D-7 from the FFR-2D packet.
4. **Then:** FFR-3B, then FFR-3A (the one big battery, ~1 day wall). Its output is the refreshed
   §2.1b scorecard — the gate-open conversation happens on THAT, per ISO, PJM first.
5. **Anytime after W3:** FFR-SA/SB/SC (default-off; baseline stays valid).
6. **WG (gate-open per ISO)** stays held: prompts are re-authored at gate-open under §2.1b(d) —
   this pack deliberately contains none (FF Wave-4 withdrawal stands).

*Produced 2026-07-30. No LP solved, no parameter changed, nothing registered by the pack itself.*
