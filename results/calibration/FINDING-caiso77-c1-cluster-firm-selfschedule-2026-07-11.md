# FINDING — C1 CC-over/CT-under cluster: the belly/evening probe's "evening CC gap" was non-CAISO contamination (16.6–18.5 TWh/yr of LADWP/SMUD/TID CC in its actual side); same-fleet the model CC is OVER in every block and the counterpart is the price-gated contracted import base — probe caiso-77 self-schedules the firm blocks (2026-07-11)

**STEP-0 decomposition for the caiso-76 session Task 1** (the C1 CC-over/CT-under
cluster, CC_REGULAR +5.05/+7.04 TWh over with CT_PEAKER −3.1/−4.1 TWh under in
2023/24). Model side throughout: the committed caiso-76 keeper payload
(`2026-07-11-caiso-76-hydro-budget`, decoded via the scorers' own
`legitimacy_diagnostics.load_payload_plants` / `load_bench`). Actual side:
CAMPD CA unit-level gross load, SAME-FLEET (restricted to the bench plant set —
see §1). CAMPD 2025 verified complete (12 months, 108 facilities, 63.5 TWh CA
gross).

## 1. The belly/evening ledger was contaminated — the evening-CC design premise is DEAD

`scripts/caiso_belly_commitment_probe.py`'s actual side routed the whole CAMPD
**CA state** extract through `eia923_dominant_class_by_plant` (not
ISO-filtered), so it counted 16.64 / 18.48 / 16.69 TWh (2023/24/25) of
**non-CAISO** California CC as CAISO actual — LADWP Haynes, Scattergood,
Valley; SMUD Cosumnes; Calpine Sutter (BANC); TID Walnut; Burbank Magnolia;
IID El Centro; Roseville; Redding — ≈1.9–2.1 GW of phantom "actual" online CC
in every hour block. Every committed number derived from that probe (the
seam-tz FINDING §4.3 belly attribution, the belly-commitment-probe handoff,
the evening-CC design doc's motivating +1.9/+1.2/+0.3 GW evening gap, and the
caiso-76 FINDING §1 re-measure) carries the artifact.

Corrected (probe fixed 2026-07-11 to restrict its actual to the bench fleet),
on the caiso-76 keeper payload — model / actual / actual−model, GW online:

| year | belly h9-15 | evening h18-21 |
|---|---|---|
| 2023 | 5.2 / 4.7 / **−0.5** | 9.1 / 8.5 / **−0.6** |
| 2024 | 5.0 / 4.1 / **−0.8** | 8.9 / 7.6 / **−1.3** |
| 2025 | 4.9 / 3.4 / **−1.5** | 7.7 / 6.3 / **−1.4** |

Same-fleet, the model gas-CC is **over-committed in the belly AND the
evening**, every year. There is no evening CC deficit to floor:
`docs/handoffs/caiso-evening-cc-commitment-design-2026-07.md` §0's gate
measurement was an artifact and the mechanism is **permanently not built** (a
floor that adds evening CC energy would push the wrong direction in every
year). The doc carries a matching tombstone note.

## 2. Same-fleet decomposition: CC over everywhere off-peak, CT under in the ramps

Model vs CAMPD, SAME plant set both sides (bench-covered CAISO fleet;
CAMPD gross — net-vs-gross ≈3-5 % overstates the actual, so the model-over
deltas below are conservative):

| year | CC_REGULAR (TWh m/a/Δ) | overnight h0-6 GW (m/a) | evening h18-21 GW (m/a) | CT_PEAKER (TWh m/a/Δ) |
|---|---|---|---|---|
| 2023 | 56.75 / 50.53 / **+6.22** | 7.1 / 6.2 | 8.2 / 7.6 | 1.07 / 3.10 / **−2.02** |
| 2024 | 56.93 / 45.75 / **+11.18** | 7.4 / 5.8 | 8.2 / 6.8 | 0.87 / 3.30 / **−2.43** |
| 2025 | 52.22 / 37.91 / **+14.32** | 6.9 / 5.1 | 7.1 / 5.6 | 0.41 / 1.19 / **−0.78** |

- The CC excess concentrates **overnight and the summer morning shoulder**
  (2024 Jun-Sep h0-11 runs +2.2 to +4.1 GW over) — reality cycles its CC fleet
  down every night, the model runs it flat. D-2 attribution: the RA bridge
  forces only 2.38/2.26/1.73 TWh (3.0-3.8 % of class) — the flatness is
  **economic dispatch**, i.e. a supply-stack input error, not forcing.
