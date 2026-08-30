# FINDING — ercot-236: the h4097 manufactured shed was OFFERS PAST THE CAP, not storage — the SWCAP clip repairs it exactly, and the re-bracketed frontier reaches the C3a-2023 band clean

**Date:** 2026-08-25 · **ISO:** ERCOT · **Authorization:** the ercot-235
promotion addendum's NAMED SUCCESSOR under the owner's standing
2023-DISCRETE-CONFIG charter (rule-16 waiver INVOKED; Q-B/R-A superseded by
the owner for 2023-targeted rounds — cited from the ercot-235 log entry).
· **Charter:** `docs/PRECOMMIT-ercot236-h4097-shed-repair-2026-08-25.md`,
pushed + blob-verified BEFORE any solve; Amendment 1 records the D-0/D-1
verdict before the V-legs ran. · **Prior keeper:**
`2026-08-25-235-2023-discrete-k24` (`results/calibration/ercot235_r10`).

## 1. The diagnosis (D-0/D-1, one solve): H-OFFER confirmed, both rivals refuted

**D-0** — the k=30 point (R8) re-solved at HEAD reproduces its committed
record to the digit: shed set {4097}, 35.948 MWh (R8: 35.95), officials
−9.3 % / 0.119 / 180. Zero HEAD drift.

**D-1** — the h4097 energy-balance A/B (k=30 vs the k=24 keeper,
`ercot236_diag_k30/ercot236_d1_diagnosis.json`):

| component | Δ at h4097 (MW) | reading |
|---|---|---|
| thermal | **−48.28** | supply the k=24 solve dispatched goes UNDISPATCHED while every zone prices exactly $5,000 = VOLL — by LP optimality its offer ≥ $5,000 |
| net storage discharge | **+12.33** | storage discharges MORE, the opposite of the SOC-starvation hypothesis — **H-STORAGE REFUTED** |
| renewables | 0.0 | — |
| total reserve held | 0.0 | **H-RESERVE REFUTED** (a NonSpin→RegUp swap of exactly 35.95 MW nets to zero — reallocation at the cap, not withholding) |

Balance closes exactly: −48.28 + 12.33 = −35.95 = −shed. The zero-solve
prediction had already located the mechanism: the keeper's h4097 energy λ
is $4,770.55, so the marginal offer crosses VOLL at k\* = 24 × 5000/4770.55
= **25.15** — inside the measured onset interval (24, 27] (R10 clean, R11
shed). **The shed was never scarcity: the tuned peak-band multipliers
walked implied offers past the LP's slack cost, making shed economically
optimal against physically-available capacity.**

## 2. The repair: `ercot_offer_swcap_clip` (zero fitted scalars)

The real market caps every SCED energy offer at the system-wide offer cap
($5,000/MWh in the backcast years — the PUCT post-Uri HCAP, equal to VOLL
by the energy-only design; the existing `iso_configs` citation), and firm
load shed is an EEA emergency action, never the economic outcome of a high
offer. The repair gives the model the same offer domain: armed,
`pipeline/solve.py::run_energy_solve` clips the thermal marginal cost at
`voll − ERCOT_SWCAP_SHED_TIEBREAK_EPS` (0.01 $/MWh, the dispatch-before-
shed strict-preference tiebreaker, [R-EPSILON] class) — `mc_base` at entry
and the fully-assembled P1 bid last. Default off, byte-identical off,
ERCOT-gated (rule 25); no window, no hour selection, no h4097 reference —
rule 17 by construction. Unit-tested at trivial scale (1 zone / 24 h: an
over-VOLL offer sheds with the flag off, dispatches with it on).

## 3. The verification legs and the re-bracket (all 2023-only, sequential, kill-gated ex ante)

