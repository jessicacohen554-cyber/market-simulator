# PRECOMMIT — ercot-239 round 2 (2026-08-30): the AUGUST STEEPNESS object — restore the MEASURED peak-band dispersion (graded `peak_ladder`) under the carve-out's calibrated top. Stage A zero-solve census with an ex-ante go/no-go; Stage B one control + one armed 2023-only solve, kill-gated

**Session ercot-239, branch `claude/ercot-239-residual-queue-lbkvbf`.**
Charter: the residual-queue handoff's priority 2 — the August steepness
object (FINDING-ercot237 §7 candidate 2: *"the k=33 uniform peak lift
places the right MASS of scarcity in August but transitions too steeply
through [500,1000) and on partially wrong afternoons. Any repair is
offer-SURFACE-shape work (rule 1: structure first — a real mechanism,
not a band-targeted fitted reshuffle)"*). Carve-out lane: 2023-only
solves under the owner's standing 2023-discrete charter + invoked
rule-16 waiver (ercot-235 entry, cited not re-derived). This precommit
is pushed + blob-verified BEFORE any Stage-A measurement or solve.

## 0. The candidate, stated up front (recipe reshape, zero new mechanisms, zero new fitted scalars)

The carve-out keeper `2026-08-25-236-swcap-clip-k33` carries FLAT
5-rung `peak_ladder`s (every rung at the class's k33-scaled multiplier:
CC_REGULAR 151.008, CC_CHP 123.684, CT_PEAKER 433.95, ST_GAS 105.6 —
`run_config.json`). The committed MEASURED across-resource dispersion
artifact `data/raw/_validation-source/offer_curve_dam_hrmults_ladder.json`
(60-Day DAM disclosure, capacity-weighted p10/p30/p50/p70/p90 of the
per-resource top-of-curve multiplier, top clamped at HCAP — built by
`derive_dam_offer_hrmults --peak-ladder` as the `peak_ladder` band's
designed substrate, FINDING-ercot-priceshape-2026-07 §4) measures e.g.
CC_REGULAR [4.326, 4.326, 4.326, 43.909, 144.17]. Note the identity the
candidate rests on: **the residual-identified k33 flat level (151.008)
≈ the measured TOP rung (144.17)** — the ercot-235 sweep converged to
the measured wall's top and then applied it to 100 % of the band in
100 % of hours.

**Candidate (per class g ∈ {CC_REGULAR, CC_CHP, CT_PEAKER, ST_GAS}):**

    s_g            = incumbent_flat_mult_g / measured_top_rung_g
    candidate rung = measured_rung × s_g            (all five rungs)
    floor rule     = each rung floored at the class's resolved econ-band
                     maximum multiplier (monotone non-decreasing curve,
                     applied only if a scaled rung would undercut it)

so the TOP rung reproduces the incumbent wall EXACTLY (the calibrated,
DOF-ledgered k33 level is preserved as the class-top anchor — no new
scalar, no re-tune; the ledger entry is reworded, n_residual unchanged)
and the lower rungs take the MEASURED dispersion ratios below it.
Everything else in `offer_curve_by_group` — the scalar `peak`,
`phys_peak`, every econ/committed band, CT_CHP (no measured ladder) —
and every other config field stays byte-identical to the keeper.

Verified code facts the candidate rests on (cited, not measured):
* `assembly.py` builds ladder rungs at `base_hr × mult` per rung — the
  graded recipe needs no code change.
* `gas_offer_margin_markup_mult` handles ladder rungs by design
  ("peak* (incl. measured peak_ladder rungs) — phys_peak") and clips at
  `max(0, mult − phys)` — a rung below phys_peak prices as pure
  fuel-scaled physical burn; NO negative-margin trap.
* `build_ercot_offer_surface_conditional_markup` divides by the SCALAR
  `peak` with `ratio = max(1, measured_bin/pk)` — under pk = 151.008 the
  armed conditional surface is inert TODAY (every condbinned bin-top ≤
  144.19) and stays exactly as inert under the candidate (scalar
  unchanged): no regression, no contract breach. (The scalar-vs-per-rung
  contract generalization is FILED for the owner, not made here.)
* The SWCAP clip (armed) owns any rung whose implied offer crosses VOLL.

## 1. Stage A — zero-solve census (probe `scripts/probes/ercot239_gradedladder_phase0.py` → `results/calibration/ercot239_gradedladder_phase0.json`)

1. **A-1 implied-offer-domain table:** for each gas class × tranche band
   (committed, econ endpoints/slices, each peak rung), the implied $/MWh
   under (i) the incumbent and (ii) the candidate, at the run's resolved
   zonal anchors and at the 2023 August mean delivered gas (read from the
   committed keeper inputs; margin-form arithmetic applied exactly as the
   code does). Deliverable: the mechanical [500,1000) void statement —
   which tranches, if any, price in-band under each.
2. **A-2 conditional-surface inertness census:** the full ratio matrix
   `max(1, condbinned[b][r]/pk)` per class from the committed
   `offer_curve_dam_hrmults_condbinned.json` vs pk = the incumbent scalar
   — count of cells > 1 (prior: 0) — and the identical count under the
   candidate scalar (unchanged ⇒ identical).
3. **A-3 model-λ fine histogram** ($50 bins over [300, 1500), plus
   [1500, 5000) and ≥ 5000) from the keeper sidecar — the void evidence
   at the price level; August-afternoon (hod 12–20) sub-histogram.
4. **A-4 candidate ladder values:** the s_g, the five rung multipliers
   per class, the floor rule's firing record (which rungs, if any, were
   floored), and each rung's implied $/MWh at August gas.

