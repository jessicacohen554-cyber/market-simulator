# Gap Register 2026-07 — parallel prompt pack

Ready-to-paste handoff prompts, one per **parallel-safe lane** of the currently-open
gaps in `docs/gap-register-2026-07.md` (open set per its 2026-07-07 reconciliation
addendum: **G-10, G-15, G-16, G-20, G-21, G-22, G-26, G-30, G-37, G-41, G-42, G-51,
G-52, G-61**; G-19 and G-40 are accepted/not-actionable and excluded). Each prompt is
self-contained: drop it into a fresh Claude Code session on this repo. Lanes are
carved by **exclusive file / registry-namespace ownership** so they do not collide,
following the register's §5 execution plan updated to the state at
`keepers.json` HEAD (2026-07-07/08).

## How to run these in parallel

- **No-solve lanes (L-A … L-D): run all concurrently, any tier.** They own disjoint
  docs / config / scalar files and never touch a keeper bundle.
- **Solve-heavy lanes (L-E … L-K): cap at 2 solving concurrently (CLAUDE.md rule 12** —
  ≤2 simultaneous per-plant multi-zone invocations; years sequential *within* a run).
  Each SH lane owns a **distinct ISO registry/bundle namespace** (or the non-keeper
  hindcast harness), so file ownership never conflicts — the cap is purely a RAM limit.
  Launch any 2, start the next when one frees.
- **Before solving, every SH lane re-verifies the current keeper** for its ISO in
  `frontend/data/backcast/keepers.json` and rebases on `origin/main` — the board churns
  hourly and the prompt's named keeper may already have been superseded.

## Model-tier assignments (rationale)

Mechanical docs/scalars → **Sonnet**. Scoped single-mechanism code+test / forecast-side
decisions → **Sonnet/Opus**. Calibration root-cause + keeper decisions → **Opus/Fable**.
Owner judgments stay with the human; any tier drafts the memo.

| Lane | Gaps | Solve? | Model |
|---|---|---|---|
| L-A Usability docs | G-51, G-52 | no | Sonnet |
| L-B Scalar / off-registry hygiene | G-26 (actionable items) | no | Sonnet |
| L-C PJM I7 forecast backstop | G-41 | no (forecast-only) | Sonnet draft + Opus code |
| L-D Scope2 CAISO Mode A frontier | G-42 | light | Opus |
| L-E Capacity/hindcast screen regime | G-30 (+G-32 co-scope) | SH | Opus/Fable |
| L-F ERCOT price-shape + storage-AS | G-22, G-37 | SH | Fable |
| L-G CAISO belly commitment + seam base | G-15, G-61 | SH | Fable |
| L-H PJM ST_GAS vintage + reserve magnitude + band generalize | G-21, G-20b resid, #1302 | SH | Opus/Fable |
| L-I NEISO ST_GAS C7 diurnal | G-16 | SH | Opus |
| L-J NYISO downstate tail + floor scalars | G-20c resid, G-26(NYISO) | SH | Fable |
| L-K Statmode D-7 re-solves | G-10 | SH | Opus |