| point | k_peak | clip | C3a-2023 | C3b | C3c (/181) | shed | max energy λ | kills |
|---|---|---|---|---|---|---|---|---|
| keeper r10 | 24 | — | −13.5 % | 0.186 | 180 | none | 4,770.55 | (incumbent) |
| V-0 | 24 | on | **−13.5 %** | **0.186** | **180** | none | 4,770.55 | clean — **IDENTICAL officials: clip provably inert below the cap** |
| V-1 | 30 | on | **−9.3 %** | **0.119** | 180 | **none** | 4,999.99 | clean — **the killed R8 scores, now shed-free** |
| R-27 | 27 | on | −11.4 % | 0.149 | 180 | none | 4,999.99 | clean (R11's killed scores, now clean) |
| **R-33** | **33** | on | **−7.3 %** | **0.102** | **180** | **none** | 4,999.99 | **clean — WINNER** |

Every clip leg: G-OFFSEASON clean, G-COAL148 +0.099 TWh vs the ercot-234
baseline (bar 0.5; +0.0001 vs the r10 keeper), spur unchanged at 68 banded
/ 74 lidless (the lift saturated at k≈6 and the clip does not move it), and
the D-4 FAIL row identity set exactly the keeper's own (inherited, none
new — the ercot-234 G-D2 standard).

## 4. Selection and the winner

Min |official C3a-2023| over clean candidates {24: 13.5, 27: 11.4, 30: 9.3,
**33: 7.3**} → **k_peak = 33 with the clip armed**, registered as
**`2026-08-25-236-swcap-clip-k33`** (bundle
`results/calibration/ercot236_k33_clip`). **The first ERCOT configuration in
program history to land ALL THREE 2023 price criteria inside their bands:
C3a −7.3 % PASS · C3b 0.102 PASS · C3c 180/181 PASS.** August lands $221.18
vs actual $220.16 (within $1); the ≥$1,000 deep tail is 59 model vs 61
actual hours *[CORRECTED 2026-08-26 by owner authorization, per ercot-237
Amendment 1: this finding originally read "EXACT (59 model vs 59 actual
hours)" — the actual-side 59 was a hardcoded constant in
`ercot235_offer2023_sweep.py`, copied into the ercot-236 scorer, never
computed from data; the true actual count is 61 (77+43+61 = 181 =
`actual_tail.json` rt_gt). No scored criterion moves.]*; the k→C3a
response on the clipped surface is monotone
(−13.5 → −11.4 → −9.3 → −7.3 across 24/27/30/33) and the charter's (24, 33]
bracket ends in the band's interior. Reported structure residual: the
[500, 1000) band under-fills (18 vs 43) while [200, 500) over-fills (103 vs
77) — the shape criterion nonetheless passes at its best-ever 0.102.
At k=33 the clip binds on the top tranches (they saturate at $4,999.99 —
exactly where the measured 2023 asks saturate, the $5k cap), so the tuned
surface now expresses the documented conduct: a scarcity wall AT the cap,
not past it.

## 5. Honest costs and open objects

- k_peak remains the ONE residual-identified scalar (DOF ledger n_residual
  7, unchanged) — re-selected on the repaired surface. The clip adds ZERO
  fitted values (a market constant and an ε-class tiebreaker).
- The 68 banded spurious mid-band hours (vs the pre-235 keeper's 11) are
  unchanged by clip or k — still the blunt-instrument price of the level
  lift, reported. **The ercot-225 G-SPUR band-top gate card is STILL
  AWAITING OWNER SIGN-OFF (since 2026-08-21)** — re-surfaced here; both
  spur forms reported per its draft.
- The in-sample-2023 identification caveat carries forward: no held-out
  validation exists for k_peak under the owner's 2023-discrete charter.
- At the cap the clipped tranches price h4097 at $5,000 — which is what the
  2023 market did in its deepest hours (the measured ask range saturates at
  the $5k cap, ercot-161/162), i.e. the clip converges the surface toward
  measured conduct exactly where the multiplier overshoots it.

## Hygiene

Years = {2023} only (owner waiver, cited); ERCOT-only; solves sequential;
every solve precommitted (charter + Amendment 1 recorded before the V-legs);
kills direction-blind; D-0 run before any repair leg; the winner registered
same-session (rule 15), non-winner points keep committed
`ercot236_point_score.json` (+ the diag's `ercot236_d1_diagnosis.json`)
under `KEEP_REQUIRED_UNMAPPED_BUNDLES`; matrix duties: rule 28(c) row +
all-shard cells landed WITH the field (commit 63750d3), rule 28(b) ERCOT
cell verdict stamped this session; no CI jobs; rule 27 blob-verification on
every ≥300-line push.