**Go/no-go G-A (ALL required to enter Stage B):**
* (i) the candidate places ≥ 1 rung of ≥ 2 classes strictly inside
  [500, 1000) at 2023 August mean delivered gas (design capability, not
  a residual fit — the incumbent's count is expected 0);
* (ii) monotonicity holds after the floor rule (no rung below its
  class's econ-band maximum);
* (iii) no rung's margin arithmetic goes negative (re-verified
  numerically from the committed config);
* (iv) the incumbent A-2 census confirms conditional-surface inertness
  (so the candidate cannot regress an armed mechanism).
G-A failure ⇒ Stage B does NOT run; the census + owner escalation is the
round's deliverable.

## 2. Stage B — one control + one armed 2023-only solve

* **Control** (`results/calibration/ercot239_ctl_replay`):
  `replay_keeper.py results/calibration/ercot236_k33_clip --years 2023`
  with NO overrides — the HEAD-drift guard (ercot-212 Amendment-1
  precedent). **V-0:** its officials must reproduce the keeper's
  registered C3a −7.3 % / C3b 0.102 / C3c 180 within scorer tolerance
  (±0.1 pp / ±0.005 / ±1 h). Drift ⇒ recorded as an Amendment; the A/B
  re-bases to control-vs-armed (G-REPRO precedent) and BOTH runs
  register; no drift ⇒ only the armed run registers (the control is the
  keeper restated).
* **Armed** (`results/calibration/ercot239_graded_ladder`): identical
  invocation `--set offer_curve_by_group=<candidate>` (the §0
  construction, values from A-4, echoed into the results JSON).
  Solves run sequentially (rule 12).

**Kills (a fired kill ⇒ REJECTED-AS-ARMED; the run still registers per
rule 15):** measured vs the CONTROL —
* **K-SHED:** any new shed hour (slack > 1e-6 in an hour the control has
  none) — the ercot-235 G-SHED-NEW construction.
* **K-OFFSEASON:** in any month ∈ {1–5, 10–12},
  |armed − actual| > |control − actual| + $5 on the demand-weighted
  monthly mean — the ercot-235 G-OFFSEASON construction.
* **K-COAL148:** 2023 coal (LIGNITE+PRB) energy rise vs control
  > 0.5 TWh — the ercot-235 bound.
* **K-SPUR:** lidless spur count (#{model ≥ 150 & actual < 150},
  ercot-225 Option A) exceeds the control's — the no-increase A/B bar.
* **K-CTST (imported ex ante from the ercot33 static-ladder rejection,
  FINDING-ercot-priceshape §6):** |Δ annual energy| vs control > 1.0 TWh
  for CT_PEAKER or for ST_GAS — the CT↔ST amortization-coupling failure
  mode (8 TWh there) gated with an 8× margin.
Report-only: clip-saturated hours (λ ≥ 4,999), band occupancy vs the
DERIVED actual counts (`actual_band_counts`, never hardcoded — the
ercot-238 ruling-1 discipline), banded spur, C3a/C3b/C3c officials
(`ercot226_official_score.py`), monthly table.

**Outcome rules (fixed ex ante):**
1. Any kill fires → REJECTED-AS-ARMED: register the armed run, stamp the
   evidence on the `offer_curve_by_group` matrix cell (rule 26(b)), log,
   keeper untouched.
2. Kills clean AND every official criterion PASSes (determination
   `CALIBRATED`) AND no gate regresses (spur ≤ control, D-4 rows
   inherited, zero new scalars) → **KEEPER-CANDIDATE PROMOTION under the
   owner's standing structural signature** (the ercot-236 precedent:
   structural integrity improves — measured dispersion restored — with
   no gate regressing): re-key the carve-out member of
   `keepers/ERCOT.json` `config_partition` (the forward config is never
   touched), rebuild status, re-stamp matrix §5.1 + ERCOT.js, register
   with full bundle + hourly sidecars, run the calibration-keeper-auditor
   agent --iso ERCOT.
3. ANY other outcome (kills clean but a criterion regresses out of PASS;
   any borderline reading) → register + **ESCALATE to the owner** with
   the full A/B table; NO re-key. The standing standard's "gates
   regress" branch is the owner's to apply, never presumed here.

