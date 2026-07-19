# CAISO-102 handoff — channels measured, +1h frame defect found/fixed, keeper = caiso-102 (hourfix, PROMOTED)

**Session 2026-07-19 (CAISO-102) outcome:** (1) the three inelastic-conduct
charge channels MEASURED from the committed Daily Energy Storage Report
(FINDING-caiso102 §1-§3) — the DAM allocates 76-84 % of realized battery
charge (belly 82-91 %), the FMM covers 94-97 %, RT additions are
reg-down-deployment-shaped (2025: slope −1.34 MW/MW-RD), and the non-belly
charge clears $6-9 ABOVE the belly floor (obligation conduct: a real
overnight→morning second cycle + AS-book SOC restoration). No conduct
mechanism built (charter discipline). (2) The evening merit diagnosis
(§4) found the caiso-95 "+2 TWh evening over-import" was a probe clock
artifact (EIA-930 hour-ending vs model interval-beginning) and, chasing
2025's phantom evening solar, exposed the **+1h frame defect**:
`_eia_hourly_frame_filled` anchored gap-bridged BA-years one hour late
(CISO-2025, PJM-2023, MISO-2025 — issue #2562). Fixed at the loader root;
2025 HSL + supply-consistent demand re-derived; single-delta
`caiso102_hourfix_B` cleared every pre-registered gate (2023/24
byte-identical, 2025 solar lag-0, C1 12/12, C7/C8 PASS) → **PROMOTED**
(`2026-07-19-caiso-102-hourfix`, owner in-session ruling). Determination
NOT-YET, fail {C3c, C4, C5a(2024 CAVEAT)}. Ladder now: belly
+6.0/+6.6/+4.3, evening −5.8/−4.9/−1.1, overnight +0.8/−0.0/+1.4.

## What CAISO-102 established (do not re-derive)

- **The charge volume is fixed upstream of the RT margin** (DAM allocation +
  FMM + reg-deployment). Any belly mechanism must HOLD volume and re-price
  the margin/allocation — a marginal bid adder cannot (caiso-100/101 stands,
  now mechanically explained). The surviving inelastic wedge after the
  hourfix: overnight second cycle (model 0.05 vs measured 0.36 TWh) + belly
  over-charge geometry (model 9.37 vs 8.26 TWh 2025 at λ above the glut
  floor).
- **The evening residual is the CT-rung merit composition, all three
  years** (Q1-deepest hours: measured CT 1.33/1.19/0.51 GW vs model
  0.58/0.31/0.12; model gas ~2-3 GW under; imports at/above measured; model
  CC over-serves). NOT an import-volume excess (aligned measurement), NOT a
  CT floor (caiso-91b stands).
- **The EIA-930 `Local time`/`Hour` labels are HOUR-ENDING** (uniform, all
  BA extracts). The `_caiso_who_serves_night/day.py` probes bucket by the
  hour-ending stamp — one hour early vs model windows; annotate or fix
  before next use. `_caiso102_evening_merit.py` is the aligned instrument.
- The frame fix is in `eia_loader._eia_hourly_frame_filled` (commit cites
  FINDING-caiso102 §5). PJM-2023 / MISO-2025 corrections are their lanes'
  work (issue #2562).

## Paste-ready next-session prompt

```
<<<CAISO-103 — BELLY ALLOCATION MECHANISM DESIGN / EVENING CT-RUNG COMPOSITION>>>
MODEL ASSIGNMENT: Opus or Fable (core-infra scope; CLAUDE.md rule 26).

STATE (2026-07-19, post-CAISO-102): CAISO keeper = 2026-07-19-caiso-102-hourfix
(the +1h frame-defect fix leg, PROMOTED; zero DOF delta), NOT-YET, fail
{C3c, C4, C5a(2024 CAVEAT)}; C1 12/12, C2/C3a/C3b/C6/C7/C8 PASS. Ladder:
belly +6.0/+6.6/+4.3, evening -5.8/-4.9/-1.1, overnight +0.8/-0.0/+1.4.
The inelastic-charge channels are MEASURED (FINDING-caiso102 s1-s3): DAM
allocates 76-84% of realized charge (belly 82-91%), FMM covers 94-97%, RT
adds are reg-down-shaped, non-belly clears $6-9 above the belly floor
(overnight second cycle + AS SOC restoration). Evening = CT-rung merit
composition, all years (s4/s9). Issues: #2562 (cross-ISO +1h corrections;
caiso-92 offer-surface 2025-slice re-derive) and #2546 ($5 literal) OPEN.

DO (priority):
1. BELLY ALLOCATION MECHANISM DESIGN (owner-gated, ask BEFORE any solve):
   from the measured channels, design the volume-holding mechanism that
   re-prices the charge margin — candidate shapes: a DA-allocation-profile
   charge schedule (measured hod allocation share x fleet, the caiso-99
   envelope's conduct sibling), an inelastic charge-demand block, or an
   AS-obligation SOC term. State driver/window/forward-story (rule 12),
   D-2/C8 implications, and the caiso-76/caiso-100 interaction. Measure any
   missing statistic FIRST (caiso-93/94 protocol); file the ask.
2. EVENING CT-RUNG COMPOSITION (the -5.8/-4.9): why the model's tight-hour
   clearing never reaches the CT rung reality prices (Q1: measured CT
   1.3/1.2 GW vs model 0.6/0.3) — decompose the Q1 hours' marginal
   economics on a same-machine repro (_caiso102_repro_A recipe now solves
   the keeper bytes): what serves the margin instead (import rung depth at
   hub prices? committed-CC headroom? battery timing?), on the ALIGNED
   clock (_caiso102_evening_merit.py). NO CT floor (caiso-91b), no import
   throttling (rule 1). Owner ask for any mechanism.
3. caiso-92 offer-surface 2025-slice re-derive (rule 23, cites issue #2562;
   pooled artifact — own gates, LOYO on any verdict flip).
4. Issue #2546 ruling if carried.

GUARDRAILS: all 3 years one bundle (rule 16); NO twin (rule 21); SEQUENTIAL
solves (~8 min/year, 15 GB box OOMs on 2 concurrent); solves IN-SESSION only
(billed CI). Step 0 fresh container: .venv/bin/python scripts/regenerate_clean.py
(~15 min), confirm data/clean/confirmed-retirements/CAISO/ exists.

DO NOT REDO (caiso-100/101/102 + prior): the +1h frame fix or its gates
(frozen; 2023/24 byte-identity proven); any battery marginal bid adder
(volume-refuted family); the day-threshold hypothesis (CLOSED); the WP-3
steam level or its LOYO (frozen); tightening the caiso-99 envelope;
re-arming caiso_storage_as_reservation; the caiso-94/96/97/99/101
mechanisms or derive gates (frozen); widening caiso-87; more CC commitment
forcing; CT_PEAKER floor; cutting CC offer costs; "fixing" the caiso-95
import comparison by touching import tranches (probe clock artifact —
FINDING-caiso102 s8); any year outside 2023-2025 (rule 22 — no CAISO
calibration-complete marker).

GIT: main advances fast -> git fetch origin main + rebase BEFORE push (expect
the calibration-log append-append conflict; keep BOTH entries; keepers.json
has BOTH a top-level ISO field AND a "keepers" array — update BOTH on any
swap, the array is what audit_keepers/build_status consume). git push WORKS
on this machine class; blob-verify pushed sources >=300 lines by SHA (rule 27).
<<<END>>>
```
