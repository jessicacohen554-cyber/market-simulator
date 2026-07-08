# Gap Register 2026-07 — parallel prompt pack (code-verified 2026-07-08)

Ready-to-paste handoff prompts for the gaps in `docs/gap-register-2026-07.md` that are
**genuinely open AND not already in-flight**, verified against `origin/main` HEAD on
2026-07-08 (five read-only code/artifact audits, not the register prose — the register's
own 2026-07-07 "open ~14" list was substantially stale). Each prompt is self-contained:
drop it into a fresh Claude Code session on this repo.

> **Why this pack is much shorter than the register's open list.** A code audit found the
> register carries closed and in-flight gaps as "open". The disposition below is the
> authority; the register rows are not.

## Disposition ledger (what the audit found)

**Already CLOSED — no prompt (verified at HEAD):**
- **G-42** — CAISO Scope2 Mode-A degenerate frontier fixed 2026-07-05 (ADR 0019,
  `build_tiebreak_epsilon`).
- **G-51 / G-52** — README has a canonical-install-path section (`uv` canonical,
  `run-simulator.sh` a convenience launcher) and the single-year/rule-16 smoke-test caveat.
- **G-26 #1349** — `GAS_AVAILABILITY_FACTOR` dead code deleted (zero refs in `src/`).
- **G-41 code + owner decision** — market-design I7 backstop split landed
  (`resolve_reserve_margin_build_enabled`, commit `00bbd4b`); only a backstop-on
  confirmation re-run remains → **L-8**.
- **G-32** (co-scoped under G-30) — ATB FOM flip + foresight A/B re-run landed
  (`fom-scarcity-defaults-flip-2026-07-07.md`); the hindcast *symptom* is what remains → **L-1**.
- **#1345** (NYISO LI 0.45) — issue CLOSED 2026-07-07; `nyiso_li_lcr_tsl` replaces it
  (the 0.45 scalar survives only on the default-off legacy path).