- CT_PEAKER under-runs exactly the **evening ramp** (−0.8..−1.4 GW h17-20
  summer) and **winter mornings** (−0.4..−0.5 GW h5-7): the intra-gas swap the
  session task hypothesized is real — the model serves CT's ramp energy with
  CC that never cycled off, and the rest with the price-gated seam (below).
- The cluster GROWS with solar/storage build-out (2023→2025), the signature of
  a mechanism error that scales with the duck curve, not a data-vintage issue.
- Cross-basis note (feeds Task 3): 2025 same-fleet CC is +14.3 TWh over while
  the C2 family gate scores 2025 gas −4.1 % UNDER — the family actual's
  non-CEMS residual balloons −5 → −8 → −17 TWh across 2023→25, so the
  930-family 2025 actual and same-year CEMS are mutually inconsistent; the C2
  2025 basis is under bench-intake investigation (session Task 2/3), and the
  CEMS same-fleet direction is the structural truth for the CC class.

## 3. The counterpart: the contracted overnight/evening import base is price-gated out

Measured CISO corridor net imports run a **5.3-6.3 GW near-flat overnight
plateau** collapsing to 0.2-1.3 GW midday (all years, model-clock; the
caiso-73 loader's own numbers). The model's firm blocks carry the measured
shape and the published DMM RA level (caiso-73) but are PRICED at the two G-26
static-fitted Tier-3 contract-cost proxies (PNW_hydro_base $28,
DSW_solar_PV $48 + wheel): any hour the model LMP sits below the proxy the LP
leaves the contracted base untaken and serves the load with flat CC — the
caiso-73 FINDING measured the result (−0.6..−2.3 GW overnight/evening import
deficit; "the LP fills only ~+0.6 GW of the +1.5 GW evening capability it was
offered"), and gap-register G-15(b) names it: *border price + wheel + CARB
wedge structurally deletes the revealed 4.3-5.9 GW self-scheduled base*.

In the real market these blocks are **self-scheduled or bid at/below $0/MWh**
(CPUC D.20-06-028 RA import must-offer; the `CAISO_FIRM_IMPORT_TRANCHES`
comment block has documented exactly this since LEVER B) — they flow
independent of the hourly spot spread. The model's own Manitoba (MISO) and
HQ/Ontario (NYISO) firm imports are already must-flow floors for the same
reason (`inject_miso_firm_imports` / `inject_nyiso_firm_imports`,
`MECH_FIRM_IMPORT`).

## 4. Probe caiso-77 (pre-registered before solving)

Single delta on the caiso-76 keeper recipe: **`caiso_firm_import_selfschedule
=True`** (`scripts/probes/_caiso77_firm_selfschedule_ab.py`, main +
zero-forcing ablation twin, 2023-2025 one bundle). The firm tranches' hourly
`min_gen` is floored at their FULL shaped capability (pmax × availability —
the published DMM RA-import × MIC-split level × the measured unit-mean
revealed-base shape, eford preserved), `MECH_FIRM_IMPORT` attribution
(a contract: ablation-kept, D-2 exempt by construction). **Zero new free
parameters** — level and shape are the keeper's existing measured inputs; the
change removes the influence of the two static-fitted firm prices from
dispatch (at pmin = pmax they can never set the margin — pure inframarginal
bookkeeping). Rule-17 declaration: driver = RA/LTC must-offer + the DMM
revealed self-scheduled base; window = the measured (month × hod) median
self-schedule itself (midday the base collapses on its own); forward story =
DMM forward ladder × pooled climatology shape.

Directions, called before the solve:

- **2023/24 (the target)**: overnight/evening imports rise toward the measured
  base; CC_REGULAR falls toward the C1 band (+5.05/+7.04 TWh → down); C4 gas r
  rises; C7 CT profile_r (0.8 gate) holds; C8 holds (the floor is on import
  pseudo-units, exempt).
- **CT_PEAKER**: flat-to-slightly-up (the caiso-70 bridge-crowding channel is
  untouched; the caiso-73 precedent — imports took the flat CT plateau, not
  the ramp — says the CT volume gap stays open as lead (c)).
- **2025**: CC_REGULAR falls toward the CEMS truth (+14.3 over). DISCLOSED:
  the C2 family metric (currently −4.1 % CAVEAT) may print FURTHER negative on
  the current bench basis — §2's cross-basis note says that basis is itself
  inconsistent with same-year CEMS for 2025 and is under bench-intake rework
  (Task 2/3); per rules 1/14 the measured mechanism stays in regardless, and a
  C2-2025 regression on a suspect basis is adjudicated against the CEMS
  same-fleet evidence, not auto-promoted/auto-rejected on the gate sign.
- **Annual imports** (model already over measured: 33.8/28.5, 32.2/30.8,
  38.5/35.9): the floor adds overnight/evening take while midday firm
  capability stays at the measured shape's own collapse; net annual import
  movement is AMBIGUOUS (disclosed) — the corridor ATC envelopes and the MIC
  simultaneous-import cap still bound delivered flow.
- **C3a body**: overnight λ eases as the must-flow base backs CC down the
  merit; direction called, magnitude emergent.

Promotion bar (vs the caiso-76 keeper's v2.4 scores): C6+C7+C8 PASS, no gate
regressed with C2-2025's CAVEAT as the floor (subject to the §2 basis
adjudication), and the targeted C1 2023/24 cluster improved. LOYO exemption
claimed per the caiso-76 precedent: nothing is fit — the delta is a behavioral
correction on existing measured inputs with zero tunable parameters (the
mechanism is identical in all years by construction); noted for owner review.

## 5. Result (2026-07-12): every pre-registered direction confirmed — PROMOTED

Solved 2023-2025 (main + zero-forcing ablation twin) on CI. Provenance: the
original `caiso77-solve-register` runner (29170225341) solved both bundles
clean and then lost the outputs at its publish step (runner token may not
push a ref whose new commits touch `.github/workflows/*` — the PR #2037
auto-merge race); re-solved identically on `caiso77-solve-register-v2`
(29182026361, Data-API-only publish). Registered
`2026-07-12-caiso-77-firm-selfschedule` (+ `-ablation`).

Scored A/B vs the caiso-76 keeper (rubric v2.4):

| gate | caiso-76 | caiso-77 | pre-registered direction |
|---|---|---|---|
| C1 CC_REGULAR 2023 | +5.05 TWh FAIL | +4.50 TWh FAIL | ✓ down |
| C1 CC_REGULAR 2024 | +7.04 TWh FAIL | **in band — clears** | ✓ down |
| C2 gas 2025 (930 family) | −4.1 % CAVEAT | −7.6 % FAIL | disclosed (§4), adjudicated below |
| C3a mean LMP | +22.2/+32.1/+40.7 % | +21.8/+29.9/+38.2 % | ✓ overnight λ eases |
| C3b NRMSE | 0.308/0.427/0.434 | 0.307/0.408/0.413 | ✓ |
| C3c tail | 458 h / 0 h | 458 h / 0 h | unchanged |
| C4 gas r (2024/25) | 0.805 / 0.576 | 0.834 / 0.590 | ✓ rises (still FAIL) |
| C5a CO₂ (2024/25) | +17.9 / +32.7 % | +11.8 / +28.3 % | ✓ (still FAIL) |
| C6/C7/C8 | PASS | PASS | ✓ hold |

CT_PEAKER volumes byte-flat (−2.02/−2.47/−0.78 TWh same-fleet) — the
bridge-crowding channel untouched as called; lead (c) stays open.

**§2 basis adjudication (the C2-2025 print).** Same-fleet (bench-restricted
CAMPD, the §2 construction) CC_REGULAR excess, model − actual TWh:

| year | caiso-76 | caiso-77 |
|---|---|---|
| 2023 | +6.22 | **+5.74** |
| 2024 | +11.11 | **+7.58** |
| 2025 | +14.32 | **+12.32** |

Corrected belly/evening online gaps (§1 probe, actual−model GW): 2023
−0.5/−0.6 → −0.5/−0.5, 2024 −0.8/−1.3 → −0.5/−1.0, 2025 −1.5/−1.4 →
−1.3/−1.1. Every year moves toward the CEMS truth — 2025 included, where the
930-family gate prints further under. Per the §4 subject-to clause the
C2-2025 print is adjudicated a bench-basis artifact (the family actual's
non-CEMS residual balloons −5 → −8 → −17 TWh across 2023→25, mutually
inconsistent with same-year CEMS; rework filed, caiso-76 FINDING §4), NOT a
mechanism regression.

**Promotion bar: MET** — C6+C7+C8 PASS; no gate regressed under the
adjudication; the targeted C1 2023/24 cluster improved with 2024 clearing.
Promoted to CAISO keeper 2026-07-12 (v2.4 determination stays NOT-YET). The
LOYO exemption (§4) remains flagged for owner review.

**Post-merge rescore note (2026-07-12, branch port):** re-scored on main's
G-21b bench (CEMS-anchored C2 preliminary-vintage fallback, commit 50dbb54):
the CAISO C2-2025 print is unchanged (−7.6 %), caiso-76's rows are unchanged,
and the caiso-77 C1-2023 row nudges +4.54 → +4.50 TWh (bench-content only).
The §5 verdict and the promotion bar evaluation are unaffected.
