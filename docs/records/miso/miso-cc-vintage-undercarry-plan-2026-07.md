# MISO CC fleet-vintage under-carry — the Cottonwood lane (charter / design)

**Date:** 2026-07-16. **Session:** `claude/miso-cc-cottonwood-lane-udeaem`
(design doc only — no solve, no mechanism, no keeper edit is produced here;
execution is a separate owner-authorized session). **Trigger:** the sole
remaining C1 fail on the promoted MISO keeper `2026-07-16-miso-67-stgas-p25`
— **CC_REGULAR-2023 = −9.79** (volume; the CC share is fine) — which the
miso-67 registration already names as "its own lane": *"the honest measured
fleet exposes the pre-existing Cottonwood (55358) status under-carry."* This
document turns that one-line pointer into an execution charter: the measured
fact (independently re-verified this session), why both existing fleet-injection
channels miss it, the two design options the owner asked to be weighed, a
recommended synthesis, and the validation + rule-compliance plan.

**Verification note.** Every number below was recomputed this session from the
committed on-disk inputs (`data/raw/eia-860/…`, `data/raw/campd-unit-level/…`)
and the registered miso-67 bundle — not carried over from the prior handoff.
Nothing is fit to a residual (rules 1/11/13). No year outside 2023–2025 was
touched (rule 22 — MISO has no calibration-complete marker).

---

## 1. The measured fact (re-verified 2026-07-16)

**Cottonwood Energy Company LP**, plant **55358**, BA = **MISO** (Entergy TX,
MISO-South). A ~1.14 GW 4×(CT+ST) natural-gas combined-cycle plant. Its status
differs between the committed operable snapshot and the year-matched vintages:

| source | rows | status split | carried (OP) net-summer MW |
|---|---|---|---|
| canonical `eia860_generators.parquet` (2025 Early Release) | 8 | **4 OP + 4 OA** | **580.4** (CT3, CT4, ST3, ST4) |
| `vintage_2023/…` (2023 final release) | 8 | **8 OP** | **1145.2** |
| `vintage_2024/…` (2024 final release) | 8 | **8 OP** | **1138.8** |

The 4 units the canonical snapshot marks **OA** (out-of-service, mothballed —
CT1, CT2, ST1, ST2, **576.2 MW** net-summer) were **OP** in both the 2023 and
2024 EIA-860 releases. The model represents every backcast year with the single
2025ER snapshot, so those four units are absent from *every* modeled MISO year.

**The dropped units demonstrably operated** — CAMPD (`TX_2023.parquet`,
`TX_2024.parquet`; CEMS monitors the four CTs) shows the OA-flagged CT1/CT2
running hard:

| unit (2023) | max MW | mean MW | hours running (>1 MW) |
|---|---|---|---|
| CT1 (OA in snapshot) | 318 | 233 | **88%** |
| CT2 (OA in snapshot) | 320 | 233 | **91%** |
| CT3 (OP) | 304 | 234 | 75% |
| CT4 (OP) | 312 | 229 | 42% |

Plant CT-block hourly gross load p999 = **1204 MW (2023) / 1214 MW (2024)**,
max ~1224/1231 MW — i.e. the whole plant ran near its ~1.14 GW nameplate, while
the model carries only 580 MW of it. This is a real ~570 MW capability the LP
never sees: the CC_REGULAR class under-generates in 2023 because ~half of
Cottonwood's fleet is missing, and the −9.79 TWh volume miss is the direct
consequence.

**Why this is the *residual* now and was not before.** The miso-66 keeper's CC
class passed only because ~580 MW of *double-filed phantom* capacity (the
un-guarded EIA-860 CA-row double count) masked this pre-existing under-carry.
The 2026-07-16 bisect removed the phantom (`cc_capacity_reconcile_MISO.csv`
re-derived `--mode both`, commit `775eea1`; guard commits `d7cc13a`/`e3b575e`)
— correctly, per rule 11 — which surfaced the honest shortfall. **The fix is to
carry the real units, never to restore the phantom** (rules 1/11/13). Do NOT
relitigate the bisect.

---

## 2. Why both existing injection channels miss it

The fleet loader has exactly two channels that add units the current operable
snapshot omits. Cottonwood falls through both:

