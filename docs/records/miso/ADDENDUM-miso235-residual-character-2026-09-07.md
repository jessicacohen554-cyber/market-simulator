# ADDENDUM miso-235 — one supplementary measurement, declared BEFORE it is computed

Extends `PREREG-miso235-manitoba-seam-and-the-sigma-question-2026-09-07.md`. Pushed **before the
numbers it governs**, on the miso-233 addendum pattern. **No pre-registered decision rule is
touched and no pre-registered verdict can move** — the PREREG's Q1/Q2/Q3 values are already
computed, committed and published in
`results/calibration/_miso235_seam_variance_decomposition_phase0.json`, and they stand exactly
as measured whatever this addendum finds.

## Why a supplementary measurement is needed

The PREREG's §3 OLS regresses **both** the measured seam flow and the model's reconstructed seam
flow on the **measured** price signal (Indiana hub DA, spread against the neighbour where the
seam has a neighbour anchor). That is the right apples-to-apples comparison and it is what the
pre-registered classification runs on.

It also has a known blind spot, which is named here rather than after the fact: **the model's
bands do not clear on the measured price — they clear on the model's own solved bus price.**
Variation the model's flow inherits from the *difference between those two prices* therefore
lands in the OLS **residual** and is counted as "non-price variation" when it is nothing of the
kind. For a seam whose pre-registered row reads `NEITHER` — PJM in all three years — that blind
spot is the difference between "the model's PJM seam behaves like the real one" and "the model's
PJM seam is entirely price-driven on a price the regressor cannot see".

## S — the measurement, fixed here

Per seam and year, on the same committed artifacts and the same `ok` hour mask:

* **S-1** `corr(r, P)` for the model residual and the measured residual, where `r` is the PREREG
  §3 OLS residual and `P` is the **Indiana-hub RT** price (the scored basis).
* **S-2** `R^2` of each side's flow on **its own native driver**: the model's flow on the
  **model's own clearing spread** (`model bus price − PJM border` / `− SPP NORTH hub DA` for the
  neighbour-anchored seams; the model bus price as a level for South and Manitoba, which clear on
  the fixed Q-Q ladder), and the measured flow on the measured spread (the PREREG's `r2_measured`,
  restated).
* **S-3** the share of each seam's model sigma explained by the model's own clearing spread.

## Interpretation rule, fixed ex ante

A seam's pre-registered `NEITHER` is **QUALIFIED as a PRICE-COHERENT RESIDUAL** iff, in **every**
year:

* `|corr(r_model, P)| >= 2 x |corr(r_measured, P)|`, **and**
* `R^2(model flow on the model's own clearing spread) >= 0.90` while
  `R^2(measured flow on the measured spread) <= 0.60`.

If the qualification fires, the honest reading of that seam is that **the residual leg of the
PREREG's split is UNDERSTATED for the model side** and the seam's flow is price-driven end to
end, on a price basis the measured regressor cannot see. If it does not fire, the pre-registered
`NEITHER` stands unqualified and this addendum reports the numbers and claims nothing.

**Neither branch changes a verdict, arms a mechanism, or licenses a lever.** In particular
nothing here can license a damping factor on the PJM `delta_k` ladder, which is derived, frozen
and pinned to its derive by test (rule 23 `[R-FROZEN-DERIVE]`); a factor swept against this
residual remains the rule 1 `[R-STRUCT]` fitted mechanism the handoff forbids.

Deliverable: `scripts/probes/_miso235_residual_character_addendum.py` →
`results/calibration/_miso235_residual_character_addendum.json`.
