# CAISO-100 handoff — charge-economics DERIVE-FIRST executed; ask filed; keeper unchanged

**Session 2026-07-19 (CAISO-100) outcome:** derive-first measurement complete
(`results/calibration/FINDING-caiso100-charge-economics-2026-07-19.md` + the
committed probe `scripts/probes/_caiso100_charge_econ.py`); the DA-spread
day-threshold hypothesis is measured-REFUTED and closed; the cited
cycling-cost hypothesis is SUPPORTED (revealed margin conduct cost $11-17
brackets the derived $14.25/MWh); **owner ask filed**
(`docs/handoffs/caiso-100-charge-econ-ask-2026-07-19.md`), pre-registered
bands/gates in FINDING §6 are BINDING on the build session. Nothing solved
with the mechanism; CAISO keeper stays `2026-07-19-caiso-99-storage-shape`.
WP-3 CT_CHP ask still PENDING. Calibration-log entry: 2026-07-19 caiso-100.

## What CAISO-100 established (do not re-derive)

- The measured fleet is NOT day-gated on spread (2024/25 skip-share ~2 %);
  its sub-envelope intensity is continuous modulation. Any day-threshold
  mechanism is closed.
- The keeper's residual belly is a PRICE defect (charge-weighted λ
  $5.8-12.2 above the measured glut floor; belly volume only +6/+5 % in
  2024/25 battery-only) — the zero-cost LP's charge bid rides up the supply
  curve; a per-MWh cycling cost lowers the bid so charging clears at the
  floor where reality buys the same volume.
- The model's annual under-charge (−4/−8 % 2024/25) sits OUTSIDE the belly
  (shoulder/overnight inelastic conduct) — a cost cannot create it; recorded
  non-target, re-charter subject if the ask is refused.
- Battery-only vs incl-PS basis: prior FINDING storage charge totals carried
  1.14/1.70/1.60 TWh of Helms PS; `_caiso100_charge_econ.py`'s battery-only
  basis is the clean one.

## Paste-ready next-session prompt

```
<<<CAISO-101 — CHARGE-ECONOMICS EXECUTION (if ruled) / RESIDUAL RE-CHARTER (if refused)>>>
MODEL ASSIGNMENT: Opus or Fable (core-infra scope possible; CLAUDE.md rule 26).

STATE (2026-07-19, post-CAISO-100): CAISO keeper = 2026-07-19-caiso-99-storage-shape
(UNCHANGED), NOT-YET, fail {C3a-2025 +10.8%, C3c, C4, C5a(2024 CAVEAT)}; C1 12/12,
C2/C3b/C6/C7/C8 PASS. CAISO-100 ran the derive-first charge-economics measurement
(results/calibration/FINDING-caiso100-charge-economics-2026-07-19.md): the
DA-spread day-threshold hypothesis is MEASURED-REFUTED (2024/25 skip-share ~2%,
u in a broad 0.4-0.9 band, weak spread corr) and CLOSED; the cited cycling-cost
hypothesis is SUPPORTED — the fleet's revealed margin conduct cost ($11-17/MWh)
brackets the DERIVED li-ion cycling cost $14.25/MWh discharged (285$/kWh NREL
ATB 2024 x1000 / 5000 LFP cycles x 0.25, constants.py:4128), while the keeper's
own margin prices only its efficiency-loss floor (c* ~$7) and its charge-wtd
lambda sits $5.8-12.2 above the measured glut floor. OWNER ASK FILED
(docs/handoffs/caiso-100-charge-econ-ask-2026-07-19.md): battery_dispatch_adder
0.0 -> derived 14.25 for the CAISO backcast recipe (re-opens caiso-76 no-change
on moved evidence).

DO (priority):
1. Read the owner ruling on the CAISO-100 ask. If GRANTED -> execute the B-leg
   EXACTLY per FINDING-caiso100 §6 (pre-registered, BINDING): fresh same-machine
   caiso100_repro_A (= _caiso99_shape_B.py recipe verbatim, out-dir renamed) vs
   caiso100_cycling_B = A + overrides["battery_dispatch_adder"]=14.25 (the ONLY
   delta), 2023-2025 one bundle each (rule 16), SEQUENTIAL; score
   _caiso92_report.py <A> <B> + _caiso_storage_timing.py <B> +
   _caiso100_charge_econ.py <A> <B>. HARD GATES (FINDING §6): belly falls all
   years, no overshoot; evening toward 0, no cross, 2025 evening dis within
   0.3 TWh of measured; two-sided +-15% battery-only NG:OTH throughput guard
   (chg floors 3.46/7.40/11.07, dis floors 3.42/6.43/9.57 TWh) + belly chg >=
   measured belly (2.16/5.57/8.70); C1 12/12; overnight no new under-price;
   C3c unchanged/toward tail; C7/C8 PASS; C5a improves/holds (2024 CAVEAT no
   regress). Register WHATEVER the result (rule 15) — registration MUST prune
   CAISO retention to top-15 — promote only on no-status-regression.
   If REFUSED -> knob stays 0.0; re-charter the residual belly to the remaining
   conduct channels (shoulder/overnight inelastic charging = the -4/-8% annual
   under-charge OUTSIDE the belly, DA-award allocation, AS-deployment variance;
   derive-first, no LP until measured).
2. WP-3 CT_CHP steam-floor rule-23 derive if ruled (ask STILL PENDING from
   CAISO-98, docs/handoffs/caiso-wp3-ctchp-steam-floor-ask-2026-07-18.md).

GUARDRAILS: all 3 years one bundle (rule 16); NO twin (rule 21); SEQUENTIAL
solves (~30 min/leg, 15 GB box OOMs on 2 concurrent); solves IN-SESSION only
(billed CI). Step 0 fresh container: .venv/bin/python scripts/regenerate_clean.py
(~10 min), confirm data/clean/confirmed-retirements/CAISO/ exists.

DO NOT REDO (CAISO-100 + prior): re-deriving the charge-day spread analysis
(committed: _caiso100_charge_econ.py + FINDING-caiso100 — re-RUN for scoring,
don't re-derive); any adder value other than the derived 14.25 (rule 25 — no
sweep, no residual fit; ERCOT's tuned $10 never crosses the ISO boundary);
re-opening the day-threshold hypothesis (measured-refuted, CLOSED); tightening
the shape envelope below p95 or sweeping its quantile (frozen rule-23
derivation); re-arming caiso_storage_as_reservation (caiso-74 inert, holdback
EMBEDDED in envelope); storage_vintage_ramp wiring (ALREADY LIVE); the
caiso-94/96/97/99 mechanisms or derive gates (frozen); widening caiso-87;
season/calendar import gates; more CC commitment forcing; CT_PEAKER floor;
cutting CC offer costs; new STACKED storage floor (rule 19); any year outside
2023-2025 (rule 22 — no CAISO calibration-complete marker).

GIT: main advances fast -> git fetch origin main + rebase BEFORE push (expect
the calibration-log append-append conflict; keep BOTH entries; keepers.json may
carry a parallel ISO's keeper swap — merge, don't overwrite). ls-remote the
designated branch before push, recreate from rebased local if gone. git push
WORKS on this machine class (caiso-98/99/100) — API create_branch first if the
branch is missing; blob-verify every pushed source >=300 lines by SHA (rule 27).
<<<END>>>
```