1. **The OP filter** (`fleet.py::_rows_to_generators`, line 5230–5232):
   `df = df[status == "OP"]`. This drops the four OA units outright. OA is a
   *mothball* (out of service, expected to return), not a retirement — so the
   filter is correct in general (a truly-idle mothball *should* be dropped);
   it just has no way to distinguish an idle mothball from one that ran all
   year.

2. **The within-window retiree channel** (`fleet.py::load_retired_within_window`
   → `process_eia860.py::build_within_window_retirees`). Two independent reasons
   it cannot see Cottonwood:
   - It reads the **"Retired and Canceled"** sheet. An OA mothball is *not*
     retired — it never appears on that sheet, so the channel never considers
     it.
   - Even if it did, the channel emits **whole-plant exits only** (lines
     267–272, 339–341): *"any plant still present in the operable snapshot is
     dropped… the plant-keyed COD map would hold the whole plant online."*
     Cottonwood is a **partial** mothball (4 of 8 units still OP), so the
     whole-plant rule — the very rule that prevents a partial-plant over-count
     — excludes it by construction.

**Net:** an OP→OA *partial* mothball of a still-operating unit is the exact
blind spot between the two channels. Cottonwood is invisible to both.

---

## 3. Scope of the general class (rule 24 — mechanism, not a per-plant fix)

Rule 24 forbids a per-plant dict. A fix must be a general mechanism keyed on
unit *status/physics*, even if Cottonwood is today the only material instance.
MISO-wide scan of the canonical snapshot:

- **8 MISO plants** carry a partial OP+OA split. **Only Cottonwood is
  material** — 576 MW dropped. The next largest is Biron Mill (10234) at
  27.8 MW; the rest are ≤28 MW hydro / gas-ICE / refinery-cogen.
- MISO-wide **total OA** dropped by the OP filter = **1,437.7 MW across 16
  plants**; Cottonwood alone is 40% of it and is the only CC-class instance.

So the mechanism must be general (any OP→OA-but-operating unit, any ISO), but
its material footprint in MISO today is essentially one plant. This matters for
the design: a *broad* re-gate (option b) moves the entire fleet to fix one
plant; a *narrow* channel (option a) touches only the affected units. Both must
be **gated, default-off, ISO-agnostic** (rules 24/25).

---

## 4. The admissibility hinge (rule 13) — the guardrail that governs every option

