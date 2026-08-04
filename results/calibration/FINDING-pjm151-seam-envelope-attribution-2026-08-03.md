# FINDING — pjm-151: the PJM seam envelopes were built on the wrong grain; repaired, PROMOTED, and the two-zone split was never the question

> Session pjm-151, 2026-08-03. Branch `claude/pjm-151-backcast-calibration-cznn3e`.
> **KEEPER → `2026-08-03-pjm-151-seam-envelope`** (was `2026-08-03-pjm-147b-chp-heat`).
> CALIBRATED, 9 scored / 9 target / 0 ledgered / 0 fails, C1 `all 16/16 · free 12/12`.
> Rule 22: 2023–2025 only; PJM's `complete` marker re-keyed with a determination
> re-verification; `final` untouched; holdout freeze untouched.
> Three phases: **Phase 0** (matrix census, no LP), **Phase 1** (D-2 record, no LP),
> **Phase 2** (the lever, one solved arm).

## §1 — headline

| | keeper (pjm-147b) | arm B (pjm-151) |
|---|---|---|
| determination | CALIBRATED 9/9 | **CALIBRATED 9/9** |
| C1 | all 16/16 · free 12/12 | **all 16/16 · free 12/12** |
| criteria moved | — | **none** |
| gas family err (TWh) | +4.98 / +10.92 / +23.05 | **+3.91 / +9.34 / +21.02** |
| coal family err | −8.01 / −7.79 / −2.61 | −8.37 / −8.22 / −3.14 |
| interchange err | −10.82 / −9.86 / **+8.20** | **−12.48 / −12.22 / +5.21** |
| DOF ledger | 19 entries / 6 residual | **19 / 6, verbatim** |

Every one of the eight model-determined criteria is identical to the incumbent's.
The promotion rests on **rule 1 `[R-STRUCT]` and rule 14 `[R-ACCURATE]`**: the
attribution is now internally consistent and the mechanism is built on the grain
it actually needs. The interchange trade is disclosed in §5, was **pre-registered
before the arm solved**, and is filed as a new open root cause rather than absorbed.

## §2 — Phase 0: PJM's rule-28(c) matrix column is CLOSED (no LP)

15 absent + 1 prose-only + 5 armed-with-no-cell → **0 / 0 / 0**; ratchet PJM
**15 → 0**. All 16 closed as **literal sub-scalar registrations on 6 existing
family rows** — zero new rows, zero mechanism verdicts, one audit-status cell mint
(`matrix_gap_census` PJM `O → K`, the ercot-156 / caiso-161 precedent). Five of the
sixteen shape the *published keeper* and had no cell anywhere:
`pjm_offer_midcurve_segments`, `pjm_seam_flow_limit`, `pjm_seam_export_limit`,
`pjm_seam_measured_ladder`, `pjm_reserve_online_rho`.

**Mechanical cause — the caiso-161 §2 defect again.** The seam family sat behind
the glob `pjm_seam_* :7371+`: natural to a human, invisible to a checker that
matches literals. The anchor was *also* stale (the fields live at `:9019+`).
**Registrations must be full literals.**

Two census findings:

* **`pjm_reserve_online_rho = 1.0` is recorded in every PJM `run_config.json` and
  is unobservable on the keeper** — sole read `reserves/spec.py:2291`, inside
  `if pjm_reserve_online_gated:` at `:2290`, which the keeper sets `False`. **Not**
  a rule-26 deletion candidate (a built, reachable, default-off mechanism at its
  own documented default), so nothing is filed for the owner.
* **Filed as an observation for a lane that may adjudicate, not adjudicated here**
  (rule 28(d)): the keeper arms `pjm_reserve_supply_cap=True` alongside
  `pjm_reserve_pergen=True`, and **both** of that flag's read paths are gated off
  by pergen — `reserves/spec.py` returns the pergen `ReserveDesign` at `:2280`
  *before* the `supply_cap` computation at `:2286` (its own docstring at `:2018`
  says "the zone-aggregate scoping flags are ignored in this mode"), and
  `pipeline/commitment.py::build_pjm_reserve_p1_prep` returns `(None, None)` at
  `:1374`.

**MISO's ratchet moved 11 → 8 in the same commit and this is NOT a MISO census.**
The PJM seam literals would have substring-shadowed three `miso_seam_*` fields into
"covered" (`pjm_seam_flow_limit` contains the matched stem `seam_flow_limit`),
silently dropping them from MISO's list with nobody having registered them. Those
three are written out as real literals on the same row so the coverage is true; no
MISO cell or verdict is touched, and MISO's remaining 8 are referenced **by line
number only** so that naming them cannot count as registering them. MISO is now the
last open column.

## §3 — Phase 2: the defect, and why the chartered question was the wrong one

Two modules attribute the same physical seam by different rules:

| | `_PJM_TIE_ZONE` (envelopes.py) | `INTERFACE_NEIGHBORS` `border_zones` |
|---|---|---|
| TVA | `PJM_Dominion` (whole tie) | `("PJM_AEP_Ohio","PJM_Dominion")` |
| LGEE | `PJM_AEP_Ohio` (whole tie) | `("PJM_West_APS","PJM_AEP_Ohio")` |
| Carolinas | `PJM_Dominion` | `("PJM_Dominion",)` |
| NYISO | `PJM_EMAAC` | `("PJM_EMAAC",)` |

**Handoff premise corrected: LGEE is inconsistent too**, not the self-consistent
contrast case.

They are not independent. `inject_pjm_seam_flow_limit` builds a per-**zone**
(month × hod) p90 envelope from `_PJM_TIE_ZONE`, then **sums it over each
neighbour's `border_zones`**. A zone bucket holds *every* tie that lands in it and
several neighbours name the same zone, so each seam's cap absorbs other seams' ties.

**The charter said: derive the TVA two-zone share from a measured basis, or STOP.
The share never needed deriving.** The object the cap needs is **per-neighbour**;
the per-zone envelope is an intermediary whose own source calls it *"Tier 3
(calibration) — approximate pending PJM's authoritative tie-to-zone assignment"*.
Building each seam's envelope from **its own ties** requires only
`spec.PJM_TIE_NEIGHBOR` — an **identity read off PJM's own tie labels**, not a
share. Zero free parameters (rule 5); same measured file at the same shipped p90,
so rule 13 is unchanged and the forward story is untouched.