**IN-FLIGHT — do NOT prompt (a session/PR is on it now; a fresh prompt would duplicate):**
- **G-21 ST_GAS volume driver (#1483)** — PR #1728 built an overnight pre-positioning drag
  (`reliability_floor` engine); `pjm-89`/`pjm-90` (CC_CHP-SRMC) keeper-candidates in flight.
  The literal register proposal (`gas_st_netload_drag` + 2023 nameplate) was deliberately left OFF.
- **G-22 offer-surface / clock round** — the ERCOT clock-unification effort
  (`ercot44b`/`ercot45`/`ercot46` A/B/C, corrected-CST re-derived parquets) SETTLED
  2026-07-08: `ercot46` (clock+steamgas) promoted to the ERCOT keeper (PR #1740) and covers
  the offer-surface leg. **L-2 is re-scoped to G-37 only** (see below); the G-22 offer-surface
  lever is no longer a free lane.
- **G-15 CAISO belly commitment** — as of 2026-07-08 a session landed the belly-grounding
  *diagnostic* (`scripts/caiso_belly_commitment_probe.py` +
  `docs/handoffs/caiso-belly-commitment-probe-2026-07.md`, PRs #1733/#1735) plus a CAISO
  ST_GAS overnight drag (ships disabled). The grounding *intake/mechanism* is not yet built,
  but the investigation is ACTIVE — **L-3 pulled from the dispatch set** (coordinate with that
  session rather than start fresh; kept below as reference, marked IN-FLIGHT).
- **G-61(b)** — `caiso-66` startup-aware probe registered, held back from promotion; the
  remaining step is an owner-adoption decision, not a build → owner queue below.

**Data-blocked / accepted — no prompt:**
- **G-20e** (MISO scarcity tail — no published Midwest zonal reserve requirement; G-25
  posture lever honesty-gate-rejected and struck).
- **G-26 #1347 / #1335 / #1336 / #1348** (coal sigmoids, merchant CHP, coal tranches, wefor —
  source-data-blocked), **#1344** (NYISO condition-varying reserve requirement — data ask).
- **G-19** (holdout intake, deferred to declaration time), **G-40** (MISO ~16 GB + swap).

**Owner decisions — surface, don't dispatch (build is exhausted; needs a human call):**
- **G-61(b)** adopt `caiso-66` onto the CAISO keeper? (weigh `FINDING-caiso-seam-tz-correction` §4.3:
  λ moved away from actual).
- **G-20b** PJM reserve magnitude — `pjm-87` (sync) vs `pjm-88` (size-split) vs hold; both
  non-promotion, referred to owner.
- **G-21** `pjm-89`/`pjm-90` keeper-candidate adjudication (in-flight solve will produce it).

## Open lanes (this pack)

| Lane | Gap(s) | Solve? | Model | ISO namespace |
|---|---|---|---|---|
| **L-1** ERCOT hindcast scarcity/retirement regime | G-30 (narrowed) | SH (non-keeper harness) | Opus/Fable | — |
| **L-2** ERCOT storage energy-vs-AS (G-22 offer-surface now in-flight) | G-37 | SH | Fable | ERCOT |
| ~~**L-3** CAISO belly-gas commitment~~ | ~~G-15~~ IN-FLIGHT (belly probe active, PRs #1733/#1735) | — | — | CAISO |
| **L-4** NEISO ST_GAS C7 diurnal | G-16 | SH | Opus | NEISO |
| **L-5** NYISO downstate import-limit tail | G-20c | SH | Fable | NYISO |
| **L-6** Statmode D-7 same-SHA re-solves | G-10 | SH | Opus | all (frozen replay) |
| **L-7** Cross-ISO SRMC committed-band audit | #1302 | no | Sonnet | — |
| **L-8** PJM I7 backstop-on confirmation re-run | G-41 remainder | light forecast | Sonnet/Opus | — (hindcast) |
| **L-9** Seam-ladder provenance comments | G-26 #1350 | no | Sonnet | — |

## How to run these in parallel

- **No-solve / light lanes (L-7, L-8, L-9): run all concurrently, any tier** — disjoint
  files, no keeper bundle touched. **This is the true first wave** (small — most of the
  original no-solve wave was already done).
- **Solve-heavy lanes (L-1, L-2, L-4, L-5, L-6): run each in its OWN session/environment and
  they can ALL go concurrently.** CLAUDE.md rule 12's "≤2 concurrent" is a *per-machine
  memory* limit (one box OOMs on 2+ per-plant multi-zone LPs) — it does not cap how many
  separate environments run at once, each with its own RAM. The cap that always holds:
  **years run sequentially WITHIN a single invocation** (`--year 2023 2024 2025` is never
  parallelized — that is the within-box OOM risk). Each lane owns a distinct ISO namespace
  (or the non-keeper hindcast harness), so registry/file ownership never conflicts. **L-1 and
  L-2 are both ERCOT** — L-1 is hindcast-harness-only (no keeper), so they don't collide.
- **Every SH lane re-verifies the current keeper** in `frontend/data/backcast/keepers.json`
  and rebases on `origin/main` before solving — the board churns hourly.

**Shared rules every prompt inherits (CLAUDE.md):** right structure first, level second (#1);
measured data only as a reproducible forward-regenerating input, never an outcome pinned to
the residual (#10/#11); a structurally-correct mechanism stays even if it worsens a metric —
fix the root cause (#11); register every completed backcast run on the dashboard
(`calibration-report` + `build_manifest.py`) and commit it same-session (#12); solve ALL
scoreable years in one bundle (#16); no Python loops over hours in LP construction; push via
`mcp__github__push_files`, never `git push`.

---

## L-7 — Cross-ISO SRMC committed-band audit (#1302)  ·  Sonnet  ·  no solve  · FIRST WAVE

```
#1302 (docs/gap-register-2026-07.md G-21 row) generalizes the PJM Manual-15 SRMC
committed-band re-grounding (landed as the pjm-83 keeper) to the OTHER four ISOs'
committed offer bands. This is a DESIGN + AUDIT task only — no solves, no keeper
touch (each ISO's re-solve belongs to its own per-ISO lane later).

For NYISO, MISO, NEISO, CAISO: locate each ISO's committed/must-run offer bands
in the offer path (offer_curves.py, the per-ISO sigmoid/tranche overrides in
config/scenarios.py + constants.py) and compare each sub-SRMC band multiplier to
that ISO's OWN cited SRMC floor (fuel heat-rate x delivered fuel + VOM). Report,
per ISO: which committed bands sit BELOW their SRMC floor (the pjm-83 defect
pattern), the citation backing the current multiplier, and whether it is an
ISO-local fitted value or an ERCOT byte-copy (rule 25 — a multiplier fitted on
one ISO's residual must not cross an ISO boundary; the MISO sigmoid family's
floor/gas_mid/gas_slope are flagged ERCOT byte-copies in the register). NOTE: PJM
is actively re-grounding CC_CHP SRMC (pjm-90 candidate) — treat PJM as the worked
example/reference, not a target.

Deliverable: a cross-ISO SRMC-floor audit table + a per-ISO re-grounding recipe
(which band -> 1.00x SRMC floor, with the citation), written to a short handoff
doc, committed and pushed. Do NOT change any numeric offer value (that changes a
solve). Honesty gate: this scopes the work; each ISO's re-grounding + re-solve is
its own lane and its own keeper decision.
```

---

## L-8 — PJM hindcast I7 backstop-on confirmation re-run (G-41 remainder)  ·  Sonnet/Opus  ·  light forecast  · FIRST WAVE

```
G-41's code + owner decision already landed: resolve_reserve_margin_build_enabled
(model/capacity.py:2143) implements the market-design split (backstop ON for
capacity-market ISOs incl. PJM, OFF for energy-only ERCOT); commit 00bbd4b. The
checker check_i7_reliability_floor was reconciled and already flips I7 FAIL->PASS
on the existing backstop-OFF bundle. FORECAST-SIDE ONLY — no keeper, no backcast
re-gate, no quarantine concern. Owns docs/hindcast-reports/pjm-i7-g41-2026-07-07.md
and the PJM hindcast harness only.

The ONE remaining item: docs/hindcast-reports/pjm-i7-g41-2026-07-07.md line ~40
carries an unfilled marker (<!-- G41_RESOLVE_MARKER ... filled after the
backstop-on PJM re-run -->) and claims a bundle results/hindcast/pjm-2021-2025-
realized-g41 that DOES NOT EXIST. Produce that backstop-default-on PJM hindcast
re-run, confirm I7 PASSES with the backstop actually building (not just the
checker reconciliation), fill the marker with the real numbers, and confirm the
ERCOT hindcast is unchanged (energy-only -> retirement-bounded, backstop stays off).

Deliverable: the backstop-on PJM hindcast bundle + the filled marker + a one-line
ERCOT-unchanged control, committed and pushed. Honesty gate: forecast-mode
capacity-adequacy structure (rule 1); report whatever the re-run shows.
```

---

## L-9 — Seam-ladder provenance comments (G-26 #1350)  ·  Sonnet  ·  no solve  · FIRST WAVE

```
G-26 #1350 in docs/gap-register-2026-07.md. MISO and NEISO seam import/export
tranches are now MEASURED, derived ladders (interchange_config.MISO_SEAM_LADDER_
BY_YEAR; IMPORT_TRANCHES_BY_YEAR["NEISO"] via scripts/derive_neiso_import_tranches.py).
The PJM and CAISO ladders are still bare/near-static literals with weaker
provenance: IMPORT_TRANCHES["PJM"] (interchange_config.py ~:122, no by-year entry
at all) and IMPORT_TRANCHES_BY_YEAR["CAISO"] (~:165, prices identical across all
three years per its own comment); NYISO's by-year prices are a fitted literal with
no derive-script. Owns src/market_sim/config/interchange_config.py (comments only).

Task: for the PJM, CAISO, and NYISO seam ladders, add a citation comment stating
the source/derivation status and an open-issue pointer (#1350 / #C-6) so each
literal is honestly labelled as static-fitted-pending-measured, matching the
MISO/NEISO derived-ladder provenance style. Do NOT change any tranche number or
price (that changes a solve). This is truth-in-labelling for rule-24/rule-11
transparency only.

Deliverable: the provenance comments + a note in the register's G-26 row marking
#1350 PJM/CAISO/NYISO as labelled-open (MISO/NEISO closed), committed and pushed.
Honesty gate: byte-identical LP — comments only.
```

---

## L-1 — ERCOT hindcast scarcity/retirement regime (G-30, narrowed)  ·  Opus/Fable  ·  SH (non-keeper harness)

```
G-30 in docs/gap-register-2026-07.md, NARROWED by a 2026-07-08 code audit: the
co-scoped G-32 work the register listed as the task is DONE — the ATB FOM flip
landed (scenarios.py:264-282, fixed_om_gas_cc=30 / gas_ct=21 / coal=45, "G-32")
and the foresight A/B re-ran (docs/handoffs/foresight-ab-ercot-2026-07-0{6,7}.*;
fom-scarcity-defaults-flip-2026-07-07.md "Closes G-32"). Do NOT redo those.

What REMAINS open: the hindcast SYMPTOM persists at HEAD despite the FOM flip.
docs/hindcast-reports/ercot-2021-2025-realized-2026-07-07.md still shows solar
additions 0.0 GW (-100% FAIL), coal retire +13.96 GW / gas_st +8.83 GW (~22.8 GW
over-retirement), CO2 -49%. The corrective arm entry_lookahead_reprice is
default-OFF (scenarios.py:815) and the foresight work is forecast-scoped. Owns the
hindcast harness scripts + model/capacity.py (coordinate capacity.py section-scope
with nobody else active there now). NON-KEEPER, forecast-side — no quarantine.

Task: determine why the hindcast forms ZERO scarcity hours even after the FOM
flip (perfect-foresight LP on the over-supplied 2020-vintage fleet vs un-grown
realized demand -> ORDC overlay inert -> solar can't clear fixed cost -> whole
coal/gas_st fleet below FOM bar). Evaluate the built-but-off entry_lookahead_reprice
(and/or a limited-foresight screen) ON the hindcast: does tempering foresight let
scarcity form so solar entry clears and the false-retire (96% genuine per the
G-31 per-plant scoring) drops? Over-retirement and 0-GW-solar are DIAGNOSTICS to
close via root cause, never fit targets (rule 11).

Deliverable: the hindcast re-run with the foresight/entry mechanism exercised,
registered, + a note on whether scarcity now forms. Honesty gate: scarcity forms
from the LP regime, never an adder tuned to a retirement or entry number.
```

---

## L-2 — ERCOT storage energy-vs-AS mechanism (G-37)  ·  Fable  ·  SH (ERCOT namespace)

```
G-37 storage energy-vs-AS. STATUS (2026-07-08): the ERCOT clock-unification round
SETTLED — ercot46 (clock+steamgas) is now the ERCOT keeper (2026-07-08-ercot46-
clock-steamgas; re-verify in keepers.json). That effort owns the G-22 offer-surface
leg, so this lane is G-37 ONLY. G-37's mechanism is default-off and touches NO
keeper, so register its ERCOT probe freely against the ercot46 base. Owns
dispatch.py storage/reserve section + data/ramp_capability.py.

G-37 (GENUINELY-OPEN, no active session): validation 0.54-0.61x below the
0.8-1.3x band, DIAGNOSED as a dispatch-choice limitation, not a coupling bug
(FINDING-ercot-storage-as-g37-2026-07.md, disposition "LIMITATION — documented,
not fixed"; dispatch.py:1441-1494 is structurally correct). Evening SOC depletion
from energy arbitrage forecloses AS via the (correct) gate. Neither missing
mechanism is built (grep confirms no forward_as / fast_as in src/): (a) forward AS
commitment under uncertainty vs perfect-foresight greedy arbitrage; (b) evening
fast-AS scarcity price formation from a grounded ramp-qualified thermal-reserve
limit (data/ramp_capability.py). Build at least (b), default-off, trivial-case
test first.

Deliverable: mechanism (b) (and ideally (a)), default-off with tests, an ERCOT
all-years probe registered against the ercot46 base. Honesty gate: duals/offers
form from the LP + grounded ramp limits, never an adder tuned to the MCPC or
price residual.
```

---

## L-3 — CAISO belly-gas commitment grounding + seam contracted base (G-15)  ·  IN-FLIGHT (do not dispatch fresh)

> **STATUS 2026-07-08: IN-FLIGHT — coordinate, do not start a fresh session.** A session
> landed the belly-grounding diagnostic (`scripts/caiso_belly_commitment_probe.py` +
> `docs/handoffs/caiso-belly-commitment-probe-2026-07.md`, PRs #1733/#1735) and a CAISO
> ST_GAS overnight drag (ships disabled). The grounding intake/mechanism isn't built yet,
> but the investigation is live. Continue THAT session (or check its handoff) rather than
> dispatch the prompt below, which would duplicate the probe. Prompt retained for reference.

```
G-15 in docs/gap-register-2026-07.md. The seam TIMEZONE artifact is resolved and
the envelope-clock fix is the current keeper (2026-07-07-caiso65-seam-envelope-
clock, re-verify in keepers.json). On the TRUE clock the model OVER-imports the
belly +2.5-3.3 GW yet never curtails, and measured CAISO runs 3.1-5.2 GW MORE
belly gas than the model at $13-33 while the model's exact-fit belly is gas-
marginal at $37-59 -> the C3a body + CT-drag residual are BELLY-GAS COMMITMENT,
not a seam-delivery problem. Read FINDING-caiso-seam-tz-correction-2026-07-07.md
§4/§6 and docs/handoffs/caiso-ct-drag-d8-closure-2026-07.md §6-8. Owns the CAISO
registry namespace + CAISO-only config sections.

Two grounded-input builds (no residual-tuned adders):
1. Ground the real belly commitment from MEASURED drivers: CEMS belly min-load
   patterns, must-offer / exceptional-dispatch records, AS-holding — the object
   that sets CAISO's curtailment/import margin. Wire via the data contract
   (schema-first, clean seam).
2. The seam's contracted evening/overnight base: DMM RA-import capacity
   (undersized vs the revealed 4.3-5.9 GW self-scheduled base), EIM transfer
   volumes / CARB specified-source imports as the measured objects.

ALSO surface (do not decide): G-61(b) — the caiso-66 startup-aware RA-bridge probe
(caiso_ra_bridge_startup_aware) is built, registered, and HELD BACK from promotion;
its λ moved AWAY from actual, consistent with the over-committed-belly finding.
Adoption is an OWNER decision (weigh tz-correction §4.3) — put it to the owner, do
not adopt unilaterally. Path (c) caiso_ra_bridge_curtailment_release stays blocked
on build #1 (P0 curtails 0 MWh 2023-25).

Deliverable: the belly-commitment grounding + contracted-base intake, a CAISO
all-years re-solve registered, and the G-61(b) adoption memo for the owner.
Honesty gate: belly commitment + contracted base are measured physical/market
inputs with a forward analogue (rule 13), never dispatch pinned to actuals.
```

---

## L-4 — NEISO ST_GAS C7 diurnal root cause (G-16)  ·  Opus  ·  SH (NEISO namespace)

```
G-16 in docs/gap-register-2026-07.md, GENUINELY-OPEN (2026-07-08 audit: PR #1728
steam-gas work is PJM-only, no NEISO files; NEISO ST_GAS untouched since the
keeper). NOTE: NEISO is declared calibration-COMPLETE (calibration-complete.json,
keeper 2026-07-07-neiso53-winter-fuelsec-coldsnap) and C7 was accepted as the
single ledgered protective-tier caveat at completion — so this is a POST-COMPLETION
refinement. Any keeper swap that results must be an explicit owner decision (a
complete ISO's keeper is frozen for its holdout one-shot); DO NOT touch the 2022 /
H1-2026 holdout years here. Owns the NEISO registry namespace + NEISO-only config.

ST_GAS D-1 diurnal PASSES 2025 (profile_r 0.844) but FAILS 2023 (r 0.49, profile
mis-phased evening-vs-actual-midday) and 2024 (r 0.725, cv_ratio 0.0, flat-floor-
only at $2.19 HH gas). Read the keeper's legitimacy_diagnostics.json (D-1 rows)
and docs/multi-iso/neiso-winter-fuel-inventory-plan-2026-07.md.

Task: root-cause the 2023 evening-vs-midday phase error and the 2024 flat-floor
collapse (the reliability-commitment limb produces a flat floor when gas is cheap
— is the diurnal shape driver missing, or is the floor binding in hours the driver
says the class is offline? cross-check D-4 off-window per rule 12). Fix the SHAPE
driver — reconcile with the existing limb, do NOT stack a new floor (rule 17, one
mechanism per phenomenon). Re-solve all TRAIN years (2023-2025). Present any
keeper-swap as an owner decision given completion status.

Deliverable: the diurnal-driver fix, the NEISO 2023-2025 re-solve registered, and
whether C7 clears + the owner keeper-swap question. Honesty gate: the diurnal
shape comes from the class's real hour-of-day CF, never a floor forced to the profile.
```

---

## L-5 — NYISO downstate import-limit scarcity tail (G-20c)  ·  Fable  ·  SH (NYISO namespace)

```
G-20c in docs/gap-register-2026-07.md, GENUINELY-OPEN on the 2024/25 tail. 2023 is
resolved by the keeper (2026-07-07-nyiso-56-measured-zonal, re-verify in
keepers.json; 2023 RT tail 0->21h). IMPORTANT (2026-07-08 audit) — a follow-up
probe nyiso-57-locational-rcpf ALREADY grounded NYISO_RCPF_LOCATIONAL to SOM
primary sources; it did NOT close the tail (C3b/C3c still FAIL) and it is a
DIFFERENT lever — do NOT repeat RCPF grounding. #1345 (LI 0.45) is CLOSED. #1344
(condition-varying reserve requirement, Ask-B) stays DATA-BLOCKED — file/confirm
the ask, do NOT hand-size a requirement (rule 11). Owns the NYISO registry
namespace + NYISO-only config.

The proposed lever is UNBUILT (confirmed 2026-07-08: the Dunwoodie-South -> NYC
zone-J import limit in iso_configs.py is still the ~3,900 MW model ESTIMATE, not
the measured value): intake the measured NYC locality import limit (~2,875 MW)
and apply it in-window (the same in-window pattern the #1345 LI LCR/TSL fix used).
Intake it through the data contract; re-solve all years; check whether the 2024
(mild) + 2025 deep >$300 tail moves toward the actual ratio band (model currently
0h). Do NOT tune the RCPF overlay breakpoints (rule 11).

Deliverable: the NYC locality import-limit intake + NYISO all-years re-solve
registered + the #1344 data-ask confirmation. Honesty gate: the locality import
limit is a measured deliverability capability (rule 13), not a flow pinned to the
measured net interchange. If the tail stays open after the import limit, the
residual is the #1344 data block — document it, don't force it.
```

---

## L-6 — Statmode D-7 same-SHA twin re-solves (G-10)  ·  Opus  ·  SH

```
G-10 in docs/gap-register-2026-07.md, GENUINELY-OPEN (2026-07-08 audit: NO statmode
bundle exists for ANY of the six current keepers). Current keepers (re-verify in
keepers.json; churn fast): ercot46-clock-steamgas / caiso65 / pjm-83 / nyiso-56 /
neiso53 / miso-47-steamgas-ct (ERCOT churned 42->46 and MISO 46->47 on 2026-07-08;
a pjm-90 CC_CHP-SRMC candidate is in flight — confirm the live PJM keeper before
replaying). Every statmode registry sidecar
replays a SUPERSEDED bundle (caiso51 / miso39 / neiso48 / nyiso41 / ercot34). The
doc's own re-solve queue (statistical-mode-results-2026-07.md:443-463) is itself
doubly stale — it names ercot34/caiso58/nyiso53/neiso50/miso44 as "current", also
superseded. Owns docs/statistical-mode-results-2026-07.md + the statmode registry
sidecars ONLY — do NOT change any keeper config (this is a FROZEN-recipe replay at
one SHA, not a re-tune).

Task: for each of the six current keepers, replay the keeper recipe (from
keepers.json) at one pinned HEAD SHA in statistical mode so the D-7 r2/v2 twin is
same-SHA-comparable to the keeper. Solve all scoreable years per bundle (rule 16).
Years run sequentially WITHIN each invocation (rule 12 within-box OOM); separate
sessions/environments may run different keepers' twins concurrently. Coordinate
the RAM cap with any live per-ISO solve lane (MISO needs ~16 GB + swap). Update
the doc's stale-boxes + re-solve queue to CURRENT as each twin lands.

Deliverable: the six same-SHA statmode twins registered + the doc's stale-boxes /
queue cleared to current, committed and pushed. Honesty gate: a D-7 number may be
quoted as skill only once its twin is a same-SHA replay of the current keeper —
this lane makes that true; it does not manufacture a better number.
```

---

*Verified 2026-07-08 against `origin/main` HEAD via five read-only code/artifact audits
(ERCOT, CAISO, PJM, NEISO/NYISO, governance/scalar), then refreshed thrice the same day
(latest: ERCOT keeper 42->46, clock round settled, PR #1740; all five solve lanes
re-confirmed unaddressed). L-3 (CAISO belly, G-15) → IN-FLIGHT (PRs #1733/#1735); L-2 →
G-37-only. Solve lanes run one-per-session/environment concurrently (rule 12's cap is
per-machine); years sequential within each invocation. The board churns hourly — each
session re-verifies keepers.json + rebases before solving.*
