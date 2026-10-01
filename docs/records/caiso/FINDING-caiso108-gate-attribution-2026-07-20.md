# FINDING (caiso-108, P0 GATE ATTRIBUTION): the three gates that hold the CAISO keeper at NOT-YET — C3c (scarcity tail), C4 (gas hourly corr), C5a (CO2, load-bearing) — are ALL driven by ONE root: the model over-imports 6–10 TWh/yr and under-dispatches gas 5–14 TWh/yr. They are a net-import VOLUME defect, NOT the evening/belly hourly PRICE ladder residual four sessions have chased — and that ladder residual anyway lives inside C3a (mean LMP) and C3b (shape), both of which PASS. The chartered P1 (evening firm-rung PRICE reprice, gated on the evening residual) would not flip any failing gate. STOP the intertie-reprice lane; re-charter onto the import/gas substitution VOLUME defect, scored on C5a/C4/C3c.

**Session 2026-07-20 (CAISO-108 — P0 gate attribution, no solve, no
mechanism armed, keeper `2026-07-19-caiso-102-hourfix` UNCHANGED). This is the
P0 finding the charter required BEFORE any P1 intertie build. The P1 condition
("only if C3c/C4/C5a are shown to be intertie/ladder-driven") is NOT met — the
failing gates are import-VOLUME-driven — so P1 as chartered is not executed.**

## 0. What P0 was asked to settle

The charter (caiso-108) suspected the caiso-104/105/106/107 "measure→refute→
re-charter, keeper UNCHANGED" loop was circling because the intertie lane may
not be what actually gates the keeper. P0: locate the C-gate scorer, read the
definition + current driver of each failing gate (C3c, C4, C5a-2024), and answer
explicitly — **is each failing gate driven by the evening/belly hourly price
residual, or by something else?** If not the intertie residual → STOP the
intertie lane and re-charter.

## 1. The failing gates (scored from committed artifacts, `scripts/calibration_verdict.py --run-id 2026-07-19-caiso-102-hourfix`)

Determination: **NOT-YET**. FAIL criteria: `price_tail` (C3c), `dispatch_corr`
(C4), `co2` (C5a).

| gate | tier | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| **C3c** scarcity tail >$200, RT-gated | SUPPORT | 19h vs 47h (0.40×) **FAIL** | 0h vs 35h (0.00×) **FAIL** | 0h vs 8h (small-count PASS) |
| **C4** gas fleet hourly r / NRMSE (CEMS basis) | SUPPORT | r 0.836 / NRMSE 0.333 **FAIL** | pass | pass |
| **C5a** CO2 vs eGRID | **LOAD** | −11.1% **FAIL** | −9.1% CAVEAT | −12.1% **FAIL** |

C5a is the only **load-bearing** (TIER_LOAD) FAIL — a keeper cannot pass without
it. C3c and C4 are TIER_SUPPORT.

## 2. The ONE root cause under all three — an import/gas VOLUME substitution error

Decoded from the keeper's committed run payload (`fuelRows`, `co2`, `ordc`):

| year | gas model / actual (TWh) | gas Δ | net interchange model / actual (TWh) | over-import Δ | CO2 result | C3c |
|---|---|---|---|---|---|---|
| 2023 | 60.57 / 74.23 | **−13.66** | −37.15 / −28.87 | **+8.28 import** | −11.1% | 19 vs 47 |
| 2024 | 54.43 / 61.04 | **−6.61** | −42.03 / −32.38 | **+9.65 import** | −9.1% | 0 vs 35 |
| 2025 | 46.20 / 51.60 | **−5.40** | −42.51 / −36.16 | **+6.35 import** | −12.1% | 0 vs 8 |

(interchange more-negative = more net import.) Every year the model **imports
6–10 TWh more than actual and dispatches 5–14 TWh less gas than actual** — a
near 1:1 substitution. The causal chain that closes all three gates:

- **C5a CO2 (−11 to −12%)** is a pure VOLUME artifact of this substitution.
  Imports carry **zero** CO2 in the model; gas carries the emissions. Replace
  ~7 TWh of gas with ~7 TWh of imports and CO2 falls ~11%. Arithmetic check:
  model CO2 27.0 at 60.57 TWh gas; scaled to the actual 74.23 TWh gas →
  27.0 × 74.23/60.57 ≈ **33.1**, i.e. **+9%**, landing on the actual (≈30.4).
  Closing the gas gap closes the CO2 gap. **C5a is a gas-volume problem, not a
  rate problem.**
- **C4 gas hourly fit** fails on NRMSE (level), not r: r = 0.836/0.907/0.871
  (shape ~right) with NRMSE 0.333/0.274/0.304 (level systematically LOW). High-r
  / low-level is the signature of a *uniform* under-dispatch (imports undercut
  gas across many hours), not peak clipping — consistent with economic
  substitution, not capacity saturation.