`_PJM_TIE_ZONE` is **not changed and not wrong**: a per-zone attribution is right
for the genuinely per-zone objects (the measured zonal net-position schedule feeding
`load_demand`, and the star topology's per-border link caps). After the repair the
two structures answer different questions and no longer collide.

## §4 — what was measured ex ante, with no LP

`scripts/probes/pjm151_seam_envelope_attribution.py` → `_pjm151_seam_envelope_attribution.json`.
p90, ties netted within the hour before the directional clip (what
`pjm_zonal_interchange` does). Legacy ÷ direct, and the share of (month × hod)
cells where the legacy cap sits below TTC and can bind at all:

| seam | dir | legacy/direct 23 / 24 / 25 | legacy binds |
|---|---|---|---|
| TVA | export | **124× / 53× / 40×** | 0.000 / 0.000 / 0.097 |
| LGEE | export | **33× / 42× / 26×** | 0.000 / 0.000 / 0.014 |
| TVA | import | 2.05× / 2.20× / 2.38× | 0.167 / 0.125 / 0.240 |
| Carolinas | import | 1.79× / 1.73× / 1.67× | 0.681 / 0.531 / 0.635 |
| MISO | import | 1,538 / 2,139 / 2,323 MW vs **0.1 / 11 / 24 MW** | 1.000 |
| LGEE | import | **0 MW vs 518 / 539 / 549 MW** | 1.000 / 1.000 / 0.986 |
| Carolinas | export | 0.67× / 0.97× / 0.81× | 1.000 |
| **NYISO** | export | **1.00× (exact)** | the control |

Three results before a solve was spent:

1. **`pjm_seam_export_limit` — armed on the incumbent *precisely* to fix the
   structural over-export — was effectively INERT on two of the five seams.**
2. **The repair loosens as well as tightens** (legacy LGEE import cap 0 MW vs a
   measured ~520–550 MW; legacy Carolinas export *tighter* than measured). A
   residual-fitted change would not do that.
3. **NYISO reproduces exactly** — its border zone holds only its own four ties.

**A construction error is recorded rather than buried:** the probe's first version
clipped each tie *before* summing and reported a MISO import cap of 2,225 MW against
a netted 0.1 MW. Netting-then-clipping is the convention both envelope builders use;
a regression test now pins it (`test_ties_are_netted_before_the_directional_clip`).

## §5 — the arm, the gates, and the trade

Single delta `pjm_seam_envelope_by_neighbor=true` on the keeper recipe, 2023–2025
in ONE bundle via the rule-12 separate-directory chain (2023 → +2024 → +2025, each
prior year byte-copied forward in ≤0.5 s, cold `results/PJM`, no dirty-tree warning).

* **K1 PASS** — one declared delta; every other diff is enumerated schema drift
  (5 fields added to / 3 deleted from `ScenarioConfig` since the keeper solved) or a
  known default move. Zero unexplained. *The declared delta arrives as `arm_only`,
  not a `False→True` value-diff, because the keeper predates the field — the
  absence-aware case `config_drift` exists for, and the first version of the gate
  scorer mis-FAILed on it.*
* **K2 discharged without a solve** — pjm-150 measured bit-identity at HEAD, and
  all six `src/market_sim` commits since are provably PJM-inert (docstring-only;
  NYISO-family-gated branches that reduce to the pre-existing condition when off;
  a CAISO kwarg defaulting to `None`). Arm A **is** the committed keeper.
* **K3 LIVE** — max |ΔMW| on the P1 class-hour **1,481.3 / 1,699.2 / 1,647.6** over
  166,440 class-hours/yr. Zonal mean LMP falls 0.07–0.17 $/MWh in every zone;
  `PJM_external` falls 0.26–0.69.
* **K4 PASS** — **no criterion regresses.** All eight model-determined criteria
  identical; C6 flipped `PASS → UNATTESTED` only while the probe carried no
  attestation, and returns to PASS once the rule-21 attestation is authored.
* **E1 PASS, zero breaches** — largest class move **1.24 TWh** against a declared
  3.0 TWh cap; every gated class well inside its 8.0 TWh band. 2025's ungated
  classes all move *toward* actual (CC_REGULAR +5.19→+3.96, COAL_BIT +5.84→+5.36,
  CT_PEAKER +4.12→+3.56).

**THE TRADE, pre-registered in PREREG §6 before the arm solved.** Net export falls
in all three years, so the interchange family error goes **−10.82 / −9.86 / +8.20 →
−12.48 / −12.22 / +5.21 TWh**: better in 2025 (the over-export year), worse in
2023–24 (the under-export years). Gas improves in all three years; coal degrades
slightly. This was declared as the expected direction *in advance*, so it is a
confirmed expectation, not a discovered surprise — and per rules 1 and 14 the
consistent attribution ships regardless of the residual.

## §6 — the new root cause the repair discovered (keeper note item 15)

PJM's modelled net export is **short of actual by 12.48 / 12.22 TWh in 2023–24**
and **long by 5.21 TWh in 2025**. The repair moved all three the same direction, so
**the deficit is not a seam-deliverability defect** and must not be chased by
loosening caps, tuning `PJM_TIE_NEIGHBOR` or the percentile, or restoring the
zone-summed path (rules 5 / 14 / 20 / 24 all bar it). What the repair establishes is
that the remainder is a **level/direction question in the reference-price seam's own
economics**, not an envelope question: the measured record is direction-structural
(export to MISO/NYISO in ~97–100 % of *all* hours, import from Carolinas/TVA/LGEE in
77–97 %) and `pjm_seam_measured_ladder` already prices that structure, so the open
question is why the LP still clears less export than the ladder's own duration curve
supports. **Needs its own charter and pre-registration. It is not a price-formation
lever and does not re-open the owner-declared frontier.**

## §7 — rule 26 `[R-DELETE]` follow-up, owed

The mechanism is gated **only** to keep this A/B single-delta on an ISO with zero
caveat budget. With it promoted, **collapsing `pjm_seam_envelope_by_neighbor` and
deleting the zone-summed path is owed** — a repaired mechanism must not leave a
re-armable broken version parsing. Stated in the PREREG, the attestation, the keeper
note and here so it cannot be lost.

## §8 — Phase 1 (the pjm-149 D-2 projection): NOT COMPLETED, and why

The charter asked whether `f46bdfd` is the *sole* contributor to the
committed-keeper → HEAD `legitimacy_diagnostics.json` delta pjm-150 measured
(D-2 32 → 42 rows, 32 shared rows re-based). Resolving it needs the artifact
regenerated from the *same bundle* at the pre-fix commit and at HEAD, and each
regeneration calls `run_year` to rebuild per-plant floors — memory-comparable to the
LP itself on a 15 GB box, so it could not be run concurrently with the arm chain
without risking an OOM of the deliverable. The pre-fix code view is materialised and
the harness is ready; **the measurement is not made and no claim is offered either
way.** No verdict depends on it (C7/C8 pass under both records, and the movers are
C7/C8-exempt CHP classes) — but rule 18 `[R-FORCED-BUDGET]` is scored entirely from
this file at every ISO, so **the record correction is still owed and is carried
forward as an explicit open item**, not quietly dropped.

## §9 — governance

* **Rule 15** — registered `2026-08-03-pjm-151-seam-envelope`; top-15 PJM retention
  re-applied (pruned `2026-07-28-pjm-136-control`). Keeper bundle commits its
  `hourly/` sidecars.
* **Rule 16** — 2023 + 2024 + 2025 in ONE bundle.
* **Rule 21 `[R-DOF]`** — DOF ledger carried **verbatim** (19 entries / 6 residual);
  `scripts/gen_pjm151_attestation.py` **asserts** it rather than claiming it.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only. PJM's `complete` entry re-keyed to the
  new keeper **with a determination re-verification** on committed artifacts (D-5(b));
  the re-verified determination is not worse (identical criterion for criterion), so
  the promotion proceeds rather than escalating. `final` absent, freeze untouched.
  `scripts/audit_keepers.py --iso PJM --check` PASSES (0 failures, 0 warnings).
* **Rule 28 `[R-MECH-MATRIX]`** — the new field's row registered on
  `seam_flow_envelopes` in the same PR (duty c); the cell's verdict + evidence
  updated this session (duty b); keeper stamp and PJM gates re-stamped. Off-queue
  entry declared explicitly under 28(a) as a NEW measured identification against an
  owner-declared frontier.