**OA status alone is NOT the re-carry signal.** Re-carrying an OA unit that
genuinely sat idle would inject phantom capacity — the *New Covert inversion,
inverted* (the same class of error the bisect just removed, in the opposite
direction). The re-carry trigger MUST be **availability-grounded**: the unit is
re-carried for a solve year only if it was demonstrably available/operating
*that year*. Two admissible oracles, both rule-13-clean (a reproducible
physical-availability fact with a forward analogue — "could this quantity be
produced for a forward year and respond to changed conditions?" → yes):

- **Vintage-status oracle:** the unit is **OP in the year-matched EIA-860
  vintage** (`vintage_<solve_year>/`). This is EIA's own contemporaneous
  status — self-consistent (a unit truly idle in 2023 would be OA in
  `vintage_2023` too), zero fitted parameters, and exactly the signal the
  vintage system was built to deliver.
- **CAMPD-demonstrated oracle:** the unit **ran** (CEMS operating hours above a
  threshold) in the solve year. Rule-13-admissible (physical availability
  event) but introduces a CAMPD dependency and a threshold DOF.

**The vintage-status oracle is preferred** — it carries no new DOF and is the
same data option (b) uses. It is the spine of the recommended synthesis (§7).

Forbidden under every option (rules 1/11/13): pinning Cottonwood to its CAMPD
MWh, adding a MW offset tuned to the −9.79 residual, or restoring the removed
double-filed phantom. The fix carries *real units at their nameplate/availability
bounds* and lets the LP dispatch them.

---

## 5. Option (a) — OA-within-window channel (narrow, status-transition-scoped)

Extend the injection machinery with a new channel for OP→OA mothballs that were
operating, mirroring `load_retired_within_window` but for the mothball
transition instead of retirement.

**Shape.** A new gated loader (working name
`load_mothballed_but_operating`, `ScenarioConfig.carry_operating_mothballs`,
default **off**, backcast-only) that:
- reads OA-status units from the **operable** sheet of the current snapshot
  (not the Retired-and-Canceled sheet — that is where the retiree channel looks
  and OA units are not there);
- keeps a unit **only if the availability oracle fires** (§4 — recommended:
  OP in the year-matched vintage);
- injects it into the fleet as an ordinary `Generator` at its measured
  net-summer capacity, `status`→OP for the loader, **per-unit** (not
  whole-plant), so a partial mothball carries only its mothballed-but-operating
  units and leaves the surviving OP units untouched.

**Structural obstacles to resolve (why this is not a one-line extension):**
1. **Partial-plant injection vs the plant-keyed COD map.** The retiree channel's
   whole-plant rule exists because `cod_ramp` is plant-keyed and would hold a
   whole plant online. A partial mothball must inject *individual units* without
   the COD map double-counting the surviving OP units. Requires the injected
   units to carry a unit-level (not plant-level) presence key, or to be excluded
   from the plant-keyed COD carry. **This is the core engineering risk.**
2. **Source sheet.** OA units live in the operable sheet; the loader must read
   status=OA there, which the current `_rows_to_generators` OP filter discards.
   The channel therefore pre-filters to OA *before* the shared row builder, or
   the builder gains a status-allowlist parameter.
3. **Forward regeneration (rule 12 forward story).** In forecast mode there is
   no year-matched vintage, so the vintage-status oracle can't fire. The forward
   rule must be explicit: a unit OP in its most recent vintage is physically
   available and carried forward until a real exit (economic screen or the
   confirmed-retirement registry) removes it. This gives option (a) a *cleaner
   forward story than option (b)* (which resets to canonical in forecast and
   keeps the units dropped).

**Blast radius:** minimal — only the mothballed-but-operating units change;
every other class stays on the calibrated canonical snapshot, preserving the
miso-67 keeper's calibration. This is option (a)'s decisive advantage.

---

## 6. Option (b) — per-solve-year EIA-860 vintage (broad, full re-gate)

Point the whole fleet at the year-matched vintage for each solved year, using
the **existing, purpose-built** machinery: `ScenarioConfig.eia860_vintage_year`
→ `paths.set_eia860_vintage` → `paths.active_eia860_dir`. `vintage_2023` and
`vintage_2024` carry all 8 Cottonwood units as OP, so this fixes the under-carry
with **no new mechanism** — it is "prefer accurate/measured data" (rule 11) in
its purest form: use the year-correct fleet for the year being solved. The
paths.py design comment already names this exact failure mode: *"the absence of
units that retired between the solved year and the 2025 snapshot."*

**How it actually runs (precise — this is a common misread).** The vintage is a
**single scalar set once per `run_scenario_iso` process**, before the year loop
(`runner.py:487`); the base fleet is built once (line 730) and `evolve_fleet`
carries it forward. So a *single multi-year process* cannot use per-year
vintages without restructuring the base-fleet build. **But the calibration path
already solves each year in a separate process** (the miso-67
per-year+`--reuse-solved` flow): each per-year invocation sets
`eia860_vintage_year = <its solve year>`, and the final `--years 2023,2024,2025`
bundle byte-reuses the 2023/2024 parquets and solves only the fresh year. So
**per-solve-year vintages emerge from the reuse orchestration, not from a runner
change** — the existing scalar suffices for the calibration flow. (A true
in-process per-year vintage would need a new `eia860_vintage_per_solve_year`
mode that moves the vintage set + base-fleet build inside the year loop,
asserted backcast-only since forecast evolution carries one fleet forward.
Not required for the calibration path; noted for completeness.)

**Gaps / costs:**
1. **No `vintage_2025` exists** (dirs on disk: 2018–2024). The canonical
   snapshot *is* the 2025 Early Release, so the 2025 solve falls back to
   canonical and **still under-carries Cottonwood in 2025**. Option (b) fixes
   2023 + 2024 only. (The failing year is CC_REGULAR-**2023**, which (b) does
   fix — but rule 16's all-years bundle and the forward story leave 2025 short.)
   Closing 2025 needs a `vintage_2025` intake (a separate data-intake session;
   the 2025 final EIA-860 may not be released yet).
2. **Blast radius is the whole MISO fleet.** Switching to `vintage_2023`
   re-gates every class/plant, not just Cottonwood — capacities, vintages, and
   the COD-ramp smear all move. The paths.py note estimates ~0.4% on ERCOT
   installed capacity, but MISO-specific effects across all classes are unknown
   and could reopen other residuals. **Mandatory full leave-one-year-out
   validation** (rule 22) — this is a structural change touching every class.
3. **Forecast:** resets to canonical (runner.py:489 gates vintage on
   backcast/hindcast only), so the forward fleet keeps the units dropped — the
   opposite of what CAMPD-through-2024 operation implies.

**Blast radius:** large. Its appeal is zero new code (flip an existing switch)
and maximal provenance-correctness; its cost is a full re-gate + LOO + the
2025/forecast gaps.

---

## 7. Recommendation — scoped option (a) with the vintage-status oracle

**Recommend the narrow channel (option a), using option (b)'s vintage data as
the availability oracle rather than a new CAMPD threshold.** This synthesis
takes the best of both:

- **Mechanism = option (a):** a gated, default-off, ISO-agnostic
  `load_mothballed_but_operating` channel that injects *only* the affected
  units (minimal blast radius — the miso-67 keeper's calibration of every other
  class is preserved).
- **Trigger = option (b)'s data:** re-carry an OA unit for solve year *Y* iff it
  is **OP in `vintage_<Y>`**. No fitted threshold, no new DOF — the year-matched
  vintage's own status is the oracle. Rule-13-clean and forward-regenerating (a
  unit OP in its latest vintage is carried forward until a real exit).

Rationale: the defect is a **provenance defect** (2025 snapshot used to
represent 2023), and the *correct* input is the year-matched fleet. Option (b)
delivers that but re-gates everything and stalls on the missing `vintage_2025`;
the scoped-(a) synthesis delivers the *same year-correct carry for the affected
units* while leaving the rest of the calibrated fleet on the canonical snapshot,
and it degrades gracefully where no vintage exists (2025: fall back to the
CAMPD-demonstrated oracle for those specific units, or carry-forward the latest
vintage-OP status — an explicit design choice for execution).

This is a **proposal, not a decision** — the owner asked for the options weighed,
and the probe adjudicates the actual scored effect. If the owner prefers the
zero-new-code route, plain option (b) on 2023/2024 is a legitimate first cut
(it fixes the failing year) with the 2025/forecast caveats documented.

**Owner decision needed** before any execution (§10).

---

## 8. Validation plan (execution session — not this one)

Structural change ⇒ **leave-one-year-out within 2023–2025 before promotion**
(rule 22). Concretely:

1. **Probe = mechanism-only.** Build a probe off the miso-67 recipe with the new
   gate ON (`main`) vs the identical recipe with it OFF (`base`), both solved in
   the same box/code state — mechanism-only footprint = `main − base`, never
   vs the registered miso-67 bundle (the miso-66 drift lesson). Reuse the
   per-year+`--reuse-solved` harness pattern
   (`scripts/probes/_miso67_stgas_vlr_level.py` is the template — a sibling
   probe script, not an edit to that one). Years **2023/2024/2025 only**, one LP
   per process, sequential, clean tree during solves.
2. **LOO scoring.** Score the verdict flip leave-one-year-out across 2023–2025
   (fit on two years, check the held-out year) — in-sample gain with held-out
   degradation is overfitting, not skill.
3. **Expected direction (probe decides, do not pre-judge):** CC_REGULAR-2023
   volume rises toward the actual (closing the −9.79), CC share stays in band,
   the price-shape vetoes (C3b ≤0.20) hold, and no other C1 class is pushed out
   of band by the added ~570 MW. Watch CC_REGULAR-2024/2025 (currently passing)
   for over-carry — the 2024 vintage also carries the units, so 2024 should
   move too; 2025 depends on the oracle choice for the missing vintage.
4. **DOF ledger.** The new gate is a boolean, default-off; the vintage-status
   oracle adds **zero fitted parameters** (a CAMPD-threshold oracle would add
   one — prefer the vintage oracle to keep DOF flat). Record it in the keeper
   attestation.
5. **Register every solve** (`dashboard_add_run`) in the same session — keeper
   *or* rejected probe, no unregistered probes (rule 15). Lead with the
   dashboard result.

---

## 9. Rule-compliance matrix

| rule | how satisfied |
|---|---|
| 1 (structure first, not fit) | fixes a real fleet-provenance defect; not tuned to the residual |
| 11 (prefer accurate data) | carries year-correct EIA-860 status instead of a stale snapshot; the whole point |
| 13 (measured input, not answer) | re-carry gated on an availability oracle with a forward analogue; never pins to CAMPD MWh or the residual |
| 12 (forward story) | scoped-(a) carries vintage-OP units forward until a real exit; option (b) documented as forecast-reset |
| 22 (holdouts / LOO) | 2023–2025 only; structural change ⇒ LOO before promotion |
| 23 (derives frozen vs residuals) | no deriver touched; the `--mode both` CC re-derive is already done/committed (`775eea1`) and is *not* redone here |
| 24 (no off-registry / per-plant) | gated `ScenarioConfig` boolean; ISO-agnostic status/physics trigger; no per-plant dict |
| 25 (ISO boundaries / deleted-means-deleted) | neutral, general mechanism; no ISO-fitted scalar |
| 27 (core-file integrity) | edits to `fleet.py`/`scenarios.py`/`runner.py` are local Edit + blob-verify; Opus/Fable only |

---

## 10. Open questions for the owner (decide before execution)

1. **Which option** — scoped-(a)+vintage-oracle (recommended §7), plain option
   (b), or (a) with a CAMPD-demonstrated oracle?
2. **2025 leg:** accept the 2025 under-carry for now (the failing year is 2023),
   authorize a `vintage_2025` data intake, or use the CAMPD/carry-forward oracle
   for units with no year-matched vintage?
3. **Forward (forecast) behavior:** carry mothballed-but-operating units forward
   (scoped-(a) can), or leave forecast on canonical? This is a methodology call
   about how long a mothball-that-ran should persist absent a confirmed exit.
4. **Scope expansion:** this session is chartered design-only. Confirm whether
   the execution (probe + LOO + register) proceeds in a follow-up Opus/Fable
   session (rule 27 lane assignment).

---

## 11. Non-goals — do NOT chase these

- **The derive SKIP-flagged plants** (Riverside EC 55641, High Bridge 1912, et
  al.): adjudicated **CAMPD facility contamination**, byte-identical in the 2023
  vintage — they are *not* under-carries and must not be treated as this lane's
  targets.
- **The other 7 partial-mothball MISO plants** (§3, all ≤28 MW): below any
  material threshold; the general mechanism will pick them up if the oracle
  fires, but none is worth structural work on its own.
- **The MISO price-formation lane** (C3a-2025 −14.3% / C3c): **F4-blocked** on
  OASIS max-gen-event access (`oasis.oati.com` / `cdn.misoenergy.org` allowlist,
  or the owner drops emergency-declaration decks into
  `data/raw/miso-maxgen-events/`) — owner action item, see
  `docs/handoffs/miso-phase-b-m1-maxgen-findings-2026-07.md`. Untouched here.
- **Restoring the removed phantom capacity** (the double-filed CA rows): that
  was the bug the bisect fixed (rule 11). The fix is real units, never the
  phantom.
- **Any keeper edit** beyond what is already authorized: owner-only.

---

**Cross-references:** miso-67 registration
`frontend/data/backcast/registry/2026-07-16-miso-67-stgas-p25.json` (names this
lane); the bisect + `--mode both` re-derive (`docs/calibration-log.md`
2026-07-16 entry, commit `775eea1`); the CC-capacity guard
(`docs/cc-capacity-reconcile-unification-2026-07.md`, New Covert inversion);
the vintage machinery (`src/market_sim/config/paths.py` §`set_eia860_vintage`,
`docs/cod-vintage-ramp.md`); the retiree channel
(`scripts/data/process_eia860.py::build_within_window_retirees`,
`src/market_sim/data/fleet.py::load_retired_within_window`).