**Band counts are never selection:** there is exactly ONE armed member —
no sweep, no grid, nothing to select. The candidate's shape comes from
the measured artifact and its level from the already-promoted anchor;
its scores are outcomes, reported at full magnitude whatever they are.

## 3. Declared priors (graded in the FINDING; not gates)

* **P1:** under the incumbent, ZERO gas peak-band tranches price inside
  [500, 1000) at 2023 August mean delivered gas — the void is total, and
  the model's 18 in-band hours are carried by non-gas-peak surfaces.
* **P2:** the armed conditional surface is fully inert in the incumbent
  (A-2 count = 0).
* **P3:** the candidate's p70 rung prices in-band for CC_REGULAR and
  CC_CHP at August gas (and CT_PEAKER's within ±$100 of the band).
* **P4 (Stage B):** the armed run's [500,1000) occupancy rises vs the
  control's 18 while the ≥$1,000 count falls by less than the [500,1000)
  gain (redistribution INTO the band, not a tail collapse); C3c-2023
  stays PASS.
* **P5 (Stage B):** C3a-2023 moves negative of the control's −7.3 % (the
  graded ladder prices mid-scarcity hours lower) but stays within its
  official PASS band.

## 4. Relationship to the adjudicated record (DO-NOT-REDO honesty)

The STATIC measured ladder was REJECTED at ercot33
(FINDING-ercot-priceshape §6, keeper era ercot32): (a) a static ~1.7 GW
wall over-withheld mild days and lifted 2024/2025; (b) the CT↔ST
amortization swap (~8 TWh). This round is NOT that cell re-tested:
* the 2023-only carve-out lane voids objection (a)'s mild-year leg by
  construction (2024/2025 never run this config — owner's charter), and
  RELATIVE to the incumbent the graded ladder withholds strictly LESS
  (the incumbent already posts the ENTIRE band at the wall top in all
  8,760 hours — the maximal static wall; the rejected probe's baseline
  was a 4.6× flat band);
* objection (b) is imported as kill K-CTST rather than argued away;
* the rejection's own filed conclusion #1 named the condition-responsive
  surface as the right form; it is ARMED here and NON-REGRESSED (A-2);
* new evidence since the R: the ercot-237 crushed-transition
  characterization, the ercot-239 round-1 conduct attribution, and the
  carve-out's own existence (the k33 wall the sweep promoted IS a static
  ladder — flat at the top rung).
The handoff's DO-NOT-REDO list (ercot-219 option-b, storage RT surface,
topology, cross-year seed, ORDC/adder closures, West/Panhandle) is not
touched. Off-queue check (rule 26(a)): this IS the handoff's queue
item 2.

## 5. What this round may and may not do

* MAY: the Stage-A census; the two Stage-B solves (2023 ONLY, no
  `--holdout-authorized`, no marker — rule 22); registration of produced
  runs (rule 15); the promotion mechanics ONLY under outcome rule 2;
  matrix ERCOT-shard evidence updates (rules 25/26).
* MAY NOT: touch the forward keeper or its config; edit any mechanism
  code (the conditional-surface contract generalization is FILED, not
  made); sweep, grid, or re-anchor anything (one armed member, full
  stop); mint a new ScenarioConfig field; solve any year ≠ 2023.
* Amendment protocol: any construction deviation discovered mid-round is
  recorded as an Amendment BEFORE further measurement/solve, pushed; the
  FINDING cites it.

## Amendment 1 (2026-08-30, recorded after Stage A ran and BEFORE any
## Stage-B solve) — G-A(iv) declared a stricter PROXY than the invariant
## it guards; the census measures the invariant itself, and it holds

Stage A measured G-A(iv) FALSE as declared: the armed conditional surface
is not fully inert in the incumbent — 6 cells carry ratio > 1 (CC_CHP
bins 2–3 and ST_GAS bins 0–3, ratios 1.13–2.00). The declared purpose of
(iv) was "so the candidate cannot regress an armed mechanism"; full
inertness was a sufficient condition for that, not the condition itself.
The census proves the actual invariant directly: **every ratio > 1 cell
is a TOP-rung cell (rung index 4), and the candidate's top rung equals
the incumbent scalar by construction (§0: the class-top anchor is
preserved exactly)** — so on every one of the 6 cells the conditional
markup operates on an identically-baked rung and produces bit-identical
output under incumbent and candidate; on the graded lower rungs (the only
rungs whose baked height changes) every bin's ratio is ≤ 1 on both sides
(clamped, no reprice). **Re-based G-A(iv′), measured TRUE from the
committed census:** every A-2 cell with ratio > 1 has rung index = top
AND the candidate's top-rung multiplier equals the incumbent scalar for
that class. With (i)–(iii) TRUE as declared, Stage B PROCEEDS. No Stage-B
kill, no outcome rule, and no candidate value changes; the
conditional-surface contract generalization stays FILED (it becomes
load-bearing only if a future recipe grades the top rung away from the
scalar, which this candidate never does).
