# PRECOMMIT — ercot-223: the EVENT-REALIZED RELEASE guard on the armed adaptive-expectation storage floor — repair design, A/B, and kill gates, pinned BEFORE any solve

> Status: PRECOMMIT, pushed and blob-verified before any LP is launched
> (dispatch requirement). Session ercot-223, branch
> `claude/ercot-223-keeper-shed-8iztwv`. Keeper at dispatch:
> **`2026-08-19-ercot221-arm-adaptive`** (PROMOTED by the owner over the
> recorded REJECTED-AS-ARMED G-SHED verdict — both records stand; NOT-YET,
> fail set {C3a-2023 −39.4 %, C3b-2023 0.723}, C3c ledgered CAVEAT ×3).
> This lane repairs the keeper's one failing kill gate — the manufactured
> 2024 h3066 shed — now a keeper defect.

## 0. What Phase-0 established (the diagnosis this repair is grounded on)

Full record: `scripts/probes/ercot223_shed_phase0.py` →
`results/calibration/ercot223_shed_phase0.json` (committed before this
precommit; read-only, committed artifacts only, no LP). Summary of the
measured causal chain, every identity closing to numerical precision:

1. The new shed is a **system-level 17.887 MW shortage at h3066** (zonal
   prices uniform at VOLL; the South booking is solver placement among
   equally-priced zones). The control's h3067 Northeast 600.16 MW shed is
   byte-identical in both runs.
2. The reserve co-optimization counts storage upward headroom
   (cap − Dis + Chg) as reserve supply in the shared headroom rows
   (`model/lp/reserve_rows.py`, pooled spec — the keeper's
   `ercot_storage_as_duration_gate` is off). The adaptive floor enters the
   LP as a discharge **cost**, so it debases the model's private value of
   stored energy (the SOC shadow μ) one-for-one — while the reserve-side
   headroom value σ carries no floor. Measured at h3066:
   μ = η·(λ − cost − σ) collapses **$575.6 → $184.4/MWh** (control → arm).
3. The μ-collapse (i) fails the control's h3065 pre-peak top-up charge
   (margin σ + μη − λ: **+78.5 → −224.5 $/MWh**), (ii) swaps 195.1 MW of
   storage energy into reserve-counted headroom at h3066
   (ΔNonSpin held = **+17.887 MW = the shed, exactly**; the storage/thermal
   headroom identity closes to 0.0001 MW), and (iii) leaves the thermal
   backfill one CT short — CT_PEAKER gives all +177.3 MW it has and the
   residual 17.887 MW is served by slack at VOLL.
4. The "arrives empty" SOC story is **false**: both runs exit h3067 with
   fleet SOC pinned at the measured AS-backing freeze (3,091.5 MWh); the
   post-window discharges are exactly the η-scaled freeze releases
   (control 938.27/127.41 at h3068/h3069; arm 1,065.69 bundled at h3069
   because at h3068 the floored energy margin $271.6 < σ $419.2 where the
   control's unfloored margin $663.4 > σ — the co-opt merit-order flip).
5. The measured AS overlays (award power dock, SOC-backing freeze,
   deployment floor) are **identical in both runs** — stage-setting, not
   the discriminator.

The defect, stated structurally: **the conduct floor is an OFFER — a claim
about the storage operator's energy offer price — but offer-as-cost also
debases the operator's PRIVATE valuation of stored energy in the
energy-vs-reserve arbitration and the intertemporal SOC value.** At hours
where the spike the conduct anticipates is REALIZED, the real fleet's
offers CLEAR and it discharges (May-8-2024 HE18: real RT $2,451, the real
fleet discharged, no shed was recorded); the LP's cost-form floor instead
withholds physically-available energy and manufactures shed.

## 1. The repair: EVENT-REALIZED RELEASE (a structural yield, rule 17)

**Definition.** In the pass-2 floor construction
(`scripts/run_calibration.py`, the ERCOT adaptive block), hours whose
**pass-1 settle basis** — the identical `_settle_t` series the mechanism's
own day-max event detector already computes (λ + the model's own
decontaminated anchored scarcity-adder mirror, Amendment 4, zero measured
content) — is **≥ `ERCOT_ADAPTIVE_EVENT_USD` ($1,000, the existing frozen
constant)** have their floor masked to 0 (the discharge cost falls back to
`storage.vom`, the seam default). Everything else is unchanged.

- **Driver:** (a) the measured event-hour conduct — the fleet discharges
  into realized event peaks (the ercot-167 measured 2023 >$1,000-hour
  fleet dispatch; the May-8-2024 storm evening itself); (b) offer-clearing
  semantics — a cleared offer does not withhold physical energy, and
  Phase-0 measured precisely the channel by which offer-as-cost does.
  The conduct story is "withhold in anticipation OF the spike"; at hours
  the model's own pass-1 path marks the spike as realized, the anticipation
  is resolved and the holdout clears.
- **Window:** pass-1 settle ≥ $1,000 within the h17–20 floored window.
  Pre-measured breadth from the committed bundles (Phase-0 §6):
  **2023: 8 of 776** floored window-hours exempt (the calibration
  signature survives ≥ 99 % intact); **2024: 5 of 568**, including exactly
  the {3065, 3066, 3067} kill window; **2025: none** (no floors — the
  self-extinction is untouched).
- **Forward story:** regenerates from the model's own pass-1 path exactly
  as the floor itself does; no measured content enters the armed path.
- **Zero new fitted scalars.** The threshold is the mechanism's own
  registered event constant, reused at hour granularity: the hours that
  MAKE a day an event day are the release hours. One new boolean
  `ScenarioConfig` field, `ercot_adaptive_event_release` (default
  **False** → HEAD replays the keeper byte-identically), ERCOT-gated
  inside the existing `iso == "ERCOT"` adaptive block.
- **What this is NOT:** not a shed-hour patch (the mask is conditioned on
  the pass-1 price basis, never on pass-2 outcomes; it applies uniformly
  across all days and years and would have applied identically had no shed
  existed); not a tuned haircut (no new numeric value anywhere); not the
  ercot-219 reservation-offer family re-litigated (the floor's cost-form
  and constants are untouched at all non-event hours); not the iterated
  fixed point (still exactly one adaptation pass; pass-2 is still THE
  scored pass).

**Ex-ante expectation, recorded for honesty:** the repair reverts the
May-8 h3065–h3067 storage economics to the control's (top-up restored,
μ restored), so the 2024 shed set returns to {3067}; h3068 keeps its floor
(pass-1 settle $675 < $1,000) so the 938 MWh h3068→h3069 re-timing may
persist — priced, not shed. The 2023 official movement should be ≈
unchanged (768/776 floored hours untouched; the 8 exempt hours were
already at/above $1,000 where the ≤$1,850 floor was largely inframarginal).
2025 must be byte-inert. If the A/B instead shows the 2023 movement
gutted, that is a FAIL of the mechanism's purpose and is recorded.