**Shared rules every prompt inherits (CLAUDE.md):** right structure first, tune the
level second (#1); measured data only as a reproducible forward-regenerating input,
never an outcome pinned to the residual (#10/#11); a structurally-correct mechanism
stays even if it worsens a metric — fix the root cause, don't bury it (#11); every
completed backcast run is registered on the dashboard (`calibration-report` skill +
`scripts/build_manifest.py`) and committed in the same session (#12); always solve ALL
scoreable years in one bundle, never a single-year keeper (#16); no Python loops over
hours in LP construction; push via `mcp__github__push_files`, never `git push`.

---

## L-A — Usability docs: canonical install path + quickstart caveat  ·  Sonnet  ·  no solve

```
Close two Goal-A usability-debt gaps from docs/gap-register-2026-07.md. Owns
README.md, run-simulator.sh, pyproject.toml ONLY. No solves, no keeper touch.

G-51: the repo ships two divergent install paths with no statement of which is
canonical — `uv` (pyproject.toml) and run-simulator.sh's pip-venv + launcher UI.
Pick the canonical one (recommend uv, matching CLAUDE.md's stack line and the
pyproject), document it as canonical in README, and add a one-line note in
run-simulator.sh's header (and README) explaining the other path is the
convenience launcher, not the reference install. Do NOT delete either path.

G-52: README's quickstart (README.md:29) is a single-year run with no note that
CLAUDE.md rule 16 forbids single-year *keepers*. Keep the single-year command as
a smoke test but add one sentence: "This is a smoke test only — a registered
calibration keeper must solve all scoreable years in one bundle (--year 2023 2024
2025); see CLAUDE.md rule 16."

Deliverable: the two doc edits + the header note, committed and pushed. Honesty
gate: documentation only — do not change any runnable behavior.
```

---

## L-B — Scalar / off-registry hygiene (the actionable G-26 items)  ·  Sonnet  ·  no solve

```
G-26 in docs/gap-register-2026-07.md tracks residual-identified scalars still
live. Most are data-blocked (coal sigmoids #1347, merchant CHP #1335, wefor
#1348 — leave those). Address ONLY the items that need NO new source data and NO
solve. Owns config/constants.py, src/market_sim/config/scenarios.py, and the
named data modules for the items below; do NOT touch any offer-curve numeric
value that feeds a keeper's dispatch (that would need a re-solve — out of scope).

1. #1349 GAS_AVAILABILITY_FACTOR dead code — confirm it is unreferenced in the
   solve path (grep the whole src/ tree) and DELETE it (CLAUDE.md rule 26:
   "deleted means deleted" — a deprecated parameter that still parses is a
   re-armable answer key). If any live reference exists, STOP and report instead.
2. #1350 static seam tranches — MISO closed via measured Q-Q ladders
   (MISO_SEAM_LADDER_BY_YEAR). Audit the NYISO/PJM/CAISO static seam ladders:
   confirm each carries a citation comment and an open follow-up issue reference;
   if a ladder is an undocumented literal, add the citation + issue pointer
   comment. Do NOT change the numbers.
3. #1373 CAISO WECC 7500 forecast fallback and #1372 PGE-TAC split — verify each
   appears in ScenarioConfig/constants.py and is reachable via run_config.json
   (rule 24: no off-registry tuning channels). Where either is a hardcoded
   fallback literal in a data/ module, promote it to a named ScenarioConfig /
   constants.py field with a citation comment (no numeric change).

Deliverable: the dead-code deletion + comment/registry-promotion edits, a short
note in the register's G-26 row marking which sub-items are now closed, committed
and pushed. Honesty gate: no numeric change to any value that alters a solve —
this is provenance + dead-code hygiene, verifiable by a byte-identical LP.
```

---

## L-C — PJM hindcast I7 forecast backstop (owner memo + forecast-only code)  ·  Sonnet draft + Opus code  ·  no keeper re-gate

```
G-41 in docs/gap-register-2026-07.md: PJM hindcast invariant I7 FAILs (~1-4k MW
"floor doesn't force-build"). The decision memo is already drafted
(docs/handoffs/pjm-hindcast-i7-decision-2026-07-06.md): frame it as an
invariant-DEFINITION owner decision (absolute floor vs retirement-bounded), root
cause F1 = apply_reserve_margin_build backstop exists but is gated off
(reserve_margin_build_enabled=False, scenarios.py). Memo recommends a
market-design-dependent split: absolute floor + backstop-ON for capacity-market
ISOs (incl. PJM); retirement-bounded for energy-only ERCOT.

This is FORECAST-SIDE ONLY — no keeper, no backcast re-gate, so no quarantine
concern. Owns model/capacity.py (apply_reserve_margin_build gate wiring) and
config/scenarios.py (reserve_margin_build_enabled + any per-ISO MARKET_DESIGN
switch). Coordinate with L-E (also owns capacity.py) — merge L-E first or
section-scope the edit.

Task:
1. Finalize the memo's two preconditions and put the absolute-vs-bounded split
   decision to the owner via AskUserQuestion (include enough context to answer
   without scrolling).
2. On owner sign-off, wire reserve_margin_build_enabled to key off the per-ISO
   MARKET_DESIGN registry (backstop-on for capacity-market ISOs) rather than a
   flat default-off, with a citation comment. Add a trivial-case test (1 zone,
   backstop binds vs doesn't).
3. Re-run the PJM hindcast to confirm I7 flips PASS under the new default; the
   ERCOT hindcast must stay unchanged (energy-only → retirement-bounded).

Deliverable: the code change + test + hindcast re-run note, committed and pushed;
register the hindcast run if it produces a scoreable artifact. Honesty gate:
forecast-mode capacity-adequacy structure (rule 1), not a backcast fit lever.
```

---

## L-D — Scope2 CAISO Mode A degenerate frontier (LP-design fix)  ·  Opus  ·  light solve

```
G-42 in docs/gap-register-2026-07.md (issue #1429): the Scope2 LCE-portfolio
CAISO "Mode A" no-cost-tiebreak frontier is degenerate — multiple equal-cost
optima with no tiebreak, so the frontier is not well-defined. Owns
scope2-lce-portfolio/** and any Mode-A LP-construction it calls. Does NOT touch
any calibration keeper bundle or the main dispatch offer path.

Task: diagnose the degeneracy (equal-objective vertices), then add a
well-motivated deterministic tiebreak to the Mode-A objective — analogous to the
storage ε=0.001 $/MWh tiebreaker (CLAUDE.md rule 9) — small enough not to change
the economics, large enough to select a unique vertex. Prefer a physically
meaningful secondary term (e.g. minimize total throughput, or a CO2 tie-break as
the retirement screen already uses) over an arbitrary lexicographic hack.

Deliverable: the LP-design fix + a trivial-case test showing a unique frontier,
+ a before/after note on the CAISO Mode-A frontier, committed and pushed. Honesty
gate: the tiebreak resolves degeneracy without moving the frontier's economics.
```

---

## L-E — Capacity/hindcast screen regime: solar-entry 0 GW + coal over-retire  ·  Opus/Fable  ·  SH (non-keeper harness)

```
G-30 (co-scoped with G-32, FOM/foresight) in docs/gap-register-2026-07.md. The
ERCOT hindcast still forms ZERO scarcity hours and therefore (a) solar entry
never clears its fixed cost (0 GW) and (b) the economic screen exits the whole
coal/gas_st fleet (22.8 GW over-retirement, false-retire 96% genuine per the
G-31 per-plant scoring fix). The toggle theory is CLOSED: scarcity_pricing_enabled
is already the harness default and the re-run is done (ercot-2021-2025-realized-g31).
The residual is a SCREEN/LP-REGIME root cause, not a config flip: the
perfect-foresight LP on the over-supplied 2020-vintage fleet against un-grown
realized demand forms no scarcity, so the ORDC overlay is inert.

Read first: the hindcast s2/s3 reports and ercot-2021-2025-realized-g31
score.json; docs/handoffs/capacity-economics-plan-2026-07.md and
fom-scarcity-joint-protocol-2026-07-05*.md (W4/W5: FOM inert behind the
nameplate->accredited floor + 15.2 GW backstop flood; foresight A/B never run on
reconciled code). Owns model/capacity.py, the hindcast harness scripts, and the
capacity-economics / fom-scarcity handoff docs. Coordinate capacity.py with L-C.

Task (sequence): (1) reconcile the FOM stage so it is not inert behind the
accredited floor + backstop flood — run the recorded-but-unrun unblocking paths
(3 in the protocol doc); (2) run the foresight A/B on the reconciled code
(perfect-foresight vs a limited-foresight/rolling screen) to test whether
tempering foresight lets scarcity form on the over-supplied vintage; (3) re-run
the hindcast and measure solar entry + coal-retire recall at per-plant grain
(the G-31 scoring fix). The over-retirement and 0-GW-solar are DIAGNOSTICS to
close via root cause, never fit targets (rule 11).

Deliverable: the reconciled FOM/foresight code, the A/B + re-run registered on
the dashboard, and a note on whether scarcity now forms. Honesty gate: scarcity
must form from the LP regime (foresight/vintage), never an adder tuned to hit a
retirement or entry number.
```

---

## L-F — ERCOT price-shape (C3b/c) + storage energy-vs-AS gate  ·  Fable  ·  SH (ERCOT namespace)

```
Two open ERCOT structural gaps, same registry namespace. Re-verify the current
ERCOT keeper in keepers.json first (was 2026-07-07-ercot42-wtx-curtailment-driver);
owns the ERCOT registry/bundle namespace + ERCOT-only config sections. All levers
below stay default-off unless a gate passes.

G-22 (price-shape C3b/C3c): three remedy families are BUILT + REJECTED/EXHAUSTED
(offer surface ercot33/37; online-capacity envelope ercot41/43; reserve-demand
side exhausted-without-a-build, ercot-g22-demand-side-design-2026-07.md). The
2024/25 legs were substantially a DATA defect now fixed (HSL CPT->CST clock bug,
ercot44). REMAINING owner-open work is the 2023 leg: (a) scarcity-anticipating,
heterogeneity-PRESERVING offer-surface formation (filed ercot37 §8 — the earlier
surfaces collapsed offer heterogeneity; build one that does not), and (b) the C3c
DA-basis premium scoring-frame question (model 103 h = 0.57x the RT tail, in-band;
0.33x the DA basis). Read ercot-g22-demand-side-design-2026-07.md,
FINDING-ercot-priceshape-2026-07.md §5-6, ercot-online-capacity-envelope-2026-07.md.

G-37 (storage energy-vs-AS): DIAGNOSED as a dispatch-choice limitation, not a
coupling bug (FINDING-ercot-storage-as-g37-2026-07.md; dispatch.py:1441-1494 is
structurally correct). Validation 0.54-0.61x, below the 0.8-1.3x band, because
evening SOC depletion from energy arbitrage forecloses AS via the (correct) gate.
The two MISSING mechanisms are new builds, not knobs: (a) forward AS commitment
under uncertainty vs perfect-foresight greedy arbitrage; (b) evening fast-AS
scarcity price formation from a grounded ramp-qualified thermal-reserve limit
(data/ramp_capability.py). Build at least (b) — it also feeds G-22's evening tail.

Task: build the heterogeneity-preserving scarcity-anticipating offer surface
(G-22a) and the ramp-qualified evening fast-AS scarcity-price mechanism (G-37b),
each default-off with a trivial-case test; re-solve ERCOT all years; gate each on
whether it reproduces the observed 2023 tail WITHOUT over-firing other
months/years. Register the run(s). Honesty gate: duals/offers form from the LP +
grounded ramp limits, never an adder tuned to the MCPC or the price residual.
```

---

## L-G — CAISO belly-gas commitment grounding + seam contracted base  ·  Fable  ·  SH (CAISO namespace)

```
G-15 + G-61 in docs/gap-register-2026-07.md, one CAISO namespace. The seam
timezone artifact is RESOLVED and the envelope-clock fix has LANDED (current
keeper 2026-07-07-caiso65-seam-envelope-clock — re-verify in keepers.json). On the
TRUE clock the model OVER-imports the belly +2.5-3.3 GW yet never curtails, and
measured CAISO runs 3.1-5.2 GW MORE belly gas than the model at $13-33 while the
model's exact-fit belly is gas-marginal at $37-59. So the C3a body and the
CT-drag's residual are NOT a seam-delivery problem — they are BELLY-GAS
COMMITMENT. Read FINDING-caiso-seam-tz-correction-2026-07-07.md §4/§6 and
docs/handoffs/caiso-ct-drag-d8-closure-2026-07.md §6-8. Owns the CAISO
registry/bundle namespace + CAISO-only config sections.

Three threads, all grounded-input builds (no residual-tuned adders):
1. G-15 residual (a) — ground the real belly commitment from MEASURED drivers:
   CEMS belly min-load patterns, must-offer / exceptional-dispatch records,
   AS-holding. This is the object that sets CAISO's curtailment/import margin.
2. G-15 residual (b) — the seam's contracted evening/overnight base: DMM RA-import
   capacity (undersized vs the revealed 4.3-5.9 GW self-scheduled base), EIM
   transfer volumes / CARB specified-source imports as the measured objects.
3. G-61(b) adoption decision — caiso_ra_bridge_startup_aware
   (2026-07-07-caiso-63-g61b-startup) cut RA phantom-anchored belly energy ~40%
   (more faithful UC physics) but moved lambda AWAY from actual, exactly as the
   over-committed-belly finding predicts. Weigh tz-correction §4.3, then put the
   keeper-adoption question to the owner. G-61(c)
   (caiso_ra_bridge_curtailment_release) stays built but is BLOCKED on thread 1
   (P0 never curtails a MWh 2023-25) — do not force it.

Deliverable: the belly-commitment grounding + contracted-base intake wired via the
data contract (schema-first, clean seam), a CAISO all-years re-solve registered on
the dashboard, and the caiso-63 adoption memo. Honesty gate: belly commitment and
the contracted base are measured physical/market inputs with a forward analogue
(rule 13), never dispatch pinned to actuals.
```

---

## L-H — PJM ST_GAS volume driver + reserve magnitude + band generalize  ·  Opus/Fable  ·  SH (PJM namespace)

```
G-21 residual + G-20b successor + #1302, one PJM namespace. Re-verify the current
PJM keeper (was 2026-07-06-pjm-83-srmc-reground; active pjm-87/88/89 probes and
a steam-gas-drag re-solve are in flight — check keepers.json and origin/main
HEAD before solving). Owns the PJM registry/bundle namespace + PJM-only config
sections.

G-21: the offer re-grounding is CLOSED (pjm-83). The relocated ST_GAS volume
residual driver is FOUND — net-load reliability commitment, NOT RMR
(FINDING-pjm-stgas-volume-driver-2026-07.md; drag slope 0.01029/GW, cap 0.39).
The pre-probe blocker is the 2023 Montour-conversion vintage nameplate overshoot
(#1483). Task: fix the 2023 conversion-vintage nameplate, then run the ST_GAS
drag probe full-span and gate on C1/C2 (does restoring the reliability-commitment
volume fix the C2 sysvol FAIL without a new floor stacking, rule 15/17).

G-20b: reserve-supply scoping is CLOSED as non-fire; the per-gen opportunity-cost
co-opt pjm_reserve_pergen_sync (pjm-87) fires 133/44/50 h/yr strictly sub-$32 —
structurally correct (opportunity-cost, not shortage) but the magnitude sits in
$0-10, below the $75-200 afternoon residual. pjm-88's size-split adds frequency
without magnitude at a real dispatch-distortion cost. This is a MAGNITUDE
follow-up, not a promotion: either find the structural reason the marginal-unit
opportunity cost is under-priced (ramp10 basis? pool granularity?) or refer to
owner as accepted-limitation. Do NOT lower any breakpoint/penalty (rule 11).

#1302: generalize the Manual-15-SRMC committed-band re-grounding (the pjm-83 fix)
to the OTHER ISOs' committed bands (NYISO/MISO/NEISO/CAISO) — but only where each
ISO's own SRMC floor is cited; a multiplier fitted on PJM's residual must NOT
cross an ISO boundary (rule 25). This sub-task is design-only here (each ISO's
re-solve belongs to its own lane); deliver the cross-ISO SRMC-floor audit + the
per-ISO recipe, not the solves.

Deliverable: the 2023 nameplate fix + ST_GAS drag probe registered; a magnitude
memo for G-20b; the #1302 cross-ISO SRMC audit. Honesty gate: reliability-commit
volume and reserve duals form from grounded physics, never a residual-tuned floor.
```

---

## L-I — NEISO ST_GAS C7 diurnal root cause  ·  Opus  ·  SH (NEISO namespace)

```
G-16 in docs/gap-register-2026-07.md. NEISO is calibration-COMPLETE (marker
2026-07-07, keeper 2026-07-07-neiso53-winter-fuelsec-coldsnap) — so its 2022 /
H1-2026 holdouts are UNLOCKED for the one-shot per rule 22, but that is a separate
declaration action; DO NOT touch holdout years here unless explicitly running the
one-shot. This lane is the remaining TRAIN-window (2023-2025) C7 structural gap.
Owns the NEISO registry/bundle namespace + NEISO-only config sections.

ST_GAS D-1 diurnal now PASSES for the first time in 2025 (profile_r 0.844, via the
CT ST_GAS net-load reliability-commitment limb + measured CAMPD offer bands) but
2023 and 2024 still FAIL: 2023 r 0.49 (profile mis-phased evening-vs-actual-midday,
off-peak cv_ratio 4.606); 2024 r 0.725, cv_ratio 0.0 (flat-floor-only year at
$2.19 HH gas). The keeper carries C7 as its single protective-tier ledgered caveat.
Read the NEISO keeper's legitimacy_diagnostics.json (D-1 rows) and
docs/multi-iso/neiso-winter-fuel-inventory-plan-2026-07.md.

Task: root-cause the 2023 evening-vs-midday phase error and the 2024 flat-floor
collapse (the commitment limb produces a flat floor when gas is cheap — is the
diurnal shape driver missing, or is the floor binding in hours the driver says the
class is offline? cross-check D-4 off-window per rule 12). Fix the SHAPE driver
(not a new floor, rule 17 — one mechanism per phenomenon; reconcile with the
existing limb), re-solve all years, and check C7 D-1 across 2023-2025.

Deliverable: the diurnal-driver fix, the NEISO all-years re-solve registered, and
whether C7 clears. Honesty gate: the diurnal shape comes from the class's real
run pattern (measured hour-of-day CF), never a floor forced to match the profile.
```

---

## L-J — NYISO downstate scarcity tail + floor scalars  ·  Fable  ·  SH (NYISO namespace)

```
G-20c residual + the NYISO G-26 scalar items, one NYISO namespace. Re-verify the
current NYISO keeper (was 2026-07-07-nyiso-56-measured-zonal). Owns the NYISO
registry/bundle namespace + NYISO-only config sections.

G-20c is LARGELY RESOLVED (nyiso-56-measured-zonal): the measured-per-zone-load
fallback made the downstate pocket BIND and the in-LP locational reserve co-opt
fire (2023 NYC LBMP $1,684 vs Upstate $152; C3c RT tail 0->21h vs actual 10h).
REMAINING open: the 2024 (mild) + 2025 deep >$300 tail (model 0h). The named next
lever is DOWNSTATE IMPORT DISCIPLINE — the measured NYC locality import limit
(2,875 MW) is below the model's Dunwoodie estimate (3,900 MW); apply the measured
locality limit in-window (like the #1345 LI LCR/TSL fix already did). Read
docs/g20-scarcity-price-formation-diagnosis-2026-07.md (G-20c) and
nyiso-rcpf-overlay.md.

G-26 NYISO items: #1345 (LI 0.45 floor) is already fixed in nyiso-53/56's recipe
via nyiso_li_lcr_tsl — verify it carries a citation + is registry-reachable, and
recommend the owner CLOSE #1345 referencing the current keeper. #1344 (endogenous
reserve-scarcity requirement, Ask-B) stays DATA-BLOCKED (measured prices exist; a
condition-varying requirement series does not) — file/confirm the data ask, do NOT
hand-size a requirement (rule 11). The LI/NYC delivered-gas Ask-A is FULFILLED
(nyiso-downstate-gas datatype v2) — no action.

Task: intake the measured NYC locality import limit through the data contract and
apply it in-window; re-solve all years; check whether the 2024/25 >$300 tail moves
toward the actual ratio band. Do NOT tune the RCPF overlay breakpoints (rule 11).

Deliverable: the import-limit intake + NYISO all-years re-solve registered, the
#1345 close recommendation, and the #1344 data-ask confirmation. Honesty gate:
the locality import limit is a measured deliverability capability (rule 13), not a
flow pinned to the measured net interchange.
```

---

## L-K — Statmode D-7 twin re-solves for the current keepers  ·  Opus  ·  SH

```
G-10 in docs/gap-register-2026-07.md. The statistical-mode (D-7) integrity
labeling is done (stale-boxes + a re-solve queue in
docs/statistical-mode-results-2026-07.md) but the D-7 NUMBERS are not yet valid
for the current keepers: PJM/MISO need a same-SHA keeper replay, and
CAISO/NYISO/NEISO r2/v2 twins remain confounded (no same-SHA replay since the
keeper swaps). Owns docs/statistical-mode-results-2026-07.md + the statmode
registry sidecars ONLY — do NOT change any keeper config (this is a replay of the
FROZEN keeper recipe at a single SHA, not a re-tune).

Task: for each ISO whose statmode twin is flagged stale, replay the CURRENT
keeper recipe (from keepers.json) at one pinned HEAD SHA in statistical mode, so
the D-7 r2/v2 twin is same-SHA-comparable to the keeper. Solve all scoreable years
per bundle (rule 16). This is SH and must obey rule 12 (≤2 concurrent, years
sequential within a run) — coordinate the RAM cap with any live per-ISO solve lane.
Update the stale-boxes to CURRENT once each twin is same-SHA.

Deliverable: the same-SHA statmode twins registered, the doc's stale-boxes cleared
to current, committed and pushed. Honesty gate: a D-7 number may only be quoted as
skill once its twin is a same-SHA replay of the current keeper — this lane makes
that true; it does not manufacture a better number.
```

---

*Compiled from `docs/gap-register-2026-07.md` (open set per its 2026-07-07
reconciliation addendum) against `keepers.json` HEAD. Excluded: G-19 (holdout
intake, deferred by owner decision to declaration time) and G-40 (MISO memory
ceiling, measured — multi-year needs ~16 GB + swap; residual is an L-effort
year-loop shave, not a fresh-session lane). Per-ISO lanes name the keeper current
at compile time; each session re-verifies before solving.*