- **C3c scarcity tail** is under-formed (0h vs 35h in 2024): the model imports
  cheap firm power into the tight hours, capping peak λ below the $200 scarcity
  band and erasing the tail. Same over-import root, plus scarcity-adder / peak-λ
  formation.

## 3. The evening/belly PRICE ladder residual the last four sessions chased lives in PASSING gates

C3a (mean LMP) and C3b (price duration/shape) both **PASS**. The chased ladder —
belly +6.0/+6.6/+4.3, evening −5.8/−4.9/−1.1 $/MWh — is a *shape wiggle whose
belly-over and evening-under roughly cancel in the mean*, so C3a passes; C3b
(shape) passes too. **The ±5–6 $/MWh ladder residual is not a keeper blocker.**
caiso-104/105/106/107 spent four sessions tuning a residual inside gates that
already pass, while the actual blockers (C3c/C4/C5a) are downstream of the
import-volume defect. This is the circling the charter suspected.

## 4. Why the chartered P1 (evening firm-rung PRICE reprice) would NOT flip any failing gate

The chartered P1 reprices the marginal firm-import rung from the static
$28/$48 contract cost to the live endogenous WECC hub dual, **gated on the
evening residual moving toward 0**. Two independent reasons it does not help the
keeper:

1. **It is a PRICE change; the blockers are VOLUME.** The charter's own P1 guard
   states "a price change forces nothing" (C8 unaffected). By the same token a
   reprice recovers the ~7 TWh/yr of missing gas only insofar as it makes the
   firm rung shed import MWh — and only in the hours where the reprice raises the
   firm price. In the **belly** (where caiso-106 located the +2.6 GW over-import
   that dominates the annual 6–10 TWh) the live WECC hub is LOW/negative, so
   repricing the firm rung "to the live hub" leaves it **cheap midday → belly
   over-import unchanged → CO2 unchanged.** The reprice raises the firm price
   only in the tight EVENING, a small slice of the annual over-import.
2. **The evening residual is in a PASSING gate.** Even a perfectly-successful
   evening reprice that zeroes the −5 $/MWh evening residual improves C3a/C3b
   (already passing) and adds at most a few C3c hours (SUPPORT) — while leaving
   **C5a (LOAD) and C4 failing**, because those are set by the belly/annual
   import VOLUME the evening reprice does not touch.

Pre-registering "evening resid → 0" as the P1 PRIMARY gate (as the charter draft
does) would therefore reproduce the loop exactly: solve, watch evening move a
little, keeper STILL NOT-YET because CO2/gas/tail did not move.

## 5. Verdict + re-charter

**P0 verdict:** the failing gates are **NOT the evening/belly price residual.**
They are one **net-import VOLUME / gas-substitution defect** (over-import 6–10
TWh, under-gas 5–14 TWh, every year). Per the charter's P0 branch, the
intertie **PRICE-reprice** lane (chartered P1) is **STOPPED** — its condition
(gates are ladder-driven) is false, and it would not flip a failing gate.

**Re-charter target (caiso-109):** the import/gas substitution itself — *why does
the model prefer 6–10 TWh of imports over CA gas every year?* Score any candidate
directly on the gates it must move: **C5a CO2, C4 gas TWh/NRMSE, C3c scarcity
tail** — NOT the ±5 $/MWh evening ladder. The lever family is still plausibly the
firm-import supply curve (caiso-103 §6: static $28/$48 firm blocks are structurally
too cheap/too available and undercut CA gas), but as a **VOLUME/availability**
lever validated on CO2 and gas-TWh, with a **specific hypothesis to measure first
(derive-first, rule 1):** is the gas under-dispatch economic (imports underprice
gas — check the marginal-hour import-vs-gas offer stack) or physical (gas fleet
capacity/availability too low — check whether gas ever clips its ceiling in the
under-dispatched hours)? The high-r/low-level C4 signature points economic, but
that is the re-charter's first measurement, not P0's conclusion.

**DO-NOT-REDO carried forward:** the evening RT-over-hub premium (caiso-107 L1);
the belly depth on hub level / hub−CA basis (caiso-107 L2); the evening volume
ceiling (caiso-106); all storage-charge families; any fitted throttle/haircut/
adder. ADD: the evening firm-rung PRICE reprice gated on the evening residual
(this finding) — it targets a passing gate and cannot move the load-bearing C5a.

## 6. Session artifacts

- No solve, no bundle, no mechanism, nothing registered. Keeper
  `2026-07-19-caiso-102-hourfix` UNCHANGED.
- Attribution reproduces from committed artifacts only:
  `scripts/calibration_verdict.py --run-id 2026-07-19-caiso-102-hourfix` (the
  verdict + FAIL set) and the payload decode in §2 (gas/interchange/CO2 per year,
  `scripts.lib.backcast_artifacts.decode_run_js`). No new probe needed — the
  numbers are in the keeper's own run payload.