## 2. A/B design

- **Control** = the CURRENT keeper recipe (`2026-08-19-ercot221-arm-adaptive`,
  bundle `results/calibration/ercot221_adaptive_B`) replayed at HEAD via
  `scripts/replay_keeper.py` (the sanctioned recipe channel) into
  `results/calibration/ercot223_control_replay`. Its 2024 baseline carries
  {3066, 3067} by construction.
- **Arm** = the identical replay plus the single delta
  `--set ercot_adaptive_event_release=true`, into
  `results/calibration/ercot223_release_arm`.
- Years 2023 2024 2025, **sequential** per-year process chain within each
  member (rule 12; 15 GB box — members run sequentially, control first).
- **G-REPRO is verified BEFORE the arm is read**: the control replay's
  hourly sidecars must be sha256-identical to the committed
  `ercot221_adaptive_B` sidecars (the strongest form, proving the code
  edit is inert with the flag off).

## 3. Kill gates — the ercot-221 §4 table UNCHANGED, plus the tightened G-SHED

Scored by the committed `scripts/probes/ercot221_gates.py` construction
(control → arm), direction-blind, mechanical: **any gate FAIL ⇒ the repair
is REJECTED, recorded unrewritten at full magnitude, and the keeper defect
stays a ledgered caveat.**

| gate | rule |
|---|---|
| G-CAP | 0 protocol-cap violations (λ + adders ≤ VOLL) in all 26,280 h |
| G-SPUR | spurious mid-band hours vs the ercot-215 9/11/1 baseline, bar ≤ +5/yr |
| **G-SHED (tightened)** | **zero NEW shed hours vs the ORIGINAL control's 0/1/0** ({}, {3067}, {}) — the repaired arm's shed sets must be ⊆ the pre-adaptive baseline; the A/B control itself carries {3066, 3067} in 2024, which the repair must clear |
| G-OWNER | C3a-2024 PASS, C3a-2025 PASS, C3b-2024 ≤ 0.20 all retained (official scorecard) |
| G-BAT | storage net discharge at actual-tail hours within ±25 % of EIA-930 BAT (2024/2025) |
| G-DOF | ledger delta = the ONE boolean guard field, no new numeric constants (`ERCOT_ADAPTIVE_EVENT_USD` reused); `n_residual` not increased |
| G-D2 | mechanism attribution row present with its declared window; no new D-4 off-window rows |
| G-REPRO | control replays the keeper's committed sidecars sha256-identical before the arm is read |
| LOYO / G-SAFE | zero new fitted scalars ⇒ LOYO structurally N/A (the ercot-221 posture); G-SAFE the declared cross-year falsifier: 2025 must remain byte-inert (the guard can only REMOVE floors, and 2025 has none) |

2023 price numbers (C3a/C3b/C3c) remain **side-effect reporting at full
magnitude under Q-B FINAL / R-A — never a gate.**

**Verdict rule:** all gates PASS ⇒ the repair is a **keeper-candidate**,
reported with a promotion recommendation and the D-5(b) duties (ERCOT
holds no `complete` marker, so no `calibration-complete.json` re-key); any
FAIL ⇒ recorded, keeper unchanged, the defect stays a ledgered caveat, and
ERCOT bandwidth returns to the Door-D hold and the R-A re-pointed queue.

## 4. Fences

Rule 22 ({2023, 2024, 2025} only, data-not-score); rule 25 (ERCOT-only —
the guard lives inside the existing `iso == "ERCOT"` adaptive block; the
CAISO leg is NOT touched); rule 27 (local edits, small commits, `git push`,
blob-verify ≥300-line pushed files); rule 28(b/c) (outcome lands as
evidence on the existing `ercot_storage_adaptive_expectation` cell; the new
field is added to that row's `def:` string in `mechanism-matrix.js` in the
build commit — same family, no new mechanism row); rules 5/23/24 (the
boolean is a registered `ScenarioConfig` field, recorded in `run_config`,
no off-registry channel); rule 15/16 (both A/B members registered with
payloads, all three years per member, same session); rule 12 (years
sequential within each invocation); no new workflows, no cron, no PR
(push-and-stop on the designated branch). DO-NOT-REDO honoured: the armed
family's basis/constants untouched; the iterated fixed point NOT entered
(one adaptation pass, pass-1 basis unchanged); Door A ×3, item 11, mid-band,
regime, ercot-219 aggregate, B-2, M-2 all stay closed; the ercot-222 seed
form stays refuted.
