# FINDING miso-131 — the coal-ladder GRANULARITY lane is DEAD at prerequisite 1: infinite granularity moves the gated statistic by ±0.001, and the miso-129 signature does not survive the grain change

Session miso-131, 2026-08-05, branch `claude/miso-131-granularity-screens`,
off `origin/main` at `99948c04`. **NO LP SOLVED. NO ARM BUILT. NO DERIVE RUN.
NO ScenarioConfig FIELD ADDED. NO RUN REGISTERED. KEEPER UNCHANGED** at
`2026-08-04-miso-127-onlinepmin` (NOT-YET, sole FAIL C7 `COAL_PRB` 2025
cv_ratio 0.347 vs 0.5, ledgered caveats 2/3 {C3a, C3c}). Rule 15 is satisfied
by this statement: a no-LP phase produced no run.

**Pre-registration**
`results/calibration/PREREG-miso131-granularity-infinite-bound-2026-08-05.md`,
pushed at `6e3562a4` BEFORE the probe ran, with the expected-kill prior
declared two-sidedly and §0 disclosing every previously-measured number.
**Probe** `scripts/probes/_miso131_granularity_infinite_bound.py`; **record**
`results/calibration/_miso131_granularity_infinite_bound.json`. Rule 22:
2023–2025 only; the probe hard-errors on any other year.

**Session-number note.** The inbound owner handoff carried the label
"miso-130"; that number was already spent by the merged PR #3573 diagnostic
session. This session is miso-131 and executed the handoff's charter — the
miso-129 named-not-chartered granularity object — under its real number.

---

## 1. Verdict

**P1 KILL, on the pre-registered bar, with a validated construction.** The
lane dies at prerequisite 1 with zero solves.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **P0a** census at HEAD | — | — | bit-identical to miso-129 (n=6, 48 plants / 38,144.8 MW, 100 % laddered, step 72.6 MW, median ratio 1.175, 41.4 % share) |
| **P0b** response-model hod-profile r vs payload | **0.999** | **0.997** | **0.997** (bar ≥ 0.90 → PASS) |
| **P0b** payload-frame cv_ratio vs official D-1 | 0.517 / 0.514 | 0.529 / 0.529 | 0.345 / 0.347 (bar ±0.10 → PASS) |
| payload cv_ratio → **n→∞ counterfactual cv_ratio** | 0.517 → **0.518** | 0.529 → **0.530** | 0.345 → **0.344** |
| Δ | **+0.001** | **+0.001** | **−0.001** |

The n→∞ 2025 cv_ratio is **0.344 < 0.50**: infinite granularity cannot reach
the gate even under price-taking, which overstates the equilibrium gain
(cycling coal into the wave softens the wave). P1-secondary does not fire
(2023/24 unharmed). The needed move was `R_dfrac` ×1.447; the best any step
count can deliver is **±0.2 % of the statistic**.

## 2. Why — the signature does not survive the grain change

The kill is not the July freeze route the §0 prior expected (the annual
frozen-band share measures **0.000**: over a full year every PRB econ band is
crossed at some point — the miso-130 freeze statistic is real but
month-scoped). The kill is direct: a 72.6 MW step quantizes each PLANT's
instantaneous response by at most ±half a step, and across ~34 plants whose
ladders sit at different price phases those residuals CANCEL in the class sum.
The C7 statistic is taken on the CLASS hour-of-day mean profile, and at that
grain the 6-step ladder already tracks the continuous limit to 0.997–0.999
profile correlation.

**The generalisable lesson (extends miso-129 §2's "a signature is not a
cause"): A PLANT-GRAIN SIGNATURE IS NOT A CLASS-GRAIN DEFECT.** miso-129's OBS
— "41.4 % of coal capacity has its whole measured diurnal swing inside ONE
step" — is true and irrelevant: quantization that parks individual plants
mid-step aggregates out of the statistic the gate scores. Checking the grain
transfer cost one no-LP reconstruction, and it inverted the lane.

## 3. What this closes and what it does not

* **CLOSED (verdict-grade): `offer_curve_smoothing_n` as a MISO C7 lever.**
  All three miso-129 prerequisites are moot — prerequisite 1 measured FALSE on
  a pre-registered bar with a validated construction. **DO NOT re-open the
  granularity object at MISO without new evidence at the CLASS grain**; a
  per-plant statistic is not such evidence (§2). P2's identification derive
  was never run (gated on P1); no n was chosen, nothing was sized on any Δ
  (KILL-4 honoured).
* **NOT touched:** the ladder's PRICE PLACEMENT (the miso-130 regime
  attribution stands — the 2025 night floor sits above the cheap-PRB majority;
  that is a level/regime question, not a step-count question); the two
  miso-130 successors, which are now the ONLY named-not-chartered items on
  §5.4: **(a) synchronized-reserve online-gating** (`_miso_design` sets no
  `online_gated`; ~1–1.4 GW of spin+reg must be synchronized in the real
  market — the hour-organizing, regime-immune candidate) and **(b) the
  CC_REGULAR committed-band re-grounding** (registered 1.20 vs its own
  measured `avg_committed_p50` 1.005). Neither is licensed by this finding;
  each needs its own prereg.
* The expected-kill prior of §0 is recorded as CONFIRMED IN OUTCOME but
  CORRECTED IN MECHANISM (freeze → aggregation cancellation), per the
  two-sided commitment.

## 4. Rule duties

* **Rule 15** — no run produced (this statement). **Rule 16** — all three
  years in one construction. **Rule 19** — nothing armed, nothing stacked; no
  new field. **Rule 21** — the unidentified-discretization-count DOF question
  is DISSOLVED for MISO: the parameter is inert at the gated grain, so no
  identification is owed. **Rule 22** — 2023–2025 only. **Rule 23** — no
  derive run. **Rule 25** — MISO-scoped; nothing inferred for another ISO
  (the cancellation argument is fleet-size-dependent and does NOT transfer).
* **Rule 28(b)** — stamped in this session: the `offer_curve_by_group` row's
  `offer_curve_smoothing_n` sub-scalar note (MISO: adjudicated inert at class
  grain, this finding) and the §5.4 queue stamp. No cell status changes (the
  row is keeper-armed `K` everywhere; the sub-scalar adjudication is a note).
* **Contamination:** declared in the prereg §0; the adjudicating statistic
  (the n→∞ counterfactual) had never been computed before this session, and
  the construction was validated (P0b) before the verdict was read.
* Next number: **miso-132.**

## 5. Reproduce

```
uv run python scripts/probes/_miso131_granularity_infinite_bound.py
```

No LP, no network; reads the keeper bundle sidecars + payload, the bench, the
F923 monthly-cost parquet, and assembles the fleet at HEAD. ~6 min.
