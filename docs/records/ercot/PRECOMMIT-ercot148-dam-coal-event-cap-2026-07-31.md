# PRECOMMIT — ERCOT-148 Phase 2: `ercot_dam_availability_coal_event_cap` (measured event windows cap the DAM COP restore on coal)

**Date** 2026-07-31 · **ISO** ERCOT · pushed BEFORE the solve (rule-15/ercot145b
protocol). Basis keeper `2026-07-31-ercot145-gas-daily-shape` (bundle
`ercot145_gas_daily_arm`, determination NOT-YET, fail set {C3a, C3b, C3c, C7},
C6 ATTESTED+PASS, n_residual 6). Diagnosis:
`docs/DIAGNOSIS-ercot148-coal-outage-windows-2026-07-31.md`; committed record
`results/calibration/ercot148_coal_outage_phase0.json`; probes
`scripts/probes/ercot148_coal_outage_phase0.py`,
`scripts/probes/ercot148_availability_capture.py`.

## 1. The arm (single delta)

`ercot_dam_availability_coal_event_cap=true` off the keeper recipe — one new
default-off ScenarioConfig gate (cache-key-optional; default key byte-stable at
`8161b094a391de90`; armed key `6593096bbcf0749e`; matrix row added in the same
PR, rule 26c). Semantics: after the DAM COP rescale, every COAL bin's
availability is `min()`-capped at the product of its ARMED measured
event-window factors (≥ 5-day CAMPD unit windows + ERCOT plant-grain partial
plateaus; short/unit-partial layers join the product only when their gates are
armed). The COP pin keeps its remove direction and every non-window hour
untouched. Zero fitted parameters — a precedence rule between two already-armed
measured instruments (rules 14/19). Full span `--year 2023 2024 2025`
(rule 16), bundle `ercot148_dam_event_cap_arm`.

**Seam verification (no LP), done before this push:** 2023 capture flag-OFF
reproduces the keeper's restore (Coleto Jan window cap-weighted availability
0.892 = its COP OFF fraction; LIM1 Feb window 0.729 vs windowed ceiling 0.517;
Sandy COP-OUT window honoured at 0.071); flag-ON capture shows every COAL bin
≤ its event-window ceiling in every hour, gas classes byte-identical, and
coal hours outside windows byte-identical (ceiling 1.0 there).

## 2. Expectation management (owner-directed, verbatim intent)

The lane's object is availability CORRECTNESS (rule 14 — accurate measured
input over a declaration that contradicts the physical record) and the C1
coal over-run; the C3a/C3b/C3c residual stays attributed to RT scarcity
formation (closed lane, ERCOT-144 attribution). The expected side-effect —
removing cheap coal MW in real outage windows (largely shoulder months)
raises shoulder prices — is reported UN-TARGETED: if C3a/C3b improve, that is
rule-14 accuracy, not tuning, and it is never the promotion basis. If correct
windows make any gate WORSE, that is rule-14 territory: keep the accurate
input, open the root cause.

## 3. Ex-ante quantification (measured on the keeper's own artifacts)

Coal dispatch above the measured-window ceiling (the phantom the cap
removes): **4.36 / 4.98 / 5.01 TWh** (2023/24/25). By plant (TWh/yr
2023/24/25): Limestone 1.11/1.12/1.49, W A Parish 1.06/1.28/1.12, J K Spruce
1.14/0.45/0.96, Oak Grove 0.07/0.84/0.76, Coleto 0.40/0.41/0.19, Martin Lake
0.20/0.50/0.25, Sandy Creek 0.27/0.32/0.06, San Miguel/Major Oak/Fayette
≤ 0.12 each.

**Predicted coal class net move: DOWN by 50–100 % of the phantom**
(re-dispatch into other coal is bounded by their own measured ceilings; the
remainder shifts to gas CC and prices). Per-year honest directions against
the keeper's class deltas (model − actual, bench-plants basis):

- 2023 (+2.91 over): |dev| IMPROVES; may cross to a small under.
- 2024 (−0.32): coal level likely goes UNDER by 2–4.5 TWh — **|dev| WORSENS
  on this year's total while the availability becomes correct**. Pre-registered
  as the rule-14 compensating-error unwind: the phantom was masking a real
  under-run elsewhere (Fayette −2.07, Parish −0.84, Martin Lake −1.55 —
  loading conduct, ERCOT-126's 90–93 % LOADING attribution, outside this
  lane). Not a rejection ground; the exposed under-run is the recorded root
  cause to pursue in its own lane.
- 2025 (+4.95 over): |dev| IMPROVES.
- Named plants move toward CAMPD: Limestone (+2.2..+2.7 over vs −1.1..−1.5
  phantom), Coleto (+0.84..+1.27 vs −0.19..−0.41; the remainder is loading
  conduct, stays), J K Spruce 2023 (+1.01 vs −1.14), Oak Grove 2024/25
  (+1.2..+1.4 vs −0.76..−0.84), Sandy Creek 2023 goes from −0.03 to ~−0.3
  (its one COP-dishonest Jan spell unwound — pre-registered honestly).

## 4. Guards (pre-registered against the ERCOT-145b promotion-note baselines)

| guard | baseline (2023/24/25) | rule |
|---|---|---|
| C3c actual->tail hours | 46 / 7 / 0 | NO DRAIN (ERCOT-119 signature 72→49/13→3 is the kill); ±1 threshold-straddling hour adjudicated hour-level per the ercot145b precedent |
| C3c spurious | 2 / 3 / 0 | must stay ≤ 2 / 3 / 0 (±1 straddle adjudicated hour-level) |
| C3a load-weighted | −36.4 / −14.3 / −13.9 % | predict IMPROVE (less negative), un-targeted; any material worsening (> 1 pp) escalates to hour-level attribution before promotion |
| C3b monthly NRMSE | 0.637 / 0.205 / PASS | predict improve-or-held; 2025 stays PASS |
| C1 | 16/16, free 12/12 | HELD. Coal cells may IMPROVE; 2024 coal may cross zero inside the band (pre-registered above) — the min(2 % load, 8 TWh)/3 pp bands hold in the worst case (max PRB swing ≈ −5.4 TWh, −1.2 pp) |
| C2 | PASS | HELD (same per-class roll-up bands) |
| C7-2024/25 COAL_LIGNITE | both legs PASS | HELD (the cap moves level in windowed days, not the diurnal profile; hard kill if either leg fails) |
| C4/C8 | PASS | HELD (no floor touched, no forced share added) |
| n_residual | 6 | MUST NOT RISE (zero fitted parameters added) |
| C6 | ATTESTED+PASS | governance block copied to the new bundle and attested honestly BEFORE the verdict run |

**LOYO:** zero fitted parameters (the cap has no level to fit — it is a
precedence rule between two committed measured artifacts) ⇒ structurally
LOYO-exempt, per-year guard table standing in (the ERCOT-145b precedent,
stated explicitly per the directive).

**Decision rule:** keeper-or-rejected on the guard table + the owner's
in-session standard ("structural integrity outranks gate regression",
re-affirmed by the owner mid-session 2026-07-31). Registered on the dashboard
either way, matrix cell + calibration log same session (rules 15/26b).

## 5. Open owner rulings carried (surfaced, not decided)

(1) `gas_hh_monthly_shape` matrix row (26c); (2) per-gate dispositions of the
attributed gates; (3) `split_coal_tranches` delete-vs-inert;
(4) `ercot_offer_hrmult_ep_rebasis/_bands` matrix rows (26c); (5) Martin Lake
lignite class composition (ercot143 §7.3 + ERCOT-146/147 evidence);
(6) authorization for the ERCOT-147 three-part CT reopen intake (matrix §5.1
item 8). NEW from this lane: (7) the gas-side symmetric COP-vs-window
collision (diagnosis §6.1, unmeasured); (8) the DAM deriver rating-basis gap
for all-year-OUT sites (diagnosis §6.2).
